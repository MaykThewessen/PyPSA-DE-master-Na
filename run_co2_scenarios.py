#!/usr/bin/env python3
"""
Run PyPSA-EUR for 4 CO2 scenarios sequentially
A) 15% of 1990 emissions
B) 5% of 1990 emissions  
C) 1% of 1990 emissions
D) 0% of 1990 emissions (net-zero)

Features:
- 2920 timesteps (3-hour resolution)
- LP optimization only
- 5-hour solver time limit
- 1e-6 tolerance
- Simplified linear transmission losses
"""

import os
import sys
import yaml
import shutil
import subprocess
import pandas as pd
import numpy as np
from pathlib import Path


def update_config_for_scenario(config_path, co2_target, scenario_name, demand_twh=None):
    """Update configuration file for specific CO2 scenario"""
    
    print(f"📝 Updating config for Scenario {scenario_name}: {co2_target*100:.0f}% CO2 target")
    
    # Load base configuration
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Update CO2 targets - convert to absolute values based on 1990 baseline
    co2_base_1990_Mt = 1487  # Mt CO2 in 1990
    co2_limit_absolute_tonnes = co2_target * co2_base_1990_Mt * 1e6  # Convert Mt to tonnes
    
    config['co2_budget'][2035] = co2_target
    config['electricity']['co2limit'] = co2_limit_absolute_tonnes
    
    print(f"🌍 CO2 limit set to {co2_limit_absolute_tonnes/1e6:.1f} Mt/year ({co2_target*100:.0f}% of 1990)")

    # Enable shared resources to avoid rebuilding common files
    config['run']['shared_resources'] = {
        'policy': True,  # Enable shared resources
        'exclude': []    # Don't exclude anything from sharing
    }
    
    # Note: Hydrogen storage uses flexible Store component, not StorageUnit with max_hours
    
    if demand_twh:
        # Default average demand is 491.5 TWh / 8760 h = 56.1 GW
        # Scaling factor = (new_demand / 491.5)
        scaling_factor = demand_twh / 491.5
        config['load']['scaling_factor'] = scaling_factor
        print(f"⚡️ Overriding demand to {demand_twh} TWh/y (scaling factor: {scaling_factor:.2f})")
    config['scenario']['opts'] = [f'Co2L{co2_target:.2f}']
    config['run']['name'] = f"de-co2-scenario-{scenario_name}-2035"
    
    # Save updated config
    scenario_config_path = f"config/de-co2-scenario-{scenario_name}-2035.yaml"
    with open(scenario_config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"✅ Config saved: {scenario_config_path}")
    return scenario_config_path

def run_scenario(config_path, scenario_name, co2_target):
    """Run PyPSA optimization for one scenario"""
    
    print(f"\n🚀 Starting Scenario {scenario_name} optimization...")
    print("=" * 60)
    
    # Create results directory
    results_dir = f"results/de-co2-scenario-{scenario_name}-2035"
    os.makedirs(results_dir, exist_ok=True)
    
    # Check if scenario is already completed
    import glob
    network_pattern = f"{results_dir}/networks/base_s_1_elec_Co2L*.nc"
    existing_networks = glob.glob(network_pattern)
    
    if existing_networks:
        print(f"✅ Scenario {scenario_name} already completed! Found network file:")
        print(f"   {existing_networks[0]}")
        print(f"⏩ Skipping optimization, using existing results")
        return True
    
    # Check if network building is already done and we just need to solve
    unsolved_pattern = f"{results_dir}/networks/base_s_1_elec_.nc"
    unsolved_networks = glob.glob(unsolved_pattern)
    
    if unsolved_networks:
        print(f"🔧 Network already built, targeting solve step only...")
        target = f"results/de-co2-scenario-{scenario_name}-2035/networks/base_s_1_elec_Co2L{co2_target:.2f}.nc"
    else:
        print(f"🏗️  Building complete network and solving...")
        target = "solve_elec_networks"
    
    try:
        # Run snakemake command with improved network settings
        # Remove --forceall to avoid unnecessary re-downloads of existing data
        cmd = [
            "snakemake", 
            "-j10",  # Reduce cores to avoid overwhelming network
            f"--configfile={config_path}",
            "solve_elec_networks",
            "--latency-wait", "30",  # Wait longer for file operations
            "--retries", "5",  # Retry failed jobs more times
            "--restart-times", "3",  # Allow more restarts
            "--rerun-triggers", "mtime"  # Only rerun if files are newer
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
        print("=" * 60)
        
        # Stream output in real-time
        try:
            for line in process.stdout:
                print(line.rstrip())
                
            # Wait for process to complete
            return_code = process.wait(timeout=7200)  # 2 hour timeout
            
            if return_code == 0:
                print("\n" + "=" * 60)
                print(f"✅ Scenario {scenario_name} completed successfully!")
                return True
            else:
                print("\n" + "=" * 60)
                print(f"❌ Scenario {scenario_name} failed with return code {return_code}!")
                return False
                
        except subprocess.TimeoutExpired:
            process.kill()
            print(f"\n⏰ Scenario {scenario_name} timed out after 2 hours")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Scenario {scenario_name} timed out after 2 hours")
        return False
    except Exception as e:
        print(f"❌ Error running Scenario {scenario_name}: {e}")
        return False

def extract_results(scenario_name, co2_target):
    """Extract key results from scenario network file"""
    
    print(f"📊 Extracting results for Scenario {scenario_name}...")
    
    try:
        import pypsa
        
        # Find the network file
        results_pattern = f"results/de-co2-scenario-{scenario_name}-2035/networks/base_s_1_elec_Co2L*.nc"
        import glob
        network_files = glob.glob(results_pattern)
        
        if not network_files:
            print(f"⚠️  No network file found for Scenario {scenario_name}")
            return None
        
        network_file = network_files[0]
        print(f"📂 Loading network: {network_file}")
        
        # Load network
        n = pypsa.Network(network_file)
        
        # Extract capacity data
        results = {
            'scenario': scenario_name,
            'co2_target_pct': co2_target * 100,
            'annual_consumption_TWh': n.loads_t.p.sum().sum() / 1e6 # TWh
        }
        
        # Generator capacities
        for tech in ['solar', 'onwind', 'offwind-ac', 'CCGT', 'OCGT', 'nuclear', 'biomass']:
            if tech in n.generators.carrier.values:
                capacity = n.generators[n.generators.carrier == tech].p_nom_opt.sum()
                results[f'{tech}_capacity_GW'] = capacity / 1000  # Convert MW to GW
            else:
                results[f'{tech}_capacity_GW'] = 0.0
        
        # Storage capacities
        for tech in ['battery', 'Hydrogen', 'iron-air', 'PHS']:
            if tech in n.storage_units.carrier.values:
                power = n.storage_units[n.storage_units.carrier == tech].p_nom_opt.sum()
                energy = n.storage_units[n.storage_units.carrier == tech].state_of_charge_initial.sum()
                results[f'{tech}_power_GW'] = power / 1000  # Convert MW to GW
                results[f'{tech}_energy_GWh'] = energy / 1000  # Convert MWh to GWh
            else:
                results[f'{tech}_power_GW'] = 0.0
                results[f'{tech}_energy_GWh'] = 0.0
        
        # System totals
        results['total_renewable_GW'] = (
            results.get('solar_capacity_GW', 0) + 
            results.get('onwind_capacity_GW', 0) + 
            results.get('offwind-ac_capacity_GW', 0)
        )
        
        results['total_storage_power_GW'] = (
            results.get('battery_power_GW', 0) + 
            results.get('Hydrogen_power_GW', 0) + 
            results.get('PHS_power_GW', 0) +
            results.get('ironair_power_GW', 0)
        )
        
        results['total_storage_energy_GWh'] = (
            results.get('battery_energy_GWh', 0) + 
            results.get('Hydrogen_energy_GWh', 0) + 
            results.get('PHS_energy_GWh', 0) +
            results.get('ironair_energy_GWh', 0)
        )
        
        # System costs
        results['total_system_cost_billion_EUR'] = n.objective / 1e9
        
        # CO2 emissions
        co2_emissions = 0
        for carrier in ['CCGT', 'OCGT', 'coal', 'lignite']:
            if carrier in n.generators.carrier.values:
                gen = n.generators[n.generators.carrier == carrier]
                if len(gen) > 0:
                    # Estimate emissions (simplified)
                    generation = gen.p.sum().sum() if hasattr(gen, 'p') else 0
                    co2_intensity = {'CCGT': 0.35, 'OCGT': 0.45, 'coal': 0.82, 'lignite': 0.95}.get(carrier, 0)
                    co2_emissions += generation * co2_intensity
        
        results['co2_emissions_MtCO2'] = co2_emissions / 1e6
        
        print(f"✅ Results extracted for Scenario {scenario_name}")
        return results
        
    except Exception as e:
        print(f"❌ Error extracting results for Scenario {scenario_name}: {e}")
        return None

def create_comparison_csv(all_results):
    """Create comparison CSV from all scenario results"""
    
    print("\n📊 Creating comparison CSV...")
    
    # Convert to DataFrame
    df = pd.DataFrame(all_results)
    df = df.round(2)
    
    # Save to CSV
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    comparison_file = f"co2_scenarios_comparison_{timestamp}.csv"
    df.to_csv(comparison_file, index=False)
    
    print(f"✅ Comparison saved: {comparison_file}")
    
    # Display summary
    print("\n📈 SCENARIO COMPARISON SUMMARY:")
    print("=" * 60)
    
    for _, row in df.iterrows():
        print(f"Scenario {row['scenario']} ({row['co2_target_pct']:.0f}% CO2):")
        print(f"  Renewables: {row['total_renewable_GW']:.1f} GW")
        print(f"  Storage: {row['total_storage_power_GW']:.1f} GW / {row['total_storage_energy_GWh']:.1f} GWh")
        print(f"  System Cost: €{row['total_system_cost_billion_EUR']:.1f} billion")
        print(f"  CO2 Emissions: {row['co2_emissions_MtCO2']:.1f} Mt")
        print()
    
    return comparison_file

def run_dashboard_generation(comparison_file):
    """Run the enhanced dashboard generation script"""
    
    print("\n🎨 Generating Enhanced Plotly dashboard...")
    
    try:
        # Use the enhanced dashboard script
        dashboard_script = "co2_scenarios_dashboard_enhanced.py"
        if not os.path.exists(dashboard_script):
            print(f"⚠️  Enhanced dashboard script not found: {dashboard_script}")
            # Fallback to regular dashboard
            dashboard_script = "co2_scenarios_dashboard.py"
            if not os.path.exists(dashboard_script):
                print(f"⚠️  No dashboard script found")
                return False
        
        cmd = ["python", dashboard_script]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Enhanced dashboard generated successfully!")
            print("📊 Features included:")
            print("   • 1-decimal precision formatting")
            print("   • Iron-Air always visible in storage plots")
            print("   • Extended summary table with storage power breakdown")
            print("   • Storage energy capacity line chart")
            print("   • Comprehensive model configuration info")
            return True
        else:
            print(f"❌ Dashboard generation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error generating dashboard: {e}")
        return False

def main(demand_twh=650):
    """Main execution function"""
    
    print("🚀 PyPSA CO2 Scenarios Analysis")
    print("=" * 60)
    print("Running 4 scenarios with:")
    print("  • 2920 timesteps (3-hour resolution)")
    print("  • LP optimization only")
    print("  • 5-hour solver time limit")
    print("  • 1e-6 tolerance")
    print("  • No heating sector")
    print("=" * 60)
    
    # Define scenarios
    scenarios = [
        ('A', 0.15, "15% of 1990 emissions"),
        ('B', 0.05, "5% of 1990 emissions"),
        ('C', 0.01, "1% of 1990 emissions"),
        ('D', 0.00, "0% of 1990 emissions (net-zero)")
    ]
    
    base_config = "config/de-co2-scenarios-2035.yaml"
    all_results = []
    
    # Run each scenario
    for scenario_name, co2_target, description in scenarios:
        
        print(f"\n{'='*60}")
        print(f"SCENARIO {scenario_name}: {description}")
        print(f"{'='*60}")
        
        # Update configuration
        config_path = update_config_for_scenario(base_config, co2_target, scenario_name, demand_twh=650)
        
        # Run scenario
        success = run_scenario(config_path, scenario_name, co2_target)
        
        if success:
            # Extract results
            results = extract_results(scenario_name, co2_target)
            if results:
                all_results.append(results)
        else:
            print(f"⚠️  Skipping result extraction for failed Scenario {scenario_name}")
    
    # Create comparison if we have any results
    if all_results:
        comparison_file = create_comparison_csv(all_results)
        
        # Generate dashboard
        run_dashboard_generation(comparison_file)
        
        print(f"\n🎉 Analysis complete!")
        print(f"📊 Results: {comparison_file}")
        print(f"🌐 Dashboard: Check for generated HTML files")
        
    else:
        print("\n❌ No successful scenarios to compare")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run CO2 scenarios with optional demand override")
    parser.add_argument("--demand", type=float, help="Annual electricity demand in TWh")
    args = parser.parse_args()
    main(demand_twh=args.demand)
