# Logging & Monitoring Best Practices

This document describes the logging and monitoring utilities implemented for PyPSA-DE benchmarking scenarios.

## Features

- **Python Logging**: Rotating file handler with 5 MB max size and 3 backups
- **PowerShell Transcript**: Full console output recording using `Start-Transcript`
- **Toast Notifications**: Windows notifications using `New-BurntToastNotification`
- **Runtime Tracking**: Automatic storage of runtime information in `reports/runtime_<timestamp>.txt`
- **Unified Logging**: Both Python and PowerShell can write to the same log files

## Directory Structure

```
├── logs/                    # Log files with rotating backups
│   ├── pypsa_scenario.log   # Main log file
│   ├── pypsa_scenario.log.1 # Backup 1 (when rotated)
│   └── pypsa_scenario.log.2 # Backup 2 (when rotated)
├── reports/                 # Runtime and execution reports
│   └── runtime_<timestamp>.txt
├── logger_utils.py          # Python logging utilities
├── LoggingUtils.ps1         # PowerShell logging utilities
└── example_scenario_with_logging.py  # Usage examples
```

## Python Usage

### Basic Logger Setup

```python
from logger_utils import create_scenario_logger

# Create a logger for your scenario
logger = create_scenario_logger("my_scenario")

# Start tracking a scenario
logger.start_scenario("My PyPSA Scenario")

# Log messages at different levels
logger.info("Processing network data...")
logger.warning("Non-critical issue detected")
logger.error("Critical error occurred")

# End the scenario (triggers notifications and runtime storage)
logger.end_scenario(success=True)  # or success=False with error_msg
```

### Advanced Usage

```python
try:
    logger.start_scenario("Complex PyPSA Analysis")
    
    # Your PyPSA code here
    logger.info("Loading network...")
    # ... do work ...
    
    logger.end_scenario(success=True)
    
except Exception as e:
    logger.error(f"Scenario failed: {str(e)}")
    logger.end_scenario(success=False, error_msg=str(e))
```

## PowerShell Usage

### Basic Script Structure

```powershell
# Import the utilities
. .\LoggingUtils.ps1

# Start logging with transcript
Start-ScenarioLogging -ScenarioName "My Scenario"

# Log messages
Write-ScenarioLog "Starting data processing" -Level Info
Write-ScenarioLog "Warning detected" -Level Warning

# Your PowerShell code here...

# Stop logging (triggers notifications and runtime storage)
Stop-ScenarioLogging -Success $true
```

### Running Python Scripts with PowerShell Logging

```powershell
. .\LoggingUtils.ps1

$ScenarioName = "Python Analysis"
Start-ScenarioLogging -ScenarioName $ScenarioName

try {
    Write-ScenarioLog "Executing Python script" -Level Info
    python .\my_pypsa_script.py
    
    if ($LASTEXITCODE -eq 0) {
        Stop-ScenarioLogging -Success $true
    } else {
        Stop-ScenarioLogging -Success $false -ErrorMessage "Python script failed"
    }
} catch {
    Stop-ScenarioLogging -Success $false -ErrorMessage $_.Exception.Message
}
```

## Log Files

### Python Log Format

```
2025-01-13 10:30:15 - pypsa_scenario - INFO - Starting scenario: My Scenario
2025-01-13 10:30:16 - pypsa_scenario - INFO - Loading network data...
2025-01-13 10:30:20 - pypsa_scenario - WARNING - Some non-critical issues found
2025-01-13 10:30:25 - pypsa_scenario - INFO - Scenario completed successfully in 0:00:10.523456
```

### PowerShell Transcript Integration

When using `LogToSameFile=$true`, PowerShell transcript output is appended to the same log file as Python, providing a complete record of all console activity.

## Toast Notifications

### Prerequisites

Install the BurntToast PowerShell module:

```powershell
Install-Module -Name BurntToast -Force -AllowPrerelease
```

### Notification Types

- **Success**: Green notification when scenarios complete successfully
- **Failure**: Red notification when scenarios fail, including error summary

### Fallback

If BurntToast is not available, the system falls back to Windows message boxes.

## Runtime Reports

Runtime information is automatically stored in `reports/runtime_<timestamp>.txt`:

```
Scenario: My PyPSA Scenario
Start Time: 2025-01-13T10:30:15
End Time: 2025-01-13T10:30:25
Runtime: 0:00:10.523456
Runtime (seconds): 10.52
Status: SUCCESS
Platform: Python
```

## Log Rotation

- **Max file size**: 5 MB per log file
- **Backup count**: 3 backup files kept
- **Rotation behavior**: When the main log file reaches 5 MB, it's renamed to `.log.1`, previous backups are shifted, and a new main log file is created

## Configuration Options

### Python Logger Options

```python
# Custom log directory
logger = ScenarioLogger("my_scenario", log_dir="custom_logs")

# Different scenario names create separate log files
logger1 = create_scenario_logger("network_analysis")  # → logs/pypsa_network_analysis.log
logger2 = create_scenario_logger("optimization")      # → logs/pypsa_optimization.log
```

### PowerShell Logging Options

```powershell
# Log to same file as Python (default)
Start-ScenarioLogging -ScenarioName "Test" -LogToSameFile $true

# Use separate PowerShell transcript file
Start-ScenarioLogging -ScenarioName "Test" -LogToSameFile $false
```

## Testing the Setup

### Test Python Logger

```bash
python logger_utils.py
```

### Test PowerShell Utilities

```powershell
. .\LoggingUtils.ps1
Test-LoggingUtils
```

### Test Complete Integration

```powershell
.\run_scenario_with_logging.ps1
```

## Integration with Existing Scripts

### For Python Scripts

Add these lines to your existing PyPSA scripts:

```python
from logger_utils import create_scenario_logger

# At the beginning of your script
logger = create_scenario_logger("your_scenario_name")
logger.start_scenario("Your Scenario Description")

# Replace print() statements with logger calls
# print("Loading data...") → logger.info("Loading data...")

# At the end of your script
try:
    # Your existing code here
    logger.end_scenario(success=True)
except Exception as e:
    logger.end_scenario(success=False, error_msg=str(e))
    raise
```

### For PowerShell Scripts

Wrap your existing scripts:

```powershell
. .\LoggingUtils.ps1
Start-ScenarioLogging -ScenarioName "Your Scenario"

# Your existing PowerShell code here
# Add Write-ScenarioLog calls where appropriate

Stop-ScenarioLogging -Success $true  # or $false if errors occurred
```

## Best Practices

1. **Always pair start/end calls**: Every `start_scenario()` or `Start-ScenarioLogging` should have a corresponding end call
2. **Use descriptive scenario names**: Names appear in notifications and reports
3. **Log at appropriate levels**: Use INFO for progress, WARNING for non-critical issues, ERROR for failures
4. **Handle exceptions**: Always wrap scenario execution in try/catch blocks
5. **Check log rotation**: Monitor disk space and adjust rotation settings if needed

## Troubleshooting

### Common Issues

1. **Toast notifications not working**: Install BurntToast module or check Windows notification settings
2. **Log files not created**: Ensure write permissions in logs/ directory
3. **PowerShell execution policy**: May need to run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
4. **Python import errors**: Ensure logger_utils.py is in the same directory or Python path

### Debugging

Enable debug logging:

```python
logger.logger.setLevel(logging.DEBUG)
logger.debug("Debug message")
```

Check current scenario info in PowerShell:

```powershell
$info = Get-CurrentScenarioInfo
if ($info) {
    Write-Host "Current scenario: $($info.ScenarioName)"
    Write-Host "Runtime: $($info.Runtime)"
}
```
