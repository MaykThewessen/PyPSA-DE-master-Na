#!/usr/bin/env python3
"""
CORRECTED Script to systematically apply technology name mapping to costs_2035.csv file.

This script:
1. Reverts the incorrect mapping file and creates a new corrected version
2. Loads the costs_2035.csv file into a DataFrame
3. Applies ONLY proper energy storage technology mappings
4. EXCLUDES transportation technologies (electric vehicles, charging infrastructure)
5. Preserves all other columns unchanged
6. Saves the updated file and provides a summary of changes

CRITICAL FIX: Electric vehicles and charging infrastructure are NOT energy storage technologies!
"""

import pandas as pd
import os
from pathlib import Path
import shutil

def backup_and_revert_original_file():
    """Backup the incorrectly mapped file and revert to original."""
    original_file = "resources/de-all-tech-2035-mayk/costs_2035.csv"
    mapped_file = "resources/de-all-tech-2035-mayk/costs_2035_mapped.csv"
    backup_file = "resources/de-all-tech-2035-mayk/costs_2035_mapped_INCORRECT_BACKUP.csv"
    
    # Backup the incorrect mapping
    if os.path.exists(mapped_file):
        shutil.copy2(mapped_file, backup_file)
        print(f"✓ Backed up incorrect mapping to: {backup_file}")
    
    # Start fresh from original
    if os.path.exists(original_file):
        print(f"✓ Using original file: {original_file}")
        return pd.read_csv(original_file)
    else:
        raise FileNotFoundError(f"Original costs file not found: {original_file}")

def create_corrected_storage_mapping():
    """Create a corrected mapping that ONLY includes actual energy storage technologies."""
    
    # Define ONLY actual energy storage technologies (exclude transportation!)
    corrected_mapping = {
        # Vanadium Redox Flow Battery
        "Vanadium-Redox-Flow": "vanadium",
        "Vanadium Redox Flow": "vanadium", 
        "vanadium-redox-flow": "vanadium",
        "VRF": "vanadium",
        "VRFB": "vanadium",
        "Vanadium-Redox-Flow-store": "vanadium-store",
        "Vanadium-Redox-Flow-charger": "vanadium-charger", 
        "Vanadium-Redox-Flow-discharger": "vanadium-discharger",
        "Vanadium-Redox-Flow-bicharger": "vanadium-bicharger",
        
        # Iron-Air Battery (grid storage)
        "Iron-Air": "IronAir",
        "iron-air": "IronAir",
        "Iron Air": "IronAir",
        "ironair": "IronAir",
        "iron-air battery": "IronAir",  # This is grid-scale iron-air, NOT vehicles
        "Iron-Air-charge": "IronAir",
        "Iron-Air-discharge": "IronAir",
        "Iron-Air-store": "IronAir-store",
        "Iron-Air-charger": "IronAir-charger",
        "Iron-Air-discharger": "IronAir-discharger",
        "Iron-Air-bicharger": "IronAir-bicharger",
        "iron-air battery charge": "IronAir-charger",
        "iron-air battery discharge": "IronAir-discharger",
        
        # Hydrogen Storage
        "hydrogen": "H2",
        "Hydrogen": "H2", 
        "hydrogen storage": "H2",
        "hydrogen storage underground": "H2",
        "H2": "H2",  # Already correct
        "h2": "H2",
        "H2-store": "H2-store",
        "H2-charger": "H2-charger",
        "H2-discharger": "H2-discharger", 
        "H2-bicharger": "H2-bicharger",
        "Hydrogen-charger": "H2-charger",
        "Hydrogen-discharger": "H2-discharger",
        "Hydrogen-store": "H2",
        
        # Electrolysis (H2 production)
        "H2 electrolysis": "H2-charger",
        "H2 electrolyzer": "H2-charger",
        "electrolysis": "H2-charger",
        "electrolyser": "H2-charger",
        "Electrolysis": "H2-charger",
        
        # Fuel Cells (H2 consumption)
        "H2 fuel cell": "H2-discharger",
        "fuel cell": "H2-discharger",
        "fuel-cell": "H2-discharger", 
        "Fuel Cell": "H2-discharger",
        
        # Compressed Air Energy Storage
        "Compressed-Air-Adiabatic": "CAES",
        "compressed-air-adiabatic": "CAES",
        "Compressed Air Adiabatic": "CAES",
        "compressed air adiabatic": "CAES",
        "Compressed-Air": "CAES",
        "compressed-air": "CAES",
        "Compressed Air": "CAES", 
        "compressed air": "CAES",
        "CAES": "CAES",  # Already correct
        "caes": "CAES",
        "Compressed-Air-Adiabatic-store": "CAES-store",
        "Compressed-Air-Adiabatic-charger": "CAES-charger",
        "Compressed-Air-Adiabatic-discharger": "CAES-discharger",
        "Compressed-Air-Adiabatic-bicharger": "CAES-bicharger",
        
        # Battery Energy Storage Systems (grid-scale, home, utility)
        "battery_1h": "battery1",
        "battery-1h": "battery1",
        "battery1h": "battery1", 
        "Battery-1h": "battery1",
        "1h-battery": "battery1",
        "battery1": "battery1",  # Already correct
        "battery_1h-store": "battery1-store",
        "battery_1h-charger": "battery1-charger",
        "battery_1h-discharger": "battery1-discharger",
        "battery_1h-bicharger": "battery1-bicharger",
        
        "battery_2h": "battery2",
        "battery-2h": "battery2", 
        "battery2h": "battery2",
        "Battery-2h": "battery2",
        "2h-battery": "battery2",
        "battery2": "battery2",  # Already correct
        "battery_2h-store": "battery2-store",
        "battery_2h-charger": "battery2-charger",
        "battery_2h-discharger": "battery2-discharger",
        "battery_2h-bicharger": "battery2-bicharger",
        
        "battery_4h": "battery4",
        "battery-4h": "battery4",
        "battery4h": "battery4",
        "Battery-4h": "battery4",
        "4h-battery": "battery4", 
        "battery4": "battery4",  # Already correct
        "battery_4h-store": "battery4-store",
        "battery_4h-charger": "battery4-charger",
        "battery_4h-discharger": "battery4-discharger",
        "battery_4h-bicharger": "battery4-bicharger",
        
        "battery_8h": "battery8",
        "battery-8h": "battery8",
        "battery8h": "battery8",
        "Battery-8h": "battery8",
        "8h-battery": "battery8",
        "battery8": "battery8",  # Already correct
        "battery_8h-store": "battery8-store",
        "battery_8h-charger": "battery8-charger",
        "battery_8h-discharger": "battery8-discharger",
        "battery_8h-bicharger": "battery8-bicharger",
        
        "battery_12h": "battery12",
        "battery_24h": "battery24",
        "battery_48h": "battery48",
        
        # Generic battery storage (grid/home)
        "battery": "battery",  # Already correct
        "Battery": "battery",
        "battery storage": "battery-store",
        "battery inverter": "battery-charger",  # Inverter acts as bidirectional charger
        "battery charger": "battery-charger",
        "battery discharger": "battery-discharger", 
        "battery bicharger": "battery-bicharger",
        
        # Home battery systems (energy storage)
        "home battery inverter": "battery",  # Home batteries are still battery storage
        "home battery storage": "battery",
        
        # Specific battery chemistries for grid storage
        "Li-Ion": "battery",
        "lithium-ion": "battery",
        "Lithium-Ion": "battery",
        "LFP": "battery",
        "Lithium-Ion-LFP": "battery",
        "Lithium-Ion-LFP-bicharger": "battery-bicharger",
        "Lithium-Ion-LFP-store": "battery-store",
        
        # Legacy naming
        "Ebattery1": "battery1",
        "Ebattery2": "battery2",
        "Ebattery4": "battery4",
        "Ebattery8": "battery8",
        
        # Industrial hydrogen processes (these are H2 related)
        "biogas plus hydrogen": "H2",
        "central hydrogen CHP": "H2",
        "digestible biomass to hydrogen": "H2", 
        "hydrogen direct iron reduction furnace": "H2",
        "hydrogen storage compressor": "H2",
        "hydrogen storage tank type 1": "H2",
        "hydrogen storage tank type 1 including compressor": "H2",
        "solid biomass to hydrogen": "H2",
        "LOHC dehydrogenation": "H2",
        "LOHC dehydrogenation (small scale)": "H2",
        "LOHC hydrogenation": "H2"
    }
    
    # EXPLICITLY EXCLUDED technologies (these are NOT energy storage):
    excluded_transportation = {
        "Battery electric (passenger cars)",
        "Battery electric (trucks)", 
        "Hydrogen fuel cell (passenger cars)",
        "Hydrogen fuel cell (trucks)",
        "Charging infrastructure fast (purely) battery electric vehicles passenger cars",
        "Charging infrastructure slow (purely) battery electric vehicles passenger cars",
        "BEV Bus city",
        "BEV Coach", 
        "BEV Truck Semi-Trailer max 50 tons",
        "BEV Truck Solo max 26 tons",
        "BEV Truck Trailer max 56 tons"
    }
    
    print("✓ Created corrected storage mapping (transportation technologies EXCLUDED)")
    print(f"  - Storage technologies to map: {len(corrected_mapping)}")
    print(f"  - Transportation technologies excluded: {len(excluded_transportation)}")
    
    return corrected_mapping, excluded_transportation

def apply_corrected_mapping(df, storage_mapping, excluded_techs):
    """Apply ONLY storage technology mappings, excluding transportation."""
    print("\n" + "="*60)
    print("APPLYING CORRECTED TECHNOLOGY MAPPING")
    print("="*60)
    
    df_mapped = df.copy()
    changes_made = {}
    
    # Apply storage mappings only
    for current_name, target_name in storage_mapping.items():
        mask = df_mapped['technology'] == current_name
        if mask.any():
            count = mask.sum()
            df_mapped.loc[mask, 'technology'] = target_name
            changes_made[current_name] = {
                'target': target_name,
                'count': count,
                'type': 'storage_technology'
            }
            print(f"  ✓ Mapped storage tech: '{current_name}' → '{target_name}' ({count} entries)")
    
    # Report excluded technologies found
    excluded_found = []
    for tech in excluded_techs:
        if tech in df['technology'].values:
            count = (df['technology'] == tech).sum()
            excluded_found.append((tech, count))
            print(f"  ⚠ EXCLUDED (transportation): '{tech}' ({count} entries) - NOT MAPPED")
    
    return df_mapped, changes_made, excluded_found

def save_corrected_results(df_mapped, changes_made, excluded_found):
    """Save the corrected mapped DataFrame."""
    # Save the corrected mapped file
    output_file = "resources/de-all-tech-2035-mayk/costs_2035_mapped.csv"
    df_mapped.to_csv(output_file, index=False)
    print(f"\n✓ Saved CORRECTED mapped costs file to: {output_file}")
    
    # Create corrected report
    report_file = "technology_mapping_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("Technology Mapping Report\n")
        f.write("="*50 + "\n\n")
        f.write(f"Total technologies mapped: {len(changes_made)}\n")
        f.write(f"Total entries changed: {sum(change['count'] for change in changes_made.values())}\n\n")
        
        f.write("Detailed mapping changes:\n")
        f.write("-" * 30 + "\n")
        for original, change_info in sorted(changes_made.items()):
            f.write(f"'{original}' → '{change_info['target']}' ({change_info['count']} entries)\n")
            if change_info.get('original_mapping'):
                f.write(f"  (partial match with '{change_info['original_mapping']}') \n")
        
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
        
        f.write("\nTransportation technologies EXCLUDED (not mapped):\n")
        f.write("-" * 30 + "\n")
        for tech, count in excluded_found:
            f.write(f"'{tech}' ({count} entries) - Transportation, NOT energy storage\n")
    
    print(f"✓ Saved corrected mapping report to: {report_file}")

def main():
    """Main function."""
    print("🔧 CORRECTED TECHNOLOGY MAPPING")
    print("="*50)
    print("FIXING INCORRECT MAPPING: Electric vehicles ≠ Energy storage!")
    print("")
    
    # Step 1: Backup and revert
    df = backup_and_revert_original_file()
    
    # Step 2: Create corrected mapping
    storage_mapping, excluded_techs = create_corrected_storage_mapping()
    
    # Step 3: Apply corrected mapping
    df_mapped, changes_made, excluded_found = apply_corrected_mapping(df, storage_mapping, excluded_techs)
    
    # Step 4: Analyze results
    print("\n" + "="*60)
    print("MAPPING RESULTS SUMMARY")
    print("="*60)
    
    technologies_before = df['technology'].nunique()
    technologies_after = df_mapped['technology'].nunique()
    total_entries_changed = sum(change['count'] for change in changes_made.values())
    
    print(f"Technologies before mapping: {technologies_before}")
    print(f"Technologies after mapping: {technologies_after}")
    print(f"Storage technologies mapped: {len(changes_made)}")
    print(f"Total entries changed: {total_entries_changed}")
    print(f"Transportation techs excluded: {len(excluded_found)}")
    
    # Step 5: Save results
    save_corrected_results(df_mapped, changes_made, excluded_found)
    
    print("\n✅ CORRECTED MAPPING COMPLETE!")
    print("✅ Energy storage technologies properly mapped")
    print("✅ Transportation technologies correctly preserved")
    print("✅ Electric vehicles are NOT confused with battery storage")

if __name__ == "__main__":
    main()
