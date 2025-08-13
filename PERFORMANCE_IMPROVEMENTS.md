# PyPSA Performance & Robustness Improvements

This document describes the performance and robustness enhancements implemented for the PyPSA-DE pipeline, based on Step 7 requirements and analysis of the results notebook.

## Overview

The following improvements have been implemented:

1. **Enhanced run script** (`run_pypsa_robust.py`) with automatic CPU detection and resource management
2. **Memory error handling** in `compare_results.py` with dataset down-casting
3. **3-scenario plotting script** (`plot_3scenarios.py`) based on the notebook analysis
4. **Comprehensive logging and error handling**
5. **Automatic cleanup and validation**

## New Scripts

### 1. `run_pypsa_robust.py`

Enhanced PyPSA run script with the following features:

**Performance Optimizations:**
- **Auto CPU Detection**: Automatically detects available logical CPUs and uses all cores for maximum performance
- **Memory Management**: Uses `--resources mem_mb=30000` to match configuration requirements  
- **Rerun Support**: Adds `--rerun-incomplete` flag for interrupted runs

**Robustness Features:**
- **Config Validation**: Validates all config files exist and have valid YAML syntax before launching Snakemake
- **Tmp Cleanup**: Automatically cleans tmp folder of files older than 7 days at script start
- **Comprehensive Logging**: Detailed logging to `logs/pypsa_run_TIMESTAMP.log`
- **Error Handling**: Graceful error handling with detailed error messages

**Usage:**
```bash
# Run with specific scenario config
python run_pypsa_robust.py config/de-all-tech-2035.yaml

# Run with additional Snakemake arguments
python run_pypsa_robust.py config/de-no-ironair-2035.yaml --dry-run

# Show help and system info
python run_pypsa_robust.py --help
```

**Features Implemented:**
- ✅ Pass `--cores` to Snakemake equal to all available logical CPUs
- ✅ Add `--rerun-incomplete` flag for interrupted runs
- ✅ Use Snakemake `--resources mem_mb=30000` matching the configs
- ✅ Clean `tmp` folder older than 7 days at script start
- ✅ Validate that each config file exists before launching Snakemake

### 2. Enhanced `compare_results.py`

Updated results comparison script with memory optimization:

**Memory Error Handling:**
- ✅ Catch `MemoryError` inside `compare_results.py` and down-cast datasets if needed
- Automatic downcast of float64 to float32 and int64 to int32
- Optimized loading of large network files
- Graceful fallback when memory issues occur

**Enhanced Features:**
- Robust network discovery across multiple result directories
- Comprehensive KPI extraction (costs, capacities, emissions, capacity factors)
- Multiple visualization types (capacity comparison, cost breakdown, storage radar chart)
- CSV export of all results

### 3. `plot_3scenarios.py`

New dedicated script for plotting the 3-scenario comparison based on the notebook structure:

**Based on Notebook Analysis:**
- ✅ Learn from the `results-analysis-3scenarios.ipynb` file to plot final results
- Implements the same capacity data extraction logic
- Uses identical carrier grouping and color schemes
- Produces publication-quality stacked bar charts

**Features:**
- Automatic network discovery and loading
- Memory-optimized loading with downcast support
- CO2 emissions comparison table
- Installed capacity comparison table and charts
- Proper carrier ordering and color mapping as per notebook

**Usage:**
```bash
# Auto-detect results folder
python plot_3scenarios.py

# Specify results folder
python plot_3scenarios.py results-de-2030-white-paper-v3
```

## Performance Improvements Summary

### CPU and Memory Optimization
- **Dynamic CPU allocation**: Uses all system CPU cores for maximum performance
- **Memory constraints**: Fixed 30GB memory limit to prevent system overload
- **Data type optimization**: Automatic downcast of numeric types to reduce memory usage
- **Memory error recovery**: Graceful handling of memory errors with optimized retry

### Robustness Enhancements
- **Config validation**: Pre-flight checks for all required configuration files
- **Automatic cleanup**: Removes old temporary files before each run
- **Comprehensive logging**: Detailed logging with timestamps for debugging
- **Error recovery**: Continues processing even when individual networks fail to load

### Workflow Improvements
- **Interrupted run recovery**: `--rerun-incomplete` allows resuming failed runs
- **Real-time monitoring**: Live output streaming with logging
- **Resource monitoring**: System resource usage tracking
- **Automatic discovery**: Smart detection of result files and directories

## Directory Structure

```
.
├── run_pypsa_robust.py          # Enhanced run script
├── compare_results.py           # Updated with memory handling
├── plot_3scenarios.py           # 3-scenario plotting script
├── PERFORMANCE_IMPROVEMENTS.md  # This documentation
├── logs/                        # Enhanced logging directory
│   ├── pypsa_run_TIMESTAMP.log  # Run logs from robust script
│   └── analysis_TIMESTAMP.log   # Analysis logs
├── plots/                       # Enhanced plots directory
│   ├── TIMESTAMP_capacity_by_scenario.png
│   ├── TIMESTAMP_emissions_comparison.csv
│   └── TIMESTAMP_installed_capacity_comparison.csv
└── tmp/                         # Auto-cleaned temporary files
```

## Configuration Requirements

The scripts expect the following configuration files:
- `config/config.default.yaml` (required)
- `config/plotting.default.yaml` (required)
- `config/config.yaml` (optional)
- Scenario configs: `config/de-*.yaml`

## System Requirements

**Minimum:**
- 8 GB RAM (16+ GB recommended)
- 4 CPU cores (8+ recommended)
- Python 3.8+ with PyPSA, pandas, numpy, matplotlib, seaborn, psutil, pyyaml

**Optimal:**
- 32+ GB RAM for large networks
- 16+ CPU cores for parallel processing
- SSD storage for faster I/O

## Usage Examples

### Running a Complete Analysis Workflow

1. **Run scenarios with robust script:**
```bash
# Run all three scenarios
python run_pypsa_robust.py config/de-all-tech-2035.yaml
python run_pypsa_robust.py config/de-no-ironair-2035.yaml  
python run_pypsa_robust.py config/de-no-mds-2035.yaml
```

2. **Analyze and compare results:**
```bash
# Generate comprehensive comparison
python compare_results.py

# Create 3-scenario specific plots
python plot_3scenarios.py
```

3. **Check outputs:**
```
plots/TIMESTAMP_capacity_by_scenario.png    # Main comparison chart
plots/TIMESTAMP_emissions_comparison.csv     # CO2 emissions table
plots/TIMESTAMP_installed_capacity_comparison.csv  # Detailed capacity data
reports/summary_TIMESTAMP.csv               # Complete KPI summary
```

### Handling Memory Issues

If you encounter memory issues:

1. The scripts automatically detect and handle `MemoryError`
2. Data types are downcast from float64/int64 to float32/int32
3. Networks are loaded with optimized settings
4. Logging indicates when memory optimization is applied

### Debugging and Monitoring

All scripts provide comprehensive logging:
- Real-time console output
- Detailed log files with timestamps
- Error traces and debugging information
- Performance metrics (duration, memory usage)

## Validation

The improvements have been designed to:
- ✅ Match the notebook's plotting style and data processing
- ✅ Handle large networks that previously caused memory errors  
- ✅ Provide robust error handling and recovery
- ✅ Optimize system resource usage
- ✅ Maintain compatibility with existing PyPSA workflows

## Future Enhancements

Potential future improvements:
- Parallel network processing
- Database storage for results
- Web interface for monitoring
- Automated benchmark comparisons
- Cloud deployment support

## Troubleshooting

**Common Issues:**

1. **Config file not found**: Ensure all required config files exist and have valid YAML
2. **Memory errors**: Scripts automatically handle these, but ensure adequate RAM
3. **Network files missing**: Check that Snakemake completed successfully
4. **Permission errors**: Ensure write access to logs/, plots/, reports/, tmp/ directories

**Getting Help:**

Check the log files for detailed error information:
- `logs/pypsa_run_TIMESTAMP.log` for run issues
- `logs/analysis_TIMESTAMP.log` for analysis issues

All scripts support `--help` for usage information.
