#!/usr/bin/env python3
"""
Scenario Comparison Analysis
Compares results from different CO2 pricing scenarios for the German electricity system
"""

import pypsa
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_and_compare_scenarios():
    """Load and compare results from different scenario network files."""
    
    logger.info("=" * 100)
    logger.info("SCENARIO COMPARISON ANALYSIS")
    logger.info("=" * 100)
    
    # Network dictionary - loading different scenario files
    networks = {
        '250Mt_CO2_Limit': 'results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_scenario1_250co2.nc',
        '300Mt_CO2_Limit': 'results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_scenario2_300co2.nc', 
        '500Mt_CO2_Limit': 'results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_scenario3_500co2.nc'
    }
    
    loaded_networks = {}
    
    # Load each scenario network
    for scenario_name, network_path in networks.items():
        logger.info(f"\nLoading {scenario_name}: {network_path}")
        
        if os.path.exists(network_path):
            try:
                loaded_networks[scenario_name] = pypsa.Network(network_path)
                logger.info(f"✅ Successfully loaded {scenario_name}")
            except Exception as e:
                logger.error(f"❌ Failed to load {scenario_name}: {str(e)}")
        else:
            logger.warning(f"⚠️  File not found: {network_path}")
    
    # Analysis and comparison of loaded scenarios
    if len(loaded_networks) >= 2:
        logger.info(f"\n=== SCENARIO COMPARISON RESULTS ===")
        
        # Compare key metrics across scenarios
        comparison_data = {}
        
        for scenario_name, network in loaded_networks.items():
            comparison_data[scenario_name] = analyze_network_metrics(network)
        
        # Display comparison table
        display_comparison_table(comparison_data)
        
        # Generate comparison plots
        create_comparison_plots(comparison_data)
        
    else:
        logger.warning("Not enough scenarios loaded for comparison")
    
    return loaded_networks

def analyze_network_metrics(network):
    """Extract key metrics from a network for comparison."""
    
    metrics = {}
    
    # System cost
    if network.objective is not None:
        metrics['system_cost_billion_eur'] = network.objective / 1e9
    else:
        metrics['system_cost_billion_eur'] = 0
    
    # Total generation by carrier
    if hasattr(network, 'generators_t') and hasattr(network.generators_t, 'p'):
        gen_by_carrier = network.generators_t.p.sum().groupby(network.generators.carrier).sum() / 1e3  # GWh
        metrics['total_generation_twh'] = gen_by_carrier.sum() / 1000  # TWh
        
        # Renewable share
        renewable_carriers = ['solar', 'solar-hsat', 'onwind', 'offwind-ac', 'offwind-dc', 'offwind-float', 'ror']
        renewable_gen = gen_by_carrier.reindex(renewable_carriers, fill_value=0).sum()
        metrics['renewable_share_pct'] = (renewable_gen / gen_by_carrier.sum() * 100) if gen_by_carrier.sum() > 0 else 0
        
        # CO2 emissions calculation
        co2_factors = {
            'coal': 0.820, 'lignite': 0.986, 'CCGT': 0.350, 'OCGT': 0.400, 'oil': 0.650
        }
        
        total_co2 = 0
        for carrier, co2_factor in co2_factors.items():
            if carrier in gen_by_carrier.index:
                total_co2 += gen_by_carrier[carrier] * co2_factor  # ktCO2
        
        metrics['co2_emissions_mt'] = total_co2 / 1000  # MtCO2
    
    # Storage capacity
    if len(network.stores) > 0:
        metrics['battery_storage_gwh'] = network.stores[network.stores.carrier == 'battery']['e_nom_opt'].sum() / 1000
    else:
        metrics['battery_storage_gwh'] = 0
    
    return metrics

def display_comparison_table(comparison_data):
    """Display a formatted comparison table of scenario metrics."""
    
    logger.info(f"\n{'Metric':<30} {'250Mt CO2':<15} {'300Mt CO2':<15} {'500Mt CO2':<15}")
    logger.info("-" * 75)
    
    metrics_order = [
        ('System Cost (B€)', 'system_cost_billion_eur', '.1f'),
        ('Total Generation (TWh)', 'total_generation_twh', '.1f'),
        ('Renewable Share (%)', 'renewable_share_pct', '.1f'),
        ('CO2 Emissions (Mt)', 'co2_emissions_mt', '.1f'),
        ('Battery Storage (GWh)', 'battery_storage_gwh', '.1f')
    ]
    
    for metric_name, metric_key, format_str in metrics_order:
        row = f"{metric_name:<30} "
        for scenario in ['250Mt_CO2_Limit', '300Mt_CO2_Limit', '500Mt_CO2_Limit']:
            if scenario in comparison_data and metric_key in comparison_data[scenario]:
                value = comparison_data[scenario][metric_key]
                formatted_value = f"{value:{format_str}}"
                row += f"{formatted_value:<15} "
            else:
                row += f"{'N/A':<15} "
        logger.info(row)

def create_comparison_plots(comparison_data):
    """Create comparison plots for the scenarios."""
    
    if len(comparison_data) < 2:
        return
    
    # Create plots directory
    plots_dir = "analysis-de-white-paper-v3/plots/scenario_comparison"
    os.makedirs(plots_dir, exist_ok=True)
    
    # Plot 1: System Cost Comparison
    scenarios = list(comparison_data.keys())
    costs = [comparison_data[s].get('system_cost_billion_eur', 0) for s in scenarios]
    
    plt.figure(figsize=(10, 6))
    plt.bar(scenarios, costs, color=['blue', 'green', 'red'])
    plt.title('System Cost Comparison Across Scenarios')
    plt.ylabel('System Cost (Billion €)')
    plt.xlabel('Scenarios')
    plt.tight_layout()
    plt.savefig(f"{plots_dir}/system_cost_comparison_250Mt_300Mt_500Mt_CO2_Limit.png")
    plt.close()
    
    # Plot 2: Renewable Share Comparison  
    renewable_shares = [comparison_data[s].get('renewable_share_pct', 0) for s in scenarios]
    
    plt.figure(figsize=(10, 6))
    plt.bar(scenarios, renewable_shares, color=['lightblue', 'lightgreen', 'lightcoral'])
    plt.title('Renewable Energy Share Comparison')
    plt.ylabel('Renewable Share (%)')
    plt.xlabel('Scenarios')
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.savefig(f"{plots_dir}/renewable_share_comparison_250Mt_300Mt_500Mt_CO2_Limit.png")
    plt.close()
    
    logger.info(f"📊 Comparison plots saved to {plots_dir}/")

if __name__ == "__main__":
    try:
        networks = load_and_compare_scenarios()
        logger.info("\n✅ Scenario comparison analysis completed successfully!")
    except Exception as e:
        logger.error(f"❌ Scenario comparison analysis failed: {str(e)}")
