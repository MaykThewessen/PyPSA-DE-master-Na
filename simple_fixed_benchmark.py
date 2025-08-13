#!/usr/bin/env python
"""Simple fixed benchmark with corrected Snakemake syntax."""

import subprocess
import sys
import time
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

def log(msg):
    """Simple logging function."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")
    sys.stdout.flush()

def main():
    """Main test function."""
    log("Simple Fixed Benchmark Test")
    log("="*50)
    
    # Check if config files exist
    if not os.path.exists("config/config.test-week.yaml"):
        log("✗ config/config.test-week.yaml not found")
        return
    
    # Backup existing config
    if os.path.exists("config/config.yaml"):
        shutil.copy2("config/config.yaml", "config/config.yaml.backup")
        log("Backed up existing config")
    
    try:
        # Apply week config
        shutil.copy2("config/config.test-week.yaml", "config/config.yaml")
        log("Applied week test configuration")
        
        # Get local temp directory for scratch files
        local_temp = Path(tempfile.gettempdir()) / "pypsa_scratch"
        local_temp.mkdir(exist_ok=True)
        log(f"Using local temp: {local_temp}")
        
        # Clean up incomplete files first
        log("Cleaning up incomplete files...")
        subprocess.run([
            "conda", "run", "-n", "pypsa-eur", 
            "snakemake", "--cleanup-metadata", "--quiet", "all"
        ], capture_output=True, text=True, timeout=60)
        
        # Run with optimized command (simplified)
        log("Starting week slice test...")
        start_time = time.time()
        
        # Simple command without problematic flags
        result = subprocess.run([
            "conda", "run", "-n", "pypsa-eur",
            "snakemake", 
            "--cores", "2",
            "--forceall",
            "results/de-all-tech-2035-test-week/networks/base_s_37_elec_.nc"
        ], capture_output=True, text=True, timeout=1800)  # 30 minute timeout
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            log(f"✓ Week slice completed successfully in {elapsed/60:.1f} minutes!")
        else:
            log(f"✗ Week slice failed in {elapsed/60:.1f} minutes")
            log(f"Return code: {result.returncode}")
            if result.stderr:
                print("STDERR (last 500 chars):")
                print(result.stderr[-500:])
        
        # Check for scratch directory warnings
        if result.stderr:
            scratch_warnings = result.stderr.count("Creating scratch directories is taking a surprisingly long time")
            if scratch_warnings > 0:
                log(f"⚠️ Found {scratch_warnings} scratch directory warnings")
                log("💡 The warnings suggest using --local-storage-prefix for performance")
            else:
                log("✓ No scratch directory warnings found")
        
        # Save logs for analysis
        os.makedirs("simple_test_logs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(f"simple_test_logs/stdout_{timestamp}.log", "w") as f:
            f.write(result.stdout or "")
        with open(f"simple_test_logs/stderr_{timestamp}.log", "w") as f:
            f.write(result.stderr or "")
        
        log(f"Logs saved to simple_test_logs/ with timestamp {timestamp}")
        
    except subprocess.TimeoutExpired:
        log("✗ Test timed out after 30 minutes")
    except Exception as e:
        log(f"✗ Error: {e}")
    finally:
        # Restore original config
        if os.path.exists("config/config.yaml.backup"):
            shutil.move("config/config.yaml.backup", "config/config.yaml")
            log("Restored original configuration")
    
    log("✅ Simple test completed!")

if __name__ == "__main__":
    main()
