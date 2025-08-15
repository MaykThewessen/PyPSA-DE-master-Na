#!/usr/bin/env python3
"""
Quick emissions check for all available scenarios
"""

import pypsa
import glob
import warnings
warnings.filterwarnings('ignore')

def quick_emissions_check(network_path):
    """Quick CO2 emissions calculation"""
    try:
        n = pypsa.Network(network_path)
        
        # CO2 emission factors (kg CO2/MWh_th)
        co2_factors = {
            'lignite': 1054, 'coal': 820, 'oil': 736,
            'CCGT': 490, 'OCGT': 490
        }
        
        total_co2 = 0
        for carrier in n.generators.carrier.unique():
            if carrier in co2_factors and co2_factors[carrier] > 0:
                carrier_gens = n.generators[n.generators.carrier == carrier]
                if len(carrier_gens) > 0:
                    total_gen_el = n.generators_t.p[carrier_gens.index].sum().sum()
                    efficiency = carrier_gens.efficiency.iloc[0] if len(carrier_gens) > 0 else 0.4
                    total_gen_th = total_gen_el / efficiency if efficiency > 0 else total_gen_el
                    co2_emissions_kg = total_gen_th * co2_factors[carrier]
                    total_co2 += co2_emissions_kg / 1e9  # Convert to Mt CO2
        
        return total_co2
    
    except Exception as e:
        return f"Error: {e}"

# Check all network files
network_files = [
    "results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_co2_pricing.nc",
    "results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_scenario1_250co2.nc",
    "results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_scenario2_300co2.nc",
    "results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_scenario3_500co2.nc",
    "results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_scenario4_900co2.nc"
]

print("Quick CO2 Emissions Check for All Scenarios")
print("=" * 60)

for i, path in enumerate(network_files):
    filename = path.split('/')[-1]
    emissions = quick_emissions_check(path)
    print(f"{filename:50s}: {emissions:>8.2f} Mt CO2" if isinstance(emissions, float) else f"{filename:50s}: {emissions}")

print("\n" + "=" * 60)
print("The scenario with the lowest emissions should be selected for zero emissions verification.")
