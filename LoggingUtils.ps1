# PowerShell Logging and Monitoring Utilities for PyPSA-DE
# Provides transcript logging, toast notifications, and runtime tracking

# Import required modules
if (Get-Module -ListAvailable -Name BurntToast) {
    Import-Module BurntToast -ErrorAction SilentlyContinue
} else {
    Write-Warning "BurntToast module not available. Install with: Install-Module -Name BurntToast -Force"
}

# Global variables
$script:ScenarioStartTime = $null
$script:CurrentScenario = $null
$script:TranscriptPath = $null
$script:LogsDir = "logs"
$script:ReportsDir = "reports"

function Initialize-LoggingDirectories {
    <#
    .SYNOPSIS
    Ensures logging directories exist
    #>
    if (-not (Test-Path $script:LogsDir)) {
        New-Item -ItemType Directory -Path $script:LogsDir -Force | Out-Null
    }
    if (-not (Test-Path $script:ReportsDir)) {
        New-Item -ItemType Directory -Path $script:ReportsDir -Force | Out-Null
    }
}

function Start-ScenarioLogging {
    <#
    .SYNOPSIS
    Starts transcript logging and scenario tracking
    
    .PARAMETER ScenarioName
    Name of the scenario being executed
    
    .PARAMETER LogToSameFile
    Whether to log to the same file as Python logger (default: true)
    #>
    param(
        [Parameter(Mandatory=$true)]
        [string]$ScenarioName,
        
        [Parameter(Mandatory=$false)]
        [bool]$LogToSameFile = $true
    )
    
    Initialize-LoggingDirectories
    
    # Stop any existing transcript
    try {
        Stop-Transcript -ErrorAction SilentlyContinue
    } catch {
        # Transcript wasn't running, ignore
    }
    
    $script:CurrentScenario = $ScenarioName
    $script:ScenarioStartTime = Get-Date
    
    # Determine transcript file path
    if ($LogToSameFile) {
        # Use same log file as Python logger
        $script:TranscriptPath = Join-Path $script:LogsDir "pypsa_$($ScenarioName.ToLower().Replace(' ', '_')).log"
    } else {
        # Use separate PowerShell transcript file
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $script:TranscriptPath = Join-Path $script:LogsDir "ps_transcript_$($ScenarioName.ToLower().Replace(' ', '_'))_$timestamp.log"
    }
    
    # Start transcript with append mode to work with Python logger
    try {
        Start-Transcript -Path $script:TranscriptPath -Append -Force
        Write-Host "PowerShell transcript started: $script:TranscriptPath" -ForegroundColor Green
        Write-Host "Scenario started: $ScenarioName at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
    } catch {
        Write-Error "Failed to start transcript: $_"
    }
}

function Stop-ScenarioLogging {
    <#
    .SYNOPSIS
    Stops transcript logging and records scenario completion
    
    .PARAMETER Success
    Whether the scenario completed successfully
    
    .PARAMETER ErrorMessage
    Error message if scenario failed
    #>
    param(
        [Parameter(Mandatory=$false)]
        [bool]$Success = $true,
        
        [Parameter(Mandatory=$false)]
        [string]$ErrorMessage = $null
    )
    
    if ($null -eq $script:ScenarioStartTime) {
        Write-Warning "Stop-ScenarioLogging called without Start-ScenarioLogging"
        return
    }
    
    $endTime = Get-Date
    $runtime = $endTime - $script:ScenarioStartTime
    
    # Log completion in transcript
    $status = if ($Success) { "COMPLETED" } else { "FAILED" }
    Write-Host "Scenario '$script:CurrentScenario' $status at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor $(if ($Success) { "Green" } else { "Red" })
    Write-Host "Total runtime: $($runtime.ToString())" -ForegroundColor Yellow
    
    if (-not $Success -and $ErrorMessage) {
        Write-Host "Error: $ErrorMessage" -ForegroundColor Red
    }
    
    # Stop transcript
    try {
        Stop-Transcript
        Write-Host "PowerShell transcript stopped" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to stop transcript: $_"
    }
    
    # Store runtime information
    Save-RuntimeInfo -Runtime $runtime -Success $Success -ErrorMessage $ErrorMessage
    
    # Emit toast notification
    Send-ToastNotification -Success $Success -Runtime $runtime -ErrorMessage $ErrorMessage
    
    # Reset tracking variables
    $script:ScenarioStartTime = $null
    $script:CurrentScenario = $null
    $script:TranscriptPath = $null
}

function Save-RuntimeInfo {
    <#
    .SYNOPSIS
    Saves runtime information to reports directory
    #>
    param(
        [Parameter(Mandatory=$true)]
        [timespan]$Runtime,
        
        [Parameter(Mandatory=$true)]
        [bool]$Success,
        
        [Parameter(Mandatory=$false)]
        [string]$ErrorMessage
    )
    
    try {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $runtimeFile = Join-Path $script:ReportsDir "runtime_$timestamp.txt"
        
        $content = @()
        $content += "Scenario: $script:CurrentScenario"
        $content += "Start Time: $($script:ScenarioStartTime.ToString('yyyy-MM-ddTHH:mm:ss'))"
        $content += "End Time: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')"
        $content += "Runtime: $($Runtime.ToString())"
        $content += "Runtime (seconds): $([math]::Round($Runtime.TotalSeconds, 2))"
        $content += "Status: $(if ($Success) { 'SUCCESS' } else { 'FAILURE' })"
        $content += "Platform: PowerShell"
        
        if ($ErrorMessage) {
            $content += "Error: $ErrorMessage"
        }
        
        $content | Out-File -FilePath $runtimeFile -Encoding UTF8
        Write-Host "Runtime info saved to: $runtimeFile" -ForegroundColor Green
        
    } catch {
        Write-Error "Failed to save runtime info: $_"
    }
}

function Send-ToastNotification {
    <#
    .SYNOPSIS
    Sends Windows toast notification for scenario completion
    #>
    param(
        [Parameter(Mandatory=$true)]
        [bool]$Success,
        
        [Parameter(Mandatory=$true)]
        [timespan]$Runtime,
        
        [Parameter(Mandatory=$false)]
        [string]$ErrorMessage
    )
    
    try {
        $status = if ($Success) { "Completed" } else { "Failed" }
        $runtimeStr = "$([math]::Round($Runtime.TotalSeconds, 1))s"
        
        $title = "PyPSA Scenario $status"
        
        if ($Success) {
            $message = "'$script:CurrentScenario' completed successfully in $runtimeStr"
        } else {
            $message = "'$script:CurrentScenario' failed after $runtimeStr"
            if ($ErrorMessage) {
                $shortError = if ($ErrorMessage.Length -gt 100) { $ErrorMessage.Substring(0, 100) + "..." } else { $ErrorMessage }
                $message += "`nError: $shortError"
            }
        }
        
        # Try to use BurntToast module
        if (Get-Module -ListAvailable -Name BurntToast) {
            Import-Module BurntToast -ErrorAction SilentlyContinue
            New-BurntToastNotification -Text $title, $message
            Write-Host "Toast notification sent" -ForegroundColor Green
        } else {
            # Fallback to message box
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.MessageBox]::Show($message, $title) | Out-Null
            Write-Host "Message box shown (BurntToast not available)" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Warning "Failed to send toast notification: $_"
    }
}

function Write-ScenarioLog {
    <#
    .SYNOPSIS
    Writes a timestamped log message to both console and transcript
    #>
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [Parameter(Mandatory=$false)]
        [ValidateSet("Info", "Warning", "Error", "Success")]
        [string]$Level = "Info"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    switch ($Level) {
        "Info"    { Write-Host $logMessage -ForegroundColor White }
        "Warning" { Write-Host $logMessage -ForegroundColor Yellow }
        "Error"   { Write-Host $logMessage -ForegroundColor Red }
        "Success" { Write-Host $logMessage -ForegroundColor Green }
    }
}

function Get-CurrentScenarioInfo {
    <#
    .SYNOPSIS
    Returns information about the currently running scenario
    #>
    if ($script:ScenarioStartTime) {
        return @{
            ScenarioName = $script:CurrentScenario
            StartTime = $script:ScenarioStartTime
            Runtime = (Get-Date) - $script:ScenarioStartTime
            TranscriptPath = $script:TranscriptPath
        }
    } else {
        return $null
    }
}

# Example usage function
function Test-LoggingUtils {
    <#
    .SYNOPSIS
    Tests the logging utilities
    #>
    Write-Host "Testing PowerShell Logging Utils..." -ForegroundColor Cyan
    
    # Test scenario logging
    Start-ScenarioLogging -ScenarioName "Test Scenario"
    
    Write-ScenarioLog "This is an info message" -Level "Info"
    Write-ScenarioLog "This is a warning message" -Level "Warning"
    Write-ScenarioLog "This is a success message" -Level "Success"
    
    # Simulate some work
    Start-Sleep -Seconds 2
    
    # Test successful completion
    Stop-ScenarioLogging -Success $true
    
    Start-Sleep -Seconds 1
    
    # Test failure scenario
    Start-ScenarioLogging -ScenarioName "Failed Test Scenario"
    Write-ScenarioLog "This is an error message" -Level "Error"
    Start-Sleep -Seconds 1
    Stop-ScenarioLogging -Success $false -ErrorMessage "Simulated failure for testing"
}

# Export functions for module usage
Export-ModuleMember -Function @(
    'Start-ScenarioLogging',
    'Stop-ScenarioLogging',
    'Write-ScenarioLog',
    'Send-ToastNotification',
    'Save-RuntimeInfo',
    'Get-CurrentScenarioInfo',
    'Test-LoggingUtils'
)

# If script is run directly, show help
if ($MyInvocation.InvocationName -eq $MyInvocation.MyCommand.Name) {
    Write-Host @"
PowerShell Logging Utilities for PyPSA-DE

Available functions:
- Start-ScenarioLogging -ScenarioName "YourScenario"
- Stop-ScenarioLogging [-Success `$true] [-ErrorMessage "Error details"]
- Write-ScenarioLog -Message "Your message" [-Level "Info|Warning|Error|Success"]
- Test-LoggingUtils

Example usage:
. .\LoggingUtils.ps1
Start-ScenarioLogging -ScenarioName "My Scenario"
Write-ScenarioLog "Processing data..." -Level "Info"
Stop-ScenarioLogging -Success `$true

"@ -ForegroundColor Green
}
