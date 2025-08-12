# Bounds Audit Table - PyPSA-DE Repository

This table lists every component with extremely large bounds (1e6, 1e7, 1e8, 1e9, 1e10, .inf) and the key bound parameters (`s_nom_max`, `p_nom_max`, `p_max_pu`, `p_nom_extendable`, `max_extension`, `link_unit_size`) found in the repository.

## Summary of Key Findings

### Critical High-Value Bounds Found:

| Component Type | Parameter | File/Location | Line | Current Value | Config Type | Comments |
|---|---|---|---|---|---|---|
| Lines | `s_nom_max` | config/config.default.yaml | 373 | `.inf` | Config | Global transmission line capacity limit |
| Lines | `s_nom_max` | config/config.updated.yaml | 170 | `.inf` | Config | Same parameter in updated config |
| Lines | `max_extension` | config/config.default.yaml | 374 | `20000` | Config | Line extension limit in MW |
| Lines | `max_extension` | config/config.updated.yaml | 171 | `20000` | Config | Same parameter in updated config |
| Links | `p_nom_max` | config/config.default.yaml | 389 | `.inf` | Config | Global DC link capacity limit |
| Links | `p_nom_max` | config/config.updated.yaml | 186 | `.inf` | Config | Same parameter in updated config |
| Links | `max_extension` | config/config.default.yaml | 390 | `.inf` | Config | Link extension limit in MW |
| Links | `max_extension` | config/config.updated.yaml | 187 | `.inf` | Config | Same parameter in updated config |
| Post-discretization | `link_unit_size` (DC) | config/config.default.yaml | 974 | `2000` | Config | Unit size for DC links |
| Post-discretization | `link_unit_size` (H2) | config/config.default.yaml | 975 | `1200` | Config | Unit size for H2 pipeline |
| Post-discretization | `link_unit_size` (gas) | config/config.default.yaml | 976 | `1500` | Config | Unit size for gas pipeline |

### Hardcoded Large Bounds in Scripts:

| Component Type | Parameter | File/Location | Line | Current Value | Config Type | Comments |
|---|---|---|---|---|---|---|
| Generator variables | Upper bound | scripts/solve_network.py | 796 | `np.inf` | Hard-coded | Reserve variable upper bound |
| Renewable bounds | p_nom_max checks | scripts/solve_network.py | 116 | `np.inf` | Hard-coded | Infinite capacity check |
| Network parameters | s_nom_max_set default | scripts/prepare_network.py | 278 | `np.inf` | Hard-coded | Line capacity limit default |
| Network parameters | p_nom_max_set default | scripts/prepare_network.py | 279 | `np.inf` | Hard-coded | Link capacity limit default |
| Network parameters | s_nom_max_ext default | scripts/prepare_network.py | 280 | `np.inf` | Hard-coded | Line extension limit default |
| Network parameters | p_nom_max_ext default | scripts/prepare_network.py | 281 | `np.inf` | Hard-coded | Link extension limit default |

### Small but Important Bounds (clip_p_max_pu):

| Component Type | Parameter | File/Location | Line | Current Value | Config Type | Comments |
|---|---|---|---|---|---|---|
| Renewable | `clip_p_max_pu` | config/config.default.yaml | 79 | `1.e-2` | Config | Solver options clip value |
| Wind Onshore | `clip_p_max_pu` | config/config.default.yaml | 259 | `1.e-2` | Config | Minimum capacity factor |
| Wind Offshore AC | `clip_p_max_pu` | config/config.default.yaml | 275 | `1.e-2` | Config | Minimum capacity factor |
| Wind Offshore DC | `clip_p_max_pu` | config/config.default.yaml | 291 | `1.e-2` | Config | Minimum capacity factor |
| Wind Offshore Float | `clip_p_max_pu` | config/config.default.yaml | 309 | `1.e-2` | Config | Minimum capacity factor |
| Solar | `clip_p_max_pu` | config/config.default.yaml | 324 | `1.e-2` | Config | Minimum capacity factor |
| Solar Tracking | `clip_p_max_pu` | config/config.default.yaml | 339 | `1.e-2` | Config | Minimum capacity factor |

### Solver-Level Bounds:

| Component Type | Parameter | File/Location | Line | Current Value | Config Type | Comments |
|---|---|---|---|---|---|---|
| Solver | `large_matrix_value` | config/config.default.yaml | 66 | `1e9` | Config | Maximum matrix value for HiGHS solver |

### p_nom_extendable Settings:

| Component Type | Parameter | File/Location | Line | Current Value | Config Type | Comments |
|---|---|---|---|---|---|---|
| Storage Units | Battery | config/config.default.yaml | 205 | `true` | Config | Battery capacity extendable |
| Storage Units | H2 | config/config.default.yaml | 206 | `true` | Config | H2 storage extendable |
| Storage Units | Vanadium-Redox | config/config.default.yaml | 207 | `true` | Config | Flow battery extendable |
| Storage Units | Compressed Air | config/config.default.yaml | 208 | `true` | Config | CAES extendable |
| Storage Units | Iron-Air | config/config.default.yaml | 209 | `true` | Config | Iron-air battery extendable |

## Additional Large Values Found in Code:

### Scripts with Large Constants:

1. **scripts/prepare_sector_network.py**: Contains multiple instances of `1e6` for unit conversions and large capacity defaults
2. **scripts/cluster_network.py**: Contains `np.inf` for clustering algorithms
3. **scripts/base_network.py**: Contains multiple large values for network topology handling

### Large Values for Data Processing:

| File | Parameter | Value | Purpose |
|---|---|---|---|
| solve_network.py | Time limit | 18000 seconds | Solver time limit (5 hours) |
| solve_network.py | Memory limit | 60000 MB | Memory limit (60GB) |

## Recommended Actions:

1. **Review Infinite Bounds**: All `.inf` values should be evaluated for realistic upper bounds
2. **Standardize Large Values**: Consider defining constants for frequently used large values
3. **Parameter Validation**: Add bounds checking for user-provided parameters
4. **Documentation**: Ensure all bounds are properly documented with their rationale

## Files to Monitor for Future Changes:

1. `config/config.default.yaml` - Primary configuration
2. `config/config.updated.yaml` - Updated configuration 
3. `scripts/prepare_network.py` - Network preparation bounds
4. `scripts/solve_network.py` - Solver constraint bounds
5. `scripts/prepare_sector_network.py` - Sector coupling bounds

## Notes:

- Most infinite bounds (`.inf`) are set at the configuration level
- The repository uses both config-based and hard-coded bounds
- Critical parameters like `s_nom_max`, `p_nom_max`, and `max_extension` are primarily configured via YAML files
- Small bounds (`1.e-2`) are used extensively for numerical stability in renewable energy calculations
