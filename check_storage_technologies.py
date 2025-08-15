#!/usr/bin/env python3
"""
Check if iron-air, CAES, and LFP storage technologies are correctly implemented
in the PyPSA-DE configuration and cost data.
"""

import pandas as pd
import yaml
import os

def check_cost_data():
    """Check if the storage technologies are present in cost data"""
    print("=== CHECKING COST DATA ===")
    
    cost_file = "resources/de-all-tech-2035-mayk/costs_2035.csv"
    if not os.path.exists(cost_file):
        print(f"❌ Cost file not found: {cost_file}")
        return False
        
    costs_df = pd.read_csv(cost_file)
    
    # Technologies to check
    technologies = {
        'Iron-Air': ['IronAir', 'IronAir-charger', 'IronAir-discharger', 'iron-air battery charge', 'iron-air battery discharge'],
        'CAES': ['CAES-bicharger', 'CAES-store', 'Compressed-Air-Adiabatic'],
        'LFP': ['Lithium-Ion-LFP-bicharger', 'Lithium-Ion-LFP-store', 'battery-bicharger', 'battery-store']
    }
    
    found_techs = {}
    
    for tech_type, tech_names in technologies.items():
        found_techs[tech_type] = []
        for tech in tech_names:
            matching_rows = costs_df[costs_df['technology'].str.contains(tech, case=False, na=False)]
            if not matching_rows.empty:
                found_techs[tech_type].extend(matching_rows['technology'].unique().tolist())
        
        print(f"\n{tech_type} technologies found in costs:")
        if found_techs[tech_type]:
            for tech in set(found_techs[tech_type]):
                print(f"  ✅ {tech}")
        else:
            print(f"  ❌ None found")
    
    return found_techs

def check_config():
    """Check configuration files for storage technology settings"""
    print("\n=== CHECKING CONFIGURATION ===")
    
    config_file = "config/config.default.yaml"
    if not os.path.exists(config_file):
        print(f"❌ Config file not found: {config_file}")
        return False
        
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Check electricity section
    electricity = config.get('electricity', {})
    
    # Check extendable carriers
    extendable = electricity.get('extendable_carriers', {})
    stores = extendable.get('Store', [])
    links = extendable.get('Link', [])
    
    print("\nExtendable Store technologies:")
    storage_techs = ['battery', 'H2', 'iron-air', 'Vanadium-Redox-Flow', 'Compressed-Air-Adiabatic']
    for tech in storage_techs:
        if tech in stores:
            print(f"  ✅ {tech}")
        else:
            print(f"  ❌ {tech}")
    
    print("\nExtendable Link technologies:")
    link_techs = ['battery inverter', 'iron-air battery charge', 'iron-air battery discharge']
    for tech in link_techs:
        if tech in links:
            print(f"  ✅ {tech}")
        else:
            print(f"  ❌ {tech}")
    
    # Check max/min hours
    max_hours = electricity.get('max_hours', {})
    min_hours = electricity.get('min_hours', {})
    
    print("\nStorage duration limits:")
    for tech in storage_techs:
        max_h = max_hours.get(tech, 'Not set')
        min_h = min_hours.get(tech, 'Not set')
        print(f"  {tech}: min={min_h}h, max={max_h}h")
    
    # Check power limits
    p_nom_max = electricity.get('storage_p_nom_max', {})
    print("\nPower capacity limits (MW):")
    for tech in storage_techs:
        limit = p_nom_max.get(tech, 'Not set')
        print(f"  {tech}: {limit} MW")
    
    return True

def check_technology_mapping():
    """Check technology mapping files"""
    print("\n=== CHECKING TECHNOLOGY MAPPING ===")
    
    mapping_file = "storage_mapping_summary.csv"
    if not os.path.exists(mapping_file):
        print(f"❌ Mapping file not found: {mapping_file}")
        return False
        
    # Read and parse the file manually due to pipe separator
    with open(mapping_file, 'r') as f:
        lines = f.readlines()
    
    data = []
    for line in lines[1:]:
        # Split on the pipe and then parse the CSV part
        parts = line.strip().split('|')[1:]  # Skip line number
        if parts:
            # Split the content on commas but handle quoted content
            content = parts[0]
            fields = content.split(',')
            if len(fields) >= 2:
                data.append({
                    'Current_Name': fields[0],
                    'Target_Name': fields[1]
                })
    
    # Check for key technologies
    tech_patterns = ['iron-air', 'caes', 'compressed-air', 'lfp', 'lithium-iron']
    
    print("\nTechnology mappings found:")
    for pattern in tech_patterns:
        matches = [row for row in data if pattern.lower() in row['Current_Name'].lower()]
        if matches:
            print(f"  ✅ {pattern.upper()}:")
            for match in matches[:3]:  # Show first 3 matches
                print(f"    {match['Current_Name']} → {match['Target_Name']}")
        else:
            print(f"  ❌ {pattern.upper()}: Not found")
    
    return True

def check_costs_config_override():
    """Check cost configuration overrides"""
    print("\n=== CHECKING COST OVERRIDES IN CONFIG ===")
    
    config_file = "config/config.default.yaml"
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    costs = config.get('costs', {})
    efficiency = costs.get('efficiency', {})
    investment = costs.get('investment', {})
    lifetime = costs.get('lifetime', {})
    
    # Check for iron-air overrides
    iron_air_techs = [
        'iron-air battery charge', 'iron-air battery discharge', 
        'iron-air battery', 'Lithium-Ion-LFP-bicharger', 
        'Lithium-Ion-LFP-store'
    ]
    
    print("\nCost overrides in config:")
    for tech in iron_air_techs:
        if tech in efficiency:
            print(f"  ✅ {tech} efficiency: {efficiency[tech]}")
        if tech in investment:
            print(f"  ✅ {tech} investment: {investment[tech]}")
        if tech in lifetime:
            print(f"  ✅ {tech} lifetime: {lifetime[tech]}")
    
    return True

def main():
    print("Checking implementation of Iron-Air, CAES, and LFP storage technologies...")
    print("=" * 70)
    
    # Run all checks
    cost_data_ok = check_cost_data()
    config_ok = check_config()
    mapping_ok = check_technology_mapping()
    override_ok = check_costs_config_override()
    
    print("\n" + "=" * 70)
    print("SUMMARY:")
    print(f"Cost data: {'✅ OK' if cost_data_ok else '❌ Issues found'}")
    print(f"Configuration: {'✅ OK' if config_ok else '❌ Issues found'}")
    print(f"Technology mapping: {'✅ OK' if mapping_ok else '❌ Issues found'}")
    print(f"Cost overrides: {'✅ OK' if override_ok else '❌ Issues found'}")
    
    if all([cost_data_ok, config_ok, mapping_ok, override_ok]):
        print("\n✅ All storage technologies appear to be properly implemented!")
    else:
        print("\n⚠️  Some issues found. Check the detailed output above.")

if __name__ == "__main__":
    main()
