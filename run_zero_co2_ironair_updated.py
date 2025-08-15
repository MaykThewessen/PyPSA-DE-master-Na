#!/usr/bin/env python3
"""
Run PyPSA with ZERO CO2 emissions with updated Iron-Air battery costs
Iron-Air: 100h storage, €150/kW inverter, €25/kWh storage, 50% discharge efficiency
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

def run_zero_co2_ironair_updated():
    """Run full year scenario with updated Iron-Air costs"""
    
    print("=" * 80)
    print("PyPSA ZERO CO2 - Updated Iron-Air Battery Costs")
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
        print("Adding Storage Technologies with Updated Iron-Air")
        print("=" * 60)
        add_storage_with_updated_ironair(n)
        
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
                'time_limit': 7200,
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
            analyze_results(n)
            save_results(n)
        else:
            print(f"⚠ Optimization failed with status: {status}")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def create_full_year_network():
    """Create network with full year of data"""
    import pypsa
    
    n = pypsa.Network()
    
    # Full year simulation - 8760 hours
    hours = 8760
    n.set_snapshots(pd.date_range('2023-01-01', periods=hours, freq='h'))
    
    # Main electricity bus
    n.add("Bus", "electricity", v_nom=380, carrier="AC")
    
    # Add hydrogen bus
    n.add("Bus", "hydrogen", carrier="hydrogen")
    
    # Add Iron-Air DC bus (for the Iron-Air battery system)
    n.add("Bus", "ironair_dc", carrier="DC")
    
    # Load profile with seasonal variation
    np.random.seed(42)
    hours_array = np.arange(hours)
    day_of_year = hours_array // 24
    hour_of_day = hours_array % 24
    
    seasonal_factor = 1 + 0.2 * np.cos(2 * np.pi * day_of_year / 365)
    
    daily_pattern = np.array([0.7, 0.65, 0.6, 0.58, 0.6, 0.65,
                              0.75, 0.85, 0.95, 1.0, 1.05, 1.1,
                              1.1, 1.05, 1.0, 0.95, 0.9, 0.95,
                              1.0, 0.95, 0.85, 0.8, 0.75, 0.72])
    
    load_profile = np.zeros(hours)
    for h in range(hours):
        base_load = 45000 * seasonal_factor[h]
        load_profile[h] = base_load * daily_pattern[hour_of_day[h]]
    
    load_profile *= (1 + 0.05 * np.random.randn(hours))
    load_profile = np.maximum(load_profile, 20000)
    
    n.add("Load", "demand",
          bus="electricity",
          p_set=load_profile)
    
    # Solar profile
    solar_profile = np.zeros(hours)
    for h in range(hours):
        day = day_of_year[h]
        hour = hour_of_day[h]
        seasonal_solar = 0.5 + 0.5 * np.cos(2 * np.pi * (day - 172) / 365)
        if 5 <= hour <= 20:
            daily_solar = np.sin((hour - 5) * np.pi / 15)
        else:
            daily_solar = 0
        solar_profile[h] = seasonal_solar * daily_solar * (0.8 + 0.2 * np.random.random())
    
    solar_profile = np.maximum(solar_profile, 0)
    
    # Wind profile
    wind_profile = np.zeros(hours)
    for h in range(hours):
        day = day_of_year[h]
        seasonal_wind = 0.5 + 0.3 * np.cos(2 * np.pi * day / 365)
        wind_profile[h] = seasonal_wind * (0.3 + 0.7 * np.random.random())
    
    wind_profile = np.clip(wind_profile, 0.05, 1.0)
    
    # Add renewable generators
    n.add("Generator", "solar",
          bus="electricity",
          p_nom_extendable=True,
          p_nom_max=400000,
          capital_cost=25000,
          marginal_cost=0,
          p_max_pu=solar_profile,
          carrier="solar")
    
    n.add("Generator", "wind_onshore",
          bus="electricity",
          p_nom_extendable=True,
          p_nom_max=300000,
          capital_cost=45000,
          marginal_cost=0,
          p_max_pu=wind_profile,
          carrier="wind")
    
    offshore_wind_profile = wind_profile * 1.2
    offshore_wind_profile = np.clip(offshore_wind_profile, 0.1, 1.0)
    
    n.add("Generator", "wind_offshore",
          bus="electricity",
          p_nom_extendable=True,
          p_nom_max=100000,
          capital_cost=65000,
          marginal_cost=0,
          p_max_pu=offshore_wind_profile,
          carrier="wind")
    
    # Add carriers
    n.add("Carrier", "solar", co2_emissions=0.0)
    n.add("Carrier", "wind", co2_emissions=0.0)
    n.add("Carrier", "AC")
    n.add("Carrier", "DC")
    n.add("Carrier", "hydrogen")
    
    print(f"Created full-year network with {len(n.snapshots)} hourly snapshots")
    print(f"Load statistics:")
    print(f"  Average: {load_profile.mean():.1f} MW")
    print(f"  Peak (winter): {load_profile.max():.1f} MW")
    print(f"  Total annual demand: {load_profile.sum()/1e6:.1f} TWh")
    
    return n

def add_storage_with_updated_ironair(n):
    """Add storage technologies with updated Iron-Air battery costs"""
    
    print("\n🔴 Updated Iron-Air Battery System:")
    print("-" * 80)
    
    # Iron-Air system with separate inverter and storage
    # 1. Iron-Air Inverter (bidirectional AC<->DC converter)
    ironair_inverter_capital = 150000  # €150/kW = €150,000/MW
    
    n.add("Link", "IronAir_charge",
          bus0="electricity",
          bus1="ironair_dc",
          p_nom_extendable=True,
          p_nom_min=0,
          p_nom_max=50000,  # 50 GW max
          capital_cost=ironair_inverter_capital/2,  # Half cost for charging
          efficiency=1.0,  # 100% charging efficiency
          carrier="ironair_charge")
    
    n.add("Link", "IronAir_discharge",
          bus0="ironair_dc",
          bus1="electricity",
          p_nom_extendable=True,
          p_nom_min=0,
          p_nom_max=50000,  # 50 GW max
          capital_cost=ironair_inverter_capital/2,  # Half cost for discharging
          efficiency=0.50,  # 50% discharging efficiency
          carrier="ironair_discharge")
    
    print(f"  Iron-Air Inverter:")
    print(f"    Capital cost: €{ironair_inverter_capital:,}/MW")
    print(f"    Charging efficiency: 100%")
    print(f"    Discharging efficiency: 50%")
    print(f"    Max power: 50 GW")
    
    # 2. Iron-Air Storage (on DC bus)
    ironair_storage_capital = 25000  # €25/kWh = €25,000/MWh
    
    n.add("Store", "IronAir_storage",
          bus="ironair_dc",
          e_nom_extendable=True,
          e_nom_min=0,
          e_nom_max=5000000,  # 5 TWh max
          e_cyclic=True,
          capital_cost=ironair_storage_capital,
          marginal_cost=0.5,
          standing_loss=0.00001,  # Very low self-discharge
          carrier="ironair_storage")
    
    print(f"\n  Iron-Air Storage:")
    print(f"    Capital cost: €{ironair_storage_capital:,}/MWh")
    print(f"    Duration: 100 hours")
    print(f"    Max capacity: 5 TWh")
    print(f"    Round-trip efficiency: 50% (100% charge × 50% discharge)")
    
    # Calculate effective costs
    print(f"\n  Effective Iron-Air System Costs:")
    print(f"    For 1 GW / 100 GWh system:")
    print(f"      Inverter: €{ironair_inverter_capital/1000:.0f}M")
    print(f"      Storage: €{ironair_storage_capital * 100 / 1000:.0f}M")
    print(f"      Total: €{(ironair_inverter_capital + ironair_storage_capital * 100)/1000:.0f}M")
    
    # Hydrogen system components
    print("\n🔵 Hydrogen System Components:")
    print("-" * 80)
    
    # Electrolyser
    n.add("Link", "electrolyser",
          bus0="electricity",
          bus1="hydrogen",
          p_nom_extendable=True,
          p_nom_min=0,
          p_nom_max=50000,
          capital_cost=1700000,
          efficiency=0.70,
          carrier="electrolyser")
    
    print(f"  Electrolyser: €1,700,000/MW, 70% efficiency")
    
    # H2 Storage
    n.add("Store", "H2_storage",
          bus="hydrogen",
          e_nom_extendable=True,
          e_nom_min=0,
          e_nom_max=10000000,
          e_cyclic=True,
          capital_cost=5000,
          marginal_cost=0.1,
          standing_loss=0.00005,
          carrier="H2_storage")
    
    print(f"  H2 Storage: €5,000/MWh")
    
    # Fuel Cell
    n.add("Link", "fuel_cell",
          bus0="hydrogen",
          bus1="electricity",
          p_nom_extendable=True,
          p_nom_min=0,
          p_nom_max=50000,
          capital_cost=1500000,
          efficiency=0.58,
          carrier="fuel_cell")
    
    print(f"  Fuel Cell: €1,500,000/MW, 58% efficiency")
    
    # H2 Power Plant
    n.add("Link", "H2_powerplant",
          bus0="hydrogen",
          bus1="electricity",
          p_nom_extendable=True,
          p_nom_min=0,
          p_nom_max=50000,
          capital_cost=1000000,
          efficiency=0.60,
          carrier="H2_powerplant")
    
    print(f"  H2 Power Plant: €1,000,000/MW, 60% efficiency")
    print(f"  H2 Round-trip: 40.6% (via Fuel Cell), 42% (via Power Plant)")
    
    # Other storage technologies
    print("\n🔋 Other Storage Technologies:")
    print("-" * 80)
    
    storage_techs = {
        "Li-ion NMC": {
            "capital_cost": 140000,
            "marginal_cost": 0.1,
            "efficiency_store": np.sqrt(0.92),
            "efficiency_dispatch": np.sqrt(0.92),
            "max_hours": 4,
            "standing_loss": 0.00001,
            "e_nom_max": 1000000,
        },
        "LFP Battery": {
            "capital_cost": 110000,
            "marginal_cost": 0.08,
            "efficiency_store": np.sqrt(0.90),
            "efficiency_dispatch": np.sqrt(0.90),
            "max_hours": 8,
            "standing_loss": 0.00001,
            "e_nom_max": 1500000,
        },
        "CAES": {
            "capital_cost": 35000,
            "marginal_cost": 2,
            "efficiency_store": np.sqrt(0.70),
            "efficiency_dispatch": np.sqrt(0.70),
            "max_hours": 48,
            "standing_loss": 0.0001,
            "e_nom_max": 500000,
        },
        "Pumped Hydro": {
            "capital_cost": 55000,
            "marginal_cost": 0.2,
            "efficiency_store": np.sqrt(0.80),
            "efficiency_dispatch": np.sqrt(0.80),
            "max_hours": 12,
            "standing_loss": 0.00001,
            "e_nom_max": 200000,
        }
    }
    
    print(f"{'Technology':<15} {'Cost(€/kWh)':<12} {'Efficiency':<12} {'Duration(h)':<12}")
    print("-" * 60)
    
    for name, params in storage_techs.items():
        efficiency_rt = params['efficiency_store'] * params['efficiency_dispatch']
        print(f"{name:<15} {params['capital_cost']/1000:<12.0f}k "
              f"{efficiency_rt*100:<11.0f}% {params['max_hours']:<12}")
    
    # Add storage technologies
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
    
    # Add carriers
    for component in ['ironair_charge', 'ironair_discharge', 'ironair_storage',
                     'electrolyser', 'fuel_cell', 'H2_powerplant', 'H2_storage']:
        n.add("Carrier", component)
    
    for name in storage_techs.keys():
        n.add("Carrier", name.lower().replace(' ', '_').replace('-', '_'))
    
    print(f"\n✓ Added all storage technologies with updated Iron-Air configuration")

def add_zero_co2_constraint(n):
    """Add ZERO CO2 emission constraint"""
    
    max_co2 = 0.0
    total_demand = n.loads_t.p_set.sum().sum()
    
    print(f"Total annual demand: {total_demand/1e6:.1f} TWh")
    print(f"CO2 limit: {max_co2:.0f} tCO2/year (ZERO EMISSIONS)")
    
    n.add("GlobalConstraint",
          "CO2_limit",
          sense="<=",
          constant=max_co2,
          carrier_attribute="co2_emissions")

def analyze_results(n):
    """Analyze optimization results"""
    
    print("\n" + "=" * 100)
    print("RESULTS - UPDATED IRON-AIR BATTERY COSTS")
    print("=" * 100)
    
    total_demand = n.loads_t.p_set.sum().sum()
    
    print(f"\n💰 Economic Results:")
    print(f"   Total System Cost: €{n.objective:,.0f}")
    print(f"   Cost per MWh: €{n.objective / total_demand:.2f}/MWh")
    print(f"   Annual demand: {total_demand/1e6:.1f} TWh")
    
    # Generators
    print("\n🌱 Renewable Generation:")
    print("-" * 60)
    total_capacity = 0
    for gen in n.generators.index:
        capacity = n.generators.at[gen, 'p_nom_opt']
        if capacity > 1:
            total_capacity += capacity
            print(f"  {gen:<20}: {capacity:>12,.0f} MW")
    print(f"  {'TOTAL':<20}: {total_capacity:>12,.0f} MW")
    
    # Iron-Air System
    print("\n🔴 Iron-Air Battery Deployment:")
    print("-" * 80)
    
    charge_capacity = n.links.at['IronAir_charge', 'p_nom_opt'] if 'IronAir_charge' in n.links.index else 0
    discharge_capacity = n.links.at['IronAir_discharge', 'p_nom_opt'] if 'IronAir_discharge' in n.links.index else 0
    storage_capacity = n.stores.at['IronAir_storage', 'e_nom_opt'] if 'IronAir_storage' in n.stores.index else 0
    
    print(f"  Charge capacity: {charge_capacity:,.0f} MW")
    print(f"  Discharge capacity: {discharge_capacity:,.0f} MW")
    print(f"  Storage capacity: {storage_capacity/1000:,.0f} GWh")
    
    if storage_capacity > 0:
        duration = storage_capacity / max(charge_capacity, discharge_capacity) if max(charge_capacity, discharge_capacity) > 0 else 0
        print(f"  Effective duration: {duration:.0f} hours")
        
        if 'IronAir_storage' in n.stores_t.p.columns:
            discharged = n.stores_t.p['IronAir_storage'].clip(lower=0).sum()
            cycles = discharged / storage_capacity if storage_capacity > 0 else 0
            print(f"  Annual cycles: {cycles:.1f}")
    
    # Hydrogen System
    print("\n🔵 Hydrogen System Deployment:")
    print("-" * 80)
    
    elec_capacity = n.links.at['electrolyser', 'p_nom_opt'] if 'electrolyser' in n.links.index else 0
    h2_storage = n.stores.at['H2_storage', 'e_nom_opt'] if 'H2_storage' in n.stores.index else 0
    fc_capacity = n.links.at['fuel_cell', 'p_nom_opt'] if 'fuel_cell' in n.links.index else 0
    h2pp_capacity = n.links.at['H2_powerplant', 'p_nom_opt'] if 'H2_powerplant' in n.links.index else 0
    
    print(f"  Electrolyser: {elec_capacity:,.0f} MW")
    print(f"  H2 Storage: {h2_storage/1000:,.0f} GWh")
    print(f"  Fuel Cell: {fc_capacity:,.0f} MW")
    print(f"  H2 Power Plant: {h2pp_capacity:,.0f} MW")
    
    # Other Storage
    print("\n🔋 Other Storage Deployment:")
    print("-" * 80)
    
    for store in n.stores.index:
        if store not in ['IronAir_storage', 'H2_storage']:
            energy = n.stores.at[store, 'e_nom_opt']
            if energy > 1:
                duration = n.stores.at[store, 'max_hours']
                power = energy / duration if duration > 0 else 0
                print(f"  {store}: {energy/1000:,.0f} GWh ({power:,.0f} MW)")

def save_results(n):
    """Save results to file"""
    
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    
    summary_file = results_dir / f"ironair_updated_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write("PYPSA ZERO CO2 - UPDATED IRON-AIR BATTERY\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Iron-Air Configuration:\n")
        f.write(f"  Inverter cost: €150,000/MW\n")
        f.write(f"  Storage cost: €25,000/MWh\n")
        f.write(f"  Duration: 100 hours\n")
        f.write(f"  Discharge efficiency: 50%\n\n")
        
        total_demand = n.loads_t.p_set.sum().sum()
        f.write(f"Total System Cost: €{n.objective:,.0f}\n")
        f.write(f"Cost per MWh: €{n.objective / total_demand:.2f}/MWh\n")
    
    print(f"\n✅ Results saved to: {summary_file}")

if __name__ == "__main__":
    run_zero_co2_ironair_updated()
