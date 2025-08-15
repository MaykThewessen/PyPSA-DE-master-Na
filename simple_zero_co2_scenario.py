#!/usr/bin/env python3
"""
Simple zero CO2 scenario creation using basic PyPSA functionality
This approach avoids complex geospatial operations that cause PyProj issues.
"""

import os
import pandas as pd
import numpy as np
import logging

# Set PROJ_DATA before importing anything that might use PyProj
os.environ['PROJ_DATA'] = r'C:\Users\mayk\miniforge3\Lib\site-packages\pyproj\proj_dir\share\proj'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_simple_zero_co2_network():
    """Create a simple network with zero CO2 emissions constraint"""
    
    logger.info("=" * 80)
    logger.info("SIMPLE ZERO CO2 SCENARIO CREATION")
    logger.info("=" * 80)
    
    try:
        # Import PyPSA after setting environment variables
        import pypsa
        
        logger.info("✅ PyPSA imported successfully")
        
        # Create a very simple network to test
        logger.info("Creating simple test network...")
        
        n = pypsa.Network()
        
        # Add a simple bus (without coordinates to avoid PyProj issues)
        n.add("Bus", "DE", country="DE")
        
        # Add a simple load
        n.add("Load", "DE_load", bus="DE", p_set=100.0)  # 100 MW constant load
        
        # Add renewable generators
        n.add("Generator", "DE_solar", bus="DE", p_nom_extendable=True, 
              p_nom_max=10000, marginal_cost=0, carrier="solar")
        
        n.add("Generator", "DE_wind", bus="DE", p_nom_extendable=True, 
              p_nom_max=10000, marginal_cost=0, carrier="onwind")
        
        # Add fossil generator with CO2 emissions
        n.add("Carrier", "gas", co2_emissions=0.375)  # tCO2/MWh
        n.add("Generator", "DE_gas", bus="DE", p_nom_extendable=True,
              p_nom_max=1000, marginal_cost=30, carrier="gas")
        
        # Add CO2 atmosphere
        n.add("Carrier", "co2_atmosphere", co2_emissions=1.0)
        
        # Add CO2 constraint (very strict: 0.1% of German 1990 emissions)
        german_1990_co2 = 148.7  # MtCO2
        co2_limit = german_1990_co2 * 0.001  # 0.1% = 0.1487 MtCO2
        
        n.add("GlobalConstraint", 
              "co2_limit", 
              type="primary_energy",
              carrier_attribute="co2_emissions", 
              sense="<=", 
              constant=co2_limit * 1000)  # Convert to ktCO2
        
        logger.info(f"Network created successfully!")
        logger.info(f"Buses: {len(n.buses)}")
        logger.info(f"Generators: {len(n.generators)}")
        logger.info(f"Loads: {len(n.loads)}")
        logger.info(f"Global constraints: {len(n.global_constraints)}")
        logger.info(f"CO2 limit: {co2_limit:.6f} MtCO2")
        
        # Try to solve
        logger.info("Attempting to solve the network...")
        
        n.optimize(solver_name="highs")
        
        if n.objective is not None:
            logger.info(f"✅ Optimization successful!")
            logger.info(f"Objective value: {n.objective:.2e} EUR")
            
            # Calculate results
            logger.info("\nGeneration results:")
            for gen in n.generators.index:
                p_opt = n.generators_t.p[gen].mean()
                p_nom_opt = n.generators.at[gen, 'p_nom_opt']
                carrier = n.generators.at[gen, 'carrier']
                logger.info(f"  {gen}: {p_opt:.1f} MW avg, {p_nom_opt:.1f} MW capacity ({carrier})")
            
            # Calculate CO2 emissions
            total_co2 = 0
            for gen in n.generators.index:
                carrier = n.generators.at[gen, 'carrier'] 
                if carrier in n.carriers.index:
                    co2_factor = n.carriers.at[carrier, 'co2_emissions']
                    if pd.notna(co2_factor) and co2_factor > 0:
                        generation = n.generators_t.p[gen].sum() / 1000  # GWh
                        emissions = generation * co2_factor / 1000  # MtCO2
                        total_co2 += emissions
                        logger.info(f"  {gen} emissions: {emissions:.6f} MtCO2")
            
            logger.info(f"\n💨 Total CO2 emissions: {total_co2:.6f} MtCO2")
            logger.info(f"🎯 CO2 limit: {co2_limit:.6f} MtCO2")
            
            if total_co2 <= co2_limit * 1.01:  # 1% tolerance
                logger.info("✅ ZERO CO2 TARGET ACHIEVED!")
            else:
                logger.info(f"❌ Target exceeded by {total_co2 - co2_limit:.6f} MtCO2")
                
            return True
            
        else:
            logger.error("❌ Optimization failed")
            return False
            
    except ImportError as e:
        logger.error(f"Failed to import PyPSA: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error creating network: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_simple_zero_co2_network()
    
    if success:
        logger.info("\n🎉 Simple zero CO2 scenario test successful!")
        logger.info("This demonstrates that zero CO2 constraints can work in PyPSA")
    else:
        logger.error("\n❌ Test failed - see errors above")
