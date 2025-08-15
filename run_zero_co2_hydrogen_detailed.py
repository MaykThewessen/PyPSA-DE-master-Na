#!/usr/bin/env python3
"""
Run PyPSA with ZERO CO2 emissions for FULL YEAR with detailed hydrogen system
Separates hydrogen into electrolyser, storage tank, and fuel cell/power plant
"""

import os
import sys
import warnings
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Suppress warnings
warnings.filterwarnings('ignore')

# Set PROJ environment variables
os.environ['PROJ_LIB'] = r'C:\ProgramData\miniforge3\envs\pypsa-de\Library\share\proj'
os.environ['PROJ_DATA'] = r'C:\ProgramData\miniforge3\envs\pypsa-de\Library\share\proj'
os.environ['PYPROJ_GLOBAL_CONTEXT'] = '1'

def run_zero_co2_hydrogen_detailed():
    """Run full year scenario with detailed hydrogen system"""
    
    print("=" * 80)
    print("PyPSA ZERO CO2 - FULL YEAR with Detailed Hydrogen System")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        import pypsa
        print(f"✓ PyPSA version: {pypsa.__version__}")
        
        # Create network
        print("\nCreating full-year 100% renewable network...")
        n = create_full_year_network()
        
        # Add all storage technologies including detailed hydrogen
        print("\n" + "=" * 60)
        print("Adding Storage Technologies with Detailed Hydrogen")
        print("=" * 60)
        add_storage_with_detailed_hydrogen(n)
        
        # Add ZERO CO2 constraint
        print("\n" + "=" * 60)
        print("Setting ZERO CO2 Constraint")
        print("=" * 60)
        add_zero_co2_constraint(n)
        
        # Run optimization
        print("\n" + "=" * 60)
        print("Running Full Year Optimization")
        print("=" * 60)
        
        start_time = datetime.now()
        
        status = n.optimize(
            solver_name='highs',
            solver_options={
                'time_limit': 7200,  # 2 hours max
                'mip_rel_gap': 0.001,
                'presolve': 'on',
                'parallel': 'on',
                'threads': 8
            },
            log_to_console=True
        )
        
        solve_time = (datetime.now() - start_time).total_seconds()
        print(f"\nOptimization completed in {solve_time:.1f} seconds")
        print(f"Optimization status: {status}")
        
        # Analyze results
        if (isinstance(status, str) and status == 'ok') or \
           (isinstance(status, tuple) and status[0] == 'ok'):
            analyze_detailed_results(n)
            save_detailed_results(n)
        else:
            print(f"⚠ Optimization failed with status: {status}")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def create_full_year_network():
    """Create network with full year of data and seasonal variations"""
    import pypsa
    
    n = pypsa.Network()
    
    # Full year simulation - 8760 hours
    hours = 8760
    n.set_snapshots(pd.date_range('2023-01-01', periods=hours, freq='h'))
    
    # Main electricity bus
    n.add("Bus", "electricity", v_nom=380, carrier="AC")
    
    # Add hydrogen bus for the hydrogen system
    n.add("Bus", "hydrogen", carrier="hydrogen")
    
    # Load profile with seasonal variation
    np.random.seed(42)
    hours_array = np.arange(hours)
    day_of_year = hours_array // 24
    hour_of_day = hours_array % 24
    
    # Base load with seasonal pattern (45-55 GW)
    seasonal_factor = 1 + 0.2 * np.cos(2 * np.pi * day_of_year / 365)  # Higher in winter
    
    # Daily pattern
    daily_pattern = np.array([0.7, 0.65, 0.6, 0.58, 0.6, 0.65,  # Night
                              0.75, 0.85, 0.95, 1.0, 1.05, 1.1,   # Morning/noon
                              1.1, 1.05, 1.0, 0.95, 0.9, 0.95,    # Afternoon
                              1.0, 0.95, 0.85, 0.8, 0.75, 0.72])  # Evening/night
    
    # Combine seasonal and daily patterns
    load_profile = np.zeros(hours)
    for h in range(hours):
        base_load = 45000 * seasonal_factor[h]  # MW
        load_profile[h] = base_load * daily_pattern[hour_of_day[h]]
    
    # Add some random variation
    load_profile *= (1 + 0.05 * np.random.randn(hours))
    load_profile = np.maximum(load_profile, 20000)  # Minimum 20 GW
    
    n.add("Load", "demand",
          bus="electricity",
          p_set=load_profile)
    
    # Solar profile with strong seasonal variation
    solar_profile = np.zeros(hours)
    for h in range(hours):
        day = day_of_year[h]
        hour = hour_of_day[h]
        
        # Seasonal solar intensity (much lower in winter)
        seasonal_solar = 0.5 + 0.5 * np.cos(2 * np.pi * (day - 172) / 365)  # Peak at summer solstice
        
        # Daily solar pattern
        if 5 <= hour <= 20:
            daily_solar = np.sin((hour - 5) * np.pi / 15)
        else:
            daily_solar = 0
        
        solar_profile[h] = seasonal_solar * daily_solar * (0.8 + 0.2 * np.random.random())
    
    solar_profile = np.maximum(solar_profile, 0)
    
    # Wind profile with inverse seasonal pattern (higher in winter)
    wind_profile = np.zeros(hours)
    for h in range(hours):
        day = day_of_year[h]
        
        # Seasonal wind (stronger in winter)
        seasonal_wind = 0.5 + 0.3 * np.cos(2 * np.pi * day / 365)
        
        # Add variability
        wind_profile[h] = seasonal_wind * (0.3 + 0.7 * np.random.random())
    
    wind_profile = np.clip(wind_profile, 0.05, 1.0)
    
    # Add ONLY renewable generators
    n.add("Generator", "solar",
          bus="electricity",
          p_nom_extendable=True,
          p_nom_max=400000,  # 400 GW max
          capital_cost=25000,  # €25/kW/year
          marginal_cost=0,
          p_max_pu=solar_profile,
          carrier="solar")
    
    n.add("Generator", "wind_onshore",
          bus="electricity",
          p_nom_extendable=True,
          p_nom_max=300000,  # 300 GW max
          capital_cost=45000,  # €45/kW/year
          marginal_cost=0,
          p_max_pu=wind_profile,
          carrier="wind")
    
    # Add offshore wind with different profile
    offshore_wind_profile = wind_profile * 1.2  # Generally higher capacity factor
    offshore_wind_profile = np.clip(offshore_wind_profile, 0.1, 1.0)
    
    n.add("Generator", "wind_offshore",
          bus="electricity",
          p_nom_extendable=True,
          p_nom_max=100000,  # 100 GW max
          capital_cost=65000,  # €65/kW/year - more expensive
          marginal_cost=0,
          p_max_pu=offshore_wind_profile,
          carrier="wind")
    
    # Add carriers
    n.add("Carrier", "solar", co2_emissions=0.0)
    n.add("Carrier", "wind", co2_emissions=0.0)
    n.add("Carrier", "AC")
    n.add("Carrier", "hydrogen")
    
    print(f"Created full-year network with {len(n.snapshots)} hourly snapshots")
    print(f"Load statistics:")
    print(f"  Average: {load_profile.mean():.1f} MW")
    print(f"  Peak (winter): {load_profile.max():.1f} MW")
    print(f"  Minimum (summer): {load_profile.min():.1f} MW")
    print(f"  Total annual demand: {load_profile.sum()/1e6:.1f} TWh")
    print("\nRenewable profiles:")
    print(f"  Solar capacity factor: {solar_profile.mean():.1%}")
    print(f"  Onshore wind capacity factor: {wind_profile.mean():.1%}")
    print(f"  Offshore wind capacity factor: {offshore_wind_profile.mean():.1%}")
    
    return n

def add_storage_with_detailed_hydrogen(n):
    """Add storage technologies with detailed hydrogen system components"""
    
    # First, add hydrogen system components as Links
    print("\n🔵 Hydrogen System Components:")
    print("-" * 80)
    
    # 1. Electrolyser (electricity -> hydrogen)
    electrolyser_capital = 1700000  # €1.7M/MW
    electrolyser_efficiency = 0.70  # 70% efficiency
    
    n.add("Link", "electrolyser",
          bus0="electricity",
          bus1="hydrogen",
          p_nom_extendable=True,
          p_nom_min=0,
          p_nom_max=50000,  # 50 GW max
          capital_cost=electrolyser_capital,  # €/MW
          efficiency=electrolyser_efficiency,
          carrier="electrolyser")
    
    print(f"  Electrolyser:")
    print(f"    Capital cost: €{electrolyser_capital:,}/MW")
    print(f"    Efficiency: {electrolyser_efficiency:.0%}")
    print(f"    Max capacity: 50 GW")
    
    # 2. Hydrogen storage tank (Store on hydrogen bus)
    h2_storage_capital = 5000  # €5,000/MWh
    
    n.add("Store", "H2_storage",
          bus="hydrogen",
          e_nom_extendable=True,
          e_nom_min=0,
          e_nom_max=10000000,  # 10 TWh max
          e_cyclic=True,
          capital_cost=h2_storage_capital,  # €/MWh
          marginal_cost=0.1,
          standing_loss=0.00005,  # Very low losses
          carrier="H2_storage")
    
    print(f"\n  Hydrogen Storage Tank:")
    print(f"    Capital cost: €{h2_storage_capital:,}/MWh")
    print(f"    Max capacity: 10 TWh")
    print(f"    Standing loss: 0.005%/hour")
    
    # 3. Fuel Cell (hydrogen -> electricity)
    fuelcell_capital = 1500000  # €1.5M/MW
    fuelcell_efficiency = 0.58  # 58% efficiency (modern fuel cell)
    
    n.add("Link", "fuel_cell",
          bus0="hydrogen",
          bus1="electricity",
          p_nom_extendable=True,
          p_nom_min=0,
          p_nom_max=50000,  # 50 GW max
          capital_cost=fuelcell_capital,  # €/MW
          efficiency=fuelcell_efficiency,
          carrier="fuel_cell")
    
    print(f"\n  Fuel Cell:")
    print(f"    Capital cost: €{fuelcell_capital:,}/MW")
    print(f"    Efficiency: {fuelcell_efficiency:.0%}")
    print(f"    Max capacity: 50 GW")
    
    # 4. Alternative: H2 Power Plant (if different from fuel cell)
    h2_powerplant_capital = 1000000  # €1M/MW
    h2_powerplant_efficiency = 0.60  # 60% efficiency (H2 turbine)
    
    n.add("Link", "H2_powerplant",
          bus0="hydrogen",
          bus1="electricity",
          p_nom_extendable=True,
          p_nom_min=0,
          p_nom_max=50000,  # 50 GW max
          capital_cost=h2_powerplant_capital,  # €/MW
          efficiency=h2_powerplant_efficiency,
          carrier="H2_powerplant")
    
    print(f"\n  H2 Power Plant (alternative):")
    print(f"    Capital cost: €{h2_powerplant_capital:,}/MW")
    print(f"    Efficiency: {h2_powerplant_efficiency:.0%}")
    print(f"    Max capacity: 50 GW")
    
    # Calculate round-trip efficiency
    h2_roundtrip_fc = electrolyser_efficiency * fuelcell_efficiency
    h2_roundtrip_pp = electrolyser_efficiency * h2_powerplant_efficiency
    
    print(f"\n  Hydrogen Round-trip Efficiencies:")
    print(f"    Via Fuel Cell: {h2_roundtrip_fc:.1%}")
    print(f"    Via H2 Power Plant: {h2_roundtrip_pp:.1%}")
    
    # Now add other storage technologies (battery, etc.)
    print("\n🔋 Other Storage Technologies:")
    print("-" * 80)
    
    storage_techs = {
        "Li-ion NMC": {
            "capital_cost": 140000,      # €140/kWh
            "marginal_cost": 0.1,
            "efficiency_store": np.sqrt(0.92),     # 92% round-trip
            "efficiency_dispatch": np.sqrt(0.92),
            "max_hours": 4,               # 4-hour duration
            "standing_loss": 0.00001,
            "e_nom_max": 1000000,         # 1 TWh max
        },
        "LFP Battery": {
            "capital_cost": 110000,      # €110/kWh
            "marginal_cost": 0.08,
            "efficiency_store": np.sqrt(0.90),     # 90% round-trip
            "efficiency_dispatch": np.sqrt(0.90),
            "max_hours": 8,               # 8-hour duration
            "standing_loss": 0.00001,
            "e_nom_max": 1500000,         # 1.5 TWh max
        },
        "CAES": {
            "capital_cost": 35000,       # €35/kWh
            "marginal_cost": 2,
            "efficiency_store": np.sqrt(0.70),     # 70% round-trip
            "efficiency_dispatch": np.sqrt(0.70),
            "max_hours": 48,              # 48-hour duration
            "standing_loss": 0.0001,
            "e_nom_max": 500000,          # 500 GWh max
        },
        "Iron-Air": {
            "capital_cost": 25000,       # €25/kWh for storage
            "marginal_cost": 0.5,
            "efficiency_store": 1.0,      # 100% charging efficiency
            "efficiency_dispatch": 0.50,  # 50% discharging efficiency
            "max_hours": 100,             # 100-hour duration
            "standing_loss": 0.00001,
            "e_nom_max": 5000000,         # 5 TWh max
            "power_cost": 150000,        # €150/kW for inverter (€150,000/MW)
        },
        "Pumped Hydro": {
            "capital_cost": 55000,       # €55/kWh
            "marginal_cost": 0.2,
            "efficiency_store": np.sqrt(0.80),     # 80% round-trip
            "efficiency_dispatch": np.sqrt(0.80),
            "max_hours": 12,              # 12-hour duration
            "standing_loss": 0.00001,
            "e_nom_max": 200000,          # 200 GWh max
        }
    }
    
    # Print comparison table
    print(f"{'Technology':<15} {'Cost(€/kWh)':<12} {'Efficiency':<12} {'Duration(h)':<15} {'Max(TWh)':<12}")
    print("-" * 70)
    
    for name, params in storage_techs.items():
        efficiency_rt = params['efficiency_store'] * params['efficiency_dispatch']
        print(f"{name:<15} {params['capital_cost']/1000:<12.0f}k "
              f"{efficiency_rt*100:<11.0f}% {params['max_hours']:<15} "
              f"{params['e_nom_max']/1000000:<12.1f}")
    
    # Add each storage technology
    for name, params in storage_techs.items():
        n.add("Store", name,
              bus="electricity",
              e_nom_extendable=True,
              e_nom_min=0,
              e_nom_max=params['e_nom_max'],
              e_cyclic=True,
              capital_cost=params['capital_cost'],
              marginal_cost=params['marginal_cost'],
              standing_loss=params['standing_loss'],
              efficiency_store=params['efficiency_store'],
              efficiency_dispatch=params['efficiency_dispatch'],
              e_initial=0.5,
              max_hours=params['max_hours'],
              carrier=name.lower().replace(' ', '_').replace('-', '_'))
    
    # Add carrier definitions
    n.add("Carrier", "electrolyser")
    n.add("Carrier", "fuel_cell")
    n.add("Carrier", "H2_powerplant")
    n.add("Carrier", "H2_storage")
    for name in storage_techs.keys():
        carrier_name = name.lower().replace(' ', '_').replace('-', '_')
        n.add("Carrier", carrier_name)
    
    print(f"\n✓ Added detailed hydrogen system + {len(storage_techs)} other storage technologies")

def add_zero_co2_constraint(n):
    """Add ZERO CO2 emission constraint"""
    
    max_co2 = 0.0  # ZERO emissions
    
    total_demand = n.loads_t.p_set.sum().sum()
    print(f"Total annual demand: {total_demand/1e6:.1f} TWh")
    print(f"CO2 limit: {max_co2:.0f} tCO2/year (ZERO EMISSIONS)")
    print("⚠️  This is a 100% renewable + storage scenario for full year")
    
    n.add("GlobalConstraint",
          "CO2_limit",
          sense="<=",
          constant=max_co2,
          carrier_attribute="co2_emissions")

def analyze_detailed_results(n):
    """Analyze results with focus on hydrogen system"""
    
    print("\n" + "=" * 100)
    print("FULL YEAR ZERO CO2 RESULTS - DETAILED HYDROGEN SYSTEM")
    print("=" * 100)
    
    # System cost
    total_demand = n.loads_t.p_set.sum().sum()
    print(f"\n💰 Economic Results:")
    print(f"   Total System Cost: €{n.objective:,.0f}")
    print(f"   Cost per MWh: €{n.objective / total_demand:.2f}/MWh")
    print(f"   Annual demand served: {total_demand/1e6:.1f} TWh")
    
    # Generator capacities
    print("\n🌱 Renewable Generation Capacities:")
    print("-" * 60)
    total_capacity = 0
    for gen in n.generators.index:
        capacity = n.generators.at[gen, 'p_nom_opt']
        if capacity > 1:
            total_capacity += capacity
            print(f"  {gen:<20}: {capacity:>12,.0f} MW")
    print(f"  {'TOTAL':<20}: {total_capacity:>12,.0f} MW")
    
    # Hydrogen system deployment
    print("\n🔵 Hydrogen System Deployment:")
    print("-" * 80)
    
    # Electrolyser
    if 'electrolyser' in n.links.index:
        elec_capacity = n.links.at['electrolyser', 'p_nom_opt']
        print(f"  Electrolyser capacity: {elec_capacity:,.0f} MW")
        if 'electrolyser' in n.links_t.p0.columns:
            elec_energy = n.links_t.p0['electrolyser'].sum()
            elec_cf = elec_energy / (elec_capacity * 8760) * 100 if elec_capacity > 0 else 0
            print(f"    Energy consumed: {elec_energy/1e6:.1f} TWh")
            print(f"    Capacity factor: {elec_cf:.1f}%")
    
    # H2 Storage
    if 'H2_storage' in n.stores.index:
        h2_storage = n.stores.at['H2_storage', 'e_nom_opt']
        print(f"\n  H2 Storage capacity: {h2_storage/1000:,.0f} GWh ({h2_storage/1e6:.2f} TWh)")
        if 'H2_storage' in n.stores_t.e.columns:
            h2_soc = n.stores_t.e['H2_storage']
            print(f"    Max state of charge: {h2_soc.max()/1000:,.0f} GWh")
            print(f"    Min state of charge: {h2_soc.min()/1000:,.0f} GWh")
            print(f"    Average SOC: {h2_soc.mean()/1000:,.0f} GWh")
    
    # Fuel Cell
    if 'fuel_cell' in n.links.index:
        fc_capacity = n.links.at['fuel_cell', 'p_nom_opt']
        print(f"\n  Fuel Cell capacity: {fc_capacity:,.0f} MW")
        if 'fuel_cell' in n.links_t.p1.columns:
            fc_energy = n.links_t.p1['fuel_cell'].sum()
            fc_cf = fc_energy / (fc_capacity * 8760) * 100 if fc_capacity > 0 else 0
            print(f"    Energy generated: {fc_energy/1e6:.1f} TWh")
            print(f"    Capacity factor: {fc_cf:.1f}%")
    
    # H2 Power Plant
    if 'H2_powerplant' in n.links.index:
        h2pp_capacity = n.links.at['H2_powerplant', 'p_nom_opt']
        print(f"\n  H2 Power Plant capacity: {h2pp_capacity:,.0f} MW")
        if 'H2_powerplant' in n.links_t.p1.columns:
            h2pp_energy = n.links_t.p1['H2_powerplant'].sum()
            h2pp_cf = h2pp_energy / (h2pp_capacity * 8760) * 100 if h2pp_capacity > 0 else 0
            print(f"    Energy generated: {h2pp_energy/1e6:.1f} TWh")
            print(f"    Capacity factor: {h2pp_cf:.1f}%")
    
    # Other storage deployment
    print("\n🔋 Other Storage Deployment:")
    print("-" * 80)
    print(f"{'Technology':<15} {'Energy(GWh)':<15} {'Power(MW)':<12} {'Cycles/year':<12}")
    print("-" * 80)
    
    for store in n.stores.index:
        if store != 'H2_storage':  # Skip H2 storage as it's shown above
            energy = n.stores.at[store, 'e_nom_opt']
            if energy > 1:
                duration = n.stores.at[store, 'max_hours']
                power = energy / duration if duration > 0 else 0
                
                # Calculate cycles
                if store in n.stores_t.p.columns:
                    discharged = n.stores_t.p[store].clip(lower=0).sum()
                    cycles = discharged / energy if energy > 0 else 0
                else:
                    cycles = 0
                
                print(f"{store:<15} {energy/1000:<15,.0f} {power:<12,.0f} {cycles:<12.1f}")
    
    # Generation mix
    print("\n⚡ Annual Energy Generation Mix:")
    print("-" * 60)
    total_gen = 0
    for gen in n.generators.index:
        if gen in n.generators_t.p.columns:
            gen_energy = n.generators_t.p[gen].sum()
            if gen_energy > 0:
                total_gen += gen_energy
                percentage = (gen_energy / total_demand * 100)
                capacity_factor = gen_energy / (n.generators.at[gen, 'p_nom_opt'] * 8760) * 100 if n.generators.at[gen, 'p_nom_opt'] > 0 else 0
                print(f"  {gen:<20}: {gen_energy/1e6:>8.1f} TWh ({percentage:>5.1f}% of demand, CF: {capacity_factor:.1f}%)")
    
    # Verify zero emissions
    print("\n🌍 CO2 Verification:")
    total_co2 = 0
    for gen in n.generators.index:
        if gen in n.generators_t.p.columns:
            carrier = n.generators.at[gen, 'carrier']
            if carrier in n.carriers.index:
                emissions_rate = n.carriers.at[carrier, 'co2_emissions']
                gen_emissions = n.generators_t.p[gen].sum() * emissions_rate
                total_co2 += gen_emissions
    
    print(f"  Total Annual CO2 Emissions: {total_co2:.0f} tCO2")
    print(f"  ✅ ZERO EMISSIONS ACHIEVED!" if total_co2 == 0 else f"  ⚠️ Non-zero emissions detected!")

def save_detailed_results(n):
    """Save results with hydrogen system details"""
    
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    
    # Save detailed summary
    summary_file = results_dir / f"zero_co2_hydrogen_detailed_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("PYPSA ZERO CO2 - FULL YEAR WITH DETAILED HYDROGEN SYSTEM\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Time horizon: 8760 hours (365 days)\n\n")
        
        total_demand = n.loads_t.p_set.sum().sum()
        
        f.write("SYSTEM OVERVIEW\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total System Cost: €{n.objective:,.0f}\n")
        f.write(f"Cost per MWh: €{n.objective / total_demand:.2f}/MWh\n")
        f.write(f"Total Annual Demand: {total_demand/1e6:.1f} TWh\n")
        f.write(f"CO2 Emissions: 0 tCO2 (ZERO)\n\n")
        
        f.write("HYDROGEN SYSTEM COMPONENTS\n")
        f.write("-" * 40 + "\n")
        if 'electrolyser' in n.links.index:
            f.write(f"Electrolyser: {n.links.at['electrolyser', 'p_nom_opt']:,.0f} MW\n")
        if 'H2_storage' in n.stores.index:
            f.write(f"H2 Storage: {n.stores.at['H2_storage', 'e_nom_opt']/1000:,.0f} GWh\n")
        if 'fuel_cell' in n.links.index:
            f.write(f"Fuel Cell: {n.links.at['fuel_cell', 'p_nom_opt']:,.0f} MW\n")
        if 'H2_powerplant' in n.links.index:
            f.write(f"H2 Power Plant: {n.links.at['H2_powerplant', 'p_nom_opt']:,.0f} MW\n")
        
        f.write("\nRENEWABLE GENERATION CAPACITY\n")
        f.write("-" * 40 + "\n")
        for gen in n.generators.index:
            capacity = n.generators.at[gen, 'p_nom_opt']
            if capacity > 1:
                f.write(f"{gen}: {capacity:,.0f} MW\n")
    
    print(f"\n✅ Results saved to: {summary_file}")
    
    # Try to save network
    try:
        nc_file = results_dir / f"zero_co2_hydrogen_detailed_{timestamp}.nc"
        n.export_to_netcdf(nc_file)
        print(f"✅ Network saved to: {nc_file}")
    except Exception as e:
        print(f"⚠ Could not save network: {e}")

if __name__ == "__main__":
    run_zero_co2_hydrogen_detailed()
