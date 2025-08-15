#!/usr/bin/env python3
"""
Run PyPSA scenario with Iron-Air storage and renewable energy focus
Forces renewable deployment through CO2 constraints
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

def run_renewable_scenario():
    """Run the iron-air storage scenario with high renewable penetration"""
    
    print("=" * 80)
    print("PyPSA Iron-Air Storage with Renewable Energy Scenario")
    print("=" * 80)
    
    try:
        import pypsa
        print(f"✓ PyPSA version: {pypsa.__version__}")
        
        # Create network
        print("\nCreating renewable-focused network...")
        n = create_renewable_network()
        
        # Add Iron-Air and other storage
        print("\n" + "=" * 60)
        print("Adding Storage Technologies")
        print("=" * 60)
        add_storage_technologies(n)
        
        # Add CO2 constraint to force renewable deployment
        print("\n" + "=" * 60)
        print("Adding CO2 Constraints")
        print("=" * 60)
        add_co2_constraint(n)
        
        # Configure and run solver
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
            analyze_detailed_results(n)
            save_detailed_results(n)
        else:
            print(f"⚠ Optimization failed with status: {status}")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

def create_renewable_network():
    """Create network with realistic renewable profiles and costs"""
    import pypsa
    
    n = pypsa.Network()
    
    # One week of hourly data
    hours = 168
    n.set_snapshots(pd.date_range('2023-07-01', periods=hours, freq='h'))
    
    # Add main bus
    n.add("Bus", "electricity", v_nom=380)
    
    # Load profile (summer week, 30-60 GW)
    np.random.seed(42)  # For reproducibility
    base_load = 45  # GW average
    daily_pattern = np.tile([0.7, 0.65, 0.6, 0.58, 0.6, 0.65,  # Night
                             0.75, 0.85, 0.95, 1.0, 1.05, 1.1,  # Morning/noon
                             1.1, 1.05, 1.0, 0.95, 0.9, 0.95,   # Afternoon
                             1.0, 0.95, 0.85, 0.8, 0.75, 0.72], 7)  # Evening/night
    load_profile = base_load * daily_pattern[:hours] * 1000  # Convert to MW
    
    n.add("Load", "demand",
          bus="electricity",
          p_set=load_profile)
    
    # Solar profile (strong summer pattern)
    hours_in_day = np.arange(hours) % 24
    solar_profile = np.where(
        (hours_in_day >= 5) & (hours_in_day <= 20),
        np.maximum(0, np.sin((hours_in_day - 5) * np.pi / 15)) * (0.8 + 0.2 * np.random.random(hours)),
        0
    )
    
    # Wind profile (variable, anti-correlated with solar)
    wind_base = 0.3 + 0.4 * np.sin(np.arange(hours) * 2 * np.pi / 48)
    wind_variability = 0.3 * np.random.random(hours)
    wind_profile = np.clip(wind_base + wind_variability - 0.2 * solar_profile, 0.1, 1.0)
    
    # Add generators with updated costs (€/MW)
    n.add("Generator", "solar",
          bus="electricity",
          p_nom_extendable=True,
          p_nom_min=0,
          p_nom_max=200000,  # 200 GW max
          capital_cost=30000,  # 30 €/kW/year
          marginal_cost=0,
          p_max_pu=solar_profile,
          carrier="solar")
    
    n.add("Generator", "wind",
          bus="electricity",
          p_nom_extendable=True,
          p_nom_min=0,
          p_nom_max=150000,  # 150 GW max
          capital_cost=50000,  # 50 €/kW/year
          marginal_cost=0,
          p_max_pu=wind_profile,
          carrier="wind")
    
    # Gas with high CO2 emissions
    n.add("Generator", "CCGT",
          bus="electricity",
          p_nom_extendable=True,
          p_nom_min=0,
          p_nom_max=100000,  # 100 GW max
          capital_cost=25000,  # 25 €/kW/year
          marginal_cost=80,   # High fuel cost
          efficiency=0.58,    # 58% efficient CCGT
          carrier="gas")
    
    # Add carrier information for CO2 tracking
    n.add("Carrier", "gas", co2_emissions=0.201)  # tCO2/MWh_thermal
    n.add("Carrier", "solar", co2_emissions=0.0)
    n.add("Carrier", "wind", co2_emissions=0.0)
    
    print(f"Created network with {len(n.snapshots)} hourly snapshots")
    print(f"Average load: {load_profile.mean():.1f} MW")
    print(f"Peak load: {load_profile.max():.1f} MW")
    
    return n

def add_storage_technologies(n):
    """Add Iron-Air, Li-ion battery, and pumped hydro storage"""
    
    # Iron-Air battery (100-hour, ultra-low cost per MWh)
    n.add("Store", "Iron-Air",
          bus="electricity",
          e_nom_extendable=True,
          e_nom_min=0,
          e_nom_max=5000000,  # 5 TWh max
          e_cyclic=True,
          capital_cost=20000,  # 20 €/kWh - very cheap per energy
          marginal_cost=0.5,
          standing_loss=0.00001,  # Minimal self-discharge
          efficiency_store=np.sqrt(0.50),  # 50% round-trip
          efficiency_dispatch=np.sqrt(0.50),
          e_initial=0.5,
          max_hours=100,
          carrier="iron_air")
    
    # Li-ion battery (4-hour, medium cost)
    n.add("Store", "Li-ion",
          bus="electricity",
          e_nom_extendable=True,
          e_nom_min=0,
          e_nom_max=500000,  # 500 GWh max
          e_cyclic=True,
          capital_cost=120000,  # 120 €/kWh
          marginal_cost=0.1,
          standing_loss=0.00001,
          efficiency_store=np.sqrt(0.90),  # 90% round-trip
          efficiency_dispatch=np.sqrt(0.90),
          e_initial=0.5,
          max_hours=4,
          carrier="battery")
    
    # Pumped hydro storage (8-hour, low cost)
    n.add("Store", "Pumped Hydro",
          bus="electricity",
          e_nom_extendable=True,
          e_nom_min=0,
          e_nom_max=50000,  # 50 GWh max (limited by geography)
          e_cyclic=True,
          capital_cost=60000,  # 60 €/kWh
          marginal_cost=0.2,
          standing_loss=0.00001,
          efficiency_store=np.sqrt(0.80),  # 80% round-trip
          efficiency_dispatch=np.sqrt(0.80),
          e_initial=0.5,
          max_hours=8,
          carrier="hydro")
    
    # Add carrier definitions
    n.add("Carrier", "iron_air")
    n.add("Carrier", "battery")
    n.add("Carrier", "hydro")
    
    print("\nStorage technologies added:")
    print(n.stores[['e_nom_max', 'capital_cost', 'max_hours', 
                   'efficiency_store', 'efficiency_dispatch']])

def add_co2_constraint(n):
    """Add CO2 emission constraint to force renewable deployment"""
    
    # Calculate emissions for each generator
    emissions = {}
    for gen in n.generators.index:
        carrier = n.generators.at[gen, 'carrier']
        if carrier in n.carriers.index:
            # Emissions in tCO2/MWh_elec
            efficiency = n.generators.at[gen, 'efficiency'] if gen == 'CCGT' else 1.0
            emissions[gen] = n.carriers.at[carrier, 'co2_emissions'] / efficiency
        else:
            emissions[gen] = 0
    
    # Add global CO2 limit (e.g., 10% of what unconstrained gas would emit)
    total_demand = n.loads_t.p_set.sum().sum()
    max_co2 = 0.1 * emissions.get('CCGT', 0) * total_demand  # 10% of full gas emissions
    
    print(f"Total demand: {total_demand:.0f} MWh")
    print(f"CO2 limit: {max_co2:.0f} tCO2 (10% of unconstrained gas)")
    
    # Add CO2 constraint
    n.add("GlobalConstraint",
          "CO2_limit",
          sense="<=",
          constant=max_co2,
          carrier_attribute="co2_emissions")

def analyze_detailed_results(n):
    """Detailed analysis of optimization results"""
    
    print("\n" + "=" * 80)
    print("OPTIMIZATION RESULTS")
    print("=" * 80)
    
    # System cost
    print(f"\n📊 Total System Cost: €{n.objective:,.0f}")
    print(f"   Cost per MWh served: €{n.objective / n.loads_t.p_set.sum().sum():.2f}/MWh")
    
    # Generator results
    print("\n⚡ Optimal Generation Capacities:")
    print("-" * 50)
    total_gen_capacity = 0
    for gen in n.generators.index:
        capacity = n.generators.at[gen, 'p_nom_opt']
        if capacity > 1:  # Only show if > 1 MW
            print(f"  {gen:15s}: {capacity:>12,.0f} MW")
            total_gen_capacity += capacity
    print(f"  {'TOTAL':15s}: {total_gen_capacity:>12,.0f} MW")
    
    # Storage results
    print("\n🔋 Optimal Storage Capacities:")
    print("-" * 50)
    for store in n.stores.index:
        energy = n.stores.at[store, 'e_nom_opt']
        if energy > 1:  # Only show if > 1 MWh
            duration = n.stores.at[store, 'max_hours']
            power = energy / duration if duration > 0 else 0
            print(f"  {store:15s}:")
            print(f"    Energy capacity: {energy:>12,.0f} MWh")
            print(f"    Power capacity:  {power:>12,.0f} MW")
            print(f"    Duration:        {duration:>12.0f} hours")
    
    # Generation mix
    print("\n📈 Energy Generation Mix:")
    print("-" * 50)
    total_generation = 0
    generation_by_type = {}
    
    for gen in n.generators.index:
        if gen in n.generators_t.p.columns:
            gen_energy = n.generators_t.p[gen].sum()
            if gen_energy > 0:
                generation_by_type[gen] = gen_energy
                total_generation += gen_energy
    
    for gen, energy in sorted(generation_by_type.items(), key=lambda x: -x[1]):
        percentage = (energy / total_generation * 100) if total_generation > 0 else 0
        print(f"  {gen:15s}: {energy:>12,.0f} MWh ({percentage:>5.1f}%)")
    
    # Renewable share
    renewable_generation = sum(generation_by_type.get(g, 0) for g in ['solar', 'wind'])
    renewable_share = renewable_generation / total_generation * 100 if total_generation > 0 else 0
    print(f"\n  🌱 Renewable share: {renewable_share:.1f}%")
    
    # Storage cycling
    print("\n🔄 Storage Utilization:")
    print("-" * 50)
    for store in n.stores.index:
        if store in n.stores_t.e.columns:
            soc = n.stores_t.e[store]
            if soc.max() > 1:  # Only show if used
                # Energy throughput (discharge only)
                if store in n.stores_t.p.columns:
                    discharged = n.stores_t.p[store].clip(lower=0).sum()
                    capacity = n.stores.at[store, 'e_nom_opt']
                    cycles = discharged / capacity if capacity > 0 else 0
                    
                    print(f"  {store:15s}:")
                    print(f"    Energy discharged: {discharged:>10,.0f} MWh")
                    print(f"    Full cycles:       {cycles:>10.1f}")
                    print(f"    Avg State-of-Charge: {soc.mean():>8,.0f} MWh")
                    print(f"    Max State-of-Charge: {soc.max():>8,.0f} MWh")
    
    # CO2 emissions
    print("\n🌍 CO2 Emissions:")
    print("-" * 50)
    total_co2 = 0
    for gen in n.generators.index:
        if gen in n.generators_t.p.columns:
            carrier = n.generators.at[gen, 'carrier']
            if carrier in n.carriers.index:
                efficiency = n.generators.at[gen, 'efficiency'] if gen == 'CCGT' else 1.0
                emissions_rate = n.carriers.at[carrier, 'co2_emissions'] / efficiency
                gen_emissions = n.generators_t.p[gen].sum() * emissions_rate
                if gen_emissions > 0:
                    print(f"  {gen:15s}: {gen_emissions:>12,.0f} tCO2")
                    total_co2 += gen_emissions
    
    print(f"  {'TOTAL':15s}: {total_co2:>12,.0f} tCO2")
    print(f"  Emissions intensity: {total_co2 / n.loads_t.p_set.sum().sum() * 1000:.1f} kgCO2/MWh")

def save_detailed_results(n):
    """Save detailed results and visualizations"""
    
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    
    # Save network
    try:
        output_file = results_dir / f"iron_air_renewable_{timestamp}.nc"
        n.export_to_netcdf(output_file)
        print(f"\n✅ Network saved to: {output_file}")
    except Exception as e:
        print(f"⚠ Could not save network: {e}")
    
    # Save detailed CSV results
    try:
        # Generator results
        gen_results = pd.DataFrame({
            'capacity_MW': n.generators.p_nom_opt,
            'generation_MWh': n.generators_t.p.sum(),
            'capacity_factor': n.generators_t.p.sum() / (n.generators.p_nom_opt * len(n.snapshots))
        })
        gen_results.to_csv(results_dir / f"generators_{timestamp}.csv")
        
        # Storage results
        store_results = pd.DataFrame({
            'energy_capacity_MWh': n.stores.e_nom_opt,
            'max_hours': n.stores.max_hours,
            'power_capacity_MW': n.stores.e_nom_opt / n.stores.max_hours
        })
        store_results.to_csv(results_dir / f"storage_{timestamp}.csv")
        
        print(f"✅ Detailed results saved to CSV files")
        
    except Exception as e:
        print(f"⚠ Could not save CSV results: {e}")
    
    # Save summary report
    summary_file = results_dir / f"iron_air_renewable_summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("PYPSA IRON-AIR RENEWABLE SCENARIO RESULTS\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Optimization Status: Optimal\n\n")
        
        f.write("SYSTEM OVERVIEW\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total System Cost: €{n.objective:,.0f}\n")
        f.write(f"Cost per MWh: €{n.objective / n.loads_t.p_set.sum().sum():.2f}/MWh\n")
        f.write(f"Total Demand: {n.loads_t.p_set.sum().sum():,.0f} MWh\n\n")
        
        f.write("GENERATION CAPACITY\n")
        f.write("-" * 40 + "\n")
        for gen in n.generators.index:
            capacity = n.generators.at[gen, 'p_nom_opt']
            if capacity > 1:
                f.write(f"{gen:20s}: {capacity:>15,.0f} MW\n")
        
        f.write("\nSTORAGE CAPACITY\n")
        f.write("-" * 40 + "\n")
        for store in n.stores.index:
            energy = n.stores.at[store, 'e_nom_opt']
            if energy > 1:
                duration = n.stores.at[store, 'max_hours']
                power = energy / duration
                f.write(f"{store:20s}:\n")
                f.write(f"  Energy: {energy:>15,.0f} MWh\n")
                f.write(f"  Power:  {power:>15,.0f} MW\n")
                f.write(f"  Duration: {duration:>13.0f} hours\n")
        
        # Calculate renewable share
        total_gen = n.generators_t.p.sum().sum()
        renewable_gen = sum(n.generators_t.p[g].sum() for g in ['solar', 'wind'] 
                           if g in n.generators_t.p.columns)
        renewable_share = renewable_gen / total_gen * 100 if total_gen > 0 else 0
        
        f.write("\nKEY METRICS\n")
        f.write("-" * 40 + "\n")
        f.write(f"Renewable Share: {renewable_share:.1f}%\n")
        
        # CO2 emissions
        total_co2 = 0
        for gen in n.generators.index:
            if gen in n.generators_t.p.columns:
                carrier = n.generators.at[gen, 'carrier']
                if carrier in n.carriers.index:
                    efficiency = n.generators.at[gen, 'efficiency'] if gen == 'CCGT' else 1.0
                    emissions_rate = n.carriers.at[carrier, 'co2_emissions'] / efficiency
                    total_co2 += n.generators_t.p[gen].sum() * emissions_rate
        
        f.write(f"Total CO2 Emissions: {total_co2:,.0f} tCO2\n")
        f.write(f"Emissions Intensity: {total_co2 / n.loads_t.p_set.sum().sum() * 1000:.1f} kgCO2/MWh\n")
    
    print(f"✅ Summary report saved to: {summary_file}")

if __name__ == "__main__":
    run_renewable_scenario()
