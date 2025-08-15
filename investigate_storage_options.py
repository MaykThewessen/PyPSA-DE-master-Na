#!/usr/bin/env python3
"""
Investigate available storage technologies and their costs.
"""

import pypsa
import pandas as pd
import os

def load_network():
    """Load the solved PyPSA network."""
    network_file = "results/de-electricity-only-2035-mayk/networks/base_s_1___2035.nc"
    if not os.path.exists(network_file):
        raise FileNotFoundError(f"Network file not found: {network_file}")
    
    print(f"Loading network from: {network_file}")
    n = pypsa.Network(network_file)
    return n

def load_costs():
    """Load the cost data."""
    cost_file = "resources/de-electricity-only-2035-mayk/costs_2035.csv"
    if not os.path.exists(cost_file):
        print(f"Cost file not found: {cost_file}")
        return None
    
    costs = pd.read_csv(cost_file, index_col=0)
    return costs

def investigate_storage(n, costs):
    """Investigate storage technologies."""
    
    print("=" * 60)
    print("INVESTIGATION: AVAILABLE STORAGE TECHNOLOGIES")
    print("=" * 60)
    
    print("\n1. CARRIERS IN NETWORK:")
    print("-" * 30)
    print("Available carriers:")
    print(n.carriers.index.tolist())
    
    print("\n2. STORAGE UNITS:")
    print("-" * 30)
    print("Storage units in network:")
    print(n.storage_units.to_string())
    
    print(f"\nStorage units with p_nom_opt > 0:")
    optimized_storage = n.storage_units[n.storage_units.p_nom_opt > 0]
    if not optimized_storage.empty:
        print(optimized_storage[['carrier', 'p_nom_opt', 'max_hours']].to_string())
    else:
        print("No optimized storage units found.")
    
    print(f"\nStorage units with p_nom_opt = 0:")
    zero_storage = n.storage_units[n.storage_units.p_nom_opt == 0]
    if not zero_storage.empty:
        print(zero_storage[['carrier', 'p_nom_opt', 'max_hours', 'capital_cost']].to_string())
    else:
        print("No zero-capacity storage units found.")
    
    print("\n3. STORES:")
    print("-" * 30)
    print("Stores in network:")
    if not n.stores.empty:
        print(n.stores.to_string())
    else:
        print("No stores found.")
    
    print("\n4. COST DATA ANALYSIS:")
    print("-" * 30)
    if costs is not None:
        print("Available storage-related technologies in cost data:")
        storage_costs = costs[costs.index.str.contains('battery|iron|vanadium|caes|h2|storage', case=False, na=False)]
        if not storage_costs.empty:
            print(storage_costs[['investment', 'FOM', 'VOM', 'lifetime']].to_string())
        else:
            print("No storage technologies found in cost data.")
        
        # Check specific technologies
        print(f"\nSpecific technology costs:")
        for tech in ['IronAir', 'iron-air', 'vanadium', 'CAES', 'battery', 'H2']:
            if tech in costs.index:
                cost_data = costs.loc[tech]
                print(f"{tech}: Investment: {cost_data.get('investment', 'N/A')} EUR/kW")
            else:
                print(f"{tech}: NOT FOUND in cost data")
    
    print("\n5. CONFIGURATION CHECK:")
    print("-" * 30)
    print("Checking if all storage technologies are properly configured...")
    
    # Check what carriers are defined for storage units
    print(f"Storage unit carriers in network: {n.storage_units['carrier'].unique().tolist()}")
    
    # Check max_hours configuration
    print(f"Max hours configuration in storage units:")
    for carrier in n.storage_units['carrier'].unique():
        carrier_data = n.storage_units[n.storage_units['carrier'] == carrier]
        if not carrier_data.empty:
            max_hours = carrier_data['max_hours'].iloc[0]
            print(f"  {carrier}: {max_hours} hours")

def main():
    """Main function."""
    try:
        n = load_network()
        costs = load_costs()
        investigate_storage(n, costs)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
