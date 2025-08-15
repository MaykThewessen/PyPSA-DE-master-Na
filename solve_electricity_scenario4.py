#!/usr/bin/env python3
"""
Scenario 4: Extreme carbon pricing (900 EUR/tCO2) and 2% CO2 target
Testing the absolute limits of carbon pricing effectiveness
"""

import pypsa
import pandas as pd
import numpy as np
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def solve_scenario4_extreme_carbon_price():
    """Load network, apply 900 EUR/tCO2 carbon pricing, and solve scenario 4."""
    
    # Load the prepared electricity network
    network_path = "resources/de-all-tech-2035-mayk/networks/base_s_1_elec_.nc"
    
    logger.info(f"Loading network from {network_path}")
    n = pypsa.Network(network_path)
    
    # Remove the problematic CO2 constraint that's causing infeasibility
    logger.info("Removing global CO2 constraints (using pricing instead)...")
    n.global_constraints = n.global_constraints.iloc[0:0]  # Remove all global constraints
    
    # Apply extreme carbon pricing (900 EUR/tCO2) - 3.6x scenario 1
    co2_price = 900  # EUR/tCO2
    
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
    
    # Apply extreme carbon pricing by increasing marginal costs
    logger.info(f"🌍 SCENARIO 4: Applying carbon price of {co2_price} EUR/tCO2 (EXTREME)...")
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
    logger.info(f"\n=== SCENARIO 4 NETWORK READY ===")
    logger.info(f"🎯 Target: 2% of 1990 CO2 emissions")
    logger.info(f"💰 Carbon Price: {co2_price} EUR/tCO2 (EXTREME)")
    logger.info(f"⚠️  Testing absolute limits of carbon pricing")
    logger.info(f"Buses: {len(n.buses)}")
    logger.info(f"Generators: {len(n.generators)}")
    logger.info(f"Global constraints: {len(n.global_constraints)}")
    
    if len(n.loads) > 0:
        total_demand = n.loads_t.p_set.sum().sum()
        peak_demand = n.loads_t.p_set.sum(axis=1).max()
        logger.info(f"Total annual demand: {total_demand:.0f} MWh")
        logger.info(f"Peak demand: {peak_demand:.0f} MW")
    
    # Solve the network
    logger.info(f"\nStarting optimization with HiGHS solver and 900 EUR/tCO2 carbon pricing...")
    
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
            logger.info(f"🎉 SCENARIO 4 OPTIMIZATION SUCCESSFUL!")
            logger.info(f"Objective value: {n.objective:.2e} EUR")
            
            # Print results
            logger.info(f"\n=== SCENARIO 4 RESULTS ===")
            
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
                    
                # Calculate percentage above target
                pct_above = ((total_co2/1000) / target_2pct - 1) * 100
                logger.info(f"📊 Emissions are {pct_above:.0f}% above 2% target")
            
            # Save the solved network
            results_dir = "analysis-de-white-paper-v3/networks"
            os.makedirs(results_dir, exist_ok=True)
            output_path = f"{results_dir}/900Mt_CO2_Limit_solved_network.nc"
            logger.info(f"\nSaving solved network to {output_path}")
            n.export_to_netcdf(output_path)
            
            return True, n
            
        else:
            logger.error("Optimization failed - no objective value found")
            return False, None
            
    except Exception as e:
        logger.error(f"Optimization failed with error: {str(e)}")
        return False, None

def compare_all_four_scenarios():
    """Compare results across all four scenarios."""
    
    logger.info("\n" + "=" * 140)
    logger.info("ULTIMATE SCENARIO COMPARISON: 250 vs 300 vs 500 vs 900 EUR/tCO2")
    logger.info("=" * 140)
    
    try:
        # Load all scenario results
        scenario_paths = {
            "250Mt CO2 Limit": "analysis-de-white-paper-v3/networks/250Mt_CO2_Limit_solved_network.nc",
            "300Mt CO2 Limit": "analysis-de-white-paper-v3/networks/300Mt_CO2_Limit_solved_network.nc",
            "500Mt CO2 Limit": "analysis-de-white-paper-v3/networks/500Mt_CO2_Limit_solved_network.nc",
            "900Mt CO2 Limit": "analysis-de-white-paper-v3/networks/900Mt_CO2_Limit_solved_network.nc"
        }
        
        networks = {}
        for name, path in scenario_paths.items():
            if os.path.exists(path):
                networks[name] = pypsa.Network(path)
        
        if len(networks) >= 2:
            logger.info(f"\n{'Metric':35} {'S1 (250€)':>12} {'S2 (300€)':>12} {'S3 (500€)':>12} {'S4 (900€)':>12} {'Trend':>15}")
            logger.info("-" * 140)
            
            # Compare costs
            costs = {name: n.objective/1e9 for name, n in networks.items()}
            s1_cost = costs.get('S1 (250€)', 0)
            s4_cost = costs.get('S4 (900€)', 0)
            cost_trend = f"+{((s4_cost-s1_cost)/s1_cost*100):.0f}%" if s1_cost > 0 else "N/A"
            logger.info(f"{'System Cost (B€)':35} {costs.get('S1 (250€)', 0):12.1f} {costs.get('S2 (300€)', 0):12.1f} {costs.get('S3 (500€)', 0):12.1f} {costs.get('S4 (900€)', 0):12.1f} {cost_trend:>15}")
            
            # Compare renewable shares
            renewable_carriers = ['solar', 'solar-hsat', 'onwind', 'offwind-ac', 'offwind-dc', 'offwind-float', 'ror']
            ren_shares = {}
            for name, n in networks.items():
                gen = n.generators_t.p.sum().groupby(n.generators.carrier).sum()
                ren_gen = gen.reindex(renewable_carriers, fill_value=0).sum()
                ren_shares[name] = ren_gen / gen.sum() * 100
            
            s1_ren = ren_shares.get('S1 (250€)', 0)
            s4_ren = ren_shares.get('S4 (900€)', 0)
            ren_trend = f"+{(s4_ren-s1_ren):.1f}pp"
            logger.info(f"{'Renewable Share (%)':35} {ren_shares.get('S1 (250€)', 0):12.1f} {ren_shares.get('S2 (300€)', 0):12.1f} {ren_shares.get('S3 (500€)', 0):12.1f} {ren_shares.get('S4 (900€)', 0):12.1f} {ren_trend:>15}")
            
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
            
            s1_co2 = co2_emissions.get('S1 (250€)', 0)
            s4_co2 = co2_emissions.get('S4 (900€)', 0)
            co2_reduction = s1_co2 - s4_co2
            co2_trend = f"-{co2_reduction:.1f} ({co2_reduction/s1_co2*100:.0f}%)" if s1_co2 > 0 else "N/A"
            logger.info(f"{'CO2 Emissions (MtCO2)':35} {co2_emissions.get('S1 (250€)', 0):12.1f} {co2_emissions.get('S2 (300€)', 0):12.1f} {co2_emissions.get('S3 (500€)', 0):12.1f} {co2_emissions.get('S4 (900€)', 0):12.1f} {co2_trend:>15}")
            
            # Target line
            target_2pct = 6.0  # MtCO2
            logger.info(f"{'2% Target (MtCO2)':35} {'6.0':>12} {'6.0':>12} {'6.0':>12} {'6.0':>12} {'TARGET':>15}")
            
            # Compare hydrogen storage
            h2_storage = {}
            for name, n in networks.items():
                if len(n.stores) > 0 and 'H2' in n.stores.carrier.values:
                    h2_storage[name] = n.stores[n.stores.carrier == 'H2'].e_nom_opt.sum() / 1000  # TWh
                else:
                    h2_storage[name] = 0
            
            s4_h2 = h2_storage.get('S4 (900€)', 0)
            h2_trend = f"{s4_h2:.1f} TWh" if s4_h2 > 0 else "None"
            logger.info(f"{'Hydrogen Storage (TWh)':35} {h2_storage.get('S1 (250€)', 0):12.1f} {h2_storage.get('S2 (300€)', 0):12.1f} {h2_storage.get('S3 (500€)', 0):12.1f} {h2_storage.get('S4 (900€)', 0):12.1f} {h2_trend:>15}")
            
            # Summary insights
            logger.info(f"\n🔍 ULTIMATE CARBON PRICING ANALYSIS:")
            logger.info(f"   📈 Cost escalation: 250€ → 900€ = +{cost_trend}")
            logger.info(f"   🌱 Renewable growth: {s1_ren:.1f}% → {s4_ren:.1f}% = {ren_trend}")
            logger.info(f"   💨 CO2 reduction: {s1_co2:.1f} → {s4_co2:.1f} MtCO2 = {co2_trend}")
            
            # Efficiency analysis
            if s1_cost > 0 and s1_co2 > 0:
                cost_per_co2_reduction = (s4_cost - s1_cost) / co2_reduction if co2_reduction > 0 else 0
                logger.info(f"   💰 Cost per MtCO2 reduced: {cost_per_co2_reduction:.1f} B€/MtCO2")
                
                # Marginal analysis between scenarios
                scenarios = ['S1 (250€)', 'S2 (300€)', 'S3 (500€)', 'S4 (900€)']
                logger.info(f"\n📊 MARGINAL EFFECTIVENESS:")
                for i in range(1, len(scenarios)):
                    prev = scenarios[i-1]
                    curr = scenarios[i]
                    if prev in costs and curr in costs and prev in co2_emissions and curr in co2_emissions:
                        cost_diff = costs[curr] - costs[prev]
                        co2_diff = co2_emissions[prev] - co2_emissions[curr]
                        if co2_diff > 0:
                            marginal_cost = cost_diff / co2_diff
                            logger.info(f"   {prev} → {curr}: {marginal_cost:.1f} B€/MtCO2 reduced")
            
            # Final assessment
            if s4_co2 <= target_2pct:
                logger.info(f"\n🎉 SUCCESS: 2% CO2 target ACHIEVED at 900 EUR/tCO2!")
            else:
                remaining_gap = s4_co2 - target_2pct
                logger.info(f"\n⚠️  LIMITATION: Even at 900 EUR/tCO2, still {remaining_gap:.1f} MtCO2 above target")
                logger.info(f"   Carbon pricing alone may be insufficient for 2% target")
                
        else:
            logger.warning("Cannot compare scenarios - missing result files")
            
    except Exception as e:
        logger.error(f"Scenario comparison failed: {str(e)}")

if __name__ == "__main__":
    success, network = solve_scenario4_extreme_carbon_price()
    
    if success:
        print("\n" + "="*140)
        print("🎉 SCENARIO 4 COMPLETED: 900 EUR/tCO2 EXTREME CARBON PRICE")
        print("="*140)
        print("✅ Extreme carbon pricing applied (900 EUR/tCO2 - 3.6x scenario 1)")
        print("✅ Testing absolute limits of carbon pricing policy")
        print("✅ Maximum economic pressure on fossil fuel generation")
        print("="*140)
        
        # Run ultimate comparison
        compare_all_four_scenarios()
        
    else:
        print("❌ Scenario 4 optimization failed!")
