#!/usr/bin/env python3
"""
Scenario 5 Verification: Near-zero CO2 emissions (0.1% of 1990 levels)
Tests the closest achievable result to zero emissions using current PyPSA configuration
"""

import pypsa
import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_co2_emissions(network_path, scenario_name="Scenario 5"):
    """Calculate CO2 emissions from a solved PyPSA network."""
    
    logger.info(f"Loading network: {network_path}")
    n = pypsa.Network(network_path)
    
    # CO2 emission factors (tCO2/MWh) for different carriers
    co2_factors = {
        'coal': 0.820,      # tCO2/MWh for hard coal
        'lignite': 0.986,   # tCO2/MWh for lignite 
        'CCGT': 0.350,      # tCO2/MWh for natural gas CCGT
        'OCGT': 0.400,      # tCO2/MWh for natural gas OCGT
        'oil': 0.650,       # tCO2/MWh for oil
        'gas': 0.375,       # tCO2/MWh for average natural gas
        'biomass': 0.000,   # Assuming carbon neutral
        'nuclear': 0.000,   # No direct CO2 emissions
        'solar': 0.000,     # No direct CO2 emissions
        'solar-hsat': 0.000,
        'onwind': 0.000,    # No direct CO2 emissions
        'offwind-ac': 0.000,
        'offwind-dc': 0.000,
        'offwind-float': 0.000,
        'ror': 0.000,       # Run-of-river hydro
        'hydro': 0.000,     # Reservoir hydro
        'geothermal': 0.000 # No direct CO2 emissions
    }
    
    # Calculate annual generation by technology
    if len(n.generators_t.p.columns) > 0:
        gen_annual = n.generators_t.p.sum() / 1000  # Convert to GWh
        gen_by_carrier = gen_annual.groupby(n.generators.carrier).sum()
        
        logger.info(f"\n=== {scenario_name} EMISSIONS ANALYSIS ===")
        logger.info(f"Annual generation by technology:")
        total_gen = gen_by_carrier.sum()
        
        # Calculate emissions and generation shares
        total_co2 = 0
        renewable_gen = 0
        fossil_gen = 0
        
        for carrier in gen_by_carrier.index:
            generation = gen_by_carrier[carrier]
            if generation > 0:
                share = generation / total_gen * 100
                co2_factor = co2_factors.get(carrier, 0.0)
                emissions = generation * co2_factor  # GWh * tCO2/MWh = ktCO2
                total_co2 += emissions
                
                # Categorize generation
                if co2_factor == 0:
                    renewable_gen += generation
                else:
                    fossil_gen += generation
                    
                logger.info(f"  {carrier:12}: {generation:8.0f} GWh ({share:5.1f}%) | {emissions:6.0f} ktCO2")
        
        logger.info(f"  {'Total':12}: {total_gen:8.0f} GWh")
        
        # Calculate renewable and fossil shares
        renewable_share = renewable_gen / total_gen * 100 if total_gen > 0 else 0
        fossil_share = fossil_gen / total_gen * 100 if total_gen > 0 else 0
        
        logger.info(f"\n🌱 Renewable share: {renewable_share:.1f}%")
        logger.info(f"🏭 Fossil fuel share: {fossil_share:.1f}%")
        logger.info(f"💨 Total CO2 emissions: {total_co2/1000:.3f} MtCO2")
        
        # Compare to CO2 targets
        target_01pct = 1.487 * 0.001  # 0.1% of 1990 emissions (1.487 GtCO2)
        target_02pct = 1.487 * 0.002  # 0.2% of 1990 emissions
        
        logger.info(f"\n🎯 CO2 Targets:")
        logger.info(f"   0.1% of 1990: {target_01pct:.3f} MtCO2")
        logger.info(f"   0.2% of 1990: {target_02pct:.3f} MtCO2")
        logger.info(f"   Actual emissions: {total_co2/1000:.3f} MtCO2")
        
        if total_co2/1000 <= target_01pct:
            logger.info("✅ 0.1% TARGET ACHIEVED!")
            achievement = "0.1% target achieved"
        elif total_co2/1000 <= target_02pct:
            logger.info("✅ 0.2% TARGET ACHIEVED!")
            achievement = "0.2% target achieved"
        else:
            excess = (total_co2/1000) - target_01pct
            logger.info(f"❌ Target missed by {excess:.3f} MtCO2")
            achievement = f"Target missed by {excess:.3f} MtCO2"
        
        # CO2 intensity
        if total_gen > 0:
            co2_intensity = (total_co2 * 1000) / (total_gen * 1000)  # tCO2/MWh
            logger.info(f"💨 CO2 intensity: {co2_intensity:.4f} tCO2/MWh")
        
        return {
            'scenario': scenario_name,
            'total_generation_gwh': total_gen,
            'renewable_share_pct': renewable_share,
            'fossil_share_pct': fossil_share,
            'total_co2_mtco2': total_co2/1000,
            'co2_intensity_tco2_mwh': co2_intensity if total_gen > 0 else 0,
            'target_01pct_mtco2': target_01pct,
            'target_02pct_mtco2': target_02pct,
            'achievement': achievement
        }
    else:
        logger.error("No generator data found in network")
        return None

def main():
    """Main function to analyze scenario 5 and existing scenarios."""
    
    logger.info("=" * 80)
    logger.info("PYPSA SCENARIO 5 VERIFICATION: NEAR-ZERO CO2 EMISSIONS")
    logger.info("=" * 80)
    
    # Try to analyze existing scenarios and any new scenario 5
    scenarios_to_check = [
        ("CO2 Pricing", "results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_co2_pricing.nc"),
        ("Scenario 1", "results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_scenario1_250co2.nc"),
        ("Scenario 2", "results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_scenario2_300co2.nc"),
        ("Scenario 3", "results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_scenario3_500co2.nc"),
        ("Scenario 4", "results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_scenario4_900co2.nc"),
    ]
    
    # Look for potential scenario 5 outputs
    import os
    potential_scenario5_paths = [
        "results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_scenario5_0co2.nc",
        "results/de-all-tech-2035-mayk/networks/base_s_1_elec_2035.nc",
        "resources/de-all-tech-2035-mayk/networks/base_s_1_elec.nc"  # Latest built network
    ]
    
    for path in potential_scenario5_paths:
        if os.path.exists(path):
            scenarios_to_check.append(("Scenario 5 (New)", path))
            break
    
    results = []
    
    for scenario_name, path in scenarios_to_check:
        if os.path.exists(path):
            try:
                result = calculate_co2_emissions(path, scenario_name)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing {scenario_name}: {e}")
        else:
            logger.warning(f"Network file not found: {path}")
    
    # Summary comparison
    if results:
        logger.info("\n" + "=" * 80)
        logger.info("SCENARIO COMPARISON SUMMARY")
        logger.info("=" * 80)
        
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('total_co2_mtco2')
        
        logger.info(f"{'Scenario':15} {'CO2 (Mt)':>10} {'Renewable%':>12} {'Achievement':>25}")
        logger.info("-" * 70)
        
        for _, row in results_df.iterrows():
            logger.info(f"{row['scenario']:15} {row['total_co2_mtco2']:>10.3f} {row['renewable_share_pct']:>12.1f} {row['achievement']:>25}")
        
        # Find the best performer
        best_scenario = results_df.iloc[0]
        logger.info(f"\n🏆 BEST PERFORMER: {best_scenario['scenario']}")
        logger.info(f"   CO2 emissions: {best_scenario['total_co2_mtco2']:.3f} MtCO2")
        logger.info(f"   Renewable share: {best_scenario['renewable_share_pct']:.1f}%")
        
        if best_scenario['total_co2_mtco2'] <= 0.001487:  # 0.1% of 1990
            logger.info("✅ NEAR-ZERO EMISSIONS ACHIEVED!")
        else:
            remaining = best_scenario['total_co2_mtco2'] - 0.001487
            logger.info(f"⚠️  Still {remaining:.3f} MtCO2 above 0.1% target")

if __name__ == "__main__":
    main()
