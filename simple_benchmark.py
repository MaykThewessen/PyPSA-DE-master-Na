#!/usr/bin/env python
"""
Simplified benchmark script for PyPSA-Eur model runs.
Runs week slice first, then full year, and compares results.
"""

import subprocess
import sys
import time
import os
import shutil
import json
from datetime import datetime

def log(message):
    """Simple logging function."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()

def run_benchmark():
    """Run the benchmark tests."""
    
    log("Starting PyPSA-Eur Benchmark Test")
    log("="*50)
    
    results = {}
    
    # Test 1: One Week Slice
    log("PHASE 1: Running one-week slice benchmark...")
    
    # Backup existing config
    if os.path.exists("config/config.yaml"):
        shutil.copy2("config/config.yaml", "config/config.yaml.backup")
        log("Backed up existing config")
    
    try:
        # Use week configuration
        shutil.copy2("config/config.test-week.yaml", "config/config.yaml") 
        log("Applied week-slice configuration")
        
        # Run week slice
        start_time = time.time()
        log("Starting week-slice run...")
        
        result = subprocess.run([
            "conda", "run", "-n", "pypsa-eur",
            "snakemake", "-j2", "--forceall",
            "results/de-all-tech-2035-test-week/networks/base_s_37_elec_.nc"
        ], capture_output=True, text=True, timeout=3600)  # 1 hour timeout
        
        week_time = time.time() - start_time
        
        results['week'] = {
            'time_minutes': week_time / 60,
            'success': result.returncode == 0,
            'stdout_lines': len(result.stdout.splitlines()) if result.stdout else 0,
            'stderr_lines': len(result.stderr.splitlines()) if result.stderr else 0
        }
        
        if result.returncode == 0:
            log(f"✓ Week slice completed successfully in {week_time/60:.1f} minutes")
        else:
            log(f"✗ Week slice failed (return code: {result.returncode})")
            print("STDERR:", result.stderr[:500])  # Show first 500 chars
        
        # Save outputs
        os.makedirs("benchmark_outputs", exist_ok=True)
        with open("benchmark_outputs/week_stdout.log", "w") as f:
            f.write(result.stdout or "")
        with open("benchmark_outputs/week_stderr.log", "w") as f:
            f.write(result.stderr or "")
            
    except subprocess.TimeoutExpired:
        log("✗ Week slice timed out after 1 hour")
        results['week'] = {'error': 'timeout'}
    except Exception as e:
        log(f"✗ Week slice error: {e}")
        results['week'] = {'error': str(e)}
    
    # Test 2: Full Year (if week slice succeeded or we want to test anyway)
    log("\nPHASE 2: Running full-year baseline...")
    
    try:
        # Use baseline configuration  
        shutil.copy2("config/config.default.yaml", "config/config.yaml")
        log("Applied full-year configuration")
        
        # Run full year
        start_time = time.time()
        log("Starting full-year run...")
        
        result = subprocess.run([
            "conda", "run", "-n", "pypsa-eur", 
            "snakemake", "-j2", "--forceall",
            "results/de-all-tech-2035-mayk/networks/base_s_37_elec_.nc"
        ], capture_output=True, text=True, timeout=7200)  # 2 hour timeout
        
        year_time = time.time() - start_time
        
        results['year'] = {
            'time_minutes': year_time / 60,
            'success': result.returncode == 0,
            'stdout_lines': len(result.stdout.splitlines()) if result.stdout else 0,
            'stderr_lines': len(result.stderr.splitlines()) if result.stderr else 0
        }
        
        if result.returncode == 0:
            log(f"✓ Full year completed successfully in {year_time/60:.1f} minutes")
        else:
            log(f"✗ Full year failed (return code: {result.returncode})")
            print("STDERR:", result.stderr[:500])
        
        # Save outputs
        with open("benchmark_outputs/year_stdout.log", "w") as f:
            f.write(result.stdout or "")
        with open("benchmark_outputs/year_stderr.log", "w") as f:
            f.write(result.stderr or "")
            
    except subprocess.TimeoutExpired:
        log("✗ Full year timed out after 2 hours")
        results['year'] = {'error': 'timeout'}
    except Exception as e:
        log(f"✗ Full year error: {e}")
        results['year'] = {'error': str(e)}
    
    finally:
        # Restore original config
        if os.path.exists("config/config.yaml.backup"):
            shutil.move("config/config.yaml.backup", "config/config.yaml")
            log("Restored original configuration")
    
    # Generate comparison report
    log("\nPHASE 3: Generating benchmark report...")
    
    results['timestamp'] = datetime.now().isoformat()
    results_file = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    log(f"Detailed results saved to: {results_file}")
    
    # Print summary
    log("\n" + "="*50)
    log("BENCHMARK SUMMARY")
    log("="*50)
    
    week = results.get('week', {})
    year = results.get('year', {})
    
    if 'time_minutes' in week:
        log(f"Week slice:  {week['time_minutes']:.1f} min ({'✓' if week['success'] else '✗'})")
    else:
        log(f"Week slice:  Failed ({week.get('error', 'unknown')})")
    
    if 'time_minutes' in year:
        log(f"Full year:   {year['time_minutes']:.1f} min ({'✓' if year['success'] else '✗'})")
    else:
        log(f"Full year:   Failed ({year.get('error', 'unknown')})")
    
    # Calculate ratios if both succeeded
    if week.get('success') and year.get('success'):
        time_ratio = week['time_minutes'] / year['time_minutes']
        log(f"Time ratio:  {time_ratio:.3f} (week/year)")
        
        if time_ratio < 0.1:
            log("🎯 Week slice is significantly faster (< 10% of full year)")
        elif time_ratio < 0.2:
            log("✓ Week slice is much faster (< 20% of full year)")
        else:
            log("⚠️  Week slice not as fast as expected")
    
    # Check for log analysis opportunities
    if os.path.exists("benchmark_outputs"):
        log("\nLog files available for analysis:")
        for f in os.listdir("benchmark_outputs"):
            if f.endswith('.log'):
                size = os.path.getsize(f"benchmark_outputs/{f}")
                log(f"  - {f} ({size:,} bytes)")
    
    log("\n✓ Benchmark test completed!")
    log(f"Results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    try:
        results = run_benchmark()
    except KeyboardInterrupt:
        log("\n⚠️  Benchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        log(f"\n✗ Benchmark failed: {e}")
        sys.exit(1)
