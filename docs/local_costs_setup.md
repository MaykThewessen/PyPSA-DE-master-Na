# Local Costs Setup

This document explains how the PyPSA-DE repository is configured to always use local `costs_2035.csv` files instead of downloading them from the cloud.

## Overview

The system has been configured to:

1. **Never download costs data from the cloud** by default
2. **Always use local costs files** that are already present in the repository
3. **Automatically find and copy** the appropriate local costs file
4. **Create a fallback** if no local costs file is found

## Configuration Changes

### Cost Data Retrieval Disabled

In `config/config.default.yaml`, cost data retrieval has been disabled:

```yaml
enable:
  retrieve_cost_data: false  # Use local costs files, don't download from cloud
```

This setting ensures that the system will never attempt to download costs data from remote sources.

## How It Works

### Local Costs Rule

A new Snakemake rule `ensure_local_costs` has been added that:

1. **Searches for existing local costs files** in multiple locations:
   - `resources/costs_2035.csv` (main location)
   - `resources/{run_name}/costs_2035.csv` (scenario-specific)
   - `resources/de-co2-scenario-A-2035/costs_2035.csv` (fallback scenarios)
   - `resources/de-co2-scenario-B-2035/costs_2035.csv`
   - `resources/de-co2-scenario-C-2035/costs_2035.csv`
   - `resources/de-co2-scenario-D-2035/costs_2035.csv`

2. **Copies the first found file** to the expected output location

3. **Creates a basic template** if no local file is found (emergency fallback)

### Current Local Files

The system has found these existing local costs files:

```
/Users/m/PyPSA-DE-master-Na/resources/de-co2-scenario-B-2035/costs_2035.csv
/Users/m/PyPSA-DE-master-Na/resources/de-co2-scenario-C-2035/costs_2035.csv
/Users/m/PyPSA-DE-master-Na/resources/de-all-tech-2035-mayk/costs_2035.csv
/Users/m/PyPSA-DE-master-Na/resources/costs_2035.csv
/Users/m/PyPSA-DE-master-Na/resources/de-co2-scenario-A-2035/costs_2035.csv
```

## Usage

### Normal Operation

When you run the workflow, it will automatically:

1. Check for local costs files
2. Use the most appropriate one for your scenario
3. Log which file it's using
4. Never attempt to download from the cloud

Example:
```bash
# Always unlock first to clear any existing locks
snakemake --unlock

# Then run the workflow
snakemake -c all
```

The system will automatically use local costs files without any additional configuration.

### Verifying Local Costs Usage

You can check the logs to see which local costs file is being used:

```bash
# Check the ensure_local_costs log
cat logs/ensure_local_costs_2035.log
```

This will show output like:
```
INFO: Using local costs file: resources/costs_2035.csv
INFO: Copied local costs from resources/costs_2035.csv to resources/costs_2035.csv
```

## Updating Local Costs Files

### To Update Costs Data

1. **Edit the local costs file directly**:
   ```bash
   # Edit the main costs file
   vim resources/costs_2035.csv
   
   # Or edit scenario-specific files
   vim resources/de-co2-scenario-A-2035/costs_2035.csv
   ```

2. **The changes will be automatically used** in the next workflow run

### To Add New Costs Files

1. **Place new costs files** in the appropriate directory:
   ```bash
   # For general use
   cp my_new_costs.csv resources/costs_2035.csv
   
   # For specific scenarios
   cp my_scenario_costs.csv resources/my-scenario/costs_2035.csv
   ```

2. **The system will automatically find and use them**

## File Structure

```
resources/
├── costs_2035.csv                           # Main costs file (preferred)
├── de-co2-scenario-A-2035/
│   └── costs_2035.csv                       # Scenario A specific costs
├── de-co2-scenario-B-2035/
│   └── costs_2035.csv                       # Scenario B specific costs
├── de-co2-scenario-C-2035/
│   └── costs_2035.csv                       # Scenario C specific costs
└── de-co2-scenario-D-2035/
    └── costs_2035.csv                       # Scenario D specific costs
```

## Benefits

### ✅ **Complete Control**
- Full control over costs data without external dependencies
- No risk of costs being overwritten by cloud updates
- Consistent costs across runs

### ✅ **No Internet Dependency**
- Workflow runs without internet connection for costs data
- Faster execution (no download time)
- Reliable operation in offline environments

### ✅ **Version Control**
- Local costs files can be tracked in git
- Changes are visible in version control
- Easy to revert to previous costs

### ✅ **Scenario Flexibility**
- Different scenarios can use different costs files
- Easy to test sensitivity to cost assumptions
- Supports custom cost scenarios

## Emergency Fallback

If no local costs file is found, the system will create a basic template with default values:

```csv
technology,parameter,value,unit,source
solar,investment,380,EUR/kW,local_default
onwind,investment,1200,EUR/kW,local_default
offwind-ac,investment,2500,EUR/kW,local_default
...
```

This ensures the workflow can always continue even if local files are missing.

## Troubleshooting

### "No local costs file found" Warning

If you see this warning:
```
WARNING: No local costs file found for year 2035. Creating basic template.
```

**Solution**: Add a local costs file:
```bash
# Copy an existing costs file to the main location
cp resources/de-co2-scenario-A-2035/costs_2035.csv resources/costs_2035.csv
```

### Costs Not Updating

If your costs changes aren't being used:

1. **Check the file location**:
   ```bash
   ls -la resources/costs_2035.csv
   ```

2. **Force regeneration**:
   ```bash
   rm resources/costs_2035.csv
   snakemake ensure_local_costs
   ```

3. **Check the log**:
   ```bash
   cat logs/ensure_local_costs_2035.log
   ```

### Wrong Costs File Being Used

If the wrong local costs file is being used:

1. **Check the search order** (first found file wins):
   - Main resources directory first
   - Then scenario-specific directories
   - Then fallback scenarios

2. **Move your preferred file** to the main location:
   ```bash
   cp path/to/preferred/costs_2035.csv resources/costs_2035.csv
   ```

## Re-enabling Cloud Downloads (If Needed)

If you ever need to re-enable cloud downloads:

1. **Change the configuration** in `config/config.default.yaml`:
   ```yaml
   enable:
     retrieve_cost_data: true  # Re-enable cloud downloads
   ```

2. **Force download** by removing local files:
   ```bash
   rm resources/costs_2035.csv
   snakemake retrieve_cost_data
   ```

**Note**: This is not recommended as it will overwrite your local costs files.

## Summary

The system is now configured to:

- ✅ **Always use local costs files**
- ✅ **Never download from cloud** (by default)
- ✅ **Automatically find appropriate local files**
- ✅ **Preserve your cost customizations**
- ✅ **Work reliably offline**

Your local `costs_2035.csv` files are protected and will always be used instead of cloud data.
