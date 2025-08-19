# Data Download Optimization

This document describes the enhanced data download system that has been implemented to avoid unnecessary re-downloading of data files that already exist.

## Overview

The PyPSA-DE repository now includes an intelligent data download system that:

1. **Checks for existing files** before attempting downloads
2. **Validates file integrity** using file size checks
3. **Provides configuration options** to control download behavior
4. **Reduces bandwidth usage** and speeds up workflow execution

## How It Works

### Automatic File Existence Checking

The system automatically checks if data files already exist before downloading them. This happens in two ways:

1. **Helper Function Level**: The enhanced `progress_retrieve()` function in `scripts/_helpers.py` checks for file existence before downloading.

2. **Script Level**: Individual retrieve scripts check if all their output files exist before starting the download process.

3. **Rule Level**: Some Snakemake rules include conditional logic to skip downloads when files exist.

### File Validation

The `file_exists_and_valid()` helper function performs basic validation:

- Checks if the file exists
- Optionally verifies the file has a reasonable size (default: >1KB)
- Can be extended to include checksum validation

## Configuration Options

### Enable/Disable Downloads

The existing configuration controls still work:

```yaml
enable:
  retrieve: auto  # auto, true, or false
  retrieve_databundle: false
  retrieve_cost_data: true
  retrieve_cutout: true
```

### Force Re-download

A new configuration option has been added:

```yaml
enable:
  force_download: false  # Set to true to force re-download even when files exist
```

When `force_download: true`, the system will:
- Download files even if they already exist
- Overwrite existing files
- Useful for updating data or fixing corrupted downloads

## Usage Examples

### Normal Operation (Skip Existing Files)

```bash
# Always unlock first to clear any locks
snakemake --unlock

# Run with default settings - skips existing files
snakemake retrieve_databundle
```

### Force Re-download All Data

1. **Via Configuration**: Set `enable.force_download: true` in your config file
2. **Via Command Line**: Override the config temporarily

```bash
# Force re-download via config override
snakemake retrieve_databundle --config enable.force_download=true
```

### Selective Force Re-download

To force re-download specific data while keeping others:

```bash
# Remove specific files and run snakemake
rm data/bundle/je-e-21.03.02.xls
snakemake retrieve_databundle
```

## Benefits

### Performance Improvements

- **Faster Workflow Startup**: Skip downloads of existing files
- **Reduced Bandwidth**: Only download missing or corrupted files
- **Better Resource Utilization**: Focus compute time on actual analysis

### Reliability Improvements

- **Graceful Handling**: System continues if files already exist
- **Validation**: Basic file integrity checks before skipping downloads
- **Flexibility**: Easy override when fresh data is needed

## Enhanced Scripts

The following scripts have been enhanced with conditional downloading:

### Core Data Scripts
- `retrieve_databundle.py` - Checks all bundle files before downloading
- `retrieve_cost_data.py` - Uses enhanced progress_retrieve function
- `retrieve_gas_infrastructure_data.py` - Checks gas network files

### Snakemake Rules
- `retrieve_cutout` - Conditional cutout downloading
- `retrieve_synthetic_electricity_demand` - Conditional demand data downloading
- Many other simple move-based rules

## Technical Details

### Enhanced Helper Functions

#### `file_exists_and_valid(file_path, check_size=True, min_size=1024)`

Checks if a file exists and appears valid:

```python
from scripts._helpers import file_exists_and_valid

# Basic existence check
if file_exists_and_valid("data/myfile.csv"):
    print("File exists and is valid")

# Custom size validation
if file_exists_and_valid("data/large_file.nc", min_size=1024*1024):  # 1MB minimum
    print("Large file exists and is valid")
```

#### `progress_retrieve(url, file, force_download=False, check_existing=True)`

Enhanced download function with existence checking:

```python
from scripts._helpers import progress_retrieve

# Normal download - skips if file exists
progress_retrieve("https://example.com/data.csv", "data/data.csv")

# Force download even if file exists
progress_retrieve("https://example.com/data.csv", "data/data.csv", force_download=True)

# Disable existence checking
progress_retrieve("https://example.com/data.csv", "data/data.csv", check_existing=False)
```

### Configuration Access

Scripts access the force_download setting via:

```python
force_download = snakemake.config["enable"].get("force_download", False)
```

## Troubleshooting

### File Appears Corrupted

If a file exists but appears corrupted:

1. **Delete the file**: `rm path/to/corrupted/file`
2. **Re-run the rule**: `snakemake rule_name`

Or use force download:

```bash
snakemake rule_name --config enable.force_download=true
```

### Downloads Still Happening

Check that:

1. Files exist in the expected location
2. Files have reasonable sizes (>1KB by default)
3. `force_download` is not set to `true`
4. The specific rule has been enhanced (not all rules include conditional logic yet)

### Mixed Behavior

Some rules have conditional logic while others don't. This is expected as the enhancement was applied selectively to:

- High-impact, frequently used rules
- Rules with large data files
- Scripts that handle multiple files

## Future Enhancements

Potential improvements for future versions:

1. **Checksum Validation**: Verify file integrity using checksums
2. **Timestamp Checking**: Download if remote file is newer
3. **Partial Download Resume**: Resume interrupted downloads
4. **Parallel Downloads**: Download multiple files simultaneously
5. **Cache Management**: Intelligent cleanup of old data files

## Migration Notes

### For Existing Users

- **No Breaking Changes**: Default behavior preserves existing functionality
- **Opt-in Enhancement**: Benefits are automatic, no configuration changes required
- **Override Available**: Force re-download when needed

### For Script Developers

When creating new retrieve scripts:

1. Use the enhanced `progress_retrieve()` function
2. Check `force_download` configuration setting
3. Validate output files before skipping downloads
4. Log decisions clearly for debugging

Example pattern:

```python
force_download = snakemake.config["enable"].get("force_download", False)

if all_outputs_exist and not force_download:
    logger.info("All files exist and force_download is False. Skipping download.")
else:
    # Proceed with download
    progress_retrieve(url, file_path, force_download=force_download)
```
