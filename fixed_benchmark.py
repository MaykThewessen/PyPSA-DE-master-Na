#!/usr/bin/env python
"""Fixed benchmark script with proper Snakemake syntax and performance optimizations."""

import subprocess
import sys
import time
import os
import shutil
import json
import tempfile
from datetime import datetime
from pathlib import Path

def log(msg):
    """Simple logging function."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")
    sys.stdout.flush()

def get_local_temp():
    """Get a local temporary directory for scratch files."""
    # Use Windows temp directory which should be local, not network
    local_temp = Path(tempfile.gettempdir()) / "pypsa_scratch"
    local_temp.mkdir(exist_ok=True)
    return str(local_temp)

def run_with_optimizations(config_file, target_name, timeout_minutes=60):
    """Run benchmark with optimized Snakemake settings."""
    log(f"Starting {target_name} with config: {config_file}")
    
    # Backup existing config
    backup_file = None
    if os.path.exists("config/config.yaml"):
        backup_file = f"config/config.yaml.backup_{int(time.time())}"
        shutil.copy2("config/config.yaml", backup_file)
        log("Backed up existing config")
    
    try:
        # Apply test config
        shutil.copy2(config_file, "config/config.yaml")
        log("Applied test configuration")
        
        # Clean up any incomplete files first
        log("Cleaning up incomplete files...")
        cleanup_result = subprocess.run([
            "conda", "run", "-n", "pypsa-eur", 
            "snakemake", "--cleanup-metadata", "--quiet", "all"
        ], capture_output=True, text=True, timeout=60)
        
        # Determine target based on configuration
        if "test-week" in config_file:
            target = "results/de-all-tech-2035-test-week/networks/base_s_37_elec_.nc"
        else:
            target = "results/de-all-tech-2035-mayk/networks/base_s_37_elec_.nc"
        
        log(f"Target: {target}")
        
        # Get local temp directory
        local_temp = get_local_temp()
        log(f"Using local temp directory: {local_temp}")
        
        # Build optimized command with performance flags
        start_time = time.time()
        log(f"Starting {target_name} run...")
        
        cmd = [
            "conda", "run", "-n", "pypsa-eur",
            "snakemake",
            "--cores", "2",              # Use 2 cores
            "--forceall",                # Force rerun for clean comparison
            "--quiet", "all",            # Quiet output (fixed syntax!)
            "--local-storage-prefix", local_temp,  # Use local storage for scratch files
            "--shared-fs-usage", "none", # Assume no shared filesystem to force local operations
            target                       # Target file (must be last)
        ]
        
        log(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=timeout_minutes * 60
        )
        
        elapsed = time.time() - start_time
        
        # Process results
        success = result.returncode == 0
        
        log(f"{'✓' if success else '✗'} {target_name} completed in {elapsed/60:.1f} minutes")
        
        if not success:
            log(f"Return code: {result.returncode}")
            if result.stderr:
                print("Last 500 chars of stderr:")
                print(result.stderr[-500:])
        
        return {
            "target_name": target_name,
            "config_file": config_file,
            "success": success,
            "time_minutes": elapsed / 60,
            "return_code": result.returncode,
            "stdout_lines": len(result.stdout.splitlines()) if result.stdout else 0,
            "stderr_lines": len(result.stderr.splitlines()) if result.stderr else 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "local_temp_used": local_temp
        }
        
    except subprocess.TimeoutExpired:
        log(f"✗ {target_name} timed out after {timeout_minutes} minutes")
        return {
            "target_name": target_name,
            "config_file": config_file,
            "success": False,
            "error": "timeout",
            "time_minutes": timeout_minutes
        }
        
    except Exception as e:
        log(f"✗ {target_name} error: {e}")
        return {
            "target_name": target_name,
            "config_file": config_file,
            "success": False,
            "error": str(e)
        }
        
    finally:
        # Restore original config
        if backup_file and os.path.exists(backup_file):
            shutil.move(backup_file, "config/config.yaml")
            log("Restored original configuration")

def check_config_files():
    """Check that required config files exist."""
    required_files = [
        "config/config.test-week.yaml",
        "config/config.default.yaml"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        log("✗ Missing required config files:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    log("✓ All required config files found")
    return True

def main():
    """Main benchmark function."""
    log("Fixed PyPSA-Eur Benchmark Starting")
    log("="*60)
    
    # Check prerequisites
    if not check_config_files():
        log("❌ Prerequisites not met. Exiting.")
        sys.exit(1)
    
    results = {"timestamp": datetime.now().isoformat()}
    
    # Test the quick week slice first
    log("\nPHASE 1: WEEK SLICE TEST")
    log("-" * 30)
    
    week_result = run_with_optimizations(
        "config/config.test-week.yaml", 
        "Week Slice", 
        timeout_minutes=30
    )
    results["week_slice"] = week_result
    
    # Only run full year if week slice was successful
    if week_result.get("success"):
        log("\nPHASE 2: FULL YEAR TEST")  
        log("-" * 30)
        
        year_result = run_with_optimizations(
            "config/config.default.yaml",
            "Full Year",
            timeout_minutes=120
        )
        results["full_year"] = year_result
    else:
        log("\n⚠️ Skipping full year test due to week slice failure")
        results["full_year"] = {"skipped": "week_slice_failed"}
    
    # Save results
    log("\nPHASE 3: SAVING RESULTS")
    log("-" * 30)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"fixed_benchmark_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        # Save clean version without huge stdout/stderr
        clean_results = {
            k: {**v, "stdout": "...", "stderr": "..."} if isinstance(v, dict) and "stdout" in v else v 
            for k, v in results.items()
        }
        json.dump(clean_results, f, indent=2)
    
    # Save logs separately
    os.makedirs("fixed_benchmark_logs", exist_ok=True)
    
    if "week_slice" in results and "stdout" in results["week_slice"]:
        with open(f"fixed_benchmark_logs/week_stdout_{timestamp}.log", 'w') as f:
            f.write(results["week_slice"]["stdout"] or "")
        with open(f"fixed_benchmark_logs/week_stderr_{timestamp}.log", 'w') as f:
            f.write(results["week_slice"]["stderr"] or "")
    
    if "full_year" in results and "stdout" in results.get("full_year", {}):
        with open(f"fixed_benchmark_logs/year_stdout_{timestamp}.log", 'w') as f:
            f.write(results["full_year"]["stdout"] or "")
        with open(f"fixed_benchmark_logs/year_stderr_{timestamp}.log", 'w') as f:
            f.write(results["full_year"]["stderr"] or "")
    
    # Print summary
    log("\n" + "="*60)
    log("BENCHMARK SUMMARY")
    log("="*60)
    
    week = results.get("week_slice", {})
    year = results.get("full_year", {})
    
    # Week slice results
    if week.get("success"):
        log(f"✓ Week slice: {week.get('time_minutes', 0):.1f} minutes")
        if "local_temp_used" in week:
            log(f"  Local temp directory: {week['local_temp_used']}")
    elif "error" in week:
        log(f"✗ Week slice: {week['error']}")
    else:
        log(f"✗ Week slice: Failed (code {week.get('return_code', 'unknown')})")
    
    # Full year results
    if year.get("success"):
        log(f"✓ Full year: {year.get('time_minutes', 0):.1f} minutes")
    elif year.get("skipped"):
        log("⚠️ Full year: Skipped due to week slice failure")
    elif "error" in year:
        log(f"✗ Full year: {year['error']}")
    else:
        log(f"✗ Full year: Failed (code {year.get('return_code', 'unknown')})")
    
    # Performance comparison
    if week.get("success") and year.get("success"):
        week_time = week.get("time_minutes", 0)
        year_time = year.get("time_minutes", 0)
        if year_time > 0:
            ratio = week_time / year_time
            log(f"\n📊 Performance Ratio: {ratio:.3f} (week/year)")
            
            if ratio < 0.1:
                log("🎯 Week slice is significantly faster (< 10% of full year)")
            elif ratio < 0.2:
                log("✅ Week slice is much faster (< 20% of full year)")
            else:
                log("⚠️ Week slice not as fast as expected (> 20% of full year)")
    
    log(f"\n📁 Results saved to: {results_file}")
    log("📁 Log files saved to: fixed_benchmark_logs/")
    
    # Check if the scratch directory warnings are resolved
    if week.get("stderr"):
        scratch_warnings = week["stderr"].count("Creating scratch directories is taking a surprisingly long time")
        if scratch_warnings == 0:
            log("🎉 Scratch directory performance issue resolved!")
        else:
            log(f"⚠️ Still {scratch_warnings} scratch directory warnings")
    
    log("\n✅ Fixed benchmark completed!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n⚠️ Benchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        log(f"\n❌ Benchmark failed: {e}")
        raise
