#!/usr/bin/env python3
"""
Post-Optimization Workflow for PyPSA-DE
Automatically triggered after optimization to process results and create dashboard.
"""

import os
import sys
import time
import subprocess
from datetime import datetime

def wait_for_results(max_wait_minutes=5):
    """Wait for optimization results to be written to disk."""
    
    print("⏳ Waiting for optimization results to be written...")
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    
    while time.time() - start_time < max_wait_seconds:
        # Check if recent .nc files exist
        recent_files = []
        for root, dirs, files in os.walk("results"):
            for file in files:
                if file.endswith('.nc') and 'elec_Co2L' in file:
                    file_path = os.path.join(root, file)
                    # Check if file was modified in last 10 minutes
                    if os.path.getmtime(file_path) > time.time() - 600:
                        recent_files.append(file_path)
        
        if len(recent_files) >= 4:  # Expect 4 scenarios
            print(f"✅ Found {len(recent_files)} recent result files")
            return True
        
        time.sleep(10)  # Wait 10 seconds before checking again
    
    print(f"⚠ Timeout waiting for results after {max_wait_minutes} minutes")
    return False

def run_dashboard_generation():
    """Run the auto dashboard generator."""
    
    print("🚀 Running dashboard generation...")
    
    try:
        # Run the styled dashboard generator
        result = subprocess.run([
            sys.executable, 'create_styled_dashboard.py'
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        if result.returncode == 0:
            print("✅ Dashboard generation completed successfully!")
            print(result.stdout)
            return True
        else:
            print("❌ Dashboard generation failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Dashboard generation timed out!")
        return False
    except Exception as e:
        print(f"❌ Error running dashboard generation: {e}")
        return False

def main():
    """Main post-optimization workflow."""
    
    print("🔄 Post-Optimization Workflow - PyPSA-DE")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Wait for results to be available
    if not wait_for_results():
        print("❌ Workflow failed: No recent results found")
        return 1
    
    # Step 2: Generate dashboard
    if not run_dashboard_generation():
        print("❌ Workflow failed: Dashboard generation error")
        return 1
    
    print("\n🎉 Post-optimization workflow completed successfully!")
    print("=" * 50)
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
