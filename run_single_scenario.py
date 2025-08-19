#!/usr/bin/env python3
"""
Run a single CO2 scenario with proper demand scaling
"""

import os
import sys
import yaml
import subprocess
import pandas as pd
import numpy as np
from pathlib import Path

def update_config_for_demand(config_path, co2_target, scenario_name, demand_twh):
    """Update configuration file for specific CO2 scenario with proper demand"""
    
    print(f"📝 Updating config for Scenario {scenario_name}: {co2_target*100:.0f}% CO2 target")
    print(f"⚡️ Setting demand to {demand_twh} TWh/y")
    
    # Load base configuration
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Update CO2 targets
    config['co2_budget'][2035] = co2_target
    config['electricity']['co2limit'] = co2_target

    # Set proper demand scaling
    # Default base demand in PyPSA-EUR is ~491.5 TWh for Germany
    scaling_factor = demand_twh / 491.5
    config['load']['scaling_factor'] = scaling_factor
    print(f"   Scaling factor: {scaling_factor:.3f}")
    
    # Scenario configuration
    config['scenario']['opts'] = [f'Co2L{co2_target:.2f}']
    config['run']['name'] = f"de-co2-scenario-{scenario_name}-2035-650TWh"
    
    # Keep existing solver configuration from base config
    
    # Save updated config
    scenario_config_path = f"config/de-co2-scenario-{scenario_name}-2035-650TWh.yaml"
    os.makedirs("config", exist_ok=True)
    with open(scenario_config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"✅ Config saved: {scenario_config_path}")
    return scenario_config_path

def run_scenario(config_path, scenario_name, co2_target):
    """Run PyPSA optimization for one scenario"""
    
    print(f"\n🚀 Starting Scenario {scenario_name} optimization with 650 TWh demand...")
    print("=" * 70)
    
    try:
        # Run snakemake command
        cmd = [
            "snakemake", 
            "-j4",  # Use fewer cores for stability
            f"--configfile={config_path}",
            "solve_elec_networks",
            "--forceall",  # Force rebuild everything
            "--latency-wait", "60",
            "--retries", "3",
            "--restart-times", "2"
        ]
        
        print(f"🔄 Running command: {' '.join(cmd)}")
        
        # Run with real-time output streaming
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=os.getcwd()
        )
        
        print("\n📺 Real-time progress:")
        print("=" * 70)
        
        # Stream output in real-time
        for line in process.stdout:
            print(line.rstrip())
            
        # Wait for process to complete
        return_code = process.wait(timeout=3600)  # 1 hour timeout
        
        if return_code == 0:
            print("\n" + "=" * 70)
            print(f"✅ Scenario {scenario_name} completed successfully!")
            return True
        else:
            print("\n" + "=" * 70)
            print(f"❌ Scenario {scenario_name} failed with return code {return_code}!")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"\n⏰ Scenario {scenario_name} timed out after 1 hour")
        return False
    except Exception as e:
        print(f"❌ Error running Scenario {scenario_name}: {e}")
        return False

def main():
    """Run single scenario test"""
    
    print("🚀 PyPSA Single Scenario Test - 650 TWh Demand")
    print("=" * 70)
    
    # Test with Scenario D (net-zero)
    scenario_name = 'D'
    co2_target = 0.00
    demand_twh = 650
    
    base_config = "config/de-co2-scenarios-2035.yaml"
    
    # Update configuration
    config_path = update_config_for_demand(base_config, co2_target, scenario_name, demand_twh)
    
    # Run scenario
    success = run_scenario(config_path, scenario_name, co2_target)
    
    if success:
        print(f"\n🎉 Scenario {scenario_name} with 650 TWh demand completed successfully!")
    else:
        print(f"\n❌ Scenario {scenario_name} failed")

if __name__ == "__main__":
    main()
