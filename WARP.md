# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

PyPSA-DE is an energy system modeling framework for Germany built on PyPSA (Python for Power System Analysis). It models multi-sector energy systems including electricity, heat, transport, and industry sectors using optimization techniques to analyze energy transition scenarios.

## Core Development Commands

### Environment Setup
```bash
# Install environment (Windows)
make install-lock-windows

# Install environment (Linux x64)
make install-lock-linux64

# Install environment (macOS Intel)
make install-lock-macos64

# Install environment (macOS ARM)
make install-lock-macos-arm

# Activate environment
conda activate pypsa-eur
```

### Running Simulations

#### Main Workflow
```bash
# Run complete workflow with Snakemake
snakemake -call

# Run with specific configuration
snakemake -call --configfile config/de-all-tech-2035.yaml

# Run with specific number of cores (e.g., 8 cores)
snakemake -call -j8

# Dry run to check workflow
snakemake -call -n
```

#### Custom CO2 Scenarios
```bash
# Run CO2 scenario analysis script
python run_co2_scenarios.py

# Run specific scenario configurations
snakemake -call --configfile config/de-co2-scenario-A-2035.yaml
snakemake -call --configfile config/de-co2-scenario-B-2035.yaml
```

#### Individual Components
```bash
# Build electricity network only
snakemake -call solve_elec_networks --configfile config/de-electricity-only-2035.yaml

# Generate renewable profiles
snakemake -call resources/renewable_profiles.nc

# Build base network
snakemake -call resources/networks/base.nc
```

### Testing

```bash
# Run all tests
make test

# Run unit tests only
make unit-test

# Run specific test configurations
snakemake -call solve_elec_networks --configfile config/test/config.electricity.yaml
```

### Maintenance

```bash
# Clean test outputs
make clean-tests

# Reset all outputs (interactive prompt)
make reset

# Clean specific Snakemake outputs
snakemake -call --delete-all-output
```

### Analysis and Visualization

```bash
# Generate cost analysis
python analyze_energy_and_costs.py

# Generate dashboard
python co2_scenarios_dashboard.py

# Analyze storage results
python analyze_storage_results.py

# Generate summary statistics
snakemake -call make_summary
```

## Architecture Overview

### Core Workflow Engine
- **Snakemake**: Orchestrates the entire modeling pipeline defined in `Snakefile`
- **Configuration Management**: YAML-based configuration in `config/` directory with inheritance from `config.default.yaml`
- **Path Management**: Dynamic resource sharing across scenarios via `scripts/_helpers.py`

### Key Components

#### Data Processing Pipeline (`rules/`)
- `retrieve.smk`: External data retrieval from ENTSO-E, JRC, Eurostat
- `build_electricity.smk`: Electricity system construction and network topology
- `build_sector.smk`: Multi-sector energy system integration (heat, transport, industry)
- `solve_electricity.smk`: Electricity-only optimization
- `solve_overnight.smk`, `solve_myopic.smk`, `solve_perfect.smk`: Different foresight optimization approaches
- `postprocess.smk`: Results analysis and visualization generation

#### Core Scripts (`scripts/`)
- `_helpers.py`: Path management, scenario handling, utility functions
- `base_network.py`: Network topology construction from OSM data
- `add_electricity.py`: Electricity system component addition
- `prepare_sector_network.py`: Multi-sector integration
- `solve_network.py`: Optimization solver interface (HiGHS)
- `build_renewable_profiles.py`: Weather-dependent generation profiles via Atlite

#### Configuration Structure
- `config.default.yaml`: Base configuration with full Germany setup
- `de-*.yaml`: Scenario-specific configurations for different policy cases
- `technical_limits.yaml`: Technology constraints and limits
- `plotting.default.yaml`: Visualization settings

### Optimization Framework
- **Solver**: HiGHS (High-performance Linear Programming solver)
- **Problem Type**: Large-scale linear programming (LP) with mixed-integer options
- **Time Resolution**: Configurable (default 2-hour resolution, 4380 timesteps/year)
- **Spatial Resolution**: Clustered network topology (configurable clustering levels)
- **Foresight**: Three modes - overnight (no learning), myopic (limited), perfect (full)

### Data Integration
- **Weather Data**: Atlite integration with ERA5/SARAH3 for renewable generation profiles
- **Network Data**: OpenStreetMap-based transmission network topology
- **Load Data**: ENTSO-E transparency platform for demand profiles
- **Technology Costs**: JRC technology cost database with time-series projections

## Key Workflow Patterns

### Scenario Management
The system uses a sophisticated scenario management approach where:
- Base configuration is inherited from `config.default.yaml`
- Scenario-specific overrides are applied via separate YAML files
- Shared resources are managed across scenarios to avoid redundant computation
- Dynamic path resolution handles both shared and scenario-specific outputs

### Resource Dependencies
Snakemake rules are organized in dependency chains:
1. **Data Retrieval**: External data sources → Raw data files
2. **Network Building**: Raw data → Network topology (`networks/base.nc`)
3. **Clustering**: Base network → Clustered networks (`networks/base_s_{clusters}.nc`)
4. **Technology Addition**: Clustered networks → Technology-enhanced networks
5. **Optimization**: Enhanced networks → Optimized results (`results/networks/`)
6. **Postprocessing**: Results → Visualizations and summaries

### Configuration Inheritance
- All configurations inherit from `config.default.yaml`
- Override specific parameters in scenario files
- Use `clusters`, `opts`, `sector_opts`, `planning_horizons` wildcards for parameter sweeps
- CO2 budget constraints drive scenario differentiation

## Development Workflow

### Adding New Scenarios
1. Create new YAML file in `config/` inheriting from `config.default.yaml`
2. Override specific parameters (CO2 targets, technology options, etc.)
3. Update scenario lists in main configuration if needed
4. Test with dry run: `snakemake -call -n --configfile config/your-scenario.yaml`

### Modifying Optimization
- Edit solver parameters in `config.default.yaml` under `solving` section
- Modify network building logic in `scripts/prepare_network.py` or `scripts/prepare_sector_network.py`
- Add new constraints in `scripts/solve_network.py`

### Adding Visualizations
- Create new plotting scripts following patterns in `scripts/plot_*.py`
- Add corresponding rules in `rules/postprocess.smk`
- Update output specifications in main `Snakefile`

### Performance Monitoring
- HiGHS solver monitoring can be enabled in configuration
- Benchmark files track execution times in `benchmarks/`
- Memory usage controlled via `mem_mb` parameter in solving section

## Important File Locations

- **Main Workflow**: `Snakefile`
- **Environment**: `envs/` directory (platform-specific conda lock files)
- **Configuration**: `config/config.default.yaml` (base), `config/*.yaml` (scenarios)
- **Results**: `results/{run_name}/` (scenario-specific outputs)
- **Shared Resources**: `resources/` (potentially shared across scenarios)
- **Weather Data**: `cutouts/` (Atlite cutout files)
- **Custom Analysis Scripts**: Root directory (e.g., `run_co2_scenarios.py`, `analyze_*.py`)

