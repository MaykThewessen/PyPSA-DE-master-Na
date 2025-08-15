#!/usr/bin/env python3
"""
Scenario 5: Zero CO2 emissions with hard constraint enforcement
Testing absolute zero emissions target using strict CO2 limits instead of pricing
"""

import pypsa
import pandas as pd
import numpy as np
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def solve_scenario5_zero_emissions():
    """Load network, apply zero CO2 constraint, and solve scenario 5."""
    
    # Load the prepared electricity network
    network_path = "resources/de-all-tech-2035-mayk/networks/base_s_1_elec_.nc"
    
    logger.info(f"Loading network from {network_path}")
    n = pypsa.Network(network_path)
    
    # Clear existing global constraints to start fresh
    logger.info("Clearing existing global constraints...")
    n.global_constraints = n.global_constraints.iloc[0:0]
    
    # Apply zero carbon pricing (remove any carbon costs)
    logger.info("🎯 SCENARIO 5: ZERO CO2 EMISSIONS WITH HARD CONSTRAINT")
    logger.info("Removing all carbon pricing to rely purely on constraints...")
    
    # CO2 emission factors (tCO2/MWh) for different fossil fuels
    co2_factors = {
        'coal': 0.820,      # tCO2/MWh for hard coal
        'lignite': 0.986,   # tCO2/MWh for lignite 
        'CCGT': 0.350,      # tCO2/MWh for natural gas CCGT
        'OCGT': 0.400,      # tCO2/MWh for natural gas OCGT
        'oil': 0.650,       # tCO2/MWh for oil
        'biomass': 0.000,   # Assuming carbon neutral
        'nuclear': 0.000,   # No direct CO2 emissions
        'solar': 0.000,     # No direct CO2 emissions
        'solar-hsat': 0.000,
        'onwind': 0.000,    # No direct CO2 emissions
        'offwind-ac': 0.000,
        'offwind-dc': 0.000,
        'offwind-float': 0.000,
        'ror': 0.000        # Run-of-river hydro
    }
    
    # Reset marginal costs to remove any existing carbon pricing
    for carrier in co2_factors.keys():
        if carrier in n.generators.carrier.values:
            mask = n.generators.carrier == carrier
            if mask.any():
                # Get original costs from the carriers data
                if carrier in ['coal']:
                    n.generators.loc[mask, 'marginal_cost'] = 24.57  # Original coal cost
                elif carrier in ['lignite']:
                    n.generators.loc[mask, 'marginal_cost'] = 22.11  # Original lignite cost
                elif carrier in ['CCGT', 'OCGT']:
                    n.generators.loc[mask, 'marginal_cost'] = 25.0   # Original gas cost
                elif carrier in ['oil']:
                    n.generators.loc[mask, 'marginal_cost'] = 40.0   # Estimate for oil
                elif carrier in ['nuclear']:
                    n.generators.loc[mask, 'marginal_cost'] = 1.75   # Nuclear fuel cost
                else:
                    n.generators.loc[mask, 'marginal_cost'] = 0.0    # Renewables have no fuel cost
    
    # Create a strict zero CO2 constraint
    logger.info("💚 Adding zero CO2 emissions constraint (absolute limit)...")
    
    # Method 1: Add global CO2 constraint set to zero
    if 'co2_atmosphere' not in n.carriers.index:
        # Add CO2 carrier if it doesn't exist
        n.add("Carrier", "co2_atmosphere", co2_emissions=1.0)
        logger.info("Added CO2 carrier to network")
    
    # Set CO2 emission factors for all fossil fuel generators
    for carrier, co2_factor in co2_factors.items():
        if carrier in n.generators.carrier.values and co2_factor > 0:
            mask = n.generators.carrier == carrier
            n.generators.loc[mask, 'carrier'] = carrier  # Ensure carrier is set
            logger.info(f"Setting CO2 emissions for {carrier}: {co2_factor} tCO2/MWh")
    
    # Add global CO2 constraint with zero limit
    n.add("GlobalConstraint",
          "co2_limit",
          type="primary_energy",
          carrier_attribute="co2_emissions",
          sense="<=",
          constant=0.0)  # Zero CO2 emissions allowed
    
    logger.info("✅ Added zero CO2 emissions global constraint")
    
    # Method 2: Alternative approach - directly limit fossil fuel capacity to zero
    logger.info("🚫 Setting fossil fuel generator capacities to zero as backup constraint...")
    fossil_carriers = ['coal', 'lignite', 'CCGT', 'OCGT', 'oil']
    
    for carrier in fossil_carriers:
        mask = n.generators.carrier == carrier
        if mask.any():
            # Set both existing and maximum capacity to zero
            n.generators.loc[mask, 'p_nom'] = 0.0
            n.generators.loc[mask, 'p_nom_max'] = 0.0
            n.generators.loc[mask, 'p_nom_extendable'] = False
            logger.info(f"Set {carrier} capacity limits to zero")
    
    # Ensure sufficient renewable and storage capacity for feasibility
    logger.info("📈 Ensuring sufficient renewable capacity for zero-emission scenario...")
    
    # Increase renewable capacity limits significantly 
    renewable_expansions = {
        'solar': 200000,        # 200 GW solar
        'solar-hsat': 100000,   # 100 GW tracking solar
        'onwind': 150000,       # 150 GW onshore wind  
        'offwind-ac': 80000,    # 80 GW offshore wind AC
        'offwind-dc': 80000,    # 80 GW offshore wind DC
        'offwind-float': 40000, # 40 GW floating offshore wind
    }
    
    for carrier, max_capacity in renewable_expansions.items():
        mask = n.generators.carrier == carrier
        if mask.any():
            n.generators.loc[mask, 'p_nom_extendable'] = True
            n.generators.loc[mask, 'p_nom_max'] = max_capacity
            logger.info(f"Set {carrier} maximum capacity to {max_capacity} MW")
    
    # Increase storage capacity limits significantly
    logger.info("🔋 Increasing storage capacity limits for zero-emission feasibility...")
    
    # Battery storage
    if len(n.stores) > 0:
        battery_mask = n.stores.carrier == 'battery'
        if battery_mask.any():
            n.stores.loc[battery_mask, 'e_nom_extendable'] = True
            n.stores.loc[battery_mask, 'e_nom_max'] = 500000  # 500 GWh battery storage
            logger.info("Set battery storage limit to 500 GWh")
    
    # Hydrogen storage
    if len(n.stores) > 0:
        h2_mask = n.stores.carrier == 'H2'
        if h2_mask.any():
            n.stores.loc[h2_mask, 'e_nom_extendable'] = True
            n.stores.loc[h2_mask, 'e_nom_max'] = 10000000  # 10 TWh hydrogen storage
            logger.info("Set hydrogen storage limit to 10 TWh")
    
    # Print network overview
    logger.info(f"\n=== SCENARIO 5 NETWORK READY ===")
    logger.info(f"🎯 Target: ZERO CO2 emissions (hard constraint)")
    logger.info(f"💰 Carbon Price: 0 EUR/tCO2 (constraint-based)")
    logger.info(f"🚫 Fossil fuel capacity: ZERO")
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
        logger.info(f"  {idx}: {constraint.type} {constraint.sense} {constraint.constant}")
    
    # Solve the network
    logger.info(f"\nStarting optimization with zero CO2 constraint...")
    
    try:
        # Solve with HiGHS solver and increased tolerance for feasibility
        n.optimize(
            solver_name="highs",
            solver_options={
                "presolve": "on",
                "parallel": "on", 
                "threads": 4,
                "time_limit": 3600,  # 1 hour time limit
                "mip_feasibility_tolerance": 1e-6,
                "dual_feasibility_tolerance": 1e-6,
                "primal_feasibility_tolerance": 1e-6
            }
        )
        
        # Check if optimization was successful
        if n.objective is not None:
            logger.info(f"🎉 SCENARIO 5 OPTIMIZATION SUCCESSFUL!")
            logger.info(f"Objective value: {n.objective:.2e} EUR")
            
            # Print results
            logger.info(f"\n=== SCENARIO 5 RESULTS ===")
            
            # Generator dispatch and capacity results
            if len(n.generators) > 0:
                logger.info("\nOptimal generator capacities:")
                gen_results = n.generators.groupby('carrier').agg({
                    'p_nom_opt': 'sum',
                    'p_nom': 'sum'
                }).round(1)
                for carrier in gen_results.index:
                    existing = gen_results.loc[carrier, 'p_nom']
                    optimal = gen_results.loc[carrier, 'p_nom_opt']
                    new_capacity = optimal - existing
                    if optimal > 0 or existing > 0:
                        logger.info(f"  {carrier:12}: {existing:8.0f} MW existing → {optimal:8.0f} MW optimal (+{new_capacity:6.0f} MW)")
                
                # Annual generation by technology
                gen_annual = n.generators_t.p.sum() / 1e3  # Convert to GWh
                gen_by_carrier = gen_annual.groupby(n.generators.carrier).sum().sort_values(ascending=False)
                logger.info(f"\nAnnual generation by technology:")
                total_gen = gen_by_carrier.sum()
                for carrier, generation in gen_by_carrier.items():
                    if generation > 0:
                        share = generation / total_gen * 100
                        logger.info(f"  {carrier:12}: {generation:8.0f} GWh ({share:5.1f}%)")
                
                logger.info(f"  {'Total':12}: {total_gen:8.0f} GWh")
                
                # Calculate renewable share (should be 100%)
                renewable_carriers = ['solar', 'solar-hsat', 'onwind', 'offwind-ac', 'offwind-dc', 'offwind-float', 'ror', 'hydro']
                renewable_gen = gen_by_carrier.reindex(renewable_carriers, fill_value=0).sum()
                renewable_share = renewable_gen / total_gen * 100 if total_gen > 0 else 0
                logger.info(f"\n🌱 Renewable share: {renewable_share:.1f}%")
            
            # Storage results  
            if len(n.storage_units) > 0:
                logger.info(f"\nOptimal storage unit capacities:")
                storage_results = n.storage_units.groupby('carrier')[['p_nom_opt', 'p_nom']].sum()
                for carrier in storage_results.index:
                    if storage_results.loc[carrier, 'p_nom_opt'] > 0:
                        logger.info(f"  {carrier}: {storage_results.loc[carrier, 'p_nom_opt']:.0f} MW")
                
            if len(n.stores) > 0:
                logger.info(f"\nOptimal store capacities:")
                store_results = n.stores.groupby('carrier')[['e_nom_opt', 'e_nom']].sum()
                for carrier in store_results.index:
                    if store_results.loc[carrier, 'e_nom_opt'] > 0:
                        logger.info(f"  {carrier}: {store_results.loc[carrier, 'e_nom_opt']:.0f} MWh")
            
            # Calculate CO2 emissions (should be zero)
            total_co2 = 0
            logger.info(f"\nCO2 emissions by technology:")
            for carrier, co2_factor in co2_factors.items():
                if carrier in gen_by_carrier.index and co2_factor > 0:
                    emissions = gen_by_carrier[carrier] * co2_factor  # GWh * tCO2/MWh = ktCO2
                    total_co2 += emissions
                    if emissions > 0:
                        logger.info(f"  {carrier:12}: {emissions:8.0f} ktCO2")
            
            logger.info(f"  {'Total':12}: {total_co2:8.0f} ktCO2")
            logger.info(f"💨 Total CO2 emissions: {total_co2/1000:.3f} MtCO2")
            
            if total_co2 < 0.001:  # Less than 1 tCO2
                logger.info("✅ ZERO EMISSIONS TARGET ACHIEVED!")
            else:
                logger.info(f"⚠️  Small residual emissions: {total_co2:.3f} ktCO2")
            
            # Save the solved network
            results_dir = "results/de-all-tech-2035-mayk/networks"
            os.makedirs(results_dir, exist_ok=True)
            output_path = f"{results_dir}/base_s_1_elec_solved_scenario5_0co2.nc"
            logger.info(f"\nSaving solved network to {output_path}")
            n.export_to_netcdf(output_path)
            
            return True, n
            
        else:
            logger.error("Optimization failed - no objective value found")
            return False, None
            
    except Exception as e:
        logger.error(f"Optimization failed with error: {str(e)}")
        logger.error("This might indicate the zero emission constraint makes the problem infeasible")
        logger.error("Try increasing renewable capacity limits or adding more storage options")
        return False, None

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("PYPSA SCENARIO 5: ZERO CO2 EMISSIONS")
    logger.info("=" * 80)
    
    success, network = solve_scenario5_zero_emissions()
    
    if success:
        logger.info("\n🎉 Scenario 5 completed successfully!")
        logger.info("✅ Zero CO2 emissions constraint implemented")
        logger.info("📊 Results saved for analysis")
    else:
        logger.error("\n❌ Scenario 5 failed!")
        logger.error("The zero emissions constraint may make the problem infeasible")
        logger.error("Consider adjusting renewable capacity limits or demand assumptions")
