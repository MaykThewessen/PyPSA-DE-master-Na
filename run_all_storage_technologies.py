#!/usr/bin/env python3
"""
Comprehensive PyPSA scenario with all major storage technologies:
- Li-ion Battery (NMC)
- LFP Battery (Lithium Iron Phosphate)
- CAES (Compressed Air Energy Storage)
- Iron-Air Battery
- Hydrogen Storage
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

def run_all_storage_scenario():
    """Run scenario with all storage technologies"""
    
    print("=" * 80)
    print("PyPSA Comprehensive Storage Technologies Scenario")
    print("=" * 80)
    
    try:
        import pypsa
        print(f"✓ PyPSA version: {pypsa.__version__}")
        
        # Create network
        print("\nCreating network with renewable generators...")
        n = create_renewable_network()
        
        # Add all storage technologies
        print("\n" + "=" * 60)
        print("Adding All Storage Technologies")
        print("=" * 60)
        add_all_storage_technologies(n)
        
        # Add CO2 constraint
        print("\n" + "=" * 60)
        print("Adding CO2 Constraints")
        print("=" * 60)
        add_co2_constraint(n)
        
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
            analyze_storage_results(n)
            save_storage_comparison(n)
        else:
            print(f"⚠ Optimization failed with status: {status}")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

def create_renewable_network():
    """Create network with renewable generators"""
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
    
    # Add generators
    n.add("Generator", "solar",
          bus="electricity",
          p_nom_extendable=True,
          p_nom_max=200000,
          capital_cost=30000,  # €30/kW/year
          marginal_cost=0,
          p_max_pu=solar_profile,
          carrier="solar")
    
    n.add("Generator", "wind",
          bus="electricity",
          p_nom_extendable=True,
          p_nom_max=150000,
          capital_cost=50000,  # €50/kW/year
          marginal_cost=0,
          p_max_pu=wind_profile,
          carrier="wind")
    
    n.add("Generator", "CCGT",
          bus="electricity",
          p_nom_extendable=True,
          p_nom_max=100000,
          capital_cost=25000,  # €25/kW/year
          marginal_cost=80,
          efficiency=0.58,
          carrier="gas")
    
    # Add carriers
    n.add("Carrier", "gas", co2_emissions=0.201)
    n.add("Carrier", "solar", co2_emissions=0.0)
    n.add("Carrier", "wind", co2_emissions=0.0)
    
    print(f"Created network with {len(n.snapshots)} snapshots")
    print(f"Average load: {load_profile.mean():.1f} MW")
    
    return n

def add_all_storage_technologies(n):
    """Add all major storage technologies with realistic parameters"""
    
    # Storage technology parameters
    storage_techs = {
        "Li-ion NMC": {
            "capital_cost": 150000,      # €150/kWh
            "marginal_cost": 0.1,
            "efficiency_store": np.sqrt(0.92),     # 92% round-trip
            "efficiency_dispatch": np.sqrt(0.92),
            "max_hours": 4,               # 4-hour duration
            "standing_loss": 0.00001,
            "e_nom_max": 200000,          # 200 GWh max
            "description": "Lithium-ion NMC battery for short-duration storage"
        },
        "LFP Battery": {
            "capital_cost": 120000,      # €120/kWh (cheaper than NMC)
            "marginal_cost": 0.08,
            "efficiency_store": np.sqrt(0.90),     # 90% round-trip
            "efficiency_dispatch": np.sqrt(0.90),
            "max_hours": 6,               # 6-hour duration
            "standing_loss": 0.00001,
            "e_nom_max": 300000,          # 300 GWh max
            "description": "Lithium Iron Phosphate battery - safer, longer life"
        },
        "CAES": {
            "capital_cost": 40000,       # €40/kWh
            "marginal_cost": 2,
            "efficiency_store": np.sqrt(0.70),     # 70% round-trip
            "efficiency_dispatch": np.sqrt(0.70),
            "max_hours": 24,              # 24-hour duration
            "standing_loss": 0.0001,
            "e_nom_max": 100000,          # 100 GWh max (geology limited)
            "description": "Compressed Air Energy Storage in underground caverns"
        },
        "Iron-Air": {
            "capital_cost": 20000,       # €20/kWh (ultra-low cost)
            "marginal_cost": 0.5,
            "efficiency_store": np.sqrt(0.50),     # 50% round-trip
            "efficiency_dispatch": np.sqrt(0.50),
            "max_hours": 100,             # 100-hour duration
            "standing_loss": 0.00001,
            "e_nom_max": 1000000,         # 1 TWh max
            "description": "Iron-Air battery for ultra-long duration storage"
        },
        "Hydrogen": {
            "capital_cost": 10000,       # €10/kWh (very low for energy)
            "marginal_cost": 5,
            "efficiency_store": np.sqrt(0.40),     # 40% round-trip (electrolysis + fuel cell)
            "efficiency_dispatch": np.sqrt(0.40),
            "max_hours": 168,             # 168-hour (1 week) duration
            "standing_loss": 0.00005,
            "e_nom_max": 2000000,         # 2 TWh max
            "description": "Green hydrogen storage with electrolysis and fuel cells"
        },
        "Pumped Hydro": {
            "capital_cost": 60000,       # €60/kWh
            "marginal_cost": 0.2,
            "efficiency_store": np.sqrt(0.80),     # 80% round-trip
            "efficiency_dispatch": np.sqrt(0.80),
            "max_hours": 8,               # 8-hour duration
            "standing_loss": 0.00001,
            "e_nom_max": 50000,           # 50 GWh max (geography limited)
            "description": "Pumped hydro storage"
        }
    }
    
    # Print storage technology comparison table
    print("\n" + "=" * 100)
    print("STORAGE TECHNOLOGY PARAMETERS")
    print("=" * 100)
    print(f"{'Technology':<15} {'Cost(€/kWh)':<12} {'Efficiency':<12} {'Duration(h)':<12} {'Max(GWh)':<12} {'Description':<40}")
    print("-" * 100)
    
    for name, params in storage_techs.items():
        efficiency_rt = params['efficiency_store'] * params['efficiency_dispatch']
        print(f"{name:<15} {params['capital_cost']/1000:<12.0f}k "
              f"{efficiency_rt*100:<11.0f}% {params['max_hours']:<12} "
              f"{params['e_nom_max']/1000:<12.0f} {params['description']:<40}")
    
    print("-" * 100)
    
    # Add each storage technology to the network
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
    
    print(f"\n✓ Added {len(storage_techs)} storage technologies to the network")

def add_co2_constraint(n):
    """Add CO2 constraint to force renewable deployment"""
    
    # Calculate baseline emissions
    total_demand = n.loads_t.p_set.sum().sum()
    ccgt_emissions_rate = 0.201 / 0.58  # tCO2/MWh_elec
    
    # Set CO2 limit to 10% of unconstrained gas emissions
    max_co2 = 0.1 * ccgt_emissions_rate * total_demand
    
    print(f"Total demand: {total_demand:.0f} MWh")
    print(f"CO2 limit: {max_co2:.0f} tCO2 (10% of unconstrained gas)")
    
    n.add("GlobalConstraint",
          "CO2_limit",
          sense="<=",
          constant=max_co2,
          carrier_attribute="co2_emissions")

def analyze_storage_results(n):
    """Analyze results focusing on storage technology comparison"""
    
    print("\n" + "=" * 100)
    print("OPTIMIZATION RESULTS - STORAGE TECHNOLOGY COMPARISON")
    print("=" * 100)
    
    # System overview
    print(f"\n📊 System Overview:")
    print(f"   Total Cost: €{n.objective:,.0f}")
    print(f"   Cost per MWh: €{n.objective / n.loads_t.p_set.sum().sum():.2f}/MWh")
    
    # Storage deployment results
    print("\n🔋 Storage Technologies Deployed:")
    print("-" * 80)
    print(f"{'Technology':<15} {'Energy(MWh)':<15} {'Power(MW)':<12} {'Cycles':<10} {'Utilization':<12} {'Cost Share':<12}")
    print("-" * 80)
    
    total_storage_cost = 0
    storage_results = {}
    
    for store in n.stores.index:
        energy = n.stores.at[store, 'e_nom_opt']
        if energy > 1:  # Only show deployed storage
            duration = n.stores.at[store, 'max_hours']
            power = energy / duration if duration > 0 else 0
            
            # Calculate cycles and utilization
            if store in n.stores_t.p.columns:
                discharged = n.stores_t.p[store].clip(lower=0).sum()
                cycles = discharged / energy if energy > 0 else 0
                
                # Calculate cost contribution
                capital_cost = n.stores.at[store, 'capital_cost']
                storage_cost = energy * capital_cost
                total_storage_cost += storage_cost
                
                # Calculate utilization (% of time actively charging/discharging)
                active_hours = ((n.stores_t.p[store].abs() > 1).sum())  # Active if > 1 MW
                utilization = active_hours / len(n.snapshots) * 100
                
                storage_results[store] = {
                    'energy': energy,
                    'power': power,
                    'cycles': cycles,
                    'utilization': utilization,
                    'cost': storage_cost
                }
                
                print(f"{store:<15} {energy:<15,.0f} {power:<12,.0f} {cycles:<10.1f} {utilization:<11.1f}% €{storage_cost/1e6:<11.1f}M")
    
    # Generation mix
    print("\n⚡ Generation Mix:")
    print("-" * 50)
    total_gen = 0
    gen_by_type = {}
    
    for gen in n.generators.index:
        if gen in n.generators_t.p.columns:
            gen_energy = n.generators_t.p[gen].sum()
            if gen_energy > 0:
                gen_by_type[gen] = gen_energy
                total_gen += gen_energy
    
    for gen, energy in sorted(gen_by_type.items(), key=lambda x: -x[1]):
        percentage = (energy / total_gen * 100) if total_gen > 0 else 0
        print(f"  {gen:<15}: {energy:>12,.0f} MWh ({percentage:>5.1f}%)")
    
    # Renewable share
    renewable_gen = sum(gen_by_type.get(g, 0) for g in ['solar', 'wind'])
    renewable_share = renewable_gen / total_gen * 100 if total_gen > 0 else 0
    print(f"\n  🌱 Renewable share: {renewable_share:.1f}%")
    
    # Storage technology effectiveness
    print("\n📈 Storage Technology Effectiveness:")
    print("-" * 80)
    
    if storage_results:
        # Sort by cycles (most active first)
        for store, data in sorted(storage_results.items(), key=lambda x: x[1]['cycles'], reverse=True):
            print(f"\n{store}:")
            print(f"  - Deployed Capacity: {data['energy']:,.0f} MWh ({data['power']:,.0f} MW)")
            print(f"  - Full Cycles: {data['cycles']:.1f}")
            print(f"  - Active Time: {data['utilization']:.1f}%")
            print(f"  - Capital Investment: €{data['cost']/1e6:.1f}M")
            
            # Cost per cycle
            if data['cycles'] > 0:
                cost_per_cycle = data['cost'] / (data['cycles'] * 365 / 7)  # Annualized
                print(f"  - Cost per cycle (annualized): €{cost_per_cycle:.0f}")

def save_storage_comparison(n):
    """Save detailed storage comparison results"""
    
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    
    # Create storage comparison DataFrame
    storage_data = []
    for store in n.stores.index:
        energy = n.stores.at[store, 'e_nom_opt']
        duration = n.stores.at[store, 'max_hours']
        power = energy / duration if duration > 0 else 0
        
        # Calculate metrics
        discharged = 0
        cycles = 0
        if store in n.stores_t.p.columns and energy > 0:
            discharged = n.stores_t.p[store].clip(lower=0).sum()
            cycles = discharged / energy
        
        efficiency = n.stores.at[store, 'efficiency_store'] * n.stores.at[store, 'efficiency_dispatch']
        
        storage_data.append({
            'Technology': store,
            'Energy_Capacity_MWh': energy,
            'Power_Capacity_MW': power,
            'Duration_Hours': duration,
            'Capital_Cost_per_kWh': n.stores.at[store, 'capital_cost'] / 1000,
            'Round_Trip_Efficiency': efficiency * 100,
            'Energy_Discharged_MWh': discharged,
            'Full_Cycles': cycles,
            'Deployed': 'Yes' if energy > 1 else 'No'
        })
    
    df_storage = pd.DataFrame(storage_data)
    
    # Save to CSV
    csv_file = results_dir / f"storage_comparison_{timestamp}.csv"
    df_storage.to_csv(csv_file, index=False)
    print(f"\n✅ Storage comparison saved to: {csv_file}")
    
    # Save summary report
    summary_file = results_dir / f"all_storage_summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write("=" * 100 + "\n")
        f.write("COMPREHENSIVE STORAGE TECHNOLOGY COMPARISON\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"Timestamp: {timestamp}\n\n")
        
        f.write("STORAGE TECHNOLOGIES OVERVIEW\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Technology':<20} {'Cost(€/kWh)':<15} {'Efficiency(%)':<15} {'Duration(h)':<15} {'Status':<15}\n")
        f.write("-" * 80 + "\n")
        
        for _, row in df_storage.iterrows():
            f.write(f"{row['Technology']:<20} {row['Capital_Cost_per_kWh']:<15.0f} "
                   f"{row['Round_Trip_Efficiency']:<15.0f} {row['Duration_Hours']:<15.0f} "
                   f"{row['Deployed']:<15}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("DEPLOYED STORAGE DETAILS\n")
        f.write("=" * 80 + "\n")
        
        deployed = df_storage[df_storage['Deployed'] == 'Yes'].sort_values('Energy_Capacity_MWh', ascending=False)
        for _, row in deployed.iterrows():
            f.write(f"\n{row['Technology']}:\n")
            f.write(f"  Energy Capacity: {row['Energy_Capacity_MWh']:,.0f} MWh\n")
            f.write(f"  Power Capacity: {row['Power_Capacity_MW']:,.0f} MW\n")
            f.write(f"  Full Cycles: {row['Full_Cycles']:.1f}\n")
            f.write(f"  Energy Throughput: {row['Energy_Discharged_MWh']:,.0f} MWh\n")
    
    print(f"✅ Summary report saved to: {summary_file}")
    
    # Try to save network
    try:
        nc_file = results_dir / f"all_storage_network_{timestamp}.nc"
        n.export_to_netcdf(nc_file)
        print(f"✅ Network saved to: {nc_file}")
    except Exception as e:
        print(f"⚠ Could not save network: {e}")

if __name__ == "__main__":
    run_all_storage_scenario()
