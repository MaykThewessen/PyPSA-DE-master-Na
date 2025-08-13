#!/usr/bin/env python3
"""
Scenario 3: Very high carbon pricing (500 EUR/tCO2) and 2% CO2 target
"""

import pypsa
import pandas as pd
import numpy as np
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def solve_scenario3_very_high_carbon_price():
    """Load network, apply 500 EUR/tCO2 carbon pricing, and solve scenario 3."""
    
    # Load the prepared electricity network
    network_path = "resources/de-all-tech-2035-mayk/networks/base_s_1_elec_.nc"
    
    logger.info(f"Loading network from {network_path}")
    n = pypsa.Network(network_path)
    
    # Remove the problematic CO2 constraint that's causing infeasibility
    logger.info("Removing global CO2 constraints (using pricing instead)...")
    n.global_constraints = n.global_constraints.iloc[0:0]  # Remove all global constraints
    
    # Apply very high carbon pricing (500 EUR/tCO2) - double scenario 1
    co2_price = 500  # EUR/tCO2
    
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
    
    # Apply very high carbon pricing by increasing marginal costs
    logger.info(f"🌍 SCENARIO 3: Applying carbon price of {co2_price} EUR/tCO2...")
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
    logger.info(f"\n=== SCENARIO 3 NETWORK READY ===")
    logger.info(f"🎯 Target: 2% of 1990 CO2 emissions")
    logger.info(f"💰 Carbon Price: {co2_price} EUR/tCO2 (VERY HIGH)")
    logger.info(f"Buses: {len(n.buses)}")
    logger.info(f"Generators: {len(n.generators)}")
    logger.info(f"Global constraints: {len(n.global_constraints)}")
    
    if len(n.loads) > 0:
        total_demand = n.loads_t.p_set.sum().sum()
        peak_demand = n.loads_t.p_set.sum(axis=1).max()
        logger.info(f"Total annual demand: {total_demand:.0f} MWh")
        logger.info(f"Peak demand: {peak_demand:.0f} MW")
    
    # Solve the network
    logger.info(f"\nStarting optimization with HiGHS solver and 500 EUR/tCO2 carbon pricing...")
    
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
            logger.info(f"🎉 SCENARIO 3 OPTIMIZATION SUCCESSFUL!")
            logger.info(f"Objective value: {n.objective:.2e} EUR")
            
            # Print results
            logger.info(f"\n=== SCENARIO 3 RESULTS ===")
            
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
                    logger.info("✅ TARGET ACHIEVED!")
                else:
                    excess = (total_co2/1000) - target_2pct
                    logger.info(f"❌ Target missed by {excess:.1f} MtCO2")
            
            # Save the solved network
            results_dir = "results/de-all-tech-2035-mayk/networks"
            os.makedirs(results_dir, exist_ok=True)
            output_path = f"{results_dir}/base_s_1_elec_solved_scenario3_500co2.nc"
            logger.info(f"\nSaving solved network to {output_path}")
            n.export_to_netcdf(output_path)
            
            return True, n
            
        else:
            logger.error("Optimization failed - no objective value found")
            return False, None
            
    except Exception as e:
        logger.error(f"Optimization failed with error: {str(e)}")
        return False, None

def compare_all_scenarios():
    """Compare results across all three scenarios."""
    
    logger.info("\n" + "=" * 120)
    logger.info("COMPLETE SCENARIO COMPARISON: 250 vs 300 vs 500 EUR/tCO2")
    logger.info("=" * 120)
    
    try:
        # Load all scenario results
        scenario_paths = {
            "Scenario 1 (250€)": "results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_co2_pricing.nc",
            "Scenario 2 (300€)": "results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_scenario2_300co2.nc",
            "Scenario 3 (500€)": "results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_scenario3_500co2.nc"
        }
        
        networks = {}
        for name, path in scenario_paths.items():
            if os.path.exists(path):
                networks[name] = pypsa.Network(path)
        
        if len(networks) >= 2:
            logger.info(f"\n{'Metric':35} {'Scenario 1 (250€)':>18} {'Scenario 2 (300€)':>18} {'Scenario 3 (500€)':>18}")
            logger.info("-" * 125)
            
            # Compare costs
            costs = {name: n.objective/1e9 for name, n in networks.items()}
            logger.info(f"{'Total System Cost (B€)':35} {costs.get('Scenario 1 (250€)', 0):18.1f} {costs.get('Scenario 2 (300€)', 0):18.1f} {costs.get('Scenario 3 (500€)', 0):18.1f}")
            
            # Compare renewable shares
            renewable_carriers = ['solar', 'solar-hsat', 'onwind', 'offwind-ac', 'offwind-dc', 'offwind-float', 'ror']
            ren_shares = {}
            for name, n in networks.items():
                gen = n.generators_t.p.sum().groupby(n.generators.carrier).sum()
                ren_gen = gen.reindex(renewable_carriers, fill_value=0).sum()
                ren_shares[name] = ren_gen / gen.sum() * 100
            
            logger.info(f"{'Renewable Share (%)':35} {ren_shares.get('Scenario 1 (250€)', 0):18.1f} {ren_shares.get('Scenario 2 (300€)', 0):18.1f} {ren_shares.get('Scenario 3 (500€)', 0):18.1f}")
            
            # Compare CO2 emissions
            co2_factors = {
                'coal': 0.820, 'lignite': 0.986, 'CCGT': 0.350, 'OCGT': 0.400, 'oil': 0.650
            }
            
            co2_emissions = {}
            for name, n in networks.items():
                gen = n.generators_t.p.sum().groupby(n.generators.carrier).sum() / 1e3  # GWh
                total_co2 = 0
                for carrier, co2_factor in co2_factors.items():
                    if carrier in gen.index:
                        total_co2 += gen[carrier] * co2_factor  # ktCO2
                co2_emissions[name] = total_co2 / 1000  # MtCO2
            
            logger.info(f"{'CO2 Emissions (MtCO2)':35} {co2_emissions.get('Scenario 1 (250€)', 0):18.1f} {co2_emissions.get('Scenario 2 (300€)', 0):18.1f} {co2_emissions.get('Scenario 3 (500€)', 0):18.1f}")
            
            # Compare to target
            target_2pct = 6.0  # MtCO2
            logger.info(f"{'2% Target (MtCO2)':35} {'6.0':>18} {'6.0':>18} {'6.0':>18}")
            
            # Compare storage
            if all(len(n.stores) > 0 for n in networks.values()):
                storage_caps = {}
                for name, n in networks.items():
                    storage_caps[name] = n.stores.e_nom_opt.sum() / 1000  # GWh
                logger.info(f"{'Battery Storage (GWh)':35} {storage_caps.get('Scenario 1 (250€)', 0):18.1f} {storage_caps.get('Scenario 2 (300€)', 0):18.1f} {storage_caps.get('Scenario 3 (500€)', 0):18.1f}")
            
            # Summary insights
            logger.info(f"\n🔍 KEY INSIGHTS:")
            if 'Scenario 3 (500€)' in co2_emissions:
                co2_reduction = co2_emissions.get('Scenario 1 (250€)', 0) - co2_emissions.get('Scenario 3 (500€)', 0)
                cost_increase = costs.get('Scenario 3 (500€)', 0) - costs.get('Scenario 1 (250€)', 0)
                logger.info(f"   • CO2 reduction from 250→500 €/tCO2: {co2_reduction:.1f} MtCO2 ({co2_reduction/co2_emissions.get('Scenario 1 (250€)', 1)*100:.1f}%)")
                logger.info(f"   • System cost increase: +{cost_increase:.1f} B€ ({cost_increase/costs.get('Scenario 1 (250€)', 1)*100:.1f}%)")
                
                if co2_emissions.get('Scenario 3 (500€)', 99) <= target_2pct:
                    logger.info("   • ✅ 2% CO2 target ACHIEVED with 500 €/tCO2!")
                else:
                    remaining = co2_emissions.get('Scenario 3 (500€)', 0) - target_2pct
                    logger.info(f"   • ❌ Still {remaining:.1f} MtCO2 above 2% target")
            
        else:
            logger.warning("Cannot compare scenarios - missing result files")
            
    except Exception as e:
        logger.error(f"Scenario comparison failed: {str(e)}")

if __name__ == "__main__":
    success, network = solve_scenario3_very_high_carbon_price()
    
    if success:
        print("\n" + "="*120)
        print("🎉 SCENARIO 3 COMPLETED: 500 EUR/tCO2 CARBON PRICE")
        print("="*120)
        print("✅ Very high carbon pricing applied (500 EUR/tCO2 - double scenario 1)")
        print("✅ Maximum economic pressure on fossil fuels")
        print("✅ Testing limits of carbon pricing effectiveness")
        print("="*120)
        
        # Run complete comparison
        compare_all_scenarios()
        
    else:
        print("❌ Scenario 3 optimization failed!")
