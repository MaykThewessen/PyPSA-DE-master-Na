# Example PowerShell script to run a PyPSA scenario with full logging

# Import logging utilities
. .\LoggingUtils.ps1

# --- Main Script ---
$ScenarioName = "Example Python Scenario"

# Start logging
Start-ScenarioLogging -ScenarioName $ScenarioName -LogToSameFile $true

# Log a message from PowerShell
Write-ScenarioLog "Starting Python scenario from PowerShell" -Level Info

$pythonExecutable = "python3"
$scriptPath = ".\example_scenario_with_logging.py"

# Prepare for potential errors
$ErrorActionPreference = "Stop"

$success = $false
$errorMessage = $null

# Execute the Python script
try {
    Write-ScenarioLog "Executing Python script: $scriptPath" -Level Info
    
    # Run Python script and capture output
    $output = & $pythonExecutable $scriptPath 2>&1 | Tee-Object -Variable pythonOutput
    
    # Check for errors in Python execution
    if ($LASTEXITCODE -ne 0) {
        throw "Python script returned a non-zero exit code: $LASTEXITCODE"
    } else {
        Write-ScenarioLog "Python script executed successfully" -Level Success
        $success = $true
    }

} catch {
    # Catch errors
    $success = $false
    $errorMessage = $_.Exception.Message
    Write-ScenarioLog "An error occurred while running the Python script: $errorMessage" -Level Error
} finally {
    # Stop logging and send notifications
    Stop-ScenarioLogging -Success $success -ErrorMessage $errorMessage
}

# Restore error action preference
$ErrorActionPreference = "Continue"

Write-ScenarioLog "Script finished" -Level Info
