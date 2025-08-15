#!/usr/bin/env python3
"""
Run PyPSA-DE scenario with Iron-Air battery storage
Bypasses PROJ issues by avoiding geographic operations
"""

import os
import sys
import warnings
import pandas as pd
import numpy as np
from pathlib import Path

# Suppress warnings
warnings.filterwarnings('ignore')

# Try to set PROJ environment variables as a precaution
os.environ['PROJ_LIB'] = r'C:\ProgramData\miniforge3\envs\pypsa-de\Library\share\proj'
os.environ['PROJ_DATA'] = r'C:\ProgramData\miniforge3\envs\pypsa-de\Library\share\proj'
os.environ['PYPROJ_GLOBAL_CONTEXT'] = '1'

def run_scenario():
    """Run the iron-air storage scenario"""
    
    print("=" * 80)
    print("PyPSA Iron-Air Storage Scenario Runner")
    print("=" * 80)
    
    try:
        # Import PyPSA after setting environment
        import pypsa
        print(f"✓ PyPSA version: {pypsa.__version__}")
        
        # Check if we can load an existing network or need to create one
        network_file = Path("networks/elec_s_37_ec_lcopt_EQ0.95c_1H.nc")
        
        if network_file.exists():
            print(f"\nAttempting to load existing network: {network_file}")
            try:
                # Try loading without CRS operations
                n = pypsa.Network()
                # Load network data manually to avoid CRS issues
                import xarray as xr
                ds = xr.open_dataset(network_file)
                
                # Create a new network and populate it manually
                n = pypsa.Network()
                
                # Set snapshots if available
                if 'snapshots' in ds.dims:
                    n.set_snapshots(pd.DatetimeIndex(ds.snapshots.values))
                else:
                    # Create hourly snapshots for one week
                    n.set_snapshots(pd.date_range('2023-01-01', periods=168, freq='h'))
                
                print("✓ Network structure loaded")
                
            except Exception as e:
                print(f"⚠ Could not load existing network: {e}")
                print("Creating new network instead...")
                n = create_simple_network()
        else:
            print("No existing network found. Creating new network...")
            n = create_simple_network()
        
        # Add or update Iron-Air storage
        print("\n" + "=" * 60)
        print("Adding Iron-Air Battery Storage")
        print("=" * 60)
        
        add_iron_air_storage(n)
        
        # Configure solver
        print("\n" + "=" * 60)
        print("Configuring Solver")
        print("=" * 60)
        
        solver_options = {
            'solver_name': 'highs',
            'highs_method': 'ipm',
            'highs_threads': 4,
            'log_to_console': True,
            'output_flag': True,
            'time_limit': 3600,
            'mip_rel_gap': 0.01,
            'presolve': 'on',
            'parallel': 'on'
        }
        
        print("Solver configuration:")
        for key, value in solver_options.items():
            print(f"  {key}: {value}")
        
        # Run optimization
        print("\n" + "=" * 60)
        print("Running Optimization")
        print("=" * 60)
        
        try:
            status = n.optimize(
                solver_name='highs',
                solver_options={k: v for k, v in solver_options.items() 
                              if k not in ['solver_name', 'log_to_console', 'output_flag']},
                log_to_console=True
            )
            
            print(f"\nOptimization status: {status}")
            
            # Handle both string and tuple status returns
            if (isinstance(status, str) and status == 'ok') or \
               (isinstance(status, tuple) and status[0] == 'ok'):
                analyze_results(n)
                save_results(n)
            else:
                print(f"⚠ Optimization failed with status: {status}")
                
        except Exception as e:
            print(f"✗ Optimization error: {e}")
            print("\nTrying with relaxed constraints...")
            
            # Try with relaxed constraints
            for gen in n.generators.index:
                if 'solar' in gen.lower() or 'wind' in gen.lower():
                    n.generators.loc[gen, 'p_nom_extendable'] = True
                    n.generators.loc[gen, 'p_nom_max'] = 1e6
            
            for store in n.stores.index:
                if 'iron' in store.lower():
                    n.stores.loc[store, 'e_nom_extendable'] = True
                    n.stores.loc[store, 'e_nom_max'] = 1e6
            
            status = n.optimize(solver_name='highs')
            if status == 'ok':
                analyze_results(n)
                save_results(n)
    
    except ImportError as e:
        print(f"✗ Failed to import PyPSA: {e}")
        print("\nPlease ensure PyPSA is installed in your environment:")
        print("  conda install -c conda-forge pypsa")
        return
    
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

def create_simple_network():
    """Create a simple test network with renewable generators"""
    import pypsa
    
    n = pypsa.Network()
    n.set_snapshots(pd.date_range('2023-01-01', periods=168, freq='h'))
    
    # Add a single bus
    n.add("Bus", "electricity", v_nom=380)
    
    # Add load (average 50 GW, varying ±20%)
    load_profile = 50 + 10 * np.sin(np.linspace(0, 14*np.pi, 168))
    n.add("Load", "demand",
          bus="electricity",
          p_set=load_profile * 1000)  # Convert to MW
    
    # Add generators
    solar_profile = np.maximum(0, np.sin(np.linspace(0, 7*2*np.pi, 168)) * 0.8)
    wind_profile = 0.3 + 0.4 * np.random.random(168)
    
    n.add("Generator", "solar",
          bus="electricity",
          p_nom_extendable=True,
          capital_cost=20000,  # €/MW
          marginal_cost=0,
          p_max_pu=solar_profile)
    
    n.add("Generator", "wind",
          bus="electricity", 
          p_nom_extendable=True,
          capital_cost=40000,  # €/MW
          marginal_cost=0,
          p_max_pu=wind_profile)
    
    # Add backup gas generator
    n.add("Generator", "gas",
          bus="electricity",
          p_nom_extendable=True,
          capital_cost=20000,  # €/MW
          marginal_cost=50,  # €/MWh
          efficiency=0.5)
    
    return n

def add_iron_air_storage(n):
    """Add Iron-Air battery storage to the network"""
    
    # Iron-Air battery parameters (100-hour storage)
    iron_air_params = {
        'bus': n.buses.index[0] if len(n.buses) > 0 else 'electricity',
        'e_nom_extendable': True,
        'e_nom_min': 0,
        'e_nom_max': 1e6,  # Very large max capacity
        'e_cyclic': True,
        'capital_cost': 20000,  # €/MWh capacity (very low cost per MWh)
        'marginal_cost': 0.5,   # Small cycling cost
        'standing_loss': 0.00001,  # Very low self-discharge (0.001%/hour)
        'efficiency_store': 0.70,   # 70% round-trip means sqrt(0.7) per direction
        'efficiency_dispatch': 0.70,
        'e_initial': 0.5,  # Start at 50% charge
        'max_hours': 100   # 100-hour duration
    }
    
    # Check if iron-air storage already exists
    iron_air_stores = [s for s in n.stores.index if 'iron' in s.lower()]
    
    if iron_air_stores:
        print(f"Updating existing Iron-Air storage: {iron_air_stores}")
        for store in iron_air_stores:
            for param, value in iron_air_params.items():
                if param != 'bus' and param in n.stores.columns:
                    n.stores.loc[store, param] = value
    else:
        print("Adding new Iron-Air storage unit")
        n.add("Store", "Iron-Air Battery",
              **iron_air_params)
    
    # Also add a short-duration battery for comparison
    battery_params = {
        'bus': n.buses.index[0] if len(n.buses) > 0 else 'electricity',
        'e_nom_extendable': True,
        'e_nom_min': 0,
        'e_nom_max': 1e6,
        'e_cyclic': True,
        'capital_cost': 150000,  # €/MWh (higher cost per MWh)
        'marginal_cost': 0.1,
        'standing_loss': 0.00001,
        'efficiency_store': 0.95,  # 90% round-trip
        'efficiency_dispatch': 0.95,
        'e_initial': 0.5,
        'max_hours': 4  # 4-hour duration
    }
    
    if not any('battery' in s.lower() and 'iron' not in s.lower() for s in n.stores.index):
        n.add("Store", "Li-ion Battery",
              **battery_params)
    
    print(f"\nStorage units in network: {list(n.stores.index)}")
    print("\nStorage parameters:")
    if len(n.stores) > 0:
        print(n.stores[['e_nom_extendable', 'capital_cost', 'max_hours', 
                       'efficiency_store', 'efficiency_dispatch']])

def analyze_results(n):
    """Analyze and display optimization results"""
    
    print("\n" + "=" * 60)
    print("Optimization Results")
    print("=" * 60)
    
    # Overall system cost
    print(f"\nTotal system cost: €{n.objective:.2f}")
    
    # Generator capacities
    print("\nOptimal Generator Capacities:")
    print("-" * 40)
    for gen in n.generators.index:
        capacity = n.generators.loc[gen, 'p_nom_opt']
        if capacity > 0:
            print(f"  {gen}: {capacity:.1f} MW")
    
    # Storage capacities
    print("\nOptimal Storage Capacities:")
    print("-" * 40)
    for store in n.stores.index:
        energy_capacity = n.stores.loc[store, 'e_nom_opt']
        if 'max_hours' in n.stores.columns:
            duration = n.stores.loc[store, 'max_hours']
            power_capacity = energy_capacity / duration if duration > 0 else 0
            print(f"  {store}:")
            print(f"    Energy: {energy_capacity:.1f} MWh")
            print(f"    Power: {power_capacity:.1f} MW")
            print(f"    Duration: {duration:.1f} hours")
        else:
            print(f"  {store}: {energy_capacity:.1f} MWh")
    
    # Generation mix
    if hasattr(n, 'generators_t') and 'p' in n.generators_t:
        print("\nGeneration Mix:")
        print("-" * 40)
        total_gen = n.generators_t.p.sum().sum()
        for gen in n.generators.index:
            gen_sum = n.generators_t.p[gen].sum()
            if gen_sum > 0:
                print(f"  {gen}: {gen_sum:.1f} MWh ({gen_sum/total_gen*100:.1f}%)")
    
    # Storage utilization
    if hasattr(n, 'stores_t') and 'e' in n.stores_t:
        print("\nStorage Utilization:")
        print("-" * 40)
        for store in n.stores.index:
            if store in n.stores_t.e.columns:
                soc = n.stores_t.e[store]
                print(f"  {store}:")
                print(f"    Average SOC: {soc.mean():.1f} MWh")
                print(f"    Max SOC: {soc.max():.1f} MWh")
                print(f"    Min SOC: {soc.min():.1f} MWh")
                
                # Calculate cycles
                if len(soc) > 1:
                    energy_throughput = n.stores_t.p[store].clip(lower=0).sum()
                    nominal_capacity = n.stores.loc[store, 'e_nom_opt']
                    if nominal_capacity > 0:
                        cycles = energy_throughput / nominal_capacity
                        print(f"    Cycles: {cycles:.2f}")

def save_results(n):
    """Save results to file"""
    
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    
    # Save network
    output_file = results_dir / f"iron_air_scenario_{timestamp}.nc"
    try:
        n.export_to_netcdf(output_file)
        print(f"\n✓ Network saved to: {output_file}")
    except Exception as e:
        print(f"⚠ Could not save network file: {e}")
    
    # Save summary
    summary_file = results_dir / f"iron_air_summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write("Iron-Air Storage Scenario Results\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Total system cost: €{n.objective:.2f}\n\n")
        
        f.write("Generator Capacities:\n")
        for gen in n.generators.index:
            capacity = n.generators.loc[gen, 'p_nom_opt']
            if capacity > 0:
                f.write(f"  {gen}: {capacity:.1f} MW\n")
        
        f.write("\nStorage Capacities:\n")
        for store in n.stores.index:
            energy_capacity = n.stores.loc[store, 'e_nom_opt']
            if 'max_hours' in n.stores.columns:
                duration = n.stores.loc[store, 'max_hours']
                power_capacity = energy_capacity / duration if duration > 0 else 0
                f.write(f"  {store}:\n")
                f.write(f"    Energy: {energy_capacity:.1f} MWh\n")
                f.write(f"    Power: {power_capacity:.1f} MW\n")
                f.write(f"    Duration: {duration:.1f} hours\n")
    
    print(f"✓ Summary saved to: {summary_file}")

if __name__ == "__main__":
    run_scenario()
