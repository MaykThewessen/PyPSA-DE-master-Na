#!/usr/bin/env python3
"""
Script to systematically apply technology name mapping to costs_2035.csv file.

This script:
1. Loads the costs_2035.csv file into a DataFrame
2. Loads the mapping from storage_mapping_summary.csv 
3. Applies the mapping to the 'technology' column
4. Ensures all related entries (with same base technology but different parameters) are renamed consistently
5. Preserves all other columns unchanged
6. Saves the updated file and provides a summary of changes
"""

import pandas as pd
import os
from pathlib import Path

def load_costs_data():
    """Load the costs CSV file."""
    costs_file = "resources/de-all-tech-2035-mayk/costs_2035.csv"
    if not os.path.exists(costs_file):
        raise FileNotFoundError(f"Costs file not found: {costs_file}")
    
    print(f"Loading costs data from: {costs_file}")
    df = pd.read_csv(costs_file)
    print(f"Loaded {len(df)} rows with {df['technology'].nunique()} unique technologies")
    return df

def load_mapping_data():
    """Load the technology mapping data."""
    mapping_file = "storage_mapping_summary.csv"
    if not os.path.exists(mapping_file):
        raise FileNotFoundError(f"Mapping file not found: {mapping_file}")
    
    print(f"Loading mapping data from: {mapping_file}")
    mapping_df = pd.read_csv(mapping_file)
    print(f"Loaded {len(mapping_df)} mapping entries")
    
    # Create a dictionary mapping from current names to target names
    mapping_dict = {}
    for _, row in mapping_df.iterrows():
        current_name = row['Current_Name']
        target_name = row['Target_Name']
        mapping_dict[current_name] = target_name
    
    print(f"Created mapping dictionary with {len(mapping_dict)} entries")
    return mapping_dict, mapping_df

def analyze_technologies_before_mapping(df):
    """Analyze technologies in the costs file before mapping."""
    print("\n" + "="*60)
    print("ANALYSIS BEFORE MAPPING")
    print("="*60)
    
    technologies = df['technology'].value_counts()
    print(f"Total unique technologies: {len(technologies)}")
    print(f"Total rows: {len(df)}")
    
    # Show technologies that might be storage-related
    storage_keywords = ['battery', 'storage', 'hydrogen', 'H2', 'vanadium', 'iron-air', 
                       'compressed', 'caes', 'flow', 'redox']
    
    storage_techs = []
    for tech in technologies.index:
        for keyword in storage_keywords:
            if keyword.lower() in tech.lower():
                storage_techs.append(tech)
                break
    
    print(f"\nPotential storage technologies found ({len(storage_techs)}):")
    for tech in sorted(storage_techs):
        count = technologies[tech]
        print(f"  - {tech} ({count} entries)")
    
    return technologies

def apply_mapping(df, mapping_dict):
    """Apply the technology mapping to the DataFrame."""
    print("\n" + "="*60)
    print("APPLYING TECHNOLOGY MAPPING")
    print("="*60)
    
    # Create a copy to avoid modifying original
    df_mapped = df.copy()
    
    # Track changes
    changes_made = {}
    technologies_mapped = set()
    
    # Apply direct mapping
    for current_name, target_name in mapping_dict.items():
        # Find exact matches
        mask = df_mapped['technology'] == current_name
        if mask.any():
            count = mask.sum()
            df_mapped.loc[mask, 'technology'] = target_name
            changes_made[current_name] = {
                'target': target_name,
                'count': count,
                'type': 'exact_match'
            }
            technologies_mapped.add(current_name)
            print(f"  ✓ Mapped '{current_name}' -> '{target_name}' ({count} entries)")
    
    # Apply partial matching for complex technology names
    # This handles cases where the costs file might have slightly different naming
    unmapped_techs = set(df_mapped['technology'].unique()) - technologies_mapped
    
    for tech in list(unmapped_techs):
        for current_name, target_name in mapping_dict.items():
            # Check if the technology contains key components of the mapping
            tech_lower = tech.lower()
            current_lower = current_name.lower()
            
            # For storage technologies, check if base name matches
            if any(keyword in tech_lower for keyword in ['battery', 'storage', 'hydrogen', 'h2', 'vanadium', 'iron', 'compressed', 'caes']):
                # Extract base technology name for comparison
                if current_lower in tech_lower or tech_lower in current_lower:
                    # Additional checks to avoid false positives
                    if len(current_name) > 3 and current_name not in tech:  # Avoid very short matches
                        mask = df_mapped['technology'] == tech
                        if mask.any():
                            count = mask.sum()
                            df_mapped.loc[mask, 'technology'] = target_name
                            changes_made[tech] = {
                                'target': target_name,
                                'count': count,
                                'type': 'partial_match',
                                'original_mapping': current_name
                            }
                            technologies_mapped.add(tech)
                            print(f"  ✓ Mapped '{tech}' -> '{target_name}' ({count} entries) [partial match with '{current_name}']")
                            break
    
    return df_mapped, changes_made

def analyze_technologies_after_mapping(df_original, df_mapped, changes_made):
    """Analyze technologies after mapping."""
    print("\n" + "="*60)
    print("ANALYSIS AFTER MAPPING")
    print("="*60)
    
    technologies_after = df_mapped['technology'].value_counts()
    print(f"Total unique technologies after mapping: {len(technologies_after)}")
    print(f"Total rows: {len(df_mapped)} (unchanged)")
    
    # Show summary of changes
    total_entries_changed = sum(change['count'] for change in changes_made.values())
    print(f"\nSummary of changes:")
    print(f"  - Technologies mapped: {len(changes_made)}")
    print(f"  - Total entries changed: {total_entries_changed}")
    
    # Group changes by target technology
    target_summary = {}
    for original, change_info in changes_made.items():
        target = change_info['target']
        if target not in target_summary:
            target_summary[target] = []
        target_summary[target].append((original, change_info['count']))
    
    print(f"\nChanges grouped by target technology:")
    for target, mappings in sorted(target_summary.items()):
        total_count = sum(count for _, count in mappings)
        print(f"  → {target} ({total_count} total entries):")
        for original, count in sorted(mappings):
            print(f"      ← {original} ({count} entries)")
    
    return technologies_after

def save_results(df_mapped, changes_made):
    """Save the mapped DataFrame and create a summary report."""
    # Save the updated costs file
    output_file = "analysis-de-white-paper-v3/costs_2035_technology_mapped.csv"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_mapped.to_csv(output_file, index=False)
    print(f"\n✓ Saved mapped costs file to: {output_file}")
    
    # Create a summary report
    report_file = "analysis-de-white-paper-v3/technology_mapping_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("Technology Mapping Report\n")
        f.write("="*50 + "\n\n")
        f.write(f"Total technologies mapped: {len(changes_made)}\n")
        f.write(f"Total entries changed: {sum(change['count'] for change in changes_made.values())}\n\n")
        
        f.write("Detailed mapping changes:\n")
        f.write("-" * 30 + "\n")
        for original, change_info in sorted(changes_made.items()):
            f.write(f"'{original}' -> '{change_info['target']}' ({change_info['count']} entries)\n")
            if change_info['type'] == 'partial_match':
                f.write(f"  (partial match with '{change_info['original_mapping']}')\n")
        
        f.write("\nTarget technology summary:\n")
        f.write("-" * 30 + "\n")
        target_summary = {}
        for original, change_info in changes_made.items():
            target = change_info['target']
            if target not in target_summary:
                target_summary[target] = []
            target_summary[target].append((original, change_info['count']))
        
        for target, mappings in sorted(target_summary.items()):
            total_count = sum(count for _, count in mappings)
            f.write(f"{target} ({total_count} total entries):\n")
            for original, count in sorted(mappings):
                f.write(f"  <- {original} ({count} entries)\n")
            f.write("\n")
    
    print(f"✓ Saved mapping report to: {report_file}")

def validate_mapping(df_original, df_mapped):
    """Validate that the mapping preserved data integrity."""
    print("\n" + "="*60)
    print("VALIDATION")
    print("="*60)
    
    # Check that no data was lost
    assert len(df_original) == len(df_mapped), "Row count mismatch!"
    
    # Check that all other columns are unchanged
    other_columns = [col for col in df_original.columns if col != 'technology']
    for col in other_columns:
        assert df_original[col].equals(df_mapped[col]), f"Column {col} was modified!"
    
    print("✓ Validation passed - all data integrity checks successful")
    print("✓ Row count preserved")
    print("✓ All non-technology columns unchanged")

def main():
    """Main function to execute the mapping process."""
    try:
        print("Technology Mapping Script")
        print("="*60)
        
        # Load data
        df_costs = load_costs_data()
        mapping_dict, mapping_df = load_mapping_data()
        
        # Analyze before mapping
        technologies_before = analyze_technologies_before_mapping(df_costs)
        
        # Apply mapping
        df_mapped, changes_made = apply_mapping(df_costs, mapping_dict)
        
        # Analyze after mapping
        technologies_after = analyze_technologies_after_mapping(df_costs, df_mapped, changes_made)
        
        # Validate results
        validate_mapping(df_costs, df_mapped)
        
        # Save results
        save_results(df_mapped, changes_made)
        
        print("\n" + "="*60)
        print("MAPPING COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"✓ Original file: resources/de-all-tech-2035-mayk/costs_2035.csv")
        print(f"✓ Mapped file: resources/de-all-tech-2035-mayk/costs_2035_mapped.csv")
        print(f"✓ Report file: technology_mapping_report.txt")
        print(f"✓ Technologies mapped: {len(changes_made)}")
        print(f"✓ Entries changed: {sum(change['count'] for change in changes_made.values())}")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
