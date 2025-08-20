#!/usr/bin/env python3
"""
PyPSA-DE Workflow with Automatic Dashboard Generation

Usage:
    python run_with_dashboard.py [snakemake_target]

Examples:
    python run_with_dashboard.py solve_elec_networks
    python run_with_dashboard.py
"""

import sys
import subprocess
import time
import os
from datetime import datetime

def run_snakemake_with_dashboard(target="solve_elec_networks"):
    """Run Snakemake target and automatically generate dashboard."""
    
    print("🚀 PyPSA-DE Workflow with Auto Dashboard")
    print("=" * 50)
    print(f"Target: {target}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Run Snakemake
    print("🔧 Running Snakemake optimization...")
    try:
        cmd = ["snakemake", "--use-conda", "-j", "1", target]
        print(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, check=True)
        print("✅ Snakemake completed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Snakemake failed with exit code {e.returncode}")
        return False
    except KeyboardInterrupt:
        print("⚠ Interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error running Snakemake: {e}")
        return False
    
    # Step 2: Wait a moment for files to be written
    print("\n⏳ Waiting for result files to be finalized...")
    time.sleep(5)
    
    # Step 3: Generate dashboard
    print("📊 Generating interactive dashboard...")
    try:
        result = subprocess.run([
            sys.executable, "create_styled_dashboard.py"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Dashboard generated successfully!")
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Dashboard generation failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"❌ Error generating dashboard: {e}")
        return False
    
    print("\n🎉 Workflow completed successfully!")
    print("=" * 50)
    return True

def main():
    """Main function."""
    
    # Get target from command line or use default
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = "solve_elec_networks"
    
    # Check if styled dashboard generator exists
    if not os.path.exists("create_styled_dashboard.py"):
        print("❌ create_styled_dashboard.py not found in current directory!")
        print("   Make sure you're running this from the PyPSA-DE directory.")
        return 1
    
    # Run the workflow
    success = run_snakemake_with_dashboard(target)
    
    if success:
        print("\n✨ All done! Check your browser for the dashboard.")
        return 0
    else:
        print("\n💥 Workflow failed. Check the error messages above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
