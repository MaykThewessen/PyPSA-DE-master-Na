#!/usr/bin/env python3

import pandas as pd
import sys
sys.path.append('scripts')
from scripts.add_electricity import load_costs

# Load the costs file manually first
costs_raw = pd.read_csv('analysis-de-white-paper-v3/costs_2035_technology_mapped.csv', index_col=[0, 1]).sort_index()
print("Raw costs file structure:")
print(costs_raw.head())
print(f"\nRaw costs shape: {costs_raw.shape}")

# Check for transmission entries
transmission_techs = ['HVAC overhead', 'HVDC overhead', 'HVDC submarine', 'HVDC inverter pair']
print(f"\nLooking for transmission technologies: {transmission_techs}")

for tech in transmission_techs:
    matches = costs_raw.index.get_level_values(0) == tech
    if matches.any():
        print(f"\nFound {tech}:")
        print(costs_raw[matches])
    else:
        print(f"\n{tech}: NOT FOUND")

# Now try the load_costs function
print("\n" + "="*50)
print("Testing load_costs function")

# Mock config
config = {
    'fill_values': {'FOM': 0, 'VOM': 0, 'efficiency': 1, 'fuel': 0, 'investment': 0, 'lifetime': 25, 'CO2 intensity': 0, 'discount rate': 0.07},
    'overwrites': {}
}

try:
    costs = load_costs('analysis-de-white-paper-v3/costs_2035_technology_mapped.csv', config, max_hours=None, nyears=1.0)
    print(f"Processed costs shape: {costs.shape}")
    print(f"Processed costs columns: {costs.columns.tolist()}")
    
    print(f"\nChecking for transmission cost entries:")
    for tech in transmission_techs:
        if tech in costs.index:
            print(f"{tech}: capital_cost = {costs.at[tech, 'capital_cost']}")
        else:
            print(f"{tech}: NOT FOUND")
            
    print(f"\nAll technologies in processed costs:")
    print(costs.index.tolist()[:20])  # First 20
    
except Exception as e:
    print(f"Error in load_costs: {e}")
    import traceback
    traceback.print_exc()
