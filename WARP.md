# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Overview

This is a specialized version of PyPSA-Eur focused on German energy system optimization and CO2 scenario analysis. The repository contains energy system modeling workflows, optimization scripts, and analysis tools specifically designed for studying Germany's electricity sector under different decarbonization pathways.

## Key Commands

### Environment Management

**Install the conda/mamba environment:**
```bash
# For macOS Apple Silicon
make install-lock-macos-arm

# For macOS Intel
make install-lock-macos64

# For Linux
make install-lock-linux64

# For Windows
make install-lock-windows

# Custom environment name
make install-lock-macos-arm name=my-pypsa-env
```

**Activate the environment:**
```bash
conda activate pypsa-eur
```

### Running Analysis

**Standard workflow (always unlock first):**
```bash
# 1. Always unlock before running any Snakemake commands
snakemake --unlock

# 2. Then run your desired command
snakemake -call results/test-elec/networks/base_s_6_elec_.nc --configfile config/test/config.electricity.yaml
```

**Run the complete test suite:**
```bash
make test
```

**Run unit tests:**
```bash
make unit-test
```

**Run CO2 scenario analysis (custom to this repo):**
```bash
python run_co2_scenarios.py
```

**Run single energy optimization scenario:**
```bash
# Using built-in test configs
snakemake -call results/test-elec/networks/base_s_6_elec_.nc --configfile config/test/config.electricity.yaml

# Using Germany-specific configs
snakemake -call results/de-scenario-A/networks/base_s_1_elec_Co2L0.15.nc --configfile config/de-co2-scenario-A-2035.yaml
```

**Run sector-coupled analysis:**
```bash
snakemake -call solve_sector_networks --configfile config/test/config.myopic.yaml
```

### Development Tools

**Linting and code quality:**
```bash
# Lint critical scripts for undefined variables
pylint --disable=all --enable=E0601,E0606 scripts/add_* scripts/prepare_* scripts/solve_*

# Format code (ruff is configured in pre-commit)
pre-commit run --all-files
```

**Clean up generated files:**
```bash
# Clean test outputs
make clean-tests

# Complete reset (removes logs, resources, benchmarks, results)
make reset
```

### Single Component Testing

**Test specific components:**
```bash
# Test a single optimization script
python scripts/solve_network.py --help

# Test renewable profile building
snakemake -call resources/profile_1_solar.nc

# Test network clustering
snakemake -call resources/networks/base_s_6.nc
```

### Dashboard and Visualization

**Generate analysis dashboards (custom to this repo):**
```bash
python co2_scenarios_dashboard_enhanced.py
python create_dashboard.py
```

## Code Architecture

### High-Level Structure

This repository implements a **Snakemake-based workflow system** for energy system optimization using PyPSA (Python for Power System Analysis). The architecture follows these key principles:

1. **Rule-based workflow**: Snakemake rules define the computational pipeline
2. **Modular scripts**: Python scripts in `scripts/` perform specific analysis tasks  
3. **Configuration-driven**: YAML files control model parameters and scenarios
4. **Hierarchical data flow**: Raw data → processed resources → optimized networks → results

### Core Components

**Workflow Management (`rules/` directory):**
- `build_electricity.smk` - Rules for building electricity networks
- `build_sector.smk` - Rules for sector-coupled models
- `solve_electricity.smk` - Optimization solving rules
- `solve_myopic.smk` - Multi-horizon pathway optimization
- `collect.smk` - Collection rules for batch processing
- `common.smk` - Shared functions and utilities

**Analysis Scripts (`scripts/` directory):**
- Network building: `base_network.py`, `cluster_network.py`, `simplify_network.py`
- Data preparation: `build_renewable_profiles.py`, `build_powerplants.py`
- Optimization: `solve_network.py`, `add_electricity.py`
- Utilities: `_helpers.py` (core helper functions)

**Configuration System:**
- `config/config.default.yaml` - Default model settings
- `config/de-*.yaml` - Germany-specific scenario configurations  
- `config/test/` - Test configurations
- Wildcard system for scenario variations: `{clusters}`, `{opts}`, `{sector_opts}`, `{planning_horizons}`

### Germany-Specific Customizations

This repository contains several Germany-focused additions:

**CO2 Scenario Analysis:**
- 4 decarbonization scenarios (15%, 5%, 1%, 0% of 1990 emissions)
- Automated batch processing via `run_co2_scenarios.py`
- Custom configuration files for each scenario

**Analysis Tools:**
- `co2_scenarios_dashboard_enhanced.py` - Interactive results visualization
- `calculate_h2_costs.py` - Hydrogen cost analysis
- `analyze_storage_results.py` - Storage technology assessment

**Model Settings:**
- Single-node Germany model (simplified spatial resolution)  
- 2-hour temporal resolution (4380 timesteps)
- Linear programming optimization only
- HiGHS solver with 5-hour time limits

### Data Flow Architecture

```
Raw Data (data/)
    ↓
Resources Pipeline (resources/)
    ├── Network building (base_network → simplify → cluster)  
    ├── Renewable profiles (weather data → capacity factors)
    ├── Demand profiles (load time series)  
    └── Technology data (costs, efficiencies)
    ↓
Optimization (solve_network)
    ├── Generator dispatch optimization
    ├── Storage operation optimization  
    ├── Transmission capacity optimization
    └── Emission constraint satisfaction
    ↓
Results (results/)
    ├── Optimized networks (.nc files)
    ├── Summary statistics  
    ├── Cost breakdowns
    └── Visualization outputs
```

### Testing Architecture

**Multi-level testing approach:**
- `make test` - Full workflow integration tests using test configurations
- `make unit-test` - Python unit tests in `test/` directory using pytest
- `test/conftest.py` - Test fixtures and data setup
- GitHub Actions CI/CD for automated testing on multiple platforms

### Key Design Patterns

**Config Provider Pattern:**
- `config_provider()` function enables dynamic configuration based on wildcards
- Allows scenario-specific parameters without code changes

**Resource Path Management:**
- `get_run_path()` handles shared vs. run-specific resource organization
- Supports collaborative development with resource sharing

**Mock Snakemake Pattern:**
- `mock_snakemake()` enables standalone script testing and development
- Simulates Snakemake execution environment for debugging

This architecture enables scalable energy system analysis while maintaining flexibility for different scenarios and research questions.

## Repository-Specific Notes

### Scenario Management
This repository uses a custom scenario system for German energy analysis with predefined CO2 targets. The main scenarios are defined in `CO2_SCENARIOS_SETUP.md` and can be run via the `run_co2_scenarios.py` script.

### Custom Analysis Scripts
Several analysis scripts are specific to this repository's research focus:
- Hydrogen cost analysis and optimization
- Storage technology comparisons
- CO2 scenario dashboards  
- Realistic technology cost assessments

### Memory and Performance
The optimization models can be memory-intensive. The default configuration allocates:
- 16GB memory for solve operations
- 60GB for large Germany scenarios
- 8-thread parallel solving with HiGHS

### File Organization
- `resources/` - Intermediate processing results (can be shared between runs)
- `results/` - Final optimization outputs and analysis (run-specific)
- `logs/` - Execution logs and solver outputs
- `benchmarks/` - Performance metrics
- `cutouts/` - Weather data cutouts (large files)
