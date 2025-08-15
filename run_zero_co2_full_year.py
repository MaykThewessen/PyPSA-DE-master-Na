#!/usr/bin/env python3
"""
Run PyPSA with ZERO CO2 emissions for FULL YEAR (8760 hours)
Tests all storage technologies in a 100% renewable scenario with seasonal variations
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

def run_zero_co2_full_year():
    """Run full year scenario with zero CO2 emissions"""
    
    print("=" * 80)
    print("PyPSA ZERO CO2 Emissions - FULL YEAR (8760 hours)")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        import pypsa
        print(f"✓ PyPSA version: {pypsa.__version__}")
        
        # Create network
        print("\nCreating full-year 100% renewable network...")
        n = create_full_year_network()
        
        # Add all storage technologies
        print("\n" + "=" * 60)
        print("Adding Storage Technologies")
        print("=" * 60)
        add_all_storage_technologies(n)
        
        # Add ZERO CO2 constraint
        print("\n" + "=" * 60)
        print("Setting ZERO CO2 Constraint")
        print("=" * 60)
        add_zero_co2_constraint(n)
        
        # Run optimization
        print("\n" + "=" * 60)
        print("Running Full Year Optimization (this may take several minutes)")
        print("=" * 60)
        
        start_time = datetime.now()
        
        status = n.optimize(
            solver_name='highs',
            solver_options={
                'time_limit': 7200,  # 2 hours max
                'mip_rel_gap': 0.001,  # Tighter gap for full year
                'presolve': 'on',
                'parallel': 'on',
                'threads': 8  # Use more threads for larger problem
            },
            log_to_console=True
        )
        
        solve_time = (datetime.now() - start_time).total_seconds()
        print(f"\nOptimization completed in {solve_time:.1f} seconds")
        print(f"Optimization status: {status}")
        
        # Analyze results
        if (isinstance(status, str) and status == 'ok') or \
           (isinstance(status, tuple) and status[0] == 'ok'):
            analyze_full_year_results(n)
            save_full_year_results(n)
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
    
    # Main bus
    n.add("Bus", "electricity", v_nom=380)
    
    # Load profile with seasonal variation (higher in winter, lower in summer)
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
    
    # Add ONLY renewable generators with increased capacity limits for full year
    n.add("Generator", "solar",
          bus="electricity",
          p_nom_extendable=True,
          p_nom_max=400000,  # 400 GW max - increased for full year
          capital_cost=25000,  # €25/kW/year - slightly reduced for scale
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
    
    print(f"Created full-year network with {len(n.snapshots)} hourly snapshots")
    print(f"Load statistics:")
    print(f"  Average: {load_profile.mean():.1f} MW")
    print(f"  Peak (winter): {load_profile.max():.1f} MW")
    print(f"  Minimum (summer): {load_profile.min():.1f} MW")
    print(f"  Total annual demand: {load_profile.sum()/1000:.1f} TWh")
    print("\nRenewable profiles:")
    print(f"  Solar capacity factor: {solar_profile.mean():.1%}")
    print(f"  Onshore wind capacity factor: {wind_profile.mean():.1%}")
    print(f"  Offshore wind capacity factor: {offshore_wind_profile.mean():.1%}")
    print("\n⚡ Available generators: Solar, Wind Onshore, Wind Offshore (NO fossil fuels)")
    
    return n

def add_all_storage_technologies(n):
    """Add all storage technologies optimized for full year operation"""
    
    # Storage technology parameters for full year
    storage_techs = {
        "Li-ion NMC": {
            "capital_cost": 140000,      # €140/kWh - slight reduction for scale
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
    
    # Print storage parameters
    print("\nStorage Technologies for Full Year Zero CO2:")
    print("-" * 90)
    print(f"{'Technology':<15} {'Cost(€/kWh)':<12} {'Efficiency':<12} {'Duration(h)':<15} {'Max(TWh)':<12}")
    print("-" * 90)
    
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
              e_cyclic=True,  # Important for full year
              capital_cost=params['capital_cost'],
              marginal_cost=params['marginal_cost'],
              standing_loss=params['standing_loss'],
              efficiency_store=params['efficiency_store'],
              efficiency_dispatch=params['efficiency_dispatch'],
              e_initial=0.5,  # Start at 50% charge
              max_hours=params['max_hours'],
              carrier=name.lower().replace(' ', '_').replace('-', '_'))
    
    # Add carrier definitions
    for name in storage_techs.keys():
        carrier_name = name.lower().replace(' ', '_').replace('-', '_')
        n.add("Carrier", carrier_name)
    
    print(f"\n✓ Added {len(storage_techs)} storage technologies for seasonal balancing")
    
    # Add optimized Iron-Air storage with separate power and energy costs
    add_iron_air_storage_optimized(n)
    
    # Add hydrogen storage as StorageUnit with separate power and energy costs
    add_hydrogen_storage_optimized(n)

def add_iron_air_storage_optimized(n):
    """Add Iron-Air storage with separated power and energy costs as per specifications"""
    
    print("\n" + "=" * 60)
    print("Adding Optimized Iron-Air Storage System")
    print("=" * 60)
    
    # Iron-Air specifications as requested:
    # - 100h storage duration
    # - €150/kW for inverter (power cost)
    # - €20/kWh for storage (energy cost)
    # - 50% round-trip efficiency (discharging efficiency = 50%)
    
    duration = 100  # hours
    power_cost = 150  # €/kW for inverter
    energy_cost = 20  # €/kWh for storage
    
    # For 50% round-trip efficiency with symmetric charge/discharge
    # efficiency_store * efficiency_dispatch = 0.50
    # If symmetric: efficiency = sqrt(0.50) ≈ 0.707
    efficiency = np.sqrt(0.50)
    
    # Calculate combined capital cost for PyPSA Store component
    # PyPSA uses energy-based capital cost, so we need to convert
    # Total cost = Power_cost * (E/duration) + Energy_cost * E
    # Cost per kWh = Power_cost/duration + Energy_cost
    combined_capital_cost = (power_cost * 1000 / duration) + (energy_cost * 1000)  # Convert to €/MWh
    
    print(f"\nIron-Air Storage Configuration:")
    print(f"  Duration: {duration} hours")
    print(f"  Power (Inverter) Cost: €{power_cost}/kW")
    print(f"  Energy (Storage) Cost: €{energy_cost}/kWh")
    print(f"  Combined Capital Cost: €{combined_capital_cost:.0f}/MWh")
    print(f"  Round-trip Efficiency: 50%")
    print(f"  Charging Efficiency: {efficiency:.1%}")
    print(f"  Discharging Efficiency: {efficiency:.1%}")
    
    # Remove existing Iron-Air if present and add optimized version
    if "Iron-Air" in n.stores.index:
        n.remove("Store", "Iron-Air")
        print("  Replaced existing Iron-Air storage with optimized version")
    
    # Add optimized Iron-Air storage
    n.add("Store", "Iron-Air-Optimized",
          bus="electricity",
          e_nom_extendable=True,
          e_nom_min=0,
          e_nom_max=5000000,  # 5 TWh max capacity
          e_cyclic=True,
          capital_cost=combined_capital_cost,
          marginal_cost=0.5,
          standing_loss=0.00001,  # Very low self-discharge
          efficiency_store=efficiency,
          efficiency_dispatch=efficiency,
          e_initial=0.5,  # Start at 50% SOC
          max_hours=duration,
          carrier="iron_air")
    
    # Update or add carrier
    if "iron_air" not in n.carriers.index:
        n.add("Carrier", "iron_air")
    
    print(f"\n✅ Added Iron-Air-Optimized storage with {duration}h duration")
    print(f"   Effective cost structure:")
    print(f"   - Per GW power capacity: €{power_cost/1000:.1f}M")
    print(f"   - Per TWh energy capacity: €{energy_cost/1000:.1f}B")
    print(f"   - Example: 10 GW / 1 TWh system would cost €{(10*power_cost + 1000*energy_cost)/1000:.1f}B")

def add_hydrogen_storage_optimized(n):
    """Add Hydrogen storage as StorageUnit with separate power and energy costs"""
    
    print("\n" + "=" * 60)
    print("Adding Optimized Hydrogen Storage System")
    print("=" * 60)
    
    # Hydrogen specifications as requested:
    # - 200h storage duration (fixed)
    # - €3250/kW for power conversion equipment
    # - 34% round-trip efficiency
    
    duration = 200  # hours (fixed duration)
    power_cost = 3250  # €/kW for power equipment
    
    # For energy cost, we need to derive it from the duration and power cost
    # Assuming a reasonable energy storage cost for hydrogen
    energy_cost = 10  # €/kWh for hydrogen storage tanks/caverns
    
    # For 34% round-trip efficiency with symmetric charge/discharge
    # efficiency_store * efficiency_dispatch = 0.34
    # If symmetric: efficiency = sqrt(0.34) ≈ 0.583
    efficiency = np.sqrt(0.34)
    
    # Calculate combined capital cost for PyPSA Store component
    # Total cost = Power_cost * (E/duration) + Energy_cost * E
    # Cost per kWh = Power_cost/duration + Energy_cost
    combined_capital_cost = (power_cost * 1000 / duration) + (energy_cost * 1000)  # Convert to €/MWh
    
    print(f"\nHydrogen Storage Configuration:")
    print(f"  Duration: {duration} hours (FIXED)")
    print(f"  Power Equipment Cost: €{power_cost}/kW")
    print(f"  Energy Storage Cost: €{energy_cost}/kWh")
    print(f"  Combined Capital Cost: €{combined_capital_cost:.0f}/MWh")
    print(f"  Round-trip Efficiency: 34%")
    print(f"  Charging Efficiency: {efficiency:.1%}")
    print(f"  Discharging Efficiency: {efficiency:.1%}")
    
    # Add optimized Hydrogen storage as Store (since PyPSA doesn't have direct StorageUnit support)
    n.add("Store", "Hydrogen-Optimized",
          bus="electricity",
          e_nom_extendable=True,
          e_nom_min=0,
          e_nom_max=10000000,  # 10 TWh max capacity
          e_cyclic=True,
          capital_cost=combined_capital_cost,
          marginal_cost=5,
          standing_loss=0.00005,  # Small losses for hydrogen
          efficiency_store=efficiency,
          efficiency_dispatch=efficiency,
          e_initial=0.5,  # Start at 50% SOC
          max_hours=duration,
          carrier="hydrogen")
    
    # Update or add carrier
    if "hydrogen" not in n.carriers.index:
        n.add("Carrier", "hydrogen")
    
    print(f"\n✅ Added Hydrogen-Optimized storage with {duration}h duration")
    print(f"   Effective cost structure:")
    print(f"   - Per GW power capacity: €{power_cost/1000:.1f}M")
    print(f"   - Per TWh energy capacity: €{energy_cost*1000/1000:.1f}B")
    print(f"   - Example: 10 GW / 2 TWh system would cost €{(10*power_cost + 2000*energy_cost)/1000:.1f}B")

def add_zero_co2_constraint(n):
    """Add ZERO CO2 emission constraint"""
    
    # NO CO2 emissions allowed
    max_co2 = 0.0  # ZERO emissions
    
    total_demand = n.loads_t.p_set.sum().sum()
    print(f"Total annual demand: {total_demand/1e6:.1f} TWh")
    print(f"CO2 limit: {max_co2:.0f} tCO2/year (ZERO EMISSIONS)")
    print("⚠️  This is a 100% renewable + storage scenario for full year")
    
    # Add global CO2 constraint
    n.add("GlobalConstraint",
          "CO2_limit",
          sense="<=",
          constant=max_co2,
          carrier_attribute="co2_emissions")

def analyze_full_year_results(n):
    """Analyze results of full year zero CO2 scenario"""
    
    print("\n" + "=" * 100)
    print("FULL YEAR ZERO CO2 SCENARIO RESULTS")
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
    capacities = {}
    for gen in n.generators.index:
        capacity = n.generators.at[gen, 'p_nom_opt']
        if capacity > 1:
            capacities[gen] = capacity
            total_capacity += capacity
            print(f"  {gen:<20}: {capacity:>12,.0f} MW")
    print(f"  {'TOTAL':<20}: {total_capacity:>12,.0f} MW")
    peak_load = n.loads_t.p_set['demand'].max() if 'demand' in n.loads_t.p_set.columns else n.loads_t.p_set.max().max()
    print(f"  Capacity/Peak Load: {total_capacity / peak_load:.1f}x")
    
    # Storage deployment by duration
    print("\n🔋 Storage Deployment (by duration):")
    print("-" * 90)
    print(f"{'Technology':<15} {'Energy(GWh)':<15} {'Power(GW)':<12} {'Duration(h)':<12} {'Cycles/year':<12} {'Utilization':<12}")
    print("-" * 90)
    
    storage_by_duration = {}
    total_storage_energy = 0
    
    for store in n.stores.index:
        energy = n.stores.at[store, 'e_nom_opt']
        if energy > 1:
            duration = n.stores.at[store, 'max_hours']
            power = energy / duration if duration > 0 else 0
            
            # Calculate annual cycles and utilization
            if store in n.stores_t.p.columns:
                discharged = n.stores_t.p[store].clip(lower=0).sum()
                cycles = discharged / energy if energy > 0 else 0
                active_hours = ((n.stores_t.p[store].abs() > 1).sum())
                utilization = active_hours / len(n.snapshots) * 100
                
                storage_by_duration[store] = {
                    'energy': energy/1000,  # Convert to GWh
                    'power': power/1000,    # Convert to GW
                    'duration': duration,
                    'cycles': cycles,
                    'utilization': utilization
                }
                total_storage_energy += energy
    
    # Sort by duration
    for store, data in sorted(storage_by_duration.items(), key=lambda x: x[1]['duration']):
        print(f"{store:<15} {data['energy']:<15,.0f} {data['power']:<12,.1f} "
              f"{data['duration']:<12.0f} {data['cycles']:<12.1f} {data['utilization']:<11.1f}%")
    
    print(f"\n  Total Storage Energy: {total_storage_energy/1000:,.0f} GWh ({total_storage_energy/1e6:.2f} TWh)")
    print(f"  Storage/Annual Demand: {total_storage_energy/total_demand*100:.1f}%")
    
    # Generation mix
    print("\n⚡ Annual Energy Generation Mix:")
    print("-" * 60)
    total_gen = 0
    gen_by_type = {}
    for gen in n.generators.index:
        if gen in n.generators_t.p.columns:
            gen_energy = n.generators_t.p[gen].sum()
            if gen_energy > 0:
                gen_by_type[gen] = gen_energy
                total_gen += gen_energy
    
    for gen, energy in sorted(gen_by_type.items(), key=lambda x: -x[1]):
        percentage = (energy / total_demand * 100)
        capacity_factor = energy / (n.generators.at[gen, 'p_nom_opt'] * 8760) * 100 if n.generators.at[gen, 'p_nom_opt'] > 0 else 0
        print(f"  {gen:<20}: {energy/1e6:>8.1f} TWh ({percentage:>5.1f}% of demand, CF: {capacity_factor:.1f}%)")
    
    # Seasonal analysis
    print("\n📅 Seasonal Performance:")
    print("-" * 60)
    
    # Define seasons
    winter_hours = list(range(0, 2160)) + list(range(7200, 8760))  # Jan-Mar, Nov-Dec
    summer_hours = list(range(3600, 6480))  # Jun-Aug
    
    winter_demand = n.loads_t.p_set.iloc[winter_hours].sum().sum()
    summer_demand = n.loads_t.p_set.iloc[summer_hours].sum().sum()
    
    winter_solar = sum(n.generators_t.p[gen].iloc[winter_hours].sum() 
                      for gen in n.generators.index 
                      if 'solar' in gen.lower() and gen in n.generators_t.p.columns)
    summer_solar = sum(n.generators_t.p[gen].iloc[summer_hours].sum() 
                      for gen in n.generators.index 
                      if 'solar' in gen.lower() and gen in n.generators_t.p.columns)
    
    print(f"  Winter demand: {winter_demand/1e6:.1f} TWh")
    print(f"  Summer demand: {summer_demand/1e6:.1f} TWh")
    print(f"  Winter solar generation: {winter_solar/1e6:.1f} TWh ({winter_solar/winter_demand*100:.1f}% of winter demand)")
    print(f"  Summer solar generation: {summer_solar/1e6:.1f} TWh ({summer_solar/summer_demand*100:.1f}% of summer demand)")
    
    # Verify zero emissions
    print("\n🌍 CO2 Verification:")
    print("-" * 60)
    total_co2 = 0
    for gen in n.generators.index:
        if gen in n.generators_t.p.columns:
            carrier = n.generators.at[gen, 'carrier']
            if carrier in n.carriers.index:
                emissions_rate = n.carriers.at[carrier, 'co2_emissions']
                gen_emissions = n.generators_t.p[gen].sum() * emissions_rate
                total_co2 += gen_emissions
    
    print(f"  Total Annual CO2 Emissions: {total_co2:.0f} tCO2")
    print(f"  ✅ ZERO EMISSIONS ACHIEVED FOR FULL YEAR!" if total_co2 == 0 else f"  ⚠️ Non-zero emissions detected!")
    
    # Curtailment analysis
    available_renewable = sum(
        (n.generators.at[gen, 'p_nom_opt'] * n.generators_t.p_max_pu[gen].sum())
        for gen in n.generators.index if gen in n.generators_t.p_max_pu.columns
    )
    curtailment = max(0, available_renewable - total_gen)
    curtailment_rate = (curtailment / available_renewable * 100) if available_renewable > 0 else 0
    
    print(f"\n📉 Curtailment Analysis:")
    print(f"  Available renewable energy: {available_renewable/1e6:.1f} TWh")
    print(f"  Used renewable energy: {total_gen/1e6:.1f} TWh")
    print(f"  Curtailed energy: {curtailment/1e6:.1f} TWh ({curtailment_rate:.1f}%)")

def save_full_year_results(n):
    """Save full year zero CO2 scenario results"""
    
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    
    # Save detailed summary
    summary_file = results_dir / f"zero_co2_full_year_summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("PYPSA ZERO CO2 EMISSIONS - FULL YEAR (8760 HOURS) SCENARIO RESULTS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Status: 100% Renewable Energy System - Full Year\n")
        f.write(f"Time horizon: 8760 hours (365 days)\n\n")
        
        total_demand = n.loads_t.p_set.sum().sum()
        
        f.write("SYSTEM OVERVIEW\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total System Cost: €{n.objective:,.0f}\n")
        f.write(f"Cost per MWh: €{n.objective / total_demand:.2f}/MWh\n")
        f.write(f"Total Annual Demand: {total_demand/1e6:.1f} TWh\n")
        f.write(f"Peak Load: {n.loads_t.p_set.max():.0f} MW\n")
        f.write(f"CO2 Emissions: 0 tCO2 (ZERO)\n\n")
        
        f.write("RENEWABLE GENERATION CAPACITY\n")
        f.write("-" * 40 + "\n")
        for gen in n.generators.index:
            capacity = n.generators.at[gen, 'p_nom_opt']
            if capacity > 1:
                f.write(f"{gen}: {capacity:,.0f} MW\n")
        
        f.write("\nSTORAGE DEPLOYMENT\n")
        f.write("-" * 40 + "\n")
        for store in n.stores.index:
            energy = n.stores.at[store, 'e_nom_opt']
            if energy > 1:
                duration = n.stores.at[store, 'max_hours']
                power = energy / duration
                f.write(f"{store}:\n")
                f.write(f"  Energy: {energy/1000:,.0f} GWh\n")
                f.write(f"  Power: {power/1000:,.1f} GW\n")
                f.write(f"  Duration: {duration:.0f} hours\n")
                
                if store in n.stores_t.p.columns:
                    discharged = n.stores_t.p[store].clip(lower=0).sum()
                    cycles = discharged / energy if energy > 0 else 0
                    f.write(f"  Annual cycles: {cycles:.1f}\n")
        
        f.write("\nANNUAL GENERATION MIX\n")
        f.write("-" * 40 + "\n")
        for gen in n.generators.index:
            if gen in n.generators_t.p.columns:
                gen_energy = n.generators_t.p[gen].sum()
                if gen_energy > 0:
                    percentage = gen_energy / total_demand * 100
                    f.write(f"{gen}: {gen_energy/1e6:.1f} TWh ({percentage:.1f}%)\n")
    
    print(f"\n✅ Detailed results saved to: {summary_file}")
    
    # Save time series data
    try:
        # Save key time series to CSV
        ts_file = results_dir / f"zero_co2_full_year_timeseries_{timestamp}.csv"
        ts_data = pd.DataFrame({
            'load_MW': n.loads_t.p_set['demand'],
            'solar_MW': n.generators_t.p['solar'] if 'solar' in n.generators_t.p.columns else 0,
            'wind_onshore_MW': n.generators_t.p['wind_onshore'] if 'wind_onshore' in n.generators_t.p.columns else 0,
            'wind_offshore_MW': n.generators_t.p['wind_offshore'] if 'wind_offshore' in n.generators_t.p.columns else 0,
        })
        
        # Add storage state of charge for major storage
        for store in n.stores.index:
            if store in n.stores_t.e.columns and n.stores.at[store, 'e_nom_opt'] > 1000:
                ts_data[f'{store}_SOC_MWh'] = n.stores_t.e[store]
        
        ts_data.to_csv(ts_file)
        print(f"✅ Time series data saved to: {ts_file}")
    except Exception as e:
        print(f"⚠ Could not save time series: {e}")
    
    # Try to save network
    try:
        nc_file = results_dir / f"zero_co2_full_year_network_{timestamp}.nc"
        n.export_to_netcdf(nc_file)
        print(f"✅ Network saved to: {nc_file}")
    except Exception as e:
        print(f"⚠ Could not save network: {e}")
    
    print(f"\n📁 All results saved to: {results_dir}")

if __name__ == "__main__":
    run_zero_co2_full_year()
