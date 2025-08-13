# PyPSA-EUR Environment Setup Script
# Run this script to set up the environment variables for PyPSA-EUR

# Activate the pypsa-eur conda environment
conda activate pypsa-eur

# Set project root variables
$env:PYPSA_ROOT = "C:\Users\mayk\PyPSA-DE-master-Na-2"
$env:PYPSA_DIR = "C:\Users\mayk\PyPSA-DE-master-Na-2"
$env:TMPDIR = "C:\Users\mayk\PyPSA-DE-master-Na-2\tmp"

# Add scripts directory to PATH
$env:PATH += ";C:\Users\mayk\PyPSA-DE-master-Na-2\scripts"

# Display current environment settings
Write-Host "Environment Setup Complete!" -ForegroundColor Green
Write-Host "PYPSA_ROOT: $env:PYPSA_ROOT" -ForegroundColor Cyan
Write-Host "PYPSA_DIR: $env:PYPSA_DIR" -ForegroundColor Cyan
Write-Host "TMPDIR: $env:TMPDIR" -ForegroundColor Cyan
Write-Host "Scripts directory added to PATH" -ForegroundColor Cyan

# Show available scenarios
Write-Host "`nAvailable scenarios:" -ForegroundColor Yellow
Get-ChildItem "config\de-*.yaml" | ForEach-Object { Write-Host "  - $($_.BaseName)" -ForegroundColor White }

# Show existing resources that can be reused
Write-Host "`nExisting resources available for reuse:" -ForegroundColor Yellow
Write-Host "  - Cutouts: $(Get-ChildItem cutouts | Measure-Object | Select-Object -ExpandProperty Count) files" -ForegroundColor White
Write-Host "  - Base networks: $(Get-ChildItem results\networks | Measure-Object | Select-Object -ExpandProperty Count) files" -ForegroundColor White
Write-Host "  - Resource files: $(Get-ChildItem resources | Where-Object {$_.Length -gt 1MB} | Measure-Object | Select-Object -ExpandProperty Count) large files" -ForegroundColor White
