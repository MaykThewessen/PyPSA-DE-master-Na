# Storage Technology Mapping Documentation

## Step 2: Comprehensive Mapping from Current Names to Target Names

This document provides detailed documentation for the comprehensive mapping table created for standardizing storage technology names across the PyPSA-DE codebase.

## Target Naming Convention Summary

| Technology Category | Target Name Pattern | Description |
|-------------------|------------------|-------------|
| Vanadium Redox Flow | `vanadium` | All vanadium/redox flow battery variants |
| Iron-Air Batteries | `IronAir` | All iron-air battery variants |
| Hydrogen Storage | `H2` | All hydrogen storage variants |
| Compressed Air Storage | `CAES` | All compressed air energy storage variants |
| 1-hour Batteries | `battery1` | 1-hour duration battery technologies |
| 2-hour Batteries | `battery2` | 2-hour duration battery technologies |
| 4-hour Batteries | `battery4` | 4-hour duration battery technologies |
| 8-hour Batteries | `battery8` | 8-hour duration battery technologies |

## Component Suffix Convention

All technologies support the following component suffixes:
- `-store`: Energy storage component (MWh capacity)
- `-charger`: Charging/input component (MW power)
- `-discharger`: Discharging/output component (MW power) 
- `-bicharger`: Bidirectional power component (MW power)

## Detailed Mapping Breakdown

### 1. Vanadium Redox Flow Battery Variants → `vanadium`

**Core Technology Mappings (20 variants):**
```
Vanadium-Redox-Flow → vanadium
Vanadium Redox Flow → vanadium
vanadium-redox-flow → vanadium
vanadium redox flow → vanadium
VRF → vanadium
VRFB → vanadium
vanadium → vanadium (already standardized)
Vanadium → vanadium

Component variants (with suffixes):
Vanadium-Redox-Flow-store → vanadium-store
Vanadium-Redox-Flow-charger → vanadium-charger
Vanadium-Redox-Flow-discharger → vanadium-discharger
Vanadium-Redox-Flow-bicharger → vanadium-bicharger
... (all case variations included)
```

### 2. Iron-Air Battery Variants → `IronAir`

**Core Technology Mappings (24 variants):**
```
Iron-Air → IronAir
iron-air → IronAir
Iron Air → IronAir
iron air → IronAir
ironair → IronAir
IronAir → IronAir (already standardized)
iron-air battery → IronAir
Iron-Air battery → IronAir
Iron-Air-charge → IronAir
Iron-Air-discharge → IronAir

Component variants:
Iron-Air-store → IronAir-store
Iron-Air-charger → IronAir-charger
Iron-Air-discharger → IronAir-discharger
Iron-Air-bicharger → IronAir-bicharger
iron-air battery charge → IronAir-charger
iron-air battery discharge → IronAir-discharger
... (all case variations included)
```

### 3. Hydrogen Storage Variants → `H2`

**Core Technology Mappings (26 variants):**
```
hydrogen → H2
Hydrogen → H2
hydrogen storage → H2
Hydrogen Storage → H2
hydrogen storage underground → H2
H2 → H2 (already standardized)
h2 → H2

Component variants:
H2-store → H2-store
hydrogen-store → H2-store
H2-charger → H2-charger
hydrogen-charger → H2-charger
H2-discharger → H2-discharger
hydrogen-discharger → H2-discharger
H2-bicharger → H2-bicharger
hydrogen-bicharger → H2-bicharger

System components (electrolysis and fuel cells):
H2 electrolysis → H2-charger
H2 electrolyzer → H2-charger
electrolysis → H2-charger
electrolyser → H2-charger
Electrolysis → H2-charger
Hydrogen-charger → H2-charger
H2 fuel cell → H2-discharger
fuel cell → H2-discharger
fuel-cell → H2-discharger
Fuel Cell → H2-discharger
Hydrogen-discharger → H2-discharger
```

### 4. Compressed Air Storage Variants → `CAES`

**Core Technology Mappings (22 variants):**
```
Compressed-Air-Adiabatic → CAES
compressed-air-adiabatic → CAES
Compressed Air Adiabatic → CAES
compressed air adiabatic → CAES
Compressed-Air → CAES
compressed-air → CAES
Compressed Air → CAES
compressed air → CAES
CAES → CAES (already standardized)
caes → CAES

Component variants:
Compressed-Air-Adiabatic-store → CAES-store
compressed-air-adiabatic-store → CAES-store
CAES-store → CAES-store
Compressed-Air-Adiabatic-charger → CAES-charger
compressed-air-adiabatic-charger → CAES-charger
CAES-charger → CAES-charger
Compressed-Air-Adiabatic-discharger → CAES-discharger
compressed-air-adiabatic-discharger → CAES-discharger
CAES-discharger → CAES-discharger
Compressed-Air-Adiabatic-bicharger → CAES-bicharger
compressed-air-adiabatic-bicharger → CAES-bicharger
CAES-bicharger → CAES-bicharger
```

### 5. Duration-Based Battery Mappings

#### 1-Hour Batteries → `battery1` (15 variants)
```
battery_1h → battery1
battery-1h → battery1
battery1h → battery1
Battery-1h → battery1
1h-battery → battery1
battery1 → battery1 (already standardized)

Component variants:
battery_1h-store → battery1-store
battery_1h-charger → battery1-charger
battery_1h-discharger → battery1-discharger
battery_1h-bicharger → battery1-bicharger
battery1-store → battery1-store
battery1-charger → battery1-charger
battery1-discharger → battery1-discharger
battery1-bicharger → battery1-bicharger
```

#### 2-Hour Batteries → `battery2` (15 variants)
```
battery_2h → battery2
battery-2h → battery2
battery2h → battery2
Battery-2h → battery2
2h-battery → battery2
battery2 → battery2 (already standardized)

Component variants:
battery_2h-store → battery2-store
battery_2h-charger → battery2-charger
battery_2h-discharger → battery2-discharger
battery_2h-bicharger → battery2-bicharger
battery2-store → battery2-store
battery2-charger → battery2-charger
battery2-discharger → battery2-discharger
battery2-bicharger → battery2-bicharger
```

#### 4-Hour Batteries → `battery4` (15 variants)
```
battery_4h → battery4
battery-4h → battery4
battery4h → battery4
Battery-4h → battery4
4h-battery → battery4
battery4 → battery4 (already standardized)

Component variants:
battery_4h-store → battery4-store
battery_4h-charger → battery4-charger
battery_4h-discharger → battery4-discharger
battery_4h-bicharger → battery4-bicharger
battery4-store → battery4-store
battery4-charger → battery4-charger
battery4-discharger → battery4-discharger
battery4-bicharger → battery4-bicharger
```

#### 8-Hour Batteries → `battery8` (15 variants)
```
battery_8h → battery8
battery-8h → battery8
battery8h → battery8
Battery-8h → battery8
8h-battery → battery8
battery8 → battery8 (already standardized)

Component variants:
battery_8h-store → battery8-store
battery_8h-charger → battery8-charger
battery_8h-discharger → battery8-discharger
battery_8h-bicharger → battery8-bicharger
battery8-store → battery8-store
battery8-charger → battery8-charger
battery8-discharger → battery8-discharger
battery8-bicharger → battery8-bicharger
```

### 6. Extended Duration Batteries (From Codebase Analysis)

#### 12-Hour Batteries → `battery12` (8 variants)
```
battery_12h → battery12
battery-12h → battery12
battery12h → battery12
battery12 → battery12

Component variants:
battery_12h-store → battery12-store
battery_12h-charger → battery12-charger
battery_12h-discharger → battery12-discharger
battery_12h-bicharger → battery12-bicharger
```

#### 24-Hour Batteries → `battery24` (8 variants)
```
battery_24h → battery24
battery-24h → battery24
battery24h → battery24
battery24 → battery24

Component variants:
battery_24h-store → battery24-store
battery_24h-charger → battery24-charger
battery_24h-discharger → battery24-discharger
battery_24h-bicharger → battery24-bicharger
```

#### 48-Hour Batteries → `battery48` (8 variants)
```
battery_48h → battery48
battery-48h → battery48
battery48h → battery48
battery48 → battery48

Component variants:
battery_48h-store → battery48-store
battery_48h-charger → battery48-charger
battery_48h-discharger → battery48-discharger
battery_48h-bicharger → battery48-bicharger
```

### 7. Generic Battery Variants → `battery` (14 variants)

```
battery → battery (generic, may need context-specific mapping)
Battery → battery
battery storage → battery-store
battery inverter → battery-charger (inverter can be both charger/discharger)
battery charger → battery-charger
battery discharger → battery-discharger
battery bicharger → battery-bicharger

Lithium-ion specific variants:
Li-Ion → battery
lithium-ion → battery
Lithium-Ion → battery
LFP → battery
Lithium-Ion-LFP → battery
Lithium-Ion-LFP-bicharger → battery-bicharger
Lithium-Ion-LFP-store → battery-store

Legacy battery names:
Ebattery1 → battery1
Ebattery2 → battery2
Ebattery4 → battery4
Ebattery8 → battery8
```

## Mapping Statistics

- **Total mappings**: 190 variants covered
- **Total unique targets**: 60 standardized names
- **Technologies covered**: 12 base technology types
- **Component types**: 4 component suffixes (store, charger, discharger, bicharger)

## Technology Coverage by Variant Count

| Target Technology | Variants Mapped |
|------------------|-----------------|
| H2 (Hydrogen) | 26 variants |
| IronAir | 24 variants |
| CAES | 22 variants |
| vanadium | 20 variants |
| battery1 | 15 variants |
| battery2 | 15 variants |
| battery4 | 15 variants |
| battery8 | 15 variants |
| battery (generic) | 14 variants |
| battery12 | 8 variants |
| battery24 | 8 variants |
| battery48 | 8 variants |

## Usage Examples

```python
from storage_technology_mapping import map_storage_technology

# Example mappings
print(map_storage_technology("Vanadium-Redox-Flow"))  # → vanadium
print(map_storage_technology("iron-air battery"))    # → IronAir  
print(map_storage_technology("battery_4h"))          # → battery4
print(map_storage_technology("Compressed-Air-Adiabatic"))  # → CAES
print(map_storage_technology("H2 electrolysis"))     # → H2-charger
print(map_storage_technology("battery inverter"))    # → battery-charger
```

## Implementation Notes

1. **Case Sensitivity**: The mapping handles various case combinations (lowercase, uppercase, mixed case).

2. **Delimiter Variations**: Supports both hyphen (-) and underscore (_) delimiters.

3. **Component Suffixes**: All major technologies include mappings for the four standard component types.

4. **Legacy Support**: Includes mappings for legacy naming conventions found in older code.

5. **Bidirectional Compatibility**: The mapping can be easily reversed to find all variants that map to a specific target.

6. **Extensibility**: The dictionary structure allows easy addition of new variants as they are discovered.

This comprehensive mapping table ensures consistent naming across the entire PyPSA-DE codebase while maintaining compatibility with existing naming conventions.
