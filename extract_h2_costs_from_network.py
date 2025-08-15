#!/usr/bin/env python3

import pypsa
import pandas as pd

def extract_h2_costs():
    """Extract hydrogen storage costs from the optimized PyPSA network"""
    
    print("Loading PyPSA network...")
    network_path = "results/de-electricity-only-2035-mayk/networks/base_s_1___2035.nc"
    n = pypsa.Network(network_path)
    
    print("\n" + "="*60)
    print("HYDROGEN STORAGE COSTS FROM PYPSA NETWORK")
    print("="*60)
    
    # Check stores for hydrogen
    print("\nHydrogen Stores (Energy Storage):")
    print("-" * 40)
    if len(n.stores) > 0:
        h2_stores = n.stores[n.stores.carrier.str.contains('H2', case=False, na=False)]
        if len(h2_stores) > 0:
            for idx, store in h2_stores.iterrows():
                print(f"Store: {idx}")
                print(f"  Carrier: {store['carrier']}")
                print(f"  Optimal Energy Capacity: {store['e_nom_opt']:.1f} MWh")
                print(f"  Capital Cost: {store['capital_cost']:.3f} EUR/MWh")
                print(f"  Marginal Cost: {store.get('marginal_cost', 'N/A')} EUR/MWh")
    
    # Check links for hydrogen charging/discharging
    print("\nHydrogen Links (P2G2P Components):")
    print("-" * 40)
    if len(n.links) > 0:
        h2_links = n.links[n.links.carrier.str.contains('H2', case=False, na=False)]
        if len(h2_links) > 0:
            for idx, link in h2_links.iterrows():
                print(f"Link: {idx}")
                print(f"  Carrier: {link['carrier']}")
                print(f"  Optimal Power Capacity: {link['p_nom_opt']:.1f} MW")
                print(f"  Capital Cost: {link['capital_cost']:.1f} EUR/MW")
                print(f"  Marginal Cost: {link.get('marginal_cost', 'N/A')} EUR/MWh")
                print(f"  Efficiency: {link.get('efficiency', 'N/A')}")
                print()
        else:
            print("No hydrogen links found. Checking all links...")
            # Check all links
            for idx, link in n.links.iterrows():
                if 'H2' in str(link['carrier']) or 'hydrogen' in str(link['carrier']).lower():
                    print(f"Found H2-related link: {idx} - {link['carrier']}")
    
    # Summary calculation
    print("\n" + "="*60)
    print("SUMMARY - PYPSA OPTIMIZED COSTS")
    print("="*60)
    
    if len(h2_stores) > 0:
        store = h2_stores.iloc[0]
        storage_cost_eur_mwh = store['capital_cost']
        storage_cost_eur_kwh = storage_cost_eur_mwh / 1000
        print(f"Hydrogen Storage CAPEX: {storage_cost_eur_mwh:.3f} EUR/MWh = {storage_cost_eur_kwh:.6f} EUR/kWh")
    
    if len(h2_links) > 0:
        # Try to identify charging vs discharging
        for idx, link in h2_links.iterrows():
            print(f"{link['carrier']} - {link['capital_cost']:.1f} EUR/MW (Efficiency: {link.get('efficiency', 'N/A')})")

if __name__ == "__main__":
    extract_h2_costs()
