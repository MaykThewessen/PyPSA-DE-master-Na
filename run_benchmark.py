#!/usr/bin/env python
"""
Final benchmark script for PyPSA-Eur model performance testing.
"""

import subprocess
import sys
import time
import os
import shutil
import json
from datetime import datetime

def log(msg):
    """Simple logging function."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")
    sys.stdout.flush()

def run_with_config(config_file, target_name, timeout_minutes=60):
    """Run a test with specified configuration."""
    log(f"Starting test with config: {config_file}")
    
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
        
        # Test what the correct target should be
        log("Finding correct target...")
        dry_result = subprocess.run([
            "snakemake", "--dry-run", "-q"
        ], capture_output=True, text=True, timeout=30)
        
        if "solve_network" in dry_result.stdout:
            log("✓ solve_network rule found")
        else:
            log("⚠️ solve_network rule not found, using electricity target")
        
        # Determine target based on configuration
        if "test-week" in config_file:
            target = f"results/de-all-tech-2035-test-week/networks/base_s_37_elec_.nc"
        else:
            target = f"results/de-all-tech-2035-mayk/networks/base_s_37_elec_.nc"
        
        log(f"Target: {target}")
        
        # Run the actual workflow
        start_time = time.time()
        log(f"Starting {target_name} run...")
        
        result = subprocess.run([
            "snakemake", "-j2", 
            target
        ], capture_output=True, text=True, timeout=timeout_minutes * 60)
        
        elapsed = time.time() - start_time
        
        # Process results
        success = result.returncode == 0
        
        log(f"{'✓' if success else '✗'} {target_name} completed in {elapsed/60:.1f} minutes")
        
        if not success:
            log(f"Return code: {result.returncode}")
            if result.stderr:
                print("Last 300 chars of stderr:")
                print(result.stderr[-300:])
        
        return {
            "target_name": target_name,
            "config_file": config_file,
            "success": success,
            "time_minutes": elapsed / 60,
            "return_code": result.returncode,
            "stdout_lines": len(result.stdout.splitlines()) if result.stdout else 0,
            "stderr_lines": len(result.stderr.splitlines()) if result.stderr else 0,
            "stdout": result.stdout,
            "stderr": result.stderr
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

def main():
    """Main benchmark function."""
    log("PyPSA-Eur Benchmark Test Starting")
    log("="*60)
    
    results = {"timestamp": datetime.now().isoformat()}
    
    # Phase 1: One week slice (quick test)
    log("\nPHASE 1: ONE WEEK SLICE")
    log("-" * 30)
    
    week_result = run_with_config(
        "config/config.test-week.yaml", 
        "Week Slice", 
        timeout_minutes=30  # 30 minutes max
    )
    results["week_slice"] = week_result
    
    # Phase 2: Full year (if week was successful or if testing anyway)
    log("\nPHASE 2: FULL YEAR BASELINE")  
    log("-" * 30)
    
    if week_result.get("success"):
        log("Week slice succeeded, proceeding with full year...")
        year_result = run_with_config(
            "config/config.default.yaml",
            "Full Year",
            timeout_minutes=120  # 2 hours max
        )
    else:
        log("Week slice failed, but testing full year anyway...")
        year_result = run_with_config(
            "config/config.default.yaml",
            "Full Year", 
            timeout_minutes=30  # Shorter test
        )
    
    results["full_year"] = year_result
    
    # Phase 3: Analysis and reporting
    log("\nPHASE 3: RESULTS ANALYSIS")
    log("-" * 30)
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"benchmark_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        # Don't save the full stdout/stderr to keep file manageable
        clean_results = {k: {**v, "stdout": "...", "stderr": "..."} if isinstance(v, dict) and "stdout" in v else v 
                        for k, v in results.items()}
        json.dump(clean_results, f, indent=2)
    
    # Save logs separately
    os.makedirs("benchmark_logs", exist_ok=True)
    
    if "week_slice" in results and "stdout" in results["week_slice"]:
        with open(f"benchmark_logs/week_stdout_{timestamp}.log", 'w') as f:
            f.write(results["week_slice"]["stdout"] or "")
        with open(f"benchmark_logs/week_stderr_{timestamp}.log", 'w') as f:
            f.write(results["week_slice"]["stderr"] or "")
            
    if "full_year" in results and "stdout" in results["full_year"]:
        with open(f"benchmark_logs/year_stdout_{timestamp}.log", 'w') as f:
            f.write(results["full_year"]["stdout"] or "")
        with open(f"benchmark_logs/year_stderr_{timestamp}.log", 'w') as f:
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
    elif "error" in week:
        log(f"✗ Week slice: {week['error']}")
    else:
        log(f"✗ Week slice: Failed (code {week.get('return_code', 'unknown')})")
    
    # Full year results
    if year.get("success"):
        log(f"✓ Full year: {year.get('time_minutes', 0):.1f} minutes")
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
            log(f"\nPerformance Ratio: {ratio:.3f} (week/year)")
            
            if ratio < 0.1:
                log("🎯 Week slice is significantly faster (< 10% of full year)")
            elif ratio < 0.2:
                log("✅ Week slice is much faster (< 20% of full year)")
            else:
                log("⚠️ Week slice not as fast as expected (> 20% of full year)")
    
    log(f"\nDetailed results: {results_file}")
    log("Log files saved to: benchmark_logs/")
    log("\n✅ Benchmark completed!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n⚠️ Benchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        log(f"\n❌ Benchmark failed: {e}")
        raise
