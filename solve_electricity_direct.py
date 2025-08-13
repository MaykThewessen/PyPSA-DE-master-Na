#!/usr/bin/env python3
"""
Direct electricity-only network optimization using PyPSA

This script loads the prepared electricity network and solves it directly
without going through the Snakemake workflow.
"""

import pypsa
import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def solve_electricity_network():
    """Load and solve the electricity network directly."""
    
    # Load the prepared electricity network
    network_path = "resources/de-all-tech-2035-mayk/networks/base_s_1_elec_.nc"
    
    logger.info(f"Loading network from {network_path}")
    n = pypsa.Network(network_path)
    
    # Print network info
    logger.info(f"Network overview:")
    logger.info(f"Buses: {len(n.buses)}")
    logger.info(f"Generators: {len(n.generators)}")
    logger.info(f"Loads: {len(n.loads)}")
    logger.info(f"Storage Units: {len(n.storage_units)}")
    logger.info(f"Stores: {len(n.stores)}")
    logger.info(f"Links: {len(n.links)}")
    logger.info(f"Lines: {len(n.lines)}")
    
    # Print some generator info
    if len(n.generators) > 0:
        logger.info("\nGenerator capacities by carrier:")
        gen_cap = n.generators.groupby('carrier')['p_nom'].sum()
        logger.info(gen_cap)
        
        extendable_gen = n.generators[n.generators.p_nom_extendable]
        if len(extendable_gen) > 0:
            logger.info("\nExtendable generators:")
            ext_cap = extendable_gen.groupby('carrier')['p_nom_max'].sum()
            logger.info(ext_cap)
    
    # Solve the network
    logger.info("\nStarting optimization with HiGHS solver...")
    
    try:
        # Solve with HiGHS solver
        n.optimize(
            solver_name="highs",
            solver_options={
                "presolve": "on",
                "parallel": "on",
                "threads": 4
            }
        )
        
        # Check if optimization was successful
        if n.objective is not None:
            logger.info(f"Optimization successful!")
            logger.info(f"Objective value: {n.objective:.2e} EUR")
            
            # Print some results
            logger.info("\nOptimal generator capacities:")
            if len(n.generators) > 0:
                optimal_gen = n.generators.groupby('carrier')[['p_nom_opt', 'p_nom']].sum()
                logger.info(optimal_gen)
            
            if len(n.storage_units) > 0:
                logger.info("\nOptimal storage capacities:")
                optimal_storage = n.storage_units.groupby('carrier')[['p_nom_opt', 'p_nom']].sum()
                logger.info(optimal_storage)
                
            if len(n.stores) > 0:
                logger.info("\nOptimal store capacities:")
                optimal_stores = n.stores.groupby('carrier')[['e_nom_opt', 'e_nom']].sum()
                logger.info(optimal_stores)
            
            # Save the solved network
            output_path = "results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved.nc"
            logger.info(f"\nSaving solved network to {output_path}")
            n.export_to_netcdf(output_path)
            
            return True
            
        else:
            logger.error("Optimization failed - no objective value found")
            return False
            
    except Exception as e:
        logger.error(f"Optimization failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = solve_electricity_network()
    if success:
        print("✅ Electricity network optimization completed successfully!")
    else:
        print("❌ Electricity network optimization failed!")
