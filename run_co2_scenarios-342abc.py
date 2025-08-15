#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CO2 Pricing Scenarios Runner
Run 5 scenarios sequentially from 100 to 1200 EUR/t CO2
"""

import os
import sys
import logging
import pandas as pd
import datetime
import pypsa

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('co2_scenarios.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def apply_co2_pricing(network, co2_price):
    """Apply CO2 pricing to network"""
    
    # Get carriers with CO2 emissions and their emission factors (t/MWh)
    co2_factors = {
        'coal': 0.96,
        'lignite': 1.18, 
        'CCGT': 0.35,
        'OCGT': 0.49,
        'oil': 0.69,
        'gas': 0.35,  # same as CCGT
        'biomass': 0.0  # assumed carbon neutral
    }
    
    # Reset marginal costs to original values first
    for carrier in co2_factors.keys():
        gen_i = network.generators[network.generators.carrier == carrier].index
        if len(gen_i) > 0:
            # Reset to fuel cost only (remove any existing CO2 cost)
            fuel_costs = {
                'coal': 8.5,      # EUR/MWh
                'lignite': 4.0,   # EUR/MWh
                'CCGT': 21.6,     # EUR/MWh
                'OCGT': 21.6,     # EUR/MWh
                'oil': 65.0,      # EUR/MWh
                'gas': 21.6,      # EUR/MWh
                'biomass': 20.0   # EUR/MWh
            }
            network.generators.loc[gen_i, 'marginal_cost'] = fuel_costs.get(carrier, 0.0)
    
    # Now apply CO2 pricing
    total_co2_cost_added = 0
    for carrier, co2_factor in co2_factors.items():
        gen_i = network.generators[network.generators.carrier == carrier].index
        if len(gen_i) > 0 and co2_factor > 0:
            co2_cost = co2_price * co2_factor  # EUR/MWh
            network.generators.loc[gen_i, 'marginal_cost'] += co2_cost
            total_co2_cost_added += co2_cost * len(gen_i)
            
    return total_co2_cost_added

def optimize_scenario(network, co2_price, solver_name='highs', logger=None):
    """Optimize network with given CO2 price"""
    
    if logger:
        logger.info(f"Optimizing scenario with CO2 price: {co2_price} EUR/t")
    
    # Apply CO2 pricing
    co2_cost_added = apply_co2_pricing(network, co2_price)
    
    if logger:
        logger.info(f"Applied CO2 pricing - average additional cost: {co2_cost_added:.2f} EUR/MWh")
    
    # Set solver options for HiGHS
    solver_options = {
        'threads': 4,
        'solver': 'ipm',           # interior point method
        'run_crossover': 'off',    # no crossover 
        'primal_feasibility_tolerance': 1e-5,
        'dual_feasibility_tolerance': 1e-5,
        'ipm_optimality_tolerance': 1e-4,
        'random_seed': 123
    }
    
    try:
        start_time = datetime.datetime.now()
        
        # Run optimization
        status, termination = network.optimize(
            solver_name=solver_name,
            solver_options=solver_options
        )
        
        end_time = datetime.datetime.now()
        optimization_time = (end_time - start_time).total_seconds()
        
        if logger:
            logger.info(f"Optimization completed in {optimization_time:.2f} seconds")
            logger.info(f"Status: {status}, Termination: {termination}")
            if hasattr(network, 'objective'):
                logger.info(f"Objective: {network.objective / 1e9:.3f} billion EUR")
        
        return status == "ok", optimization_time
        
    except Exception as e:
        if logger:
            logger.error(f"Optimization failed: {e}")
        return False, 0

def generate_results_summary(network, co2_price, optimization_time):
    """Generate summary of results"""
    
    results = {
        'co2_price': co2_price,
        'optimization_time': optimization_time,
        'objective_value': getattr(network, 'objective', 0) / 1e9,  # Billion EUR
        'total_cost_billion_eur': getattr(network, 'objective', 0) / 1e9
    }
    
    # Generator capacities
    if len(network.generators) > 0:
        gen_capacity = network.generators.groupby('carrier')['p_nom_opt'].sum() / 1000  # GW
        for carrier, capacity in gen_capacity.items():
            results[f'{carrier}_capacity_gw'] = capacity
    
    # Storage capacities  
    if len(network.storage_units) > 0:
        storage_capacity = network.storage_units.groupby('carrier')['p_nom_opt'].sum() / 1000  # GW
        for carrier, capacity in storage_capacity.items():
            results[f'{carrier}_storage_gw'] = capacity
    
    return results

def run_co2_scenarios():
    """Run all 5 CO2 pricing scenarios"""
    
    logger = setup_logging()
    logger.info("Starting CO2 pricing scenarios analysis")
    
    # Define scenarios
    co2_prices = [100, 200, 300, 500, 1200]  # EUR/t CO2
    
    # Try to find existing network file
    network_files = [
        "results/de-all-tech-2035/networks/base_s_1_elec_solved_co2_pricing.nc",
        "results/de-all-tech-2035/networks/base_s_1_elec_solved_scenario1_250co2.nc",
        "resources/de-all-tech-2035/networks/base_s_1_elec.nc",
        "resources/de-all-tech-2035/networks/base_s_1.nc"
    ]
    
    base_network = None
    for network_file in network_files:
        if os.path.exists(network_file):
            logger.info(f"Loading base network from: {network_file}")
            try:
                base_network = pypsa.Network(network_file)
                logger.info(f"Network loaded successfully: {len(base_network.buses)} buses, {len(base_network.generators)} generators")
                break
            except Exception as e:
                logger.warning(f"Failed to load {network_file}: {e}")
                continue
    
    if base_network is None:
        logger.error("No suitable base network found!")
        return False
    
    # Results storage
    all_results = []
    
    # Create results directory
    results_dir = "results/co2_scenarios"
    os.makedirs(results_dir, exist_ok=True)
    
    # Run each scenario
    for i, co2_price in enumerate(co2_prices, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"SCENARIO {i}: CO2 PRICE = {co2_price} EUR/t")
        logger.info(f"{'='*60}")
        
        # Create a copy of the base network
        network = base_network.copy()
        
        # Optimize scenario
        success, opt_time = optimize_scenario(network, co2_price, logger=logger)
        
        if success:
            # Generate results summary
            results = generate_results_summary(network, co2_price, opt_time)
            all_results.append(results)
            
            # Save optimized network
            output_file = f"{results_dir}/network_co2_{co2_price}.nc"
            network.export_to_netcdf(output_file)
            logger.info(f"Network saved: {output_file}")
            
            # Print key results
            print(f"\nScenario {i} Results (CO2: {co2_price} EUR/t):")
            print(f"  Total Cost: {results['total_cost_billion_eur']:.2f} billion EUR")
            if 'solar_capacity_gw' in results:
                print(f"  Solar: {results['solar_capacity_gw']:.1f} GW")
            if 'onwind_capacity_gw' in results:
                print(f"  Onshore Wind: {results['onwind_capacity_gw']:.1f} GW")
            if 'offwind_capacity_gw' in results:
                print(f"  Offshore Wind: {results['offwind_capacity_gw']:.1f} GW")
            
        else:
            logger.error(f"Scenario {i} optimization failed!")
            return False
    
    # Save all results to CSV
    results_df = pd.DataFrame(all_results)
    results_file = f"{results_dir}/co2_scenarios_results.csv"
    results_df.to_csv(results_file, index=False)
    logger.info(f"All results saved to: {results_file}")
    
    # Print summary table
    print(f"\n{'='*80}")
    print("CO2 PRICING SCENARIOS SUMMARY")
    print(f"{'='*80}")
    
    print(f"{'CO2 Price':<12} {'Total Cost':<12} {'Solar':<8} {'Onwind':<8} {'Offwind':<8}")
    print(f"{'(EUR/t)':<12} {'(B EUR)':<12} {'(GW)':<8} {'(GW)':<8} {'(GW)':<8}")
    print("-" * 60)
    
    for _, row in results_df.iterrows():
        solar = row.get('solar_capacity_gw', 0)
        onwind = row.get('onwind_capacity_gw', 0) 
        offwind = row.get('offwind_capacity_gw', 0) + row.get('offwind-ac_capacity_gw', 0)
        
        print(f"{row['co2_price']:<12.0f} {row['total_cost_billion_eur']:<12.2f} {solar:<8.1f} {onwind:<8.1f} {offwind:<8.1f}")
    
    logger.info("All scenarios completed successfully!")
    return True

if __name__ == "__main__":
    success = run_co2_scenarios()
    if success:
        print("\nAll scenarios completed successfully!")
    else:
        print("\nScenarios failed!")
        sys.exit(1)
