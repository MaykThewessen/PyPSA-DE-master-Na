#!/usr/bin/env python3
"""
Comprehensive Storage Technology Mapping Table

Maps all current storage technology naming variants to standardized target names.
This mapping covers all components including stores, chargers, dischargers, and bichargers.

Step 2: Create mapping from current names to target names

Target naming convention:
- Vanadium/redox flow variants → `vanadium`
- Iron-air battery variants → `IronAir`
- Hydrogen storage variants → `H2`
- Compressed air storage variants → `CAES`
- Battery technologies to duration-based names:
  - 1-hour duration batteries → `battery1`
  - 2-hour duration batteries → `battery2`
  - 4-hour duration batteries → `battery4`
  - 8-hour duration batteries → `battery8`
"""

# =============================================================================
# MAIN TECHNOLOGY MAPPING DICTIONARY
# =============================================================================

STORAGE_TECHNOLOGY_MAPPING = {
    
    # =================================================================
    # VANADIUM REDOX FLOW BATTERY VARIANTS → vanadium
    # =================================================================
    
    # Core vanadium technologies
    "Vanadium-Redox-Flow": "vanadium",
    "Vanadium Redox Flow": "vanadium",
    "vanadium-redox-flow": "vanadium",
    "vanadium redox flow": "vanadium",
    "VRF": "vanadium",
    "VRFB": "vanadium",
    "vanadium": "vanadium",  # Already standardized
    "Vanadium": "vanadium",
    
    # Vanadium with component suffixes
    "Vanadium-Redox-Flow-store": "vanadium-store",
    "Vanadium-Redox-Flow-charger": "vanadium-charger",
    "Vanadium-Redox-Flow-discharger": "vanadium-discharger",
    "Vanadium-Redox-Flow-bicharger": "vanadium-bicharger",
    "vanadium-redox-flow-store": "vanadium-store",
    "vanadium-redox-flow-charger": "vanadium-charger",
    "vanadium-redox-flow-discharger": "vanadium-discharger",
    "vanadium-redox-flow-bicharger": "vanadium-bicharger",
    "vanadium-store": "vanadium-store",
    "vanadium-charger": "vanadium-charger",
    "vanadium-discharger": "vanadium-discharger",
    "vanadium-bicharger": "vanadium-bicharger",
    
    # =================================================================
    # IRON-AIR BATTERY VARIANTS → IronAir
    # =================================================================
    
    # Core iron-air technologies
    "Iron-Air": "IronAir",
    "iron-air": "IronAir",
    "Iron Air": "IronAir",
    "iron air": "IronAir",
    "ironair": "IronAir",
    "IronAir": "IronAir",  # Already standardized
    "iron-air battery": "IronAir",
    "Iron-Air battery": "IronAir",
    "Iron-Air-charge": "IronAir",
    "Iron-Air-discharge": "IronAir",
    
    # Iron-air with component suffixes
    "Iron-Air-store": "IronAir-store",
    "iron-air-store": "IronAir-store",
    "ironair-store": "IronAir-store",
    "Iron-Air-charger": "IronAir-charger",
    "iron-air-charger": "IronAir-charger",
    "ironair-charger": "IronAir-charger",
    "Iron-Air-discharger": "IronAir-discharger",
    "iron-air-discharger": "IronAir-discharger",
    "ironair-discharger": "IronAir-discharger",
    "Iron-Air-bicharger": "IronAir-bicharger",
    "iron-air-bicharger": "IronAir-bicharger",
    "ironair-bicharger": "IronAir-bicharger",
    "iron-air battery charge": "IronAir-charger",
    "iron-air battery discharge": "IronAir-discharger",
    
    # =================================================================
    # HYDROGEN STORAGE VARIANTS → H2
    # =================================================================
    
    # Core hydrogen technologies
    "hydrogen": "H2",
    "Hydrogen": "H2",
    "hydrogen storage": "H2",
    "Hydrogen Storage": "H2",
    "hydrogen storage underground": "H2",
    "H2": "H2",  # Already standardized
    "h2": "H2",
    
    # Hydrogen with component suffixes
    "H2-store": "H2-store",
    "hydrogen-store": "H2-store",
    "H2-charger": "H2-charger",
    "hydrogen-charger": "H2-charger",
    "H2-discharger": "H2-discharger",
    "hydrogen-discharger": "H2-discharger",
    "H2-bicharger": "H2-bicharger",
    "hydrogen-bicharger": "H2-bicharger",
    
    # Hydrogen system components (electrolysis and fuel cells)
    "H2 electrolysis": "H2-charger",
    "H2 electrolyzer": "H2-charger",
    "electrolysis": "H2-charger",
    "electrolyser": "H2-charger",
    "Electrolysis": "H2-charger",
    "Hydrogen-charger": "H2-charger",
    "H2 fuel cell": "H2-discharger",
    "fuel cell": "H2-discharger",
    "fuel-cell": "H2-discharger",
    "Fuel Cell": "H2-discharger",
    "Hydrogen-discharger": "H2-discharger",
    
    # =================================================================
    # COMPRESSED AIR STORAGE VARIANTS → CAES
    # =================================================================
    
    # Core compressed air technologies
    "Compressed-Air-Adiabatic": "CAES",
    "compressed-air-adiabatic": "CAES",
    "Compressed Air Adiabatic": "CAES",
    "compressed air adiabatic": "CAES",
    "Compressed-Air": "CAES",
    "compressed-air": "CAES",
    "Compressed Air": "CAES",
    "compressed air": "CAES",
    "CAES": "CAES",  # Already standardized
    "caes": "CAES",
    
    # CAES with component suffixes
    "Compressed-Air-Adiabatic-store": "CAES-store",
    "compressed-air-adiabatic-store": "CAES-store",
    "CAES-store": "CAES-store",
    "Compressed-Air-Adiabatic-charger": "CAES-charger",
    "compressed-air-adiabatic-charger": "CAES-charger",
    "CAES-charger": "CAES-charger",
    "Compressed-Air-Adiabatic-discharger": "CAES-discharger",
    "compressed-air-adiabatic-discharger": "CAES-discharger",
    "CAES-discharger": "CAES-discharger",
    "Compressed-Air-Adiabatic-bicharger": "CAES-bicharger",
    "compressed-air-adiabatic-bicharger": "CAES-bicharger",
    "CAES-bicharger": "CAES-bicharger",
    
    # =================================================================
    # BATTERY DURATION-BASED NAMING
    # =================================================================
    
    # 1-hour duration batteries → battery1
    "battery_1h": "battery1",
    "battery-1h": "battery1",
    "battery1h": "battery1",
    "Battery-1h": "battery1",
    "1h-battery": "battery1",
    "battery1": "battery1",  # Already standardized
    "battery_1h-store": "battery1-store",
    "battery_1h-charger": "battery1-charger",
    "battery_1h-discharger": "battery1-discharger",
    "battery_1h-bicharger": "battery1-bicharger",
    "battery1-store": "battery1-store",
    "battery1-charger": "battery1-charger",
    "battery1-discharger": "battery1-discharger",
    "battery1-bicharger": "battery1-bicharger",
    
    # 2-hour duration batteries → battery2
    "battery_2h": "battery2",
    "battery-2h": "battery2",
    "battery2h": "battery2",
    "Battery-2h": "battery2",
    "2h-battery": "battery2",
    "battery2": "battery2",  # Already standardized
    "battery_2h-store": "battery2-store",
    "battery_2h-charger": "battery2-charger",
    "battery_2h-discharger": "battery2-discharger",
    "battery_2h-bicharger": "battery2-bicharger",
    "battery2-store": "battery2-store",
    "battery2-charger": "battery2-charger",
    "battery2-discharger": "battery2-discharger",
    "battery2-bicharger": "battery2-bicharger",
    
    # 4-hour duration batteries → battery4
    "battery_4h": "battery4",
    "battery-4h": "battery4",
    "battery4h": "battery4",
    "Battery-4h": "battery4",
    "4h-battery": "battery4",
    "battery4": "battery4",  # Already standardized
    "battery_4h-store": "battery4-store",
    "battery_4h-charger": "battery4-charger",
    "battery_4h-discharger": "battery4-discharger",
    "battery_4h-bicharger": "battery4-bicharger",
    "battery4-store": "battery4-store",
    "battery4-charger": "battery4-charger",
    "battery4-discharger": "battery4-discharger",
    "battery4-bicharger": "battery4-bicharger",
    
    # 8-hour duration batteries → battery8
    "battery_8h": "battery8",
    "battery-8h": "battery8",
    "battery8h": "battery8",
    "Battery-8h": "battery8",
    "8h-battery": "battery8",
    "battery8": "battery8",  # Already standardized
    "battery_8h-store": "battery8-store",
    "battery_8h-charger": "battery8-charger",
    "battery_8h-discharger": "battery8-discharger",
    "battery_8h-bicharger": "battery8-bicharger",
    "battery8-store": "battery8-store",
    "battery8-charger": "battery8-charger",
    "battery8-discharger": "battery8-discharger",
    "battery8-bicharger": "battery8-bicharger",
    
    # =================================================================
    # ADDITIONAL BATTERY VARIANTS (from codebase analysis)
    # =================================================================
    
    # Generic battery variants
    "battery": "battery",  # Generic, may need context-specific mapping
    "Battery": "battery",
    "battery storage": "battery-store",
    "battery inverter": "battery-charger",  # Inverter can be both charger/discharger
    "battery charger": "battery-charger",
    "battery discharger": "battery-discharger",
    "battery bicharger": "battery-bicharger",
    
    # Extended duration batteries (from codebase)
    "battery_12h": "battery12",
    "battery-12h": "battery12",
    "battery12h": "battery12",
    "battery12": "battery12",
    "battery_12h-store": "battery12-store",
    "battery_12h-charger": "battery12-charger",
    "battery_12h-discharger": "battery12-discharger",
    "battery_12h-bicharger": "battery12-bicharger",
    
    "battery_24h": "battery24",
    "battery-24h": "battery24",
    "battery24h": "battery24",
    "battery24": "battery24",
    "battery_24h-store": "battery24-store",
    "battery_24h-charger": "battery24-charger",
    "battery_24h-discharger": "battery24-discharger",
    "battery_24h-bicharger": "battery24-bicharger",
    
    "battery_48h": "battery48",
    "battery-48h": "battery48",
    "battery48h": "battery48",
    "battery48": "battery48",
    "battery_48h-store": "battery48-store",
    "battery_48h-charger": "battery48-charger",
    "battery_48h-discharger": "battery48-discharger",
    "battery_48h-bicharger": "battery48-bicharger",
    
    # Lithium-ion specific variants
    "Li-Ion": "battery",
    "lithium-ion": "battery",
    "Lithium-Ion": "battery",
    "LFP": "battery",
    "Lithium-Ion-LFP": "battery",
    "Lithium-Ion-LFP-bicharger": "battery-bicharger",
    "Lithium-Ion-LFP-store": "battery-store",
    
    # Legacy battery names (found in old code)
    "Ebattery1": "battery1",
    "Ebattery2": "battery2",
    "Ebattery4": "battery4",
    "Ebattery8": "battery8",
}

# =============================================================================
# COMPONENT SUFFIX PATTERNS
# =============================================================================

COMPONENT_SUFFIXES = [
    "store",
    "charger", 
    "discharger",
    "bicharger"
]

# =============================================================================
# REVERSE MAPPING (TARGET → CURRENT VARIANTS)
# =============================================================================

def get_reverse_mapping():
    """
    Create reverse mapping from target names to lists of current variants.
    Useful for understanding what names map to each target.
    """
    reverse_map = {}
    for current, target in STORAGE_TECHNOLOGY_MAPPING.items():
        if target not in reverse_map:
            reverse_map[target] = []
        reverse_map[target].append(current)
    return reverse_map

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def map_storage_technology(current_name: str) -> str:
    """
    Map a current storage technology name to the standardized target name.
    
    Parameters:
    -----------
    current_name : str
        Current technology name to be mapped
        
    Returns:
    --------
    str
        Standardized target name, or original name if no mapping found
    """
    return STORAGE_TECHNOLOGY_MAPPING.get(current_name, current_name)

def get_technology_base_name(target_name: str) -> str:
    """
    Get the base technology name without component suffixes.
    
    Parameters:
    -----------
    target_name : str
        Target technology name (possibly with suffix)
        
    Returns:
    --------
    str
        Base technology name without suffix
    """
    for suffix in COMPONENT_SUFFIXES:
        if target_name.endswith(f"-{suffix}"):
            return target_name[:-len(f"-{suffix}")]
    return target_name

def get_component_suffix(target_name: str) -> str:
    """
    Get the component suffix from a target technology name.
    
    Parameters:
    -----------
    target_name : str
        Target technology name (possibly with suffix)
        
    Returns:
    --------
    str
        Component suffix, or empty string if no suffix found
    """
    for suffix in COMPONENT_SUFFIXES:
        if target_name.endswith(f"-{suffix}"):
            return suffix
    return ""

def validate_mapping():
    """
    Validate the mapping dictionary for consistency and completeness.
    """
    print("=== STORAGE TECHNOLOGY MAPPING VALIDATION ===\n")
    
    # Count mappings by target technology
    target_counts = {}
    for current, target in STORAGE_TECHNOLOGY_MAPPING.items():
        base_target = get_technology_base_name(target)
        if base_target not in target_counts:
            target_counts[base_target] = 0
        target_counts[base_target] += 1
    
    print("Target Technology Mapping Counts:")
    for target, count in sorted(target_counts.items()):
        print(f"  {target}: {count} variants mapped")
    
    print(f"\nTotal mappings: {len(STORAGE_TECHNOLOGY_MAPPING)}")
    
    # Show reverse mapping summary
    reverse_map = get_reverse_mapping()
    print(f"Total unique targets: {len(reverse_map)}")
    
    return True

if __name__ == "__main__":
    print(__doc__)
    validate_mapping()
    
    # Example usage
    print("\n=== EXAMPLE MAPPINGS ===")
    test_cases = [
        "Vanadium-Redox-Flow",
        "iron-air battery",
        "battery_4h",
        "Compressed-Air-Adiabatic",
        "H2 electrolysis",
        "battery inverter"
    ]
    
    for test in test_cases:
        mapped = map_storage_technology(test)
        print(f"'{test}' → '{mapped}'")
