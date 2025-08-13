#!/usr/bin/env python3
"""
Debug script to analyze PyPSA network infeasibility
"""

import pypsa
import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_network_infeasibility():
    """Analyze the network to identify sources of infeasibility."""
    
    # Load the network
    network_path = "resources/de-all-tech-2035-mayk/networks/base_s_1_elec_.nc"
    logger.info(f"Loading network from {network_path}")
    n = pypsa.Network(network_path)
    
    # Basic network info
    logger.info("\n=== NETWORK OVERVIEW ===")
    logger.info(f"Buses: {len(n.buses)}")
    logger.info(f"Generators: {len(n.generators)}")
    logger.info(f"Loads: {len(n.loads)}")
    logger.info(f"Storage Units: {len(n.storage_units)}")
    logger.info(f"Stores: {len(n.stores)}")
    logger.info(f"Links: {len(n.links)}")
    logger.info(f"Lines: {len(n.lines)}")
    logger.info(f"Global constraints: {len(n.global_constraints)}")
    
    # Check demand vs supply capacity
    logger.info("\n=== DEMAND ANALYSIS ===")
    if len(n.loads) > 0:
        total_demand = n.loads_t.p_set.sum().sum()
        peak_demand = n.loads_t.p_set.sum(axis=1).max()
        logger.info(f"Total annual demand: {total_demand:.2f} MWh")
        logger.info(f"Peak demand: {peak_demand:.2f} MW")
    
    # Check generator capacities
    logger.info("\n=== GENERATOR ANALYSIS ===")
    if len(n.generators) > 0:
        total_capacity = n.generators.p_nom.sum()
        extendable_max = n.generators[n.generators.p_nom_extendable].p_nom_max.sum()
        logger.info(f"Total existing capacity: {total_capacity:.2f} MW")
        logger.info(f"Total maximum extendable capacity: {extendable_max:.2f} MW")
        
        # Check by carrier
        gen_by_carrier = n.generators.groupby('carrier').agg({
            'p_nom': 'sum',
            'p_nom_max': 'sum',
            'marginal_cost': 'mean'
        })
        logger.info("\nCapacity by carrier:")
        logger.info(gen_by_carrier)
        
        # Check for generators with problematic parameters
        problematic = n.generators[
            (n.generators.marginal_cost.isna()) | 
            (n.generators.marginal_cost < 0) |
            (n.generators.p_nom_max < n.generators.p_nom_min)
        ]
        if len(problematic) > 0:
            logger.warning(f"\nProblematic generators found: {len(problematic)}")
            logger.warning(problematic[['carrier', 'p_nom', 'p_nom_min', 'p_nom_max', 'marginal_cost']])
    
    # Check global constraints
    logger.info("\n=== GLOBAL CONSTRAINTS ===")
    if len(n.global_constraints) > 0:
        logger.info("Global constraints:")
        for idx, constraint in n.global_constraints.iterrows():
            logger.info(f"  {idx}: {constraint['type']} = {constraint['constant']}")
            
            # Check if constraint is too restrictive
            if constraint['type'] == 'primary_energy':
                logger.info(f"    Primary energy constraint: {constraint['constant']}")
            elif 'co2' in constraint['type'].lower():
                logger.info(f"    CO2 constraint: {constraint['constant']}")
    
    # Check storage
    logger.info("\n=== STORAGE ANALYSIS ===")
    if len(n.storage_units) > 0:
        logger.info("Storage units:")
        storage_info = n.storage_units[['carrier', 'p_nom', 'p_nom_max', 'max_hours']]
        logger.info(storage_info)
    
    if len(n.stores) > 0:
        logger.info("Stores:")
        store_info = n.stores[['carrier', 'e_nom', 'e_nom_max']]
        logger.info(store_info)
    
    # Check links
    logger.info("\n=== LINKS ANALYSIS ===")
    if len(n.links) > 0:
        logger.info("Links:")
        link_info = n.links[['carrier', 'bus0', 'bus1', 'p_nom', 'p_nom_max', 'efficiency']]
        logger.info(link_info)
        
        # Check for problematic links
        problematic_links = n.links[
            (n.links.efficiency <= 0) |
            (n.links.efficiency.isna()) |
            (n.links.p_nom_max < 0)
        ]
        if len(problematic_links) > 0:
            logger.warning(f"\nProblematic links found: {len(problematic_links)}")
            logger.warning(problematic_links)
    
    # Try a simplified solve to get more info
    logger.info("\n=== ATTEMPTING SIMPLIFIED SOLVE ===")
    try:
        # Create a copy and try removing global constraints
        n_simple = n.copy()
        n_simple.global_constraints = n_simple.global_constraints.iloc[0:0]  # Remove all global constraints
        
        logger.info("Trying solve without global constraints...")
        n_simple.optimize(solver_name="highs", solver_options={"presolve": "on"})
        
        if n_simple.objective is not None:
            logger.info("✅ Model is feasible without global constraints!")
            logger.info(f"Objective: {n_simple.objective:.2e} EUR")
        else:
            logger.warning("❌ Still infeasible without global constraints")
            
    except Exception as e:
        logger.error(f"Error in simplified solve: {str(e)}")
    
    # Check for missing data
    logger.info("\n=== DATA COMPLETENESS CHECK ===")
    
    # Check for NaN values in key parameters
    if len(n.generators) > 0:
        nan_marginal = n.generators.marginal_cost.isna().sum()
        nan_capital = n.generators.capital_cost.isna().sum()
        logger.info(f"Generators with NaN marginal_cost: {nan_marginal}")
        logger.info(f"Generators with NaN capital_cost: {nan_capital}")
    
    if len(n.loads) > 0:
        nan_loads = n.loads_t.p_set.isna().sum().sum()
        logger.info(f"Time steps with NaN load: {nan_loads}")
    
    return n

if __name__ == "__main__":
    try:
        network = analyze_network_infeasibility()
        logger.info("\n🔍 Network analysis completed. Check the output above for potential issues.")
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
