#!/usr/bin/env python3

import pypsa
import pandas as pd
import numpy as np

def analyze_energy_and_costs():
    """Analyze annual energy consumption and hydrogen storage costs"""
    
    print("Loading PyPSA network...")
    network_path = "results/de-electricity-only-2035-mayk/networks/base_s_1___2035.nc"
    n = pypsa.Network(network_path)
    
    print("\n" + "="*60)
    print("ANNUAL ENERGY ANALYSIS")
    print("="*60)
    
    # Calculate total annual electricity demand (TWh/year)
    total_load_mwh = n.loads_t.p.sum().sum()  # Sum over all buses and timesteps
    total_load_twh = total_load_mwh / 1e6  # Convert MWh to TWh
    
    print(f"Total Annual Electricity Demand: {total_load_twh:.2f} TWh/year")
    
    # Calculate demand by bus if there are multiple buses
    load_by_bus = n.loads_t.p.sum()
    print(f"Number of load buses: {len(load_by_bus)}")
    for bus, load_mwh in load_by_bus.items():
        load_twh = load_mwh / 1e6
        print(f"  {bus}: {load_twh:.2f} TWh/year")
    
    print("\n" + "="*60)
    print("HYDROGEN STORAGE COST ANALYSIS")
    print("="*60)
    
    # Check costs data
    try:
        costs_file = "data/costs_2035.csv"
        costs_df = pd.read_csv(costs_file)
        print(f"Loading costs from: {costs_file}")
    except:
        # Try alternative path
        costs_file = "data/costs.csv"
        try:
            costs_df = pd.read_csv(costs_file)
            print(f"Loading costs from: {costs_file}")
        except:
            print("Could not find costs file. Checking what's in data directory...")
            import os
            data_files = os.listdir("data")
            print("Data directory contents:", data_files)
            return
    
    # Filter for hydrogen-related technologies
    h2_costs = costs_df[costs_df['technology'].str.contains('H2|hydrogen', case=False, na=False)]
    
    if len(h2_costs) > 0:
        print("\nHydrogen-related cost parameters:")
        print("-" * 40)
        for idx, row in h2_costs.iterrows():
            tech = row['technology']
            print(f"\nTechnology: {tech}")
            
            # Display relevant cost columns
            relevant_cols = ['capital_cost', 'fixed_cost', 'variable_cost', 'efficiency', 'marginal_cost']
            for col in relevant_cols:
                if col in row and pd.notna(row[col]):
                    print(f"  {col}: {row[col]}")
    else:
        print("No hydrogen-specific costs found. Showing all available technologies:")
        print(costs_df['technology'].unique())
    
    # Check network components for hydrogen storage
    print("\n" + "="*60)
    print("HYDROGEN STORAGE COMPONENTS IN NETWORK")
    print("="*60)
    
    # Check stores for hydrogen
    if len(n.stores) > 0:
        h2_stores = n.stores[n.stores.carrier.str.contains('H2', case=False, na=False)]
        if len(h2_stores) > 0:
            print("\nHydrogen Stores:")
            print(h2_stores[['carrier', 'e_nom_opt', 'capital_cost', 'marginal_cost']])
    
    # Check links for hydrogen (P2G2P)
    if len(n.links) > 0:
        h2_links = n.links[n.links.carrier.str.contains('H2', case=False, na=False)]
        if len(h2_links) > 0:
            print("\nHydrogen Links (P2G2P):")
            print(h2_links[['carrier', 'p_nom_opt', 'capital_cost', 'marginal_cost', 'efficiency']])
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Annual Electricity Demand: {total_load_twh:.2f} TWh/year")
    
    # Extract specific hydrogen costs if available
    try:
        if len(h2_stores) > 0:
            h2_store = h2_stores.iloc[0]
            print(f"Hydrogen Storage CAPEX: {h2_store.get('capital_cost', 'N/A')} €/MWh")
        
        if len(h2_links) > 0:
            # Separate charging and discharging links
            charge_links = h2_links[h2_links.index.str.contains('charge|electrolysis', case=False)]
            discharge_links = h2_links[h2_links.index.str.contains('discharge|fuel.*cell', case=False)]
            
            if len(charge_links) > 0:
                charge_link = charge_links.iloc[0]
                print(f"Hydrogen Charging Cost: {charge_link.get('capital_cost', 'N/A')} €/MW")
                print(f"Hydrogen Charging Efficiency: {charge_link.get('efficiency', 'N/A')}")
            
            if len(discharge_links) > 0:
                discharge_link = discharge_links.iloc[0]
                print(f"Hydrogen Discharging Cost: {discharge_link.get('capital_cost', 'N/A')} €/MW")
                print(f"Hydrogen Discharging Efficiency: {discharge_link.get('efficiency', 'N/A')}")
    except:
        print("Could not extract specific hydrogen cost components")

if __name__ == "__main__":
    analyze_energy_and_costs()
