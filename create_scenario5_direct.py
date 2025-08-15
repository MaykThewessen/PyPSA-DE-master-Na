#!/usr/bin/env python3
"""
Direct creation of Scenario 5: Zero CO2 emissions constraint
Takes an existing solved network and applies zero/near-zero CO2 constraints
"""

# Fix PyProj database context issue
import os
os.environ['PROJ_DATA'] = r'C:\Users\mayk\miniforge3\Lib\site-packages\pyproj\proj_dir\share\proj'
import pyproj
pyproj.datadir.set_data_dir(r'C:\Users\mayk\miniforge3\Lib\site-packages\pyproj\proj_dir\share\proj')

import pypsa
import pandas as pd
import numpy as np
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_scenario5_zero_emissions():
    """Load an existing network, apply zero CO2 constraint, and solve as scenario 5."""
    
    # Use the CO2 pricing scenario as the base
    base_network_path = "results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_co2_pricing.nc"
    
    if not os.path.exists(base_network_path):
        logger.error(f"Base network not found: {base_network_path}")
        return False
    
    logger.info(f"Loading base network from {base_network_path}")
    n = pypsa.Network(base_network_path)
    
    logger.info("🎯 SCENARIO 5: CREATING ZERO CO2 EMISSIONS VERSION")
    
    # Reset the network to unsolved state
    logger.info("Resetting network to unsolved state...")
    n.generators_t.p = n.generators_t.p * 0  # Clear solved generation
    n.storage_units_t.p = n.storage_units_t.p * 0  # Clear solved storage
    n.stores_t.p = n.stores_t.p * 0  # Clear solved store
    
    # Clear objective value to indicate unsolved
    n.objective = None
    
    # Apply zero CO2 constraint approach
    logger.info("💚 Applying zero CO2 emissions constraint...")
    
    # Method 1: Add CO2 emission factors to carriers
    co2_factors = {
        'coal': 0.820,      # tCO2/MWh
        'lignite': 0.986,   # tCO2/MWh  
        'CCGT': 0.350,      # tCO2/MWh
        'OCGT': 0.400,      # tCO2/MWh
        'oil': 0.650,       # tCO2/MWh
        'gas': 0.375,       # tCO2/MWh
    }
    
    # Add CO2 emission factors to the carriers
    for carrier, factor in co2_factors.items():
        if carrier in n.carriers.index:
            n.carriers.loc[carrier, 'co2_emissions'] = factor
            logger.info(f"Set CO2 factor for {carrier}: {factor} tCO2/MWh")
    
    # Add a CO2 atmosphere carrier if not exists
    if 'co2_atmosphere' not in n.carriers.index:
        n.add("Carrier", "co2_atmosphere", co2_emissions=1.0)
        logger.info("Added CO2 atmosphere carrier")
    
    # Clear existing global constraints
    n.global_constraints = n.global_constraints.iloc[0:0]
    logger.info("Cleared existing global constraints")
    
    # Add very strict CO2 constraint (0.1% of 1990 levels = 1.487 MtCO2)
    co2_limit_mtco2 = 0.001487  # 0.1% of 1990 German CO2 emissions
    
    # Add global CO2 constraint
    n.add("GlobalConstraint",
          "co2_limit_scenario5",
          type="primary_energy", 
          carrier_attribute="co2_emissions",
          sense="<=",
          constant=co2_limit_mtco2 * 1000)  # Convert to ktCO2
    
    logger.info(f"Added CO2 constraint: {co2_limit_mtco2} MtCO2 limit")
    
    # Method 2: Increase renewable capacity limits to ensure feasibility
    logger.info("📈 Expanding renewable capacity limits for feasibility...")
    
    renewable_expansions = {
        'solar': 500000,        # 500 GW solar
        'solar-hsat': 300000,   # 300 GW tracking solar
        'onwind': 250000,       # 250 GW onshore wind  
        'offwind-ac': 150000,   # 150 GW offshore wind AC
        'offwind-dc': 150000,   # 150 GW offshore wind DC
        'offwind-float': 100000, # 100 GW floating offshore wind
    }
    
    for carrier, max_capacity in renewable_expansions.items():
        mask = n.generators.carrier == carrier
        if mask.any():
            n.generators.loc[mask, 'p_nom_extendable'] = True
            n.generators.loc[mask, 'p_nom_max'] = max_capacity
            logger.info(f"Expanded {carrier} max capacity to {max_capacity} MW")
    
    # Method 3: Vastly increase storage capacity limits
    logger.info("🔋 Expanding storage capacity limits for feasibility...")
    
    # Battery storage
    if len(n.stores) > 0:
        battery_mask = n.stores.carrier == 'battery'
        if battery_mask.any():
            n.stores.loc[battery_mask, 'e_nom_extendable'] = True
            n.stores.loc[battery_mask, 'e_nom_max'] = 2000000  # 2 TWh battery storage
            logger.info("Expanded battery storage limit to 2 TWh")
    
    # Hydrogen storage
    if len(n.stores) > 0:
        h2_mask = n.stores.carrier == 'H2'
        if h2_mask.any():
            n.stores.loc[h2_mask, 'e_nom_extendable'] = True
            n.stores.loc[h2_mask, 'e_nom_max'] = 50000000  # 50 TWh hydrogen storage
            logger.info("Expanded hydrogen storage limit to 50 TWh")
    
    # Print network overview
    logger.info(f"\n=== SCENARIO 5 NETWORK READY ===")
    logger.info(f"🎯 Target: {co2_limit_mtco2} MtCO2 (0.1% of 1990)")
    logger.info(f"Buses: {len(n.buses)}")
    logger.info(f"Generators: {len(n.generators)}")
    logger.info(f"Global constraints: {len(n.global_constraints)}")
    
    if len(n.loads) > 0:
        total_demand = n.loads_t.p_set.sum().sum()
        peak_demand = n.loads_t.p_set.sum(axis=1).max()
        logger.info(f"Total annual demand: {total_demand:.0f} MWh")
        logger.info(f"Peak demand: {peak_demand:.0f} MW")
    
    # Print constraint details
    logger.info(f"\nGlobal constraints:")
    for idx in n.global_constraints.index:
        constraint = n.global_constraints.loc[idx]
        logger.info(f"  {idx}: {constraint.type} {constraint.sense} {constraint.constant} ktCO2")
    
    # Solve the network
    logger.info(f"\nStarting optimization with near-zero CO2 constraint...")
    
    try:
        # Solve with HiGHS solver
        n.optimize(
            solver_name="highs",
            solver_options={
                "presolve": "on",
                "parallel": "on", 
                "threads": 4,
                "time_limit": 7200,  # 2 hour time limit
            }
        )
        
        # Check if optimization was successful
        if n.objective is not None and n.objective_optimum:
            logger.info(f"🎉 SCENARIO 5 OPTIMIZATION SUCCESSFUL!")
            logger.info(f"Objective value: {n.objective:.2e} EUR")
            
            # Calculate results 
            logger.info(f"\n=== SCENARIO 5 RESULTS ===")
            
            # Calculate CO2 emissions
            co2_factors_check = {
                'coal': 0.820, 'lignite': 0.986, 'CCGT': 0.350, 'OCGT': 0.400, 'oil': 0.650, 'gas': 0.375
            }
            
            gen_annual = n.generators_t.p.sum() / 1000  # Convert to GWh
            gen_by_carrier = gen_annual.groupby(n.generators.carrier).sum()
            
            total_co2 = 0
            total_gen = gen_by_carrier.sum()
            renewable_gen = 0
            
            logger.info("Annual generation by technology:")
            for carrier in gen_by_carrier.index:
                generation = gen_by_carrier[carrier]
                if generation > 0:
                    share = generation / total_gen * 100
                    co2_factor = co2_factors_check.get(carrier, 0.0)
                    emissions = generation * co2_factor  # GWh * tCO2/MWh = ktCO2
                    total_co2 += emissions
                    
                    if co2_factor == 0:
                        renewable_gen += generation
                    
                    logger.info(f"  {carrier:12}: {generation:8.0f} GWh ({share:5.1f}%) | {emissions:6.0f} ktCO2")
            
            renewable_share = renewable_gen / total_gen * 100 if total_gen > 0 else 0
            
            logger.info(f"\n🌱 Renewable share: {renewable_share:.1f}%")
            logger.info(f"💨 Total CO2 emissions: {total_co2/1000:.6f} MtCO2")
            logger.info(f"🎯 CO2 limit: {co2_limit_mtco2:.6f} MtCO2")
            
            if total_co2/1000 <= co2_limit_mtco2 * 1.01:  # Allow 1% tolerance
                logger.info("✅ NEAR-ZERO EMISSIONS TARGET ACHIEVED!")
            else:
                excess = (total_co2/1000) - co2_limit_mtco2
                logger.info(f"❌ Target exceeded by {excess:.6f} MtCO2")
            
            # Save the solved network
            results_dir = "results/de-all-tech-2035-mayk/networks"
            os.makedirs(results_dir, exist_ok=True)
            output_path = f"{results_dir}/base_s_1_elec_solved_scenario5_nearzero_co2.nc"
            logger.info(f"\nSaving solved network to {output_path}")
            n.export_to_netcdf(output_path)
            
            return True
            
        else:
            logger.error("Optimization failed - no objective value found or not optimal")
            return False
            
    except Exception as e:
        logger.error(f"Optimization failed with error: {str(e)}")
        logger.error("The near-zero emission constraint may make the problem infeasible")
        logger.error("This indicates that zero emissions is not achievable with current assumptions")
        return False

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("PYPSA SCENARIO 5: DIRECT ZERO CO2 EMISSIONS CREATION")
    logger.info("=" * 80)
    
    success = create_scenario5_zero_emissions()
    
    if success:
        logger.info("\n🎉 Scenario 5 created successfully!")
        logger.info("✅ Near-zero CO2 emissions constraint applied and solved")
        logger.info("📊 Results saved for analysis")
        
        # Run verification
        logger.info("\n" + "=" * 50)
        logger.info("Running verification...")
        os.system("python verify_scenario5.py")
        
    else:
        logger.error("\n❌ Scenario 5 creation failed!")
        logger.error("The near-zero emissions constraint appears to make the problem infeasible")
        logger.error("This demonstrates the challenges of achieving absolute zero emissions")
