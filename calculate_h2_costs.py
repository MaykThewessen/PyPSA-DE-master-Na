#!/usr/bin/env python3
"""
Calculate hydrogen storage CAPEX costs from PyPSA network results.
"""

import pypsa
import pandas as pd
import numpy as np
import os

def load_network():
    """Load the solved PyPSA network."""
    network_file = "results/de-electricity-only-2035-mayk/networks/base_s_1___2035.nc"
    if not os.path.exists(network_file):
        raise FileNotFoundError(f"Network file not found: {network_file}")
    
    print(f"Loading network from: {network_file}")
    n = pypsa.Network(network_file)
    return n

def analyze_hydrogen_costs(n):
    """Analyze hydrogen storage costs and capacities."""
    
    print("=== HYDROGEN STORAGE COST ANALYSIS ===\n")
    
    # Find H2 stores
    h2_stores = n.stores[n.stores.carrier == 'H2 Store']
    h2_stores_opt = h2_stores[h2_stores.e_nom_opt > 0]
    
    if h2_stores_opt.empty:
        print("No optimized H2 stores found.")
        return
    
    print("H2 Stores (Energy Storage):")
    print(f"Number of H2 stores: {len(h2_stores_opt)}")
    
    total_h2_energy_mwh = h2_stores_opt['e_nom_opt'].sum()
    total_h2_energy_gwh = total_h2_energy_mwh / 1000
    total_h2_energy_twh = total_h2_energy_mwh / 1e6
    
    print(f"Total H2 energy capacity: {total_h2_energy_mwh:.1f} MWh = {total_h2_energy_gwh:.1f} GWh = {total_h2_energy_twh:.2f} TWh")
    
    # Check cost parameters
    if 'capital_cost' in h2_stores_opt.columns:
        h2_energy_cost_eur_mwh = h2_stores_opt['capital_cost'].iloc[0]
        h2_energy_cost_eur_kwh = h2_energy_cost_eur_mwh / 1000
        
        print(f"H2 energy storage cost: {h2_energy_cost_eur_mwh:.2f} EUR/MWh = {h2_energy_cost_eur_kwh:.3f} EUR/kWh")
        
        total_h2_energy_capex = total_h2_energy_mwh * h2_energy_cost_eur_mwh
        print(f"Total H2 energy CAPEX: {total_h2_energy_capex/1e9:.2f} billion EUR")
    else:
        print("No capital_cost data found in stores.")
    
    # Find H2-related links (electrolyzers, fuel cells)
    h2_links = n.links[n.links.carrier.str.contains('H2', na=False) | 
                      n.links.bus1.str.contains('H2', na=False)]
    h2_links_opt = h2_links[h2_links.p_nom_opt > 0]
    
    if not h2_links_opt.empty:
        print(f"\nH2 Links (Power Equipment):")
        print(f"Number of H2 links: {len(h2_links_opt)}")
        
        for idx, link in h2_links_opt.iterrows():
            power_mw = link['p_nom_opt']
            power_gw = power_mw / 1000
            carrier = link['carrier']
            
            print(f"  {carrier}: {power_mw:.1f} MW = {power_gw:.2f} GW")
            
            if 'capital_cost' in link and pd.notna(link['capital_cost']):
                cost_eur_mw = link['capital_cost']
                cost_eur_kw = cost_eur_mw / 1000
                total_link_capex = power_mw * cost_eur_mw
                
                print(f"    Cost: {cost_eur_mw:.2f} EUR/MW = {cost_eur_kw:.3f} EUR/kW")
                print(f"    Total CAPEX: {total_link_capex/1e6:.2f} million EUR")
    
    # Summary calculation
    print(f"\n=== SUMMARY ===")
    print(f"H2 Storage Energy Capacity: {total_h2_energy_gwh:.1f} GWh")
    
    # Try to find associated power capacity from our storage details
    try:
        storage_details = pd.read_csv("germany_2035_storage_details.csv")
        h2_row = storage_details[storage_details['technology'] == 'H2 Store']
        if not h2_row.empty:
            h2_power_gw = h2_row['power_gw'].iloc[0]
            h2_power_mw = h2_power_gw * 1000
            print(f"H2 Storage Power Capacity: {h2_power_gw:.1f} GW = {h2_power_mw:.1f} MW")
            
            duration_hours = h2_row['duration_hours'].iloc[0]
            print(f"H2 Storage Duration: {duration_hours:.1f} hours = {duration_hours/24:.1f} days")
        
    except FileNotFoundError:
        print("Storage details file not found.")
    
    # Print all available cost-related columns for debugging
    print(f"\n=== DEBUGGING INFO ===")
    print("Available columns in stores:")
    print(h2_stores_opt.columns.tolist())
    
    if not h2_links_opt.empty:
        print("\nAvailable columns in H2 links:")
        print(h2_links_opt.columns.tolist())
        print("\nH2 links details:")
        print(h2_links_opt[['carrier', 'bus0', 'bus1', 'p_nom_opt']].to_string())

def main():
    """Main function."""
    
    try:
        n = load_network()
        analyze_hydrogen_costs(n)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
