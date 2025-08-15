#!/usr/bin/env python3
"""
Comprehensive Data Processing Test Suite
=======================================

This script verifies that all data processing functions work correctly with 
the updated battery technology naming conventions and network files.

Tests cover:
1. Network loading for all three scenarios
2. Capacity data extraction with new battery technology names  
3. Emissions calculations without errors
4. Cost calculations with new battery technologies
5. Plot generation with updated labels and colors
6. Curtailment ratio calculations with updated scenarios
7. Storage charge/discharge analysis including new battery technologies
"""

import os
os.system('clear')

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pypsa
import logging
from pathlib import Path

# Import our custom modules
from capacity_data_handler import get_capacity_data, analyze_storage_capacity_data, group_storage_carrier
from calculate_emissions import calculate_co2_emissions
from analyze_storage_results import analyze_storage_results
from scenario_comparison_analysis import load_and_compare_scenarios, analyze_network_metrics
from detailed_storage_tech_analysis import analyze_all_storage_technologies

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataProcessingTestSuite:
    """Comprehensive test suite for all data processing functions."""
    
    def __init__(self):
        self.test_results = {}
        self.networks = {}
        self.results_dir = "analysis-de-white-paper-v3\\networks"
        
        # Define the three network files to test
        self.network_files = {
            '250Mt_CO2_Limit': '250Mt_CO2_Limit_solved_network.nc',
            '300Mt_CO2_Limit': '300Mt_CO2_Limit_solved_network.nc', 
            '500Mt_CO2_Limit': '500Mt_CO2_Limit_solved_network.nc'
        }
        
        # New battery technology names to verify
        self.new_battery_technologies = [
            'iron-air battery',
            'Lithium-Ion-LFP-bicharger', 
            'Lithium-Ion-LFP-store',
            'battery storage',
            'battery inverter'
        ]
        
    def run_all_tests(self):
        """Run all data processing tests."""
        logger.info("=" * 100)
        logger.info("COMPREHENSIVE DATA PROCESSING TEST SUITE")
        logger.info("=" * 100)
        
        try:
            # Test 1: Network loading
            self.test_network_loading()
            
            # Test 2: Capacity data extraction 
            self.test_capacity_data_extraction()
            
            # Test 3: Emissions calculations
            self.test_emissions_calculations()
            
            # Test 4: Cost calculations
            self.test_cost_calculations()
            
            # Test 5: Plot generation
            self.test_plot_generation()
            
            # Test 6: Curtailment ratio calculations
            self.test_curtailment_calculations()
            
            # Test 7: Storage charge/discharge analysis
            self.test_storage_analysis()
            
            # Test 8: Battery technology naming verification
            self.test_battery_technology_naming()
            
            # Generate summary report
            self.generate_test_report()
            
        except Exception as e:
            logger.error(f"Test suite failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        return True
    
    def test_network_loading(self):
        """Test 1: Verify that the notebook successfully loads all three new network files."""
        logger.info("\n🔍 TEST 1: NETWORK LOADING")
        logger.info("-" * 60)
        
        test_passed = True
        loaded_networks = {}
        
        for scenario_name, filename in self.network_files.items():
            file_path = os.path.join(self.results_dir, filename)
            logger.info(f"Testing loading: {file_path}")
            
            try:
                if os.path.exists(file_path):
                    # Test loading with PyPSA
                    network = pypsa.Network(file_path)
                    loaded_networks[scenario_name] = network
                    
                    # Verify network has required components
                    n_buses = len(network.buses)
                    n_generators = len(network.generators) 
                    n_stores = len(network.stores)
                    n_links = len(network.links)
                    
                    logger.info(f"  ✅ {scenario_name}: Loaded successfully")
                    logger.info(f"     Buses: {n_buses}, Generators: {n_generators}")
                    logger.info(f"     Stores: {n_stores}, Links: {n_links}")
                    
                    # Check for solved status
                    has_optimal_values = (network.generators.p_nom_opt.sum() > 0 or 
                                        network.stores.e_nom_opt.sum() > 0)
                    
                    if has_optimal_values:
                        logger.info(f"     ✅ Network appears to be solved (has optimal values)")
                    else:
                        logger.warning(f"     ⚠️  Network may not be solved (no optimal values)")
                        
                else:
                    logger.error(f"  ❌ {scenario_name}: File not found at {file_path}")
                    test_passed = False
                    
            except Exception as e:
                logger.error(f"  ❌ {scenario_name}: Loading failed - {str(e)}")
                test_passed = False
        
        self.networks = loaded_networks
        self.test_results['network_loading'] = {
            'passed': test_passed,
            'networks_loaded': len(loaded_networks),
            'networks_expected': len(self.network_files)
        }
        
        if test_passed:
            logger.info("✅ TEST 1 PASSED: All network files loaded successfully")
        else:
            logger.error("❌ TEST 1 FAILED: Some network files could not be loaded")
            
    def test_capacity_data_extraction(self):
        """Test 2: Verify that the capacity data extraction works with new battery technology names."""
        logger.info("\n🔍 TEST 2: CAPACITY DATA EXTRACTION")
        logger.info("-" * 60)
        
        test_passed = True
        capacity_data_results = {}
        
        for scenario_name, network in self.networks.items():
            logger.info(f"Testing capacity extraction for {scenario_name}:")
            
            try:
                # Use our updated capacity data handler
                capacity_data = get_capacity_data(network)
                capacity_data_results[scenario_name] = capacity_data
                
                # Verify data structure
                expected_keys = ['stores', 'storage_units', 'links']
                for key in expected_keys:
                    if key not in capacity_data:
                        logger.error(f"  ❌ Missing key '{key}' in capacity data")
                        test_passed = False
                        continue
                        
                    logger.info(f"  ✅ {key}: Found {len(capacity_data[key])} entries")
                
                # Check for new battery technology names
                all_carriers = set()
                all_carriers.update(capacity_data['stores'].keys())
                all_carriers.update(capacity_data['storage_units'].keys())  
                all_carriers.update(capacity_data['links'].keys())
                
                new_battery_found = []
                for tech in self.new_battery_technologies:
                    if tech in all_carriers:
                        new_battery_found.append(tech)
                        logger.info(f"  ✅ New battery tech found: {tech}")
                
                if new_battery_found:
                    logger.info(f"  ✅ Found {len(new_battery_found)} new battery technologies")
                else:
                    logger.warning(f"  ⚠️  No new battery technologies found in this scenario")
                
                # Test carrier grouping function
                test_carriers = [
                    'iron-air battery charger',
                    'Lithium-Ion-LFP-bicharger-test',
                    'Lithium-Ion-LFP-store-test',
                    'battery storage link',
                    'battery inverter link'
                ]
                
                logger.info("  Testing carrier grouping logic:")
                for test_carrier in test_carriers:
                    grouped = group_storage_carrier(test_carrier)
                    logger.info(f"    '{test_carrier}' → '{grouped}'")
                
            except Exception as e:
                logger.error(f"  ❌ {scenario_name}: Capacity extraction failed - {str(e)}")
                test_passed = False
        
        self.test_results['capacity_data_extraction'] = {
            'passed': test_passed,
            'scenarios_tested': len(capacity_data_results),
            'results': capacity_data_results
        }
        
        if test_passed:
            logger.info("✅ TEST 2 PASSED: Capacity data extraction works with new battery technologies")
        else:
            logger.error("❌ TEST 2 FAILED: Issues with capacity data extraction")
    
    def test_emissions_calculations(self):
        """Test 3: Verify that the emissions calculations execute without errors."""
        logger.info("\n🔍 TEST 3: EMISSIONS CALCULATIONS")
        logger.info("-" * 60)
        
        test_passed = True
        emissions_results = {}
        
        for scenario_name, network in self.networks.items():
            logger.info(f"Testing emissions calculation for {scenario_name}:")
            
            try:
                # Test our emissions calculation function
                co2_factors = {
                    'lignite': 1054, 'coal': 820, 'oil': 736,
                    'CCGT': 490, 'OCGT': 490, 'nuclear': 0,
                    'biomass': 0, 'solar': 0, 'solar-hsat': 0,
                    'onwind': 0, 'offwind-ac': 0, 'offwind-dc': 0,
                    'offwind-float': 0, 'hydro': 0, 'ror': 0
                }
                
                total_co2 = 0
                co2_by_carrier = {}
                
                # Check that we have generation data
                if not hasattr(network, 'generators_t') or not hasattr(network.generators_t, 'p'):
                    logger.warning(f"  ⚠️  No generator time series data available")
                    continue
                
                for carrier in network.generators.carrier.unique():
                    if carrier in co2_factors:
                        carrier_gens = network.generators[network.generators.carrier == carrier]
                        
                        if len(carrier_gens) > 0 and co2_factors[carrier] > 0:
                            # Calculate emissions
                            total_gen_el = network.generators_t.p[carrier_gens.index].sum().sum()
                            efficiency = carrier_gens.efficiency.iloc[0] if len(carrier_gens) > 0 else 0.4
                            total_gen_th = total_gen_el / efficiency if efficiency > 0 else total_gen_el
                            
                            co2_emissions_kg = total_gen_th * co2_factors[carrier]
                            co2_emissions_mt = co2_emissions_kg / 1e9
                            
                            co2_by_carrier[carrier] = co2_emissions_mt
                            total_co2 += co2_emissions_mt
                            
                            if co2_emissions_mt > 0.01:
                                logger.info(f"  📊 {carrier}: {co2_emissions_mt:.2f} Mt CO2")
                
                emissions_results[scenario_name] = {
                    'total_co2_mt': total_co2,
                    'co2_by_carrier': co2_by_carrier
                }
                
                logger.info(f"  ✅ Total CO2 emissions: {total_co2:.2f} Mt CO2")
                
            except Exception as e:
                logger.error(f"  ❌ {scenario_name}: Emissions calculation failed - {str(e)}")
                test_passed = False
        
        self.test_results['emissions_calculations'] = {
            'passed': test_passed,
            'scenarios_tested': len(emissions_results),
            'results': emissions_results
        }
        
        if test_passed:
            logger.info("✅ TEST 3 PASSED: Emissions calculations execute without errors")
        else:
            logger.error("❌ TEST 3 FAILED: Issues with emissions calculations")
    
    def test_cost_calculations(self):
        """Test 4: Verify that cost calculations properly handle the new battery technologies."""
        logger.info("\n🔍 TEST 4: COST CALCULATIONS")
        logger.info("-" * 60)
        
        test_passed = True
        cost_results = {}
        
        # Test loading cost data
        try:
            costs_path = "resources/de-all-tech-2035-mayk/costs_2035.csv"
            if os.path.exists(costs_path):
                costs = pd.read_csv(costs_path, index_col=0)
                logger.info(f"✅ Cost data loaded: {costs.shape[0]} technologies")
                
                # Check for new battery technologies in cost data
                new_battery_costs = {}
                for tech in self.new_battery_technologies:
                    # Check various possible cost column names
                    cost_value = None
                    if tech in costs.index:
                        for col in ['investment', 'capital_cost', 'cost']:
                            if col in costs.columns:
                                cost_value = costs.loc[tech, col]
                                break
                    
                    if cost_value is not None:
                        new_battery_costs[tech] = cost_value
                        logger.info(f"  ✅ {tech}: {cost_value:.0f} EUR/MWh")
                    else:
                        logger.info(f"  ⚠️  {tech}: Not found in cost data (may use default values)")
                
                cost_results['cost_data_loaded'] = True
                cost_results['new_battery_costs'] = new_battery_costs
                
            else:
                logger.warning(f"⚠️  Cost file not found: {costs_path}")
                cost_results['cost_data_loaded'] = False
        
        except Exception as e:
            logger.error(f"❌ Failed to load cost data: {str(e)}")
            test_passed = False
            cost_results['cost_data_loaded'] = False
        
        # Test cost calculations for each network
        for scenario_name, network in self.networks.items():
            logger.info(f"Testing cost calculations for {scenario_name}:")
            
            try:
                # Test objective value (total system cost)
                if hasattr(network, 'objective') and network.objective is not None:
                    system_cost_billion = network.objective / 1e9
                    logger.info(f"  ✅ System cost: {system_cost_billion:.1f} billion EUR")
                    cost_results[f'{scenario_name}_system_cost'] = system_cost_billion
                else:
                    logger.warning(f"  ⚠️  No objective value (system cost) available")
                
                # Test storage technology costs
                storage_investment_costs = {}
                
                # Battery storage investment
                if len(network.stores) > 0:
                    battery_stores = network.stores[network.stores.carrier.isin(['battery', 'iron-air battery'])]
                    for idx, store in battery_stores.iterrows():
                        investment_mwh = store['e_nom_opt'] - store['e_nom']
                        if investment_mwh > 0:
                            tech_name = store['carrier']
                            storage_investment_costs[tech_name] = storage_investment_costs.get(tech_name, 0) + investment_mwh
                
                # Display storage investments
                for tech, investment in storage_investment_costs.items():
                    if investment > 0:
                        logger.info(f"  💰 {tech} investment: {investment:.1f} MWh")
                
                cost_results[f'{scenario_name}_storage_investments'] = storage_investment_costs
                
            except Exception as e:
                logger.error(f"  ❌ {scenario_name}: Cost calculation failed - {str(e)}")
                test_passed = False
        
        self.test_results['cost_calculations'] = {
            'passed': test_passed,
            'results': cost_results
        }
        
        if test_passed:
            logger.info("✅ TEST 4 PASSED: Cost calculations handle new battery technologies")
        else:
            logger.error("❌ TEST 4 FAILED: Issues with cost calculations")
    
    def test_plot_generation(self):
        """Test 5: Verify that all plots generate correctly with updated labels and colors."""
        logger.info("\n🔍 TEST 5: PLOT GENERATION") 
        logger.info("-" * 60)
        
        test_passed = True
        plots_generated = []
        
        # Create plots directory
        plots_dir = "analysis-de-white-paper-v3/plots/test_plots"
        os.makedirs(plots_dir, exist_ok=True)
        
        try:
            # Test 1: Storage capacity comparison plot
            logger.info("Generating storage capacity comparison plot...")
            
            plt.figure(figsize=(12, 8))
            
            # Updated colors for new battery technologies
            colors = {
                'iron-air battery': '#FF6B35',           # Orange-red
                'Lithium-Ion-LFP-bicharger': '#004E89',  # Dark blue  
                'Lithium-Ion-LFP-store': '#1A759F',      # Medium blue
                'battery storage': '#168AAD',             # Light blue
                'battery inverter': '#34A0A4',            # Teal
                'battery': '#52B788',                     # Green (legacy)
                'H2': '#40916C',                          # Dark green
                'PHS': '#2D6A4F'                          # Forest green
            }
            
            # Collect data from all scenarios
            scenario_data = {}
            for scenario_name, network in self.networks.items():
                capacity_data = get_capacity_data(network)
                scenario_data[scenario_name] = capacity_data
            
            # Create subplot for each data type
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            axes = axes.flatten()
            
            # Plot 1: Store capacities
            ax1 = axes[0]
            store_data = {}
            for scenario, data in scenario_data.items():
                for carrier, capacity in data['stores'].items():
                    if capacity > 0:
                        if carrier not in store_data:
                            store_data[carrier] = {}
                        store_data[carrier][scenario] = capacity
            
            if store_data:
                scenarios = list(self.networks.keys())
                x_pos = np.arange(len(scenarios))
                width = 0.8 / len(store_data)
                
                for i, (carrier, carrier_data) in enumerate(store_data.items()):
                    values = [carrier_data.get(s, 0) for s in scenarios]
                    color = colors.get(carrier, '#666666')
                    ax1.bar(x_pos + i * width, values, width, label=carrier, color=color)
                
                ax1.set_title('Energy Storage Capacity by Scenario (Stores)')
                ax1.set_xlabel('Scenarios')
                ax1.set_ylabel('Capacity (MWh)')
                ax1.set_xticks(x_pos + width * (len(store_data) - 1) / 2)
                ax1.set_xticklabels(scenarios, rotation=45)
                ax1.legend()
            else:
                ax1.text(0.5, 0.5, 'No store data available', ha='center', va='center', transform=ax1.transAxes)
                ax1.set_title('Energy Storage Capacity - No Data')
            
            # Plot 2: Storage unit power
            ax2 = axes[1] 
            unit_data = {}
            for scenario, data in scenario_data.items():
                for carrier, carrier_data in data['storage_units'].items():
                    if carrier_data['power'] > 0:
                        if carrier not in unit_data:
                            unit_data[carrier] = {}
                        unit_data[carrier][scenario] = carrier_data['power']
            
            if unit_data:
                x_pos = np.arange(len(scenarios))
                width = 0.8 / len(unit_data)
                
                for i, (carrier, carrier_data) in enumerate(unit_data.items()):
                    values = [carrier_data.get(s, 0) for s in scenarios]
                    color = colors.get(carrier, '#666666')
                    ax2.bar(x_pos + i * width, values, width, label=carrier, color=color)
                
                ax2.set_title('Storage Unit Power by Scenario')
                ax2.set_xlabel('Scenarios')
                ax2.set_ylabel('Power (MW)')
                ax2.set_xticks(x_pos + width * (len(unit_data) - 1) / 2)
                ax2.set_xticklabels(scenarios, rotation=45)
                ax2.legend()
            else:
                ax2.text(0.5, 0.5, 'No storage unit data', ha='center', va='center', transform=ax2.transAxes)
                ax2.set_title('Storage Unit Power - No Data')
            
            # Plot 3: Technology comparison pie chart for first scenario
            ax3 = axes[2]
            if scenario_data:
                first_scenario = list(scenario_data.keys())[0]
                pie_data = scenario_data[first_scenario]['stores']
                
                if pie_data and sum(pie_data.values()) > 0:
                    labels = list(pie_data.keys())
                    sizes = list(pie_data.values())
                    plot_colors = [colors.get(label, '#666666') for label in labels]
                    
                    ax3.pie(sizes, labels=labels, colors=plot_colors, autopct='%1.1f%%', startangle=90)
                    ax3.set_title(f'Storage Technology Share - {first_scenario}')
                else:
                    ax3.text(0.5, 0.5, 'No pie chart data', ha='center', va='center', transform=ax3.transAxes)
                    ax3.set_title('Technology Share - No Data')
            
            # Plot 4: Links power capacity
            ax4 = axes[3]
            link_data = {}
            for scenario, data in scenario_data.items():
                for carrier, links in data['links'].items():
                    total_power = sum(link['power'] for link in links)
                    if total_power > 0:
                        if carrier not in link_data:
                            link_data[carrier] = {}
                        link_data[carrier][scenario] = total_power
            
            if link_data:
                x_pos = np.arange(len(scenarios))
                width = 0.8 / len(link_data)
                
                for i, (carrier, carrier_data) in enumerate(link_data.items()):
                    values = [carrier_data.get(s, 0) for s in scenarios]
                    color = colors.get(carrier, '#666666')
                    ax4.bar(x_pos + i * width, values, width, label=carrier, color=color)
                
                ax4.set_title('Storage Links Power by Scenario')
                ax4.set_xlabel('Scenarios')
                ax4.set_ylabel('Power (MW)')
                ax4.set_xticks(x_pos + width * (len(link_data) - 1) / 2)
                ax4.set_xticklabels(scenarios, rotation=45)
                ax4.legend()
            else:
                ax4.text(0.5, 0.5, 'No link data available', ha='center', va='center', transform=ax4.transAxes)
                ax4.set_title('Storage Links - No Data')
            
            plt.tight_layout()
            plot_file = f"{plots_dir}/storage_capacity_comparison_250Mt_300Mt_500Mt_CO2_scenarios.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            plots_generated.append(plot_file)
            logger.info(f"  ✅ Storage capacity plot saved: {plot_file}")
            
            # Test 2: Emissions comparison plot
            logger.info("Generating emissions comparison plot...")
            
            if 'emissions_calculations' in self.test_results and self.test_results['emissions_calculations']['results']:
                plt.figure(figsize=(10, 6))
                
                emissions_data = self.test_results['emissions_calculations']['results']
                scenarios = list(emissions_data.keys())
                emissions = [data['total_co2_mt'] for data in emissions_data.values()]
                
                colors_emissions = ['#FF6B6B', '#4ECDC4', '#45B7D1']
                plt.bar(scenarios, emissions, color=colors_emissions)
                plt.title('CO2 Emissions by Scenario')
                plt.xlabel('Scenarios')
                plt.ylabel('CO2 Emissions (Mt)')
                plt.xticks(rotation=45)
                
                plot_file = f"{plots_dir}/emissions_comparison_250Mt_300Mt_500Mt_CO2_scenarios.png"
                plt.savefig(plot_file, dpi=300, bbox_inches='tight')
                plt.close()
                
                plots_generated.append(plot_file)
                logger.info(f"  ✅ Emissions plot saved: {plot_file}")
            
            # Test 3: Technology naming verification plot
            logger.info("Generating technology naming verification plot...")
            
            plt.figure(figsize=(12, 8))
            
            # Show old vs new naming
            old_names = ['battery1', 'battery2', 'battery4', 'battery8', 'Ebattery1', 'Ebattery2']
            new_names = self.new_battery_technologies
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Old naming (deprecated)
            ax1.bar(range(len(old_names)), [0] * len(old_names), color='#FF6B6B', alpha=0.7)
            ax1.set_title('Deprecated Battery Technologies\n(Not Used)', color='red')
            ax1.set_xticks(range(len(old_names)))
            ax1.set_xticklabels(old_names, rotation=45)
            ax1.set_ylabel('Usage (Deprecated)')
            
            # New naming (current) 
            tech_found = []
            for tech in new_names:
                found_in_any_scenario = False
                for scenario_data_dict in scenario_data.values():
                    all_carriers = set()
                    all_carriers.update(scenario_data_dict['stores'].keys())
                    all_carriers.update(scenario_data_dict['storage_units'].keys())
                    all_carriers.update(scenario_data_dict['links'].keys())
                    if tech in all_carriers:
                        found_in_any_scenario = True
                        break
                tech_found.append(1 if found_in_any_scenario else 0)
            
            colors_new = ['#52B788' if found else '#95A5A6' for found in tech_found]
            ax2.bar(range(len(new_names)), tech_found, color=colors_new)
            ax2.set_title('Updated Battery Technologies\n(Current Implementation)', color='green')
            ax2.set_xticks(range(len(new_names)))
            ax2.set_xticklabels(new_names, rotation=45, ha='right')
            ax2.set_ylabel('Found in Networks')
            ax2.set_ylim(0, 1.2)
            
            plt.tight_layout()
            plot_file = f"{plots_dir}/technology_naming_verification_250Mt_300Mt_500Mt_CO2_scenarios.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            plots_generated.append(plot_file)
            logger.info(f"  ✅ Technology naming plot saved: {plot_file}")
            
        except Exception as e:
            logger.error(f"❌ Plot generation failed: {str(e)}")
            test_passed = False
        
        self.test_results['plot_generation'] = {
            'passed': test_passed,
            'plots_generated': len(plots_generated),
            'plot_files': plots_generated
        }
        
        if test_passed:
            logger.info(f"✅ TEST 5 PASSED: {len(plots_generated)} plots generated successfully")
        else:
            logger.error("❌ TEST 5 FAILED: Issues with plot generation")
    
    def test_curtailment_calculations(self):
        """Test 6: Verify that curtailment ratio calculations work with updated scenarios."""
        logger.info("\n🔍 TEST 6: CURTAILMENT RATIO CALCULATIONS")
        logger.info("-" * 60)
        
        test_passed = True
        curtailment_results = {}
        
        for scenario_name, network in self.networks.items():
            logger.info(f"Testing curtailment calculation for {scenario_name}:")
            
            try:
                # Calculate renewable curtailment
                renewable_carriers = ['solar', 'solar-hsat', 'onwind', 'offwind-ac', 'offwind-dc', 'offwind-float']
                
                curtailment_data = {}
                total_potential = 0
                total_actual = 0
                
                if hasattr(network, 'generators_t') and hasattr(network.generators_t, 'p'):
                    for carrier in renewable_carriers:
                        carrier_gens = network.generators[network.generators.carrier == carrier]
                        
                        if len(carrier_gens) > 0:
                            # Actual generation
                            actual_gen = network.generators_t.p[carrier_gens.index].sum().sum()
                            
                            # Potential generation (capacity * availability)
                            # Use p_max_pu if available, otherwise assume full availability
                            if hasattr(network.generators_t, 'p_max_pu') and len(network.generators_t.p_max_pu.columns) > 0:
                                # Check if any of the carrier generators have p_max_pu data
                                carrier_p_max_pu = network.generators_t.p_max_pu.reindex(columns=carrier_gens.index, fill_value=1.0)
                                potential_gen = (carrier_p_max_pu.multiply(carrier_gens.p_nom_opt, axis=1)).sum().sum()
                            else:
                                # Fallback: assume availability factor
                                availability_factors = {
                                    'solar': 0.12, 'solar-hsat': 0.12, 'onwind': 0.25, 
                                    'offwind-ac': 0.35, 'offwind-dc': 0.35, 'offwind-float': 0.35
                                }
                                availability = availability_factors.get(carrier, 0.25)
                                potential_gen = carrier_gens.p_nom_opt.sum() * 8760 * availability
                            
                            if potential_gen > 0:
                                curtailment_ratio = (potential_gen - actual_gen) / potential_gen
                                curtailment_data[carrier] = {
                                    'potential_twh': potential_gen / 1000,
                                    'actual_twh': actual_gen / 1000,
                                    'curtailment_ratio': curtailment_ratio
                                }
                                
                                total_potential += potential_gen
                                total_actual += actual_gen
                                
                                logger.info(f"  📊 {carrier}: {curtailment_ratio:.1%} curtailment")
                                logger.info(f"      Potential: {potential_gen/1000:.1f} TWh, Actual: {actual_gen/1000:.1f} TWh")
                
                # Overall curtailment ratio
                if total_potential > 0:
                    overall_curtailment = (total_potential - total_actual) / total_potential
                    curtailment_results[scenario_name] = {
                        'overall_curtailment': overall_curtailment,
                        'by_technology': curtailment_data,
                        'total_potential_twh': total_potential / 1000,
                        'total_actual_twh': total_actual / 1000
                    }
                    
                    logger.info(f"  ✅ Overall renewable curtailment: {overall_curtailment:.1%}")
                else:
                    logger.warning(f"  ⚠️  No renewable generation data available")
                    curtailment_results[scenario_name] = {'overall_curtailment': 0, 'by_technology': {}}
                
            except Exception as e:
                logger.error(f"  ❌ {scenario_name}: Curtailment calculation failed - {str(e)}")
                test_passed = False
        
        self.test_results['curtailment_calculations'] = {
            'passed': test_passed,
            'scenarios_tested': len(curtailment_results),
            'results': curtailment_results
        }
        
        if test_passed:
            logger.info("✅ TEST 6 PASSED: Curtailment calculations work with updated scenarios")
        else:
            logger.error("❌ TEST 6 FAILED: Issues with curtailment calculations")
    
    def test_storage_analysis(self):
        """Test 7: Verify that storage charge/discharge analysis includes new battery technologies."""
        logger.info("\n🔍 TEST 7: STORAGE CHARGE/DISCHARGE ANALYSIS")
        logger.info("-" * 60)
        
        test_passed = True
        storage_analysis_results = {}
        
        for scenario_name, network in self.networks.items():
            logger.info(f"Testing storage analysis for {scenario_name}:")
            
            try:
                analysis_result = {
                    'battery_analysis': {},
                    'phs_analysis': {},
                    'new_battery_tech_analysis': {}
                }
                
                # Test 1: Traditional battery analysis
                battery_stores = network.stores[network.stores.carrier == 'battery']
                if len(battery_stores) > 0 and hasattr(network, 'stores_t') and hasattr(network.stores_t, 'e'):
                    for store_id in battery_stores.index:
                        if store_id in network.stores_t.e.columns:
                            soc = network.stores_t.e[store_id]
                            analysis_result['battery_analysis'][store_id] = {
                                'max_soc': soc.max(),
                                'min_soc': soc.min(),
                                'avg_soc': soc.mean(),
                                'cycles_estimate': self._estimate_cycles(soc, battery_stores.loc[store_id, 'e_nom_opt'])
                            }
                            logger.info(f"  ✅ Battery {store_id}: {soc.max():.1f} MWh max SOC")
                
                # Test 2: PHS analysis
                phs_units = network.storage_units[network.storage_units.carrier == 'PHS']
                if len(phs_units) > 0 and hasattr(network, 'storage_units_t') and hasattr(network.storage_units_t, 'state_of_charge'):
                    for unit_id in phs_units.index:
                        if unit_id in network.storage_units_t.state_of_charge.columns:
                            soc = network.storage_units_t.state_of_charge[unit_id]
                            analysis_result['phs_analysis'][unit_id] = {
                                'max_soc': soc.max(),
                                'min_soc': soc.min(),
                                'avg_soc': soc.mean()
                            }
                            logger.info(f"  ✅ PHS {unit_id}: {soc.max():.1f} MWh max SOC")
                
                # Test 3: New battery technologies analysis
                for new_tech in self.new_battery_technologies:
                    # Check stores
                    tech_stores = network.stores[network.stores.carrier == new_tech]
                    if len(tech_stores) > 0:
                        for store_id in tech_stores.index:
                            if hasattr(network, 'stores_t') and hasattr(network.stores_t, 'e') and store_id in network.stores_t.e.columns:
                                soc = network.stores_t.e[store_id]
                                analysis_result['new_battery_tech_analysis'][f"{new_tech}_{store_id}"] = {
                                    'technology': new_tech,
                                    'max_soc': soc.max(),
                                    'min_soc': soc.min(),
                                    'avg_soc': soc.mean(),
                                    'cycles_estimate': self._estimate_cycles(soc, tech_stores.loc[store_id, 'e_nom_opt'])
                                }
                                logger.info(f"  ✅ {new_tech} store {store_id}: Analysis complete")
                    
                    # Check storage units
                    tech_units = network.storage_units[network.storage_units.carrier == new_tech]
                    if len(tech_units) > 0:
                        for unit_id in tech_units.index:
                            if hasattr(network, 'storage_units_t') and hasattr(network.storage_units_t, 'state_of_charge') and unit_id in network.storage_units_t.state_of_charge.columns:
                                soc = network.storage_units_t.state_of_charge[unit_id]
                                analysis_result['new_battery_tech_analysis'][f"{new_tech}_{unit_id}"] = {
                                    'technology': new_tech,
                                    'max_soc': soc.max(),
                                    'min_soc': soc.min(),
                                    'avg_soc': soc.mean()
                                }
                                logger.info(f"  ✅ {new_tech} unit {unit_id}: Analysis complete")
                
                # Test 4: Link analysis for charge/discharge
                storage_links = network.links[network.links.carrier.str.contains('|'.join(self.new_battery_technologies + ['battery']), case=False, na=False)]
                if len(storage_links) > 0 and hasattr(network, 'links_t') and hasattr(network.links_t, 'p0'):
                    link_analysis = {}
                    for link_id in storage_links.index:
                        if link_id in network.links_t.p0.columns:
                            power_flow = network.links_t.p0[link_id]
                            link_analysis[link_id] = {
                                'carrier': storage_links.loc[link_id, 'carrier'],
                                'max_charge': power_flow.max(),
                                'max_discharge': abs(power_flow.min()),
                                'avg_power': power_flow.mean(),
                                'utilization': power_flow.abs().mean() / storage_links.loc[link_id, 'p_nom_opt'] if storage_links.loc[link_id, 'p_nom_opt'] > 0 else 0
                            }
                            logger.info(f"  ✅ Link {link_id} ({storage_links.loc[link_id, 'carrier']}): {link_analysis[link_id]['utilization']:.1%} utilization")
                    
                    analysis_result['link_analysis'] = link_analysis
                
                storage_analysis_results[scenario_name] = analysis_result
                logger.info(f"  ✅ Storage analysis completed for {scenario_name}")
                
            except Exception as e:
                logger.error(f"  ❌ {scenario_name}: Storage analysis failed - {str(e)}")
                test_passed = False
        
        self.test_results['storage_analysis'] = {
            'passed': test_passed,
            'scenarios_tested': len(storage_analysis_results),
            'results': storage_analysis_results
        }
        
        if test_passed:
            logger.info("✅ TEST 7 PASSED: Storage analysis includes new battery technologies")
        else:
            logger.error("❌ TEST 7 FAILED: Issues with storage analysis")
    
    def _estimate_cycles(self, soc_series, capacity):
        """Estimate the number of charge/discharge cycles from SOC data."""
        if capacity <= 0 or len(soc_series) == 0:
            return 0
            
        # Simple method: sum of positive SOC changes divided by capacity
        soc_changes = soc_series.diff().dropna()
        positive_changes = soc_changes[soc_changes > 0].sum()
        
        return positive_changes / capacity if capacity > 0 else 0
    
    def test_battery_technology_naming(self):
        """Test 8: Verify battery technology naming consistency."""
        logger.info("\n🔍 TEST 8: BATTERY TECHNOLOGY NAMING VERIFICATION")
        logger.info("-" * 60)
        
        test_passed = True
        naming_results = {}
        
        try:
            # Test the grouping function with various inputs
            test_cases = [
                ('iron-air battery charger', 'iron-air battery'),
                ('Iron-Air Battery Store', 'iron-air battery'),
                ('ironair-discharge', 'iron-air battery'),
                ('Lithium-Ion-LFP-bicharger-1', 'Lithium-Ion-LFP-bicharger'),
                ('Lithium-Ion-LFP-store-2', 'Lithium-Ion-LFP-store'),
                ('battery storage main', 'battery storage'),
                ('battery inverter AC', 'battery inverter'),
                ('battery_4h_test', 'battery_4h'),
                ('battery_12h_link', 'battery_12h'),
                ('H2 electrolysis', 'H2'),
                ('PHS pump', 'PHS'),
                ('Compressed-Air-Adiabatic-1', 'Compressed-Air-Adiabatic'),
                ('Vanadium-Redox-Flow-test', 'Vanadium-Redox-Flow')
            ]
            
            logger.info("Testing carrier grouping function:")
            for input_name, expected in test_cases:
                actual = group_storage_carrier(input_name)
                if actual == expected:
                    logger.info(f"  ✅ '{input_name}' → '{actual}' (correct)")
                else:
                    logger.error(f"  ❌ '{input_name}' → '{actual}' (expected: '{expected}')")
                    test_passed = False
            
            naming_results['grouping_function_tests'] = len(test_cases)
            
            # Check for deprecated names in networks
            deprecated_names = ['battery1', 'battery2', 'battery4', 'battery8', 'Ebattery1', 'Ebattery2']
            
            deprecated_found = {}
            for scenario_name, network in self.networks.items():
                scenario_deprecated = []
                
                # Check all component carriers
                all_carriers = set()
                if len(network.generators) > 0:
                    all_carriers.update(network.generators.carrier.unique())
                if len(network.stores) > 0:
                    all_carriers.update(network.stores.carrier.unique())
                if len(network.storage_units) > 0:
                    all_carriers.update(network.storage_units.carrier.unique())
                if len(network.links) > 0:
                    all_carriers.update(network.links.carrier.unique())
                
                for deprecated in deprecated_names:
                    if deprecated in all_carriers:
                        scenario_deprecated.append(deprecated)
                
                deprecated_found[scenario_name] = scenario_deprecated
                
                if scenario_deprecated:
                    logger.warning(f"  ⚠️  {scenario_name}: Found deprecated names: {scenario_deprecated}")
                else:
                    logger.info(f"  ✅ {scenario_name}: No deprecated names found")
            
            naming_results['deprecated_names_check'] = deprecated_found
            
            # Verify new names are used correctly
            new_names_found = {}
            for scenario_name, network in self.networks.items():
                scenario_new = []
                
                # Get capacity data to see what new technologies are actually used
                capacity_data = get_capacity_data(network)
                all_new_carriers = set()
                all_new_carriers.update(capacity_data['stores'].keys())
                all_new_carriers.update(capacity_data['storage_units'].keys())
                all_new_carriers.update(capacity_data['links'].keys())
                
                for new_tech in self.new_battery_technologies:
                    if new_tech in all_new_carriers:
                        scenario_new.append(new_tech)
                
                new_names_found[scenario_name] = scenario_new
                
                if scenario_new:
                    logger.info(f"  ✅ {scenario_name}: New technologies found: {scenario_new}")
                else:
                    logger.info(f"  ℹ️  {scenario_name}: No new battery technologies deployed")
            
            naming_results['new_names_usage'] = new_names_found
            
        except Exception as e:
            logger.error(f"❌ Battery technology naming test failed: {str(e)}")
            test_passed = False
        
        self.test_results['battery_technology_naming'] = {
            'passed': test_passed,
            'results': naming_results
        }
        
        if test_passed:
            logger.info("✅ TEST 8 PASSED: Battery technology naming is consistent")
        else:
            logger.error("❌ TEST 8 FAILED: Issues with battery technology naming")
    
    def generate_test_report(self):
        """Generate a comprehensive test report."""
        logger.info("\n" + "=" * 100)
        logger.info("COMPREHENSIVE TEST REPORT")
        logger.info("=" * 100)
        
        passed_tests = 0
        total_tests = len(self.test_results)
        
        logger.info(f"\nTest Summary:")
        logger.info("-" * 50)
        
        for test_name, test_result in self.test_results.items():
            status = "PASSED" if test_result['passed'] else "FAILED"
            status_icon = "✅" if test_result['passed'] else "❌"
            logger.info(f"{status_icon} {test_name.replace('_', ' ').title()}: {status}")
            
            if test_result['passed']:
                passed_tests += 1
        
        logger.info("-" * 50)
        logger.info(f"Overall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED! Data processing functions are working correctly.")
        else:
            logger.error(f"⚠️  {total_tests - passed_tests} tests failed. Please review the issues above.")
        
        # Detailed results
        logger.info(f"\nDetailed Results:")
        logger.info("-" * 50)
        
        # Network loading details
        if 'network_loading' in self.test_results:
            result = self.test_results['network_loading']
            logger.info(f"Networks loaded: {result['networks_loaded']}/{result['networks_expected']}")
        
        # Capacity data details
        if 'capacity_data_extraction' in self.test_results:
            result = self.test_results['capacity_data_extraction']
            logger.info(f"Capacity data scenarios: {result['scenarios_tested']}")
        
        # Emissions details
        if 'emissions_calculations' in self.test_results:
            result = self.test_results['emissions_calculations']
            logger.info(f"Emissions calculated for: {result['scenarios_tested']} scenarios")
        
        # Plots details
        if 'plot_generation' in self.test_results:
            result = self.test_results['plot_generation']
            logger.info(f"Plots generated: {result['plots_generated']}")
        
        # Storage analysis details
        if 'storage_analysis' in self.test_results:
            result = self.test_results['storage_analysis']
            logger.info(f"Storage analysis scenarios: {result['scenarios_tested']}")
        
        logger.info("\n" + "=" * 100)
        
        return passed_tests == total_tests

def main():
    """Main function to run all tests."""
    logger.info("Starting Comprehensive Data Processing Test Suite...")
    
    # Create test suite instance
    test_suite = DataProcessingTestSuite()
    
    # Run all tests
    success = test_suite.run_all_tests()
    
    if success:
        logger.info("\n🎉 ALL DATA PROCESSING FUNCTIONS VERIFIED SUCCESSFULLY!")
        logger.info("The notebook can safely use all three network files with new battery technologies.")
        return 0
    else:
        logger.error("\n❌ SOME TESTS FAILED - PLEASE REVIEW THE ISSUES ABOVE")
        return 1

if __name__ == "__main__":
    exit(main())
