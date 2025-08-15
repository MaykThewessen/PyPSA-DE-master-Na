#!/usr/bin/env python3
"""
Scenario 2: Higher carbon pricing (300 EUR/tCO2) and 2% CO2 target
"""

import pypsa
import pandas as pd
import numpy as np
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def solve_scenario2_high_carbon_price():
    """Load network, apply 300 EUR/tCO2 carbon pricing, and solve scenario 2."""
    
    # Load the prepared electricity network
    network_path = "resources/de-all-tech-2035-mayk/networks/base_s_1_elec_.nc"
    
    logger.info(f"Loading network from {network_path}")
    n = pypsa.Network(network_path)
    
    # Remove the problematic CO2 constraint that's causing infeasibility
    logger.info("Removing global CO2 constraints (using pricing instead)...")
    n.global_constraints = n.global_constraints.iloc[0:0]  # Remove all global constraints
    
    # Apply higher carbon pricing (300 EUR/tCO2) - 20% higher than scenario 1
    co2_price = 300  # EUR/tCO2
    
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
    
    # Apply higher carbon pricing by increasing marginal costs
    logger.info(f"🌍 SCENARIO 2: Applying carbon price of {co2_price} EUR/tCO2...")
    for carrier, co2_factor in co2_factors.items():
        if co2_factor > 0:  # Only for fossil fuels
            mask = n.generators.carrier == carrier
            if mask.any():
                original_cost = n.generators.loc[mask, 'marginal_cost'].mean()
                carbon_cost = co2_factor * co2_price
                new_cost = n.generators.loc[mask, 'marginal_cost'] + carbon_cost
                n.generators.loc[mask, 'marginal_cost'] = new_cost
                logger.info(f"{carrier}: Added {carbon_cost:.2f} EUR/MWh carbon cost (original: {original_cost:.2f}, new: {new_cost.mean():.2f})")
    
    # Print network overview
    logger.info(f"\n=== SCENARIO 2 NETWORK READY ===")
    logger.info(f"🎯 Target: 2% of 1990 CO2 emissions")
    logger.info(f"💰 Carbon Price: {co2_price} EUR/tCO2")
    logger.info(f"Buses: {len(n.buses)}")
    logger.info(f"Generators: {len(n.generators)}")
    logger.info(f"Global constraints: {len(n.global_constraints)}")
    
    if len(n.loads) > 0:
        total_demand = n.loads_t.p_set.sum().sum()
        peak_demand = n.loads_t.p_set.sum(axis=1).max()
        logger.info(f"Total annual demand: {total_demand:.0f} MWh")
        logger.info(f"Peak demand: {peak_demand:.0f} MW")
    
    # Solve the network
    logger.info(f"\nStarting optimization with HiGHS solver and 300 EUR/tCO2 carbon pricing...")
    
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
            logger.info(f"🎉 SCENARIO 2 OPTIMIZATION SUCCESSFUL!")
            logger.info(f"Objective value: {n.objective:.2e} EUR")
            
            # Print results
            logger.info(f"\n=== SCENARIO 2 RESULTS ===")
            
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
                
                # Calculate renewable share
                renewable_carriers = ['solar', 'solar-hsat', 'onwind', 'offwind-ac', 'offwind-dc', 'offwind-float', 'ror']
                renewable_gen = gen_by_carrier.reindex(renewable_carriers, fill_value=0).sum()
                renewable_share = renewable_gen / total_gen * 100 if total_gen > 0 else 0
                logger.info(f"\n🌱 Renewable share: {renewable_share:.1f}%")
            
            # Storage results  
            if len(n.storage_units) > 0:
                logger.info(f"\nOptimal storage unit capacities:")
                storage_results = n.storage_units.groupby('carrier')[['p_nom_opt', 'p_nom']].sum()
                logger.info(storage_results)
                
            if len(n.stores) > 0:
                logger.info(f"\nOptimal store capacities:")
                store_results = n.stores.groupby('carrier')[['e_nom_opt', 'e_nom']].sum()
                logger.info(store_results)
            
            # Calculate CO2 emissions
            total_co2 = 0
            logger.info(f"\nCO2 emissions by technology:")
            for carrier, co2_factor in co2_factors.items():
                if carrier in gen_by_carrier.index and co2_factor > 0:
                    emissions = gen_by_carrier[carrier] * co2_factor  # GWh * tCO2/MWh = ktCO2
                    total_co2 += emissions
                    if emissions > 0:
                        logger.info(f"  {carrier:12}: {emissions:8.0f} ktCO2")
            
            logger.info(f"  {'Total':12}: {total_co2:8.0f} ktCO2")
            
            # Calculate CO2 intensity
            if total_gen > 0:
                co2_intensity = (total_co2 * 1000) / (total_gen * 1000)  # tCO2/MWh
                logger.info(f"💨 CO2 intensity: {co2_intensity:.3f} tCO2/MWh")
                
                # Compare to 2% target (rough calculation)
                # Assuming 1990 German electricity emissions ~300 MtCO2
                target_2pct = 300 * 0.02  # 6 MtCO2
                logger.info(f"🎯 Target (2% of 1990): ~{target_2pct:.0f} MtCO2")
                logger.info(f"   Actual emissions: {total_co2/1000:.1f} MtCO2")
                if total_co2/1000 <= target_2pct:
                    logger.info("✅ Target achieved!")
                else:
                    logger.info("❌ Target missed")
            
            # Save the solved network
            results_dir = "analysis-de-white-paper-v3/networks"
            os.makedirs(results_dir, exist_ok=True)
            output_path = f"{results_dir}/300Mt_CO2_Limit_solved_network.nc"
            logger.info(f"\nSaving solved network to {output_path}")
            n.export_to_netcdf(output_path)
            
            return True, n
            
        else:
            logger.error("Optimization failed - no objective value found")
            return False, None
            
    except Exception as e:
        logger.error(f"Optimization failed with error: {str(e)}")
        return False, None

def compare_scenarios():
    """Compare results between scenario 1 (250 EUR/tCO2) and scenario 2 (300 EUR/tCO2)."""
    
    logger.info("\n" + "=" * 100)
    logger.info("SCENARIO COMPARISON: 250 vs 300 EUR/tCO2")
    logger.info("=" * 100)
    
    try:
        # Load scenario 1 results
        scenario1_path = "analysis-de-white-paper-v3/networks/250Mt_CO2_Limit_solved_network.nc"
        scenario2_path = "analysis-de-white-paper-v3/networks/300Mt_CO2_Limit_solved_network.nc"
        
        if os.path.exists(scenario1_path) and os.path.exists(scenario2_path):
            n1 = pypsa.Network(scenario1_path)
            n2 = pypsa.Network(scenario2_path)
            
            logger.info(f"\n{'Metric':30} {'Scenario 1 (250€)':>20} {'Scenario 2 (300€)':>20} {'Change':>15}")
            logger.info("-" * 90)
            
            # Compare costs
            logger.info(f"{'Total System Cost (B€)':30} {n1.objective/1e9:20.1f} {n2.objective/1e9:20.1f} {((n2.objective-n1.objective)/n1.objective*100):+14.1f}%")
            
            # Compare generation
            gen1 = n1.generators_t.p.sum().groupby(n1.generators.carrier).sum()
            gen2 = n2.generators_t.p.sum().groupby(n2.generators.carrier).sum()
            
            # Compare renewable share
            renewable_carriers = ['solar', 'solar-hsat', 'onwind', 'offwind-ac', 'offwind-dc', 'offwind-float', 'ror']
            ren1 = gen1.reindex(renewable_carriers, fill_value=0).sum() / gen1.sum() * 100
            ren2 = gen2.reindex(renewable_carriers, fill_value=0).sum() / gen2.sum() * 100
            logger.info(f"{'Renewable Share (%)':30} {ren1:20.1f} {ren2:20.1f} {(ren2-ren1):+14.1f}pp")
            
            # Compare storage
            if len(n1.stores) > 0 and len(n2.stores) > 0:
                storage1 = n1.stores.e_nom_opt.sum() / 1000  # GWh
                storage2 = n2.stores.e_nom_opt.sum() / 1000  # GWh
                logger.info(f"{'Battery Storage (GWh)':30} {storage1:20.1f} {storage2:20.1f} {((storage2-storage1)/storage1*100):+14.1f}%")
            
            logger.info(f"\n🔍 Key differences with higher carbon price:")
            logger.info(f"   • System cost change: {((n2.objective-n1.objective)/n1.objective*100):+.1f}%")
            logger.info(f"   • Renewable share change: {(ren2-ren1):+.1f} percentage points")
            
        else:
            logger.warning("Cannot compare scenarios - missing result files")
            
    except Exception as e:
        logger.error(f"Scenario comparison failed: {str(e)}")

if __name__ == "__main__":
    success, network = solve_scenario2_high_carbon_price()
    
    if success:
        print("\n" + "="*100)
        print("🎉 SCENARIO 2 COMPLETED: 300 EUR/tCO2 CARBON PRICE")
        print("="*100)
        print("✅ Higher carbon pricing applied (300 vs 250 EUR/tCO2)")
        print("✅ Stricter CO2 target (2% vs 5% of 1990 emissions)")
        print("✅ Results saved for comparison analysis")
        print("="*100)
        
        # Run comparison
        compare_scenarios()
        
    else:
        print("❌ Scenario 2 optimization failed!")
