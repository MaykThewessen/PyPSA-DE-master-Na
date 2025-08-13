# PowerShell wrapper script to run all PyPSA-Eur scenario analysis steps
# Usage: .\run_all.ps1
# Or schedule with Windows Task Scheduler

param(
    [switch]$Verbose
)

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PyPSA-Eur Scenario Analysis Pipeline" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Start time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Green
Write-Host ""

try {
    # Step 1: Run the scenario queue
    Write-Host "Step 1: Running scenario queue..." -ForegroundColor Yellow
    & .\run-queue.ps1
    
    if ($LASTEXITCODE -ne 0) { 
        Write-Error "Scenario run failed. Abort."
        exit 1 
    }
    Write-Host "✓ Scenario queue completed successfully" -ForegroundColor Green
    Write-Host ""

    # Step 2: Activate conda environment and run comparison script
    Write-Host "Step 2: Activating conda environment and running comparison..." -ForegroundColor Yellow
    
    # Check if conda is available
    $condaCommand = Get-Command conda -ErrorAction SilentlyContinue
    if (-not $condaCommand) {
        Write-Error "Conda is not available in PATH. Please ensure Anaconda/Miniconda is installed and added to PATH."
        exit 1
    }
    
    # Activate conda environment
    conda activate pypsa-eur
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to activate pypsa-eur conda environment. Please ensure the environment exists."
        exit 1
    }
    Write-Host "✓ Conda environment 'pypsa-eur' activated" -ForegroundColor Green
    
    # Run comparison script
    python scripts\compare_results.py
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Results comparison script failed."
        exit 1
    }
    Write-Host "✓ Results comparison completed successfully" -ForegroundColor Green
    Write-Host ""

    # Step 3: Final summary
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "PIPELINE COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "End time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Generated outputs:" -ForegroundColor Yellow
    Write-Host "• Results report: Check the results/ directory for CSV files and analysis reports" -ForegroundColor White
    Write-Host "• Plots and figures: Check the plots/ directory for generated visualizations" -ForegroundColor White
    Write-Host "• Log files: Check the logs/ directory for detailed execution logs" -ForegroundColor White
    Write-Host ""
    
    # Check if output directories exist and provide specific paths
    $resultsDir = "results"
    $plotsDir = "plots"
    $logsDir = "logs"
    
    if (Test-Path $resultsDir) {
        $resultFiles = Get-ChildItem $resultsDir -Filter "*.csv" | Select-Object -First 5
        if ($resultFiles) {
            Write-Host "Recent result files:" -ForegroundColor Cyan
            $resultFiles | ForEach-Object { Write-Host "  • $($_.FullName)" -ForegroundColor Gray }
        }
    }
    
    if (Test-Path $plotsDir) {
        $plotFiles = Get-ChildItem $plotsDir -Filter "*.png" | Select-Object -First 5
        if ($plotFiles) {
            Write-Host "Recent plot files:" -ForegroundColor Cyan
            $plotFiles | ForEach-Object { Write-Host "  • $($_.FullName)" -ForegroundColor Gray }
        }
    }
    
    Write-Host ""
    Write-Host "To schedule this script with Windows Task Scheduler:" -ForegroundColor Yellow
    Write-Host "1. Open Task Scheduler (taskschd.msc)" -ForegroundColor White
    Write-Host "2. Create Basic Task..." -ForegroundColor White
    Write-Host "3. Set trigger (daily, weekly, etc.)" -ForegroundColor White
    Write-Host "4. Action: Start a program" -ForegroundColor White
    Write-Host "   Program: powershell.exe" -ForegroundColor White
    Write-Host "   Arguments: -ExecutionPolicy Bypass -File `"$(Resolve-Path $PSCommandPath)`"" -ForegroundColor White
    Write-Host "   Start in: `"$(Get-Location)`"" -ForegroundColor White
    Write-Host ""

} catch {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "PIPELINE FAILED!" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "End time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Red
    exit 1
}

Write-Host "All done! 🎉" -ForegroundColor Green
