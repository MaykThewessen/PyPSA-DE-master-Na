#!/usr/bin/env python3
"""
Script to fix missing 'battery storage' entries by duplicating 'battery-store' data.
"""

import pandas as pd

def fix_battery_storage(file_path):
    """Add 'battery storage' entries based on 'battery-store' data"""
    df = pd.read_csv(file_path)
    
    # Find all battery-store entries
    battery_store_entries = df[df['technology'] == 'battery-store'].copy()
    
    print(f"Found {len(battery_store_entries)} 'battery-store' entries")
    
    if len(battery_store_entries) > 0:
        # Create duplicate entries with 'battery storage' name
        battery_storage_entries = battery_store_entries.copy()
        battery_storage_entries['technology'] = 'battery storage'
        
        # Append to the dataframe
        df_updated = pd.concat([df, battery_storage_entries], ignore_index=True)
        
        print(f"Added {len(battery_storage_entries)} 'battery storage' entries")
        
        # Save the updated file
        df_updated.to_csv(file_path, index=False)
        print(f"Updated file saved")
        
        return df_updated
    else:
        print("No 'battery-store' entries found to duplicate")
        return df

if __name__ == "__main__":
    file_path = "resources/de-all-tech-2035-mayk/costs_2035.csv"
    fix_battery_storage(file_path)
