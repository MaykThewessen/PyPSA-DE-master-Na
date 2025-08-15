#!/usr/bin/env python3

import pandas as pd
import sys

def update_hydrogen_costs():
    """Update the costs file with realistic hydrogen costs"""
    
    costs_file = "resources/de-realistic-h2-costs-2035/costs_2035.csv"
    
    print(f"Loading costs from {costs_file}")
    costs_df = pd.read_csv(costs_file)
    
    print(f"Original costs shape: {costs_df.shape}")
    
    # Create dictionary of cost updates
    cost_updates = {
        # HYDROGEN STORAGE - REALISTIC COSTS (53x more expensive)
        "H2 Store": 5000000,  # €5,000,000/GWh = €5000/MWh
        "Hydrogen-store": 5000000,
        "hydrogen storage underground": 5000000,
        
        # HYDROGEN PRODUCTION - REALISTIC COSTS (11x more expensive)
        "electrolysis": 1710000,  # €1,710,000/MW
        "H2 Electrolysis": 1710000,
        "Hydrogen-charger": 1710000,
        "Alkaline electrolyzer large size": 1710000,
        "PEM electrolyzer small size": 1710000,
        
        # HYDROGEN POWER GENERATION - REALISTIC COSTS
        "H2 Fuel Cell": 1510000,  # €1,510,000/MW (15x more expensive)
        "Hydrogen-discharger": 1510000,
        "fuel cell": 1510000,
        "central hydrogen CHP": 1510000,
        "H2 Turbine": 1200000,     # €1,200,000/MW
        "H2 CCGT": 1300000,        # €1,300,000/MW  
        "H2 OCGT": 1100000,        # €1,100,000/MW
    }
    
    updates_made = 0
    
    for technology, new_cost in cost_updates.items():
        # Find rows with this technology and investment parameter
        mask = (costs_df['technology'] == technology) & (costs_df['parameter'] == 'investment')
        
        if mask.any():
            old_cost = costs_df.loc[mask, 'value'].iloc[0]
            costs_df.loc[mask, 'value'] = new_cost
            print(f"Updated {technology}: {old_cost:.0f} -> {new_cost:.0f} EUR/MW or EUR/MWh")
            updates_made += 1
        else:
            print(f"WARNING: {technology} not found in costs database")
    
    print(f"\nMade {updates_made} cost updates")
    
    # Save updated costs
    costs_df.to_csv(costs_file, index=False)
    print(f"Updated costs saved to {costs_file}")
    
    # Show hydrogen-related costs for verification
    print("\nHydrogen-related costs after update:")
    h2_costs = costs_df[costs_df['technology'].str.contains('H2|hydrogen|electrolysis|fuel cell', case=False, na=False)]
    h2_investments = h2_costs[h2_costs['parameter'] == 'investment']
    
    for idx, row in h2_investments.iterrows():
        print(f"  {row['technology']}: {row['value']:,.0f} {row['unit']}")
    
    return costs_df

if __name__ == "__main__":
    update_hydrogen_costs()
