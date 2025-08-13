# PyPSA-DE Queue Runner Script
# Processes scenarios from queue file with comprehensive logging and error handling

param(
    [string]$QueueFile = "scenario_queue.yaml",
    [string]$Profile = "windows",
    [string]$SnakemakeArgs = ""
)

# Import required modules
Add-Type -AssemblyName System.Web

# Initialize directories
$LogsDir = "logs"
$RunsDir = "runs"

if (!(Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
}

if (!(Test-Path $RunsDir)) {
    New-Item -ItemType Directory -Path $RunsDir -Force | Out-Null
}

# Function to get timestamp
function Get-TimeStamp {
    return Get-Date -Format "yyyyMMdd_HHmmss"
}

# Function to write log with timestamp
function Write-Log {
    param(
        [string]$Message,
        [string]$LogFile,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    if ($LogFile) {
        Add-Content -Path $LogFile -Value $logEntry -Encoding UTF8
    }
}

# Function to parse YAML (simple parsing for our structure)
function Parse-YamlQueue {
    param([string]$FilePath)
    
    if (!(Test-Path $FilePath)) {
        throw "Queue file not found: $FilePath"
    }
    
    $content = Get-Content $FilePath -Raw
    $scenarios = @()
    
    # Simple YAML parsing for our specific structure
    $lines = $content -split "`r?`n"
    $inScenarios = $false
    $currentScenario = @{}
    
    foreach ($line in $lines) {
        $line = $line.Trim()
        if ($line -eq "scenarios:") {
            $inScenarios = $true
            continue
        }
        
        if ($inScenarios) {
            if ($line -match "^\s*-\s*file:\s*(.+)") {
                if ($currentScenario.Count -gt 0) {
                    $scenarios += [PSCustomObject]$currentScenario
                }
                $currentScenario = @{
                    file = $matches[1].Trim()
                }
            }
            elseif ($line -match "^\s*tag:\s*(.+)") {
                $currentScenario.tag = $matches[1].Trim()
            }
        }
    }
    
    # Add the last scenario
    if ($currentScenario.Count -gt 0) {
        $scenarios += [PSCustomObject]$currentScenario
    }
    
    return $scenarios
}

# Main execution with error handling
try {
    $startTime = Get-Date
    $timestamp = Get-TimeStamp
    $mainLogFile = Join-Path $LogsDir "queue_run_$timestamp.log"
    
    Write-Log "Starting queue runner at $startTime" $mainLogFile
    Write-Log "Queue file: $QueueFile" $mainLogFile
    Write-Log "Profile: $Profile" $mainLogFile
    Write-Log "Additional Snakemake args: $SnakemakeArgs" $mainLogFile
    
    # Parse queue file
    Write-Log "Parsing queue file..." $mainLogFile
    $scenarios = Parse-YamlQueue $QueueFile
    Write-Log "Found $($scenarios.Count) scenarios to process" $mainLogFile
    
    $successCount = 0
    $failureCount = 0
    
    # Process each scenario
    for ($i = 0; $i -lt $scenarios.Count; $i++) {
        $scenario = $scenarios[$i]
        $scenarioStartTime = Get-Date
        $scenarioNumber = $i + 1
        
        Write-Host "`n" -NoNewline
        Write-Host "=" * 80 -ForegroundColor Cyan
        Write-Host "Processing scenario $scenarioNumber/$($scenarios.Count): $($scenario.tag)" -ForegroundColor Green
        Write-Host "Config file: $($scenario.file)" -ForegroundColor Yellow
        Write-Host "=" * 80 -ForegroundColor Cyan
        
        # Create scenario-specific log file
        $scenarioTimestamp = Get-TimeStamp
        $scenarioLogFile = Join-Path $LogsDir "${scenarioTimestamp}_$($scenario.tag).log"
        
        Write-Log "Starting scenario: $($scenario.tag)" $scenarioLogFile
        Write-Log "Config file: $($scenario.file)" $scenarioLogFile
        Write-Log "Start time: $scenarioStartTime" $scenarioLogFile
        
        # Verify config file exists
        if (!(Test-Path $scenario.file)) {
            $errorMsg = "Config file not found: $($scenario.file)"
            Write-Log $errorMsg $scenarioLogFile "ERROR"
            Write-Log $errorMsg $mainLogFile "ERROR"
            $failureCount++
            Write-Host "ERROR: $errorMsg" -ForegroundColor Red
            break
        }
        
        # Create runs directory for this scenario
        $scenarioRunsDir = Join-Path $RunsDir $scenario.tag
        if (!(Test-Path $scenarioRunsDir)) {
            New-Item -ItemType Directory -Path $scenarioRunsDir -Force | Out-Null
        }
        
        # Build Snakemake command
        $cores = $env:NUMBER_OF_PROCESSORS
        if (-not $cores) {
            $cores = 4  # Default fallback
        }
        
        $snakemakeCmd = "snakemake -j $cores --configfile `"$($scenario.file)`" --profile $Profile"
        if ($SnakemakeArgs) {
            $snakemakeCmd += " $SnakemakeArgs"
        }
        $snakemakeCmd += " all"
        
        Write-Log "Executing: $snakemakeCmd" $scenarioLogFile
        Write-Log "Executing: $snakemakeCmd" $mainLogFile
        
        # Execute Snakemake
        try {
            $process = Start-Process -FilePath "powershell" -ArgumentList "-Command", $snakemakeCmd -NoNewWindow -PassThru -RedirectStandardOutput "$scenarioLogFile.stdout" -RedirectStandardError "$scenarioLogFile.stderr"
            $process.WaitForExit()
            $exitCode = $process.ExitCode
            
            # Append stdout and stderr to main log
            if (Test-Path "$scenarioLogFile.stdout") {
                $stdout = Get-Content "$scenarioLogFile.stdout" -Raw
                if ($stdout) {
                    Add-Content -Path $scenarioLogFile -Value "`n--- STDOUT ---`n$stdout" -Encoding UTF8
                }
                Remove-Item "$scenarioLogFile.stdout" -Force
            }
            
            if (Test-Path "$scenarioLogFile.stderr") {
                $stderr = Get-Content "$scenarioLogFile.stderr" -Raw
                if ($stderr) {
                    Add-Content -Path $scenarioLogFile -Value "`n--- STDERR ---`n$stderr" -Encoding UTF8
                }
                Remove-Item "$scenarioLogFile.stderr" -Force
            }
        }
        catch {
            $exitCode = 1
            $errorMsg = "Failed to execute Snakemake: $($_.Exception.Message)"
            Write-Log $errorMsg $scenarioLogFile "ERROR"
            Write-Log $errorMsg $mainLogFile "ERROR"
        }
        
        $scenarioEndTime = Get-Date
        $elapsed = $scenarioEndTime - $scenarioStartTime
        $elapsedString = "{0:hh\:mm\:ss}" -f $elapsed
        
        Write-Log "Exit code: $exitCode" $scenarioLogFile
        Write-Log "End time: $scenarioEndTime" $scenarioLogFile
        Write-Log "Elapsed time: $elapsedString" $scenarioLogFile
        
        if ($exitCode -eq 0) {
            # Success - create DONE marker
            $doneFile = Join-Path $scenarioRunsDir "DONE"
            $doneContent = @"
Scenario: $($scenario.tag)
Config: $($scenario.file)
Start Time: $scenarioStartTime
End Time: $scenarioEndTime
Elapsed Time: $elapsedString
Exit Code: $exitCode
"@
            Set-Content -Path $doneFile -Value $doneContent -Encoding UTF8
            
            $successCount++
            Write-Host "SUCCESS: Scenario '$($scenario.tag)' completed in $elapsedString" -ForegroundColor Green
            Write-Log "SUCCESS: Scenario '$($scenario.tag)' completed in $elapsedString" $mainLogFile
        }
        else {
            # Failure - log and abort
            $failureCount++
            $errorMsg = "FAILURE: Scenario '$($scenario.tag)' failed with exit code $exitCode after $elapsedString"
            Write-Host $errorMsg -ForegroundColor Red
            Write-Log $errorMsg $mainLogFile "ERROR"
            Write-Log "Aborting remaining runs due to failure" $mainLogFile "ERROR"
            
            break
        }
    }
    
    # Final summary
    $totalEndTime = Get-Date
    $totalElapsed = $totalEndTime - $startTime
    $totalElapsedString = "{0:hh\:mm\:ss}" -f $totalElapsed
    
    Write-Host "`n" -NoNewline
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host "Queue Runner Summary" -ForegroundColor Green
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host "Total scenarios: $($scenarios.Count)" -ForegroundColor Yellow
    Write-Host "Successful: $successCount" -ForegroundColor Green
    Write-Host "Failed: $failureCount" -ForegroundColor Red
    Write-Host "Total elapsed time: $totalElapsedString" -ForegroundColor Yellow
    Write-Host "=" * 80 -ForegroundColor Cyan
    
    Write-Log "Queue runner completed" $mainLogFile
    Write-Log "Total scenarios: $($scenarios.Count)" $mainLogFile
    Write-Log "Successful: $successCount" $mainLogFile  
    Write-Log "Failed: $failureCount" $mainLogFile
    Write-Log "Total elapsed time: $totalElapsedString" $mainLogFile
    
    # Exit with appropriate code
    if ($failureCount -gt 0) {
        exit 1
    }
    else {
        exit 0
    }
}
catch {
    # Global error handling
    $errorTimestamp = Get-TimeStamp
    $errorLogFile = Join-Path $LogsDir "error_$errorTimestamp.log"
    
    $errorMsg = "FATAL ERROR in queue runner: $($_.Exception.Message)"
    $stackTrace = $_.Exception.StackTrace
    
    $errorContent = @"
Timestamp: $(Get-Date)
Error: $($_.Exception.Message)
Script: $($_.InvocationInfo.ScriptName)
Line: $($_.InvocationInfo.ScriptLineNumber)
Command: $($_.InvocationInfo.Line.Trim())

Full Exception:
$($_.Exception | Out-String)

Stack Trace:
$stackTrace
"@
    
    Set-Content -Path $errorLogFile -Value $errorContent -Encoding UTF8
    
    Write-Host $errorMsg -ForegroundColor Red
    Write-Host "Error details written to: $errorLogFile" -ForegroundColor Red
    
    exit 1
}
