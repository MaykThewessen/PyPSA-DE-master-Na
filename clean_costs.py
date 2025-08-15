#!/usr/bin/env python3
"""
Script to clean duplicate entries from cost data file.
For duplicates, keep the first occurrence and remove the rest.
"""

import pandas as pd
import sys

def clean_cost_data(input_file, output_file):
    """Clean duplicate entries from cost data CSV file"""
    # Read the CSV file
    print(f"Reading {input_file}...")
    df = pd.read_csv(input_file)
    
    print(f"Original entries: {len(df)}")
    
    # Check for duplicates based on technology and parameter columns
    duplicate_mask = df.duplicated(subset=['technology', 'parameter'], keep='first')
    duplicates = df[duplicate_mask]
    
    print(f"Found {len(duplicates)} duplicate entries")
    
    if len(duplicates) > 0:
        print("Duplicate entries found:")
        for _, row in duplicates.iterrows():
            print(f"  {row['technology']} - {row['parameter']}")
    
    # Remove duplicates, keeping the first occurrence
    cleaned_df = df.drop_duplicates(subset=['technology', 'parameter'], keep='first')
    
    print(f"Cleaned entries: {len(cleaned_df)}")
    print(f"Removed {len(df) - len(cleaned_df)} duplicate entries")
    
    # Save the cleaned data
    cleaned_df.to_csv(output_file, index=False)
    print(f"Cleaned data saved to {output_file}")

if __name__ == "__main__":
    input_file = "resources/de-all-tech-2035-mayk/costs_2035.csv"
    output_file = "resources/de-all-tech-2035-mayk/costs_2035_cleaned.csv"
    
    clean_cost_data(input_file, output_file)
