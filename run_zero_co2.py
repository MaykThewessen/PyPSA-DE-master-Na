#!/usr/bin/env python3
"""
Run PyPSA with ZERO CO2 emissions allowed
Tests all storage technologies in a 100% renewable scenario
"""

import os
import sys
import warnings
import pandas as pd
import numpy as np
from pathlib import Path

# Suppress warnings
warnings.filterwarnings('ignore')

# Set PROJ environment variables
os.environ['PROJ_LIB'] = r'C:\ProgramData\miniforge3\envs\pypsa-de\Library\share\proj'
os.environ['PROJ_DATA'] = r'C:\ProgramData\miniforge3\envs\pypsa-de\Library\share\proj'
os.environ['PYPROJ_GLOBAL_CONTEXT'] = '1'

def run_zero_co2_scenario():
    """Run scenario with zero CO2 emissions"""
    
    print("=" * 80)
    print("PyPSA ZERO CO2 Emissions Scenario")
    print("=" * 80)
    
    try:
        import pypsa
        print(f"✓ PyPSA version: {pypsa.__version__}")
        
        # Create network
        print("\nCreating 100% renewable network...")
        n = create_renewable_network()
        
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
        print("Running Optimization")
        print("=" * 60)
        
        status = n.optimize(
            solver_name='highs',
            solver_options={
                'time_limit': 3600,
                'mip_rel_gap': 0.01,
                'presolve': 'on',
                'parallel': 'on'
            },
            log_to_console=True
        )
        
        print(f"\nOptimization status: {status}")
        
        # Analyze results
        if (isinstance(status, str) and status == 'ok') or \
           (isinstance(status, tuple) and status[0] == 'ok'):
            analyze_zero_co2_results(n)
            save_zero_co2_results(n)
        else:
            print(f"⚠ Optimization failed with status: {status}")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

def create_renewable_network():
    """Create network with only renewable generators (no fossil fuels)"""
    import pypsa
    
    n = pypsa.Network()
    
    # One week simulation
    hours = 168
    n.set_snapshots(pd.date_range('2023-07-01', periods=hours, freq='h'))
    
    # Main bus
    n.add("Bus", "electricity", v_nom=380)
    
    # Load profile (45 GW average)
    np.random.seed(42)
    base_load = 45  # GW
    daily_pattern = np.tile([0.7, 0.65, 0.6, 0.58, 0.6, 0.65,
                             0.75, 0.85, 0.95, 1.0, 1.05, 1.1,
                             1.1, 1.05, 1.0, 0.95, 0.9, 0.95,
                             1.0, 0.95, 0.85, 0.8, 0.75, 0.72], 7)
    load_profile = base_load * daily_pattern[:hours] * 1000  # MW
    
    n.add("Load", "demand",
          bus="electricity",
          p_set=load_profile)
    
    # Solar profile
    hours_in_day = np.arange(hours) % 24
    solar_profile = np.where(
        (hours_in_day >= 5) & (hours_in_day <= 20),
        np.maximum(0, np.sin((hours_in_day - 5) * np.pi / 15)) * (0.8 + 0.2 * np.random.random(hours)),
        0
    )
    
    # Wind profile
    wind_base = 0.3 + 0.4 * np.sin(np.arange(hours) * 2 * np.pi / 48)
    wind_variability = 0.3 * np.random.random(hours)
    wind_profile = np.clip(wind_base + wind_variability - 0.2 * solar_profile, 0.1, 1.0)
    
    # Add ONLY renewable generators
    n.add("Generator", "solar",
          bus="electricity",
          p_nom_extendable=True,
          p_nom_max=300000,  # 300 GW max - increased for 100% renewable
          capital_cost=30000,  # €30/kW/year
          marginal_cost=0,
          p_max_pu=solar_profile,
          carrier="solar")
    
    n.add("Generator", "wind",
          bus="electricity",
          p_nom_extendable=True,
          p_nom_max=250000,  # 250 GW max - increased for 100% renewable
          capital_cost=50000,  # €50/kW/year
          marginal_cost=0,
          p_max_pu=wind_profile,
          carrier="wind")
    
    # NO fossil fuel generators added!
    
    # Add carriers
    n.add("Carrier", "solar", co2_emissions=0.0)
    n.add("Carrier", "wind", co2_emissions=0.0)
    
    print(f"Created 100% renewable network with {len(n.snapshots)} snapshots")
    print(f"Average load: {load_profile.mean():.1f} MW")
    print(f"Peak load: {load_profile.max():.1f} MW")
    print("⚡ Available generators: Solar, Wind (NO fossil fuels)")
    
    return n

def add_all_storage_technologies(n):
    """Add all storage technologies for 100% renewable system"""
    
    # Storage technology parameters optimized for zero CO2
    storage_techs = {
        "Li-ion NMC": {
            "capital_cost": 150000,      # €150/kWh
            "marginal_cost": 0.1,
            "efficiency_store": np.sqrt(0.92),     # 92% round-trip
            "efficiency_dispatch": np.sqrt(0.92),
            "max_hours": 4,               # 4-hour duration
            "standing_loss": 0.00001,
            "e_nom_max": 500000,          # 500 GWh max - increased
        },
        "LFP Battery": {
            "capital_cost": 120000,      # €120/kWh
            "marginal_cost": 0.08,
            "efficiency_store": np.sqrt(0.90),     # 90% round-trip
            "efficiency_dispatch": np.sqrt(0.90),
            "max_hours": 6,               # 6-hour duration
            "standing_loss": 0.00001,
            "e_nom_max": 600000,          # 600 GWh max - increased
        },
        "CAES": {
            "capital_cost": 40000,       # €40/kWh
            "marginal_cost": 2,
            "efficiency_store": np.sqrt(0.70),     # 70% round-trip
            "efficiency_dispatch": np.sqrt(0.70),
            "max_hours": 24,              # 24-hour duration
            "standing_loss": 0.0001,
            "e_nom_max": 200000,          # 200 GWh max
        },
        "Iron-Air": {
            "capital_cost": 20000,       # €20/kWh
            "marginal_cost": 0.5,
            "efficiency_store": np.sqrt(0.50),     # 50% round-trip
            "efficiency_dispatch": np.sqrt(0.50),
            "max_hours": 100,             # 100-hour duration
            "standing_loss": 0.00001,
            "e_nom_max": 2000000,         # 2 TWh max - increased
        },
        "Hydrogen": {
            "capital_cost": 10000,       # €10/kWh
            "marginal_cost": 5,
            "efficiency_store": np.sqrt(0.40),     # 40% round-trip
            "efficiency_dispatch": np.sqrt(0.40),
            "max_hours": 168,             # 168-hour (1 week) duration
            "standing_loss": 0.00005,
            "e_nom_max": 5000000,         # 5 TWh max - increased
        },
        "Pumped Hydro": {
            "capital_cost": 60000,       # €60/kWh
            "marginal_cost": 0.2,
            "efficiency_store": np.sqrt(0.80),     # 80% round-trip
            "efficiency_dispatch": np.sqrt(0.80),
            "max_hours": 8,               # 8-hour duration
            "standing_loss": 0.00001,
            "e_nom_max": 100000,          # 100 GWh max
        }
    }
    
    # Print storage parameters
    print("\nStorage Technologies for Zero CO2:")
    print("-" * 80)
    print(f"{'Technology':<15} {'Cost(€/kWh)':<12} {'Efficiency':<12} {'Duration(h)':<12} {'Max(GWh)':<12}")
    print("-" * 80)
    
    for name, params in storage_techs.items():
        efficiency_rt = params['efficiency_store'] * params['efficiency_dispatch']
        print(f"{name:<15} {params['capital_cost']/1000:<12.0f}k "
              f"{efficiency_rt*100:<11.0f}% {params['max_hours']:<12} "
              f"{params['e_nom_max']/1000:<12.0f}")
    
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
    for name in storage_techs.keys():
        carrier_name = name.lower().replace(' ', '_').replace('-', '_')
        n.add("Carrier", carrier_name)
    
    print(f"\n✓ Added {len(storage_techs)} storage technologies")

def add_zero_co2_constraint(n):
    """Add ZERO CO2 emission constraint"""
    
    # NO CO2 emissions allowed
    max_co2 = 0.0  # ZERO emissions
    
    total_demand = n.loads_t.p_set.sum().sum()
    print(f"Total demand: {total_demand:.0f} MWh")
    print(f"CO2 limit: {max_co2:.0f} tCO2 (ZERO EMISSIONS)")
    print("⚠️  This is a 100% renewable + storage scenario")
    
    # Add global CO2 constraint
    n.add("GlobalConstraint",
          "CO2_limit",
          sense="<=",
          constant=max_co2,
          carrier_attribute="co2_emissions")

def analyze_zero_co2_results(n):
    """Analyze results of zero CO2 scenario"""
    
    print("\n" + "=" * 100)
    print("ZERO CO2 SCENARIO RESULTS")
    print("=" * 100)
    
    # System cost
    print(f"\n💰 Total System Cost: €{n.objective:,.0f}")
    print(f"   Cost per MWh: €{n.objective / n.loads_t.p_set.sum().sum():.2f}/MWh")
    
    # Generator capacities
    print("\n🌱 Renewable Generation Capacities:")
    print("-" * 50)
    total_capacity = 0
    for gen in n.generators.index:
        capacity = n.generators.at[gen, 'p_nom_opt']
        if capacity > 1:
            print(f"  {gen:<15}: {capacity:>12,.0f} MW")
            total_capacity += capacity
    print(f"  {'TOTAL':<15}: {total_capacity:>12,.0f} MW")
    
    # Storage deployment
    print("\n🔋 Storage Deployment:")
    print("-" * 80)
    print(f"{'Technology':<15} {'Energy(MWh)':<15} {'Power(MW)':<12} {'Cycles':<10} {'Utilization':<12}")
    print("-" * 80)
    
    total_storage_energy = 0
    for store in n.stores.index:
        energy = n.stores.at[store, 'e_nom_opt']
        if energy > 1:
            duration = n.stores.at[store, 'max_hours']
            power = energy / duration if duration > 0 else 0
            
            # Calculate utilization
            if store in n.stores_t.p.columns:
                discharged = n.stores_t.p[store].clip(lower=0).sum()
                cycles = discharged / energy if energy > 0 else 0
                active_hours = ((n.stores_t.p[store].abs() > 1).sum())
                utilization = active_hours / len(n.snapshots) * 100
                
                print(f"{store:<15} {energy:<15,.0f} {power:<12,.0f} {cycles:<10.1f} {utilization:<11.1f}%")
                total_storage_energy += energy
    
    print(f"\n  Total Storage: {total_storage_energy:,.0f} MWh")
    
    # Generation mix
    print("\n⚡ Energy Generation Mix (100% Renewable):")
    print("-" * 50)
    total_gen = 0
    for gen in n.generators.index:
        if gen in n.generators_t.p.columns:
            gen_energy = n.generators_t.p[gen].sum()
            if gen_energy > 0:
                total_gen += gen_energy
                percentage = (gen_energy / n.loads_t.p_set.sum().sum() * 100)
                print(f"  {gen:<15}: {gen_energy:>12,.0f} MWh ({percentage:>5.1f}% of demand)")
    
    # Verify zero emissions
    print("\n🌍 CO2 Verification:")
    print("-" * 50)
    total_co2 = 0
    for gen in n.generators.index:
        if gen in n.generators_t.p.columns:
            carrier = n.generators.at[gen, 'carrier']
            if carrier in n.carriers.index:
                emissions_rate = n.carriers.at[carrier, 'co2_emissions']
                gen_emissions = n.generators_t.p[gen].sum() * emissions_rate
                total_co2 += gen_emissions
    
    print(f"  Total CO2 Emissions: {total_co2:.0f} tCO2")
    print(f"  ✅ ZERO EMISSIONS ACHIEVED!" if total_co2 == 0 else f"  ⚠️ Non-zero emissions detected!")
    
    # Curtailment
    available_renewable = sum(
        (n.generators.at[gen, 'p_nom_opt'] * n.generators_t.p_max_pu[gen].sum())
        for gen in n.generators.index if gen in n.generators_t.p_max_pu.columns
    )
    actual_generation = total_gen
    curtailment = max(0, available_renewable - actual_generation)
    curtailment_rate = (curtailment / available_renewable * 100) if available_renewable > 0 else 0
    
    print(f"\n📉 Curtailment Analysis:")
    print(f"  Available renewable energy: {available_renewable:,.0f} MWh")
    print(f"  Used renewable energy: {actual_generation:,.0f} MWh")
    print(f"  Curtailed energy: {curtailment:,.0f} MWh ({curtailment_rate:.1f}%)")

def save_zero_co2_results(n):
    """Save zero CO2 scenario results"""
    
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    
    # Save summary
    summary_file = results_dir / f"zero_co2_summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("PYPSA ZERO CO2 EMISSIONS SCENARIO RESULTS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Status: 100% Renewable Energy System\n\n")
        
        f.write("SYSTEM OVERVIEW\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total System Cost: €{n.objective:,.0f}\n")
        f.write(f"Cost per MWh: €{n.objective / n.loads_t.p_set.sum().sum():.2f}/MWh\n")
        f.write(f"Total Demand: {n.loads_t.p_set.sum().sum():,.0f} MWh\n")
        f.write(f"CO2 Emissions: 0 tCO2 (ZERO)\n\n")
        
        f.write("RENEWABLE GENERATION\n")
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
                f.write(f"  Energy: {energy:,.0f} MWh\n")
                f.write(f"  Power: {power:,.0f} MW\n")
                f.write(f"  Duration: {duration:.0f} hours\n")
    
    print(f"\n✅ Results saved to: {summary_file}")
    
    # Try to save network
    try:
        nc_file = results_dir / f"zero_co2_network_{timestamp}.nc"
        n.export_to_netcdf(nc_file)
        print(f"✅ Network saved to: {nc_file}")
    except Exception as e:
        print(f"⚠ Could not save network: {e}")

if __name__ == "__main__":
    run_zero_co2_scenario()
