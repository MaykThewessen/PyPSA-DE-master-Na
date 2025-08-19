#!/usr/bin/env python3
"""
Run PyPSA-EUR for 4 CO2 scenarios sequentially
A) 15% of 1990 emissions
B) 5% of 1990 emissions  
C) 1% of 1990 emissions
D) 0% of 1990 emissions (net-zero)

Features:
- 4380 timesteps (2-hour resolution)
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

def check_missing_files():
    """Check which data files are missing and need to be downloaded"""
    missing_files = []
    
    # Check key data files
    data_files = {
        'electricity_demand': 'data/electricity_demand_raw.csv',
        'synthetic_demand': 'data/load_synthetic_raw.csv',
        'osm_prebuilt': 'data/osm-prebuilt/0.6/buses.csv',
        'nuts_shapes': 'data/nuts/NUTS_RG_01M_2021_4326_LEVL_3.geojson',
        'eez_data': 'data/eez/World_EEZ_v12_20231025_LR/eez_v12_lowres.gpkg',
        'jrc_data': 'data/jrc-ardeco/ARDECO-SUVGDP.2021.table.csv',
        'databundle': 'data/bundle/GDP_per_capita_PPP_1990_2015_v2.nc'
    }
    
    for name, filepath in data_files.items():
        if not os.path.exists(filepath):
            missing_files.append(name)
    
    return missing_files

def update_config_for_scenario(config_path, co2_target, scenario_name, demand_twh=None):
    """Update configuration file for specific CO2 scenario"""
    
    print(f"📝 Updating config for Scenario {scenario_name}: {co2_target*100:.0f}% CO2 target")
    
    # Load base configuration
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Update CO2 targets
    config['co2_budget'][2035] = co2_target
    config['electricity']['co2limit'] = co2_target
    
    # Check which files are missing and enable only necessary downloads
    missing_files = check_missing_files()
    
    if missing_files:
        print(f"🌐 Missing data files detected: {', '.join(missing_files)}")
        print("📥 Enabling downloads for missing files only...")
        
        # Enable downloads only for missing files
        config['enable']['retrieve'] = 'auto'
        config['enable']['retrieve_databundle'] = 'databundle' in missing_files
        config['enable']['retrieve_cost_data'] = True  # Always get latest costs
    else:
        print("✅ All required data files found locally - no downloads needed")
        # Keep downloads disabled to use local files
        config['enable']['retrieve'] = False
        config['enable']['retrieve_databundle'] = False
        config['enable']['retrieve_cost_data'] = True  # Always get latest costs
    
    # Never build or retrieve cutouts - we have them locally
    config['enable']['build_cutout'] = False
    config['enable']['retrieve_cutout'] = False

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

def run_scenario(config_path, scenario_name):
    """Run PyPSA optimization for one scenario"""
    
    print(f"\n🚀 Starting Scenario {scenario_name} optimization...")
    print("=" * 60)
    
    # Create results directory
    results_dir = f"results/de-co2-scenario-{scenario_name}-2035"
    os.makedirs(results_dir, exist_ok=True)
    
    # Auto-unlock Snakemake before starting
    print("🔓 Auto-unlocking Snakemake directory...")
    
    # Try multiple unlock strategies
    unlock_strategies = [
        ["snakemake", "--unlock", "--nolock"],
        ["snakemake", "--unlock"],
        ["snakemake", "--unlock", "--rerun-incomplete"]
    ]
    
    for i, unlock_cmd in enumerate(unlock_strategies, 1):
        try:
            print(f"🔄 Trying unlock strategy {i}/{len(unlock_strategies)}: {' '.join(unlock_cmd)}")
            unlock_result = subprocess.run(
                unlock_cmd,
                capture_output=True,
                text=True,
                timeout=45,  # 45 second timeout for unlock
                cwd=os.getcwd()
            )
            
            if unlock_result.returncode == 0:
                print("✅ Snakemake directory unlocked successfully")
                break
            else:
                print(f"⚠️  Strategy {i} warning: {unlock_result.stderr[:200]}...")
                
        except subprocess.TimeoutExpired:
            print(f"⚠️  Strategy {i} timed out")
        except Exception as e:
            print(f"⚠️  Strategy {i} error: {e}")
    
    # Force cleanup of potential lock files
    try:
        if os.path.exists(".snakemake"):
            print("🧹 Cleaning up .snakemake directory...")
            shutil.rmtree(".snakemake", ignore_errors=True)
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    
    try:
        # Run snakemake command with no-lock option
        cmd = [
            "snakemake", 
            "-j16",  # Use 16 cores
            f"--configfile={config_path}",
            "solve_elec_networks",
            "--forceall",
            "--nolock",  # Disable locking to prevent lock issues
            "--rerun-incomplete"  # Rerun any incomplete jobs
        ]
        
        print(f"🔄 Running command: {' '.join(cmd)}")
        print("📊 Progress will be shown below (press Ctrl+C to cancel scenario)...\n")
        
        # Run with real-time output display
        result = subprocess.run(
            cmd, 
            timeout=7200,  # 2 hour timeout per scenario
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            print(f"✅ Scenario {scenario_name} completed successfully!")
            return True
        else:
            print(f"❌ Scenario {scenario_name} failed!")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
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
        for tech in ['solar', 'onwind', 'offwind-ac', 'offwind-dcß', 'CCGT', 'OCGT', 'nuclear', 'biomass']:
            if tech in n.generators.carrier.values:
                capacity = n.generators[n.generators.carrier == tech].p_nom_opt.sum()
                results[f'{tech}_capacity_GW'] = capacity
            else:
                results[f'{tech}_capacity_GW'] = 0.0
        
        # Storage capacities
        for tech in ['battery', 'H2', 'PHS', 'IronAir']:
            if tech in n.storage_units.carrier.values:
                power = n.storage_units[n.storage_units.carrier == tech].p_nom_opt.sum()
                energy = n.storage_units[n.storage_units.carrier == tech].state_of_charge_initial.sum()
                results[f'{tech}_power_GW'] = power
                results[f'{tech}_energy_GWh'] = energy
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
            results.get('H2_power_GW', 0) + 
            results.get('PHS_power_GW', 0) +
            results.get('IronAir_power_GW', 0)
        )
        
        results['total_storage_energy_GWh'] = (
            results.get('battery_energy_GWh', 0) + 
            results.get('H2_energy_GWh', 0) + 
            results.get('PHS_energy_GWh', 0) +
            results.get('IronAir_energy_GWh', 0)
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
    
    # Save to CSV
    comparison_file = "co2_scenarios_comparison.csv"
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

def main(demand_twh=None):
    """Main execution function"""
    
    print("🚀 PyPSA CO2 Scenarios Analysis")
    print("=" * 60)
    print("Running 4 scenarios with:")
    print("  • 4380 timesteps (2-hour resolution)")
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
        config_path = update_config_for_scenario(base_config, co2_target, scenario_name, demand_twh=demand_twh)
        
        # Run scenario
        success = run_scenario(config_path, scenario_name)
        
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
