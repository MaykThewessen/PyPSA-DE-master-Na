# PyPSA-DE Weekly Run Script
# Optimized for repeated runs - skips data downloads and shape building

param(
    [string]$Mode = "quick",
    [int]$Cores = 4
)

Write-Host "Starting PyPSA-DE weekly run in $Mode mode..." -ForegroundColor Green

switch ($Mode) {
    "quick" {
        # Skip data downloads, shapes, and base network - only solve
        Write-Host "Quick mode: Only solving optimization..." -ForegroundColor Yellow
        snakemake --cores $Cores `
            --forcerun solve_electricity_network `
            --rerun-triggers mtime params `
            all
    }
    "update-profiles" {
        # Update renewable profiles and solve
        Write-Host "Update mode: Refreshing renewable profiles..." -ForegroundColor Yellow
        snakemake --cores $Cores `
            --forcerun build_renewable_profiles solve_electricity_network `
            --rerun-triggers mtime params `
            all
    }
    "full-skip-data" {
        # Full run but skip data downloads
        Write-Host "Full mode: Complete run but skip data downloads..." -ForegroundColor Yellow
        snakemake --cores $Cores `
            --omit-from retrieve_databundle retrieve_eurostat_data retrieve_cutout `
            --rerun-triggers mtime params `
            all
    }
    "fresh" {
        # Complete fresh run
        Write-Host "Fresh mode: Complete run from scratch..." -ForegroundColor Red
        snakemake --cores $Cores all
    }
}

Write-Host "PyPSA-DE run completed!" -ForegroundColor Green
