# Technical Upper Limits Implementation Summary

## Overview
This document summarizes the realistic technical upper limits that have been implemented for power system components in PyPSA-Eur, replacing the previous infinite (`.inf`) values with evidence-based caps derived from existing infrastructure and engineering constraints.

## Implementation Details

### 1. AC Transmission Lines (`lines`)
**Previous limit:** `.inf` (unlimited)
**New limit:** `s_nom_max: 4000` MW

**Evidence base:**
- Double-circuit 380 kV lines typically carry 3-4 GW
- German transmission corridors (north-south) are designed for ~4 GW thermal rating
- Conservative estimate accounting for thermal limits, N-1 security margin, and practical engineering constraints

**Sources:**
- ENTSO-E Ten-Year Network Development Plan 2022
- BNetzA Grid Development Plan 2035 (Netzentwicklungsplan)
- IEEE Standards for High Voltage Transmission Systems

### 2. HVDC Links (`links`)
**Previous limit:** `.inf` (unlimited)
**New limit:** `p_nom_max: 6000` MW

**Evidence base:**
- Existing projects: NordLink (1.4 GW), planned SuedOstLink (4 GW)
- Engineering feasible upper bound for single bipolar HVDC link
- Accounts for converter technology limitations and grid integration constraints

**Sources:**
- ENTSO-E infrastructure data and project pipeline
- ABB and Siemens Energy HVDC project references
- Analysis of major European HVDC corridor projects

### 3. Generator Capacity Limits (`generator_p_nom_max`)
Evidence-based limits for each technology based on largest operational units:

#### Nuclear Generators
- **Limit:** 1650 MW
- **Basis:** EPR reactor scale (Flamanville-3: 1650 MW)
- **Source:** IAEA Power Reactor Information System (PRIS)

#### Conventional Thermal
- **Coal/Lignite:** 1100 MW (largest German units: Neurath, Niederaussem, Jänschwalde)
- **CCGT:** 850 MW (largest European combined-cycle gas turbines)
- **OCGT:** 400 MW (typical large peaking units)
- **Sources:** BNetzA power plant registry, ENTSO-E generation adequacy data

#### Renewable Generators
- **Onshore Wind:** 500 MW (Markbygden project scale: 650 MW planned)
- **Offshore Wind AC:** 1200 MW (large projects with scaling potential)
- **Offshore Wind DC:** 1400 MW (future large projects with HVDC transmission)
- **Offshore Wind Floating:** 500 MW (technology limitations)
- **Solar PV:** 800 MW (largest European utility-scale projects)
- **Sources:** Wind Europe statistics, Solar Power Europe data, project databases

#### Hydro Generators
- **Run-of-River:** 400 MW (geographical and environmental constraints)
- **Hydro Reservoir:** 1800 MW (largest European installations with scaling potential)
- **Pumped Hydro Storage:** 1800 MW (Goldisthal: 1060 MW, Bath County scale reference)
- **Sources:** International Hydropower Association, ENTSO-E hydro registry

### 4. Storage System Limits

#### Power Capacity Limits (`storage_p_nom_max`)
- **Battery:** 2000 MW (utility-scale projects: Moss Landing 400 MW + scaling)
- **Pumped Hydro:** 1800 MW (largest European installations)
- **Compressed Air (Adiabatic):** 500 MW (advanced CAES technology limits)
- **Hydrogen Storage:** 500 MW (integration limits for power-to-gas systems)
- **Iron-Air:** 200 MW (emerging long-duration technology)
- **Vanadium Redox Flow:** 100 MW (flow battery project scale)

#### Energy Capacity Limits (`storage_e_nom_max`)
- **Battery:** 10,000 MWh (large-scale deployment potential)
- **Pumped Hydro:** 25,000 MWh (geographic constraints in Germany/Europe)
- **Compressed Air:** 12,000 MWh (underground storage capacity)
- **Hydrogen:** 2,000,000 MWh (2 TWh for national-scale seasonal balancing)
- **Iron-Air:** 2,000 MWh (100-hour duration systems)
- **Vanadium Redox Flow:** 1,000 MWh (10-hour duration systems)

**Sources:**
- Energy Storage Association databases
- IRENA Global Energy Storage Roadmap 2030
- IEA Energy Storage Monitor
- Hydrogen Europe Strategic Research Agenda

## Technical Justification

### Methodology
1. **Data Collection:** Surveyed existing infrastructure databases (ENTSO-E, BNetzA, IAEA, IEA)
2. **Benchmarking:** Analyzed largest operational units by technology type
3. **Engineering Assessment:** Considered practical constraints (grid integration, N-1 security, thermal limits)
4. **Forward-Looking:** Included planned projects and technology scaling potential
5. **Conservative Approach:** Set limits with safety margins for optimization stability

### Benefits of Realistic Limits
1. **Numerical Stability:** Prevents unrealistic capacity allocation in optimization
2. **Engineering Realism:** Ensures solutions reflect practical deployment constraints
3. **Policy Relevance:** Results align with real-world infrastructure planning
4. **Model Validation:** Facilitates comparison with actual energy system development

## File Locations
- **Main Configuration:** `config/config.default.yaml` (updated with limits)
- **Detailed Documentation:** `config/technical_limits.yaml` (comprehensive reference)
- **Implementation Summary:** `technical_limits_summary.md` (this document)

## References
1. ENTSO-E Ten-Year Network Development Plan 2022
2. BNetzA Grid Development Plan 2035 (Netzentwicklungsplan)
3. IEEE Standards for High Voltage Transmission Systems
4. IAEA Power Reactor Information System (PRIS)
5. IRENA Global Energy Storage Roadmap 2030
6. Wind Europe Statistics and Outlook Reports
7. Solar Power Europe Market Outlook
8. IEA Energy Storage Monitor
9. Hydrogen Europe Strategic Research Agenda
10. European Network of Transmission System Operators (ENTSO-E) transparency data

---

**Note:** These limits represent technically feasible upper bounds for individual components. Actual deployment will be constrained by economic optimization, policy frameworks, and resource availability within the PyPSA-Eur model.
