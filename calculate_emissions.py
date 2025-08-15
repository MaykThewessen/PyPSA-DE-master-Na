#!/usr/bin/env python3
"""
CO2 Emissions Calculator for PyPSA Results
==========================================

This script calculates CO2 emissions from the solved PyPSA network
"""

import pypsa
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

def load_network(specific_path=None):
    """Load the solved PyPSA network"""
    if specific_path:
        try:
            print(f"Loading: {specific_path}")
            n = pypsa.Network(specific_path)
            print(f"Successfully loaded network from: {specific_path}")
            return n
        except FileNotFoundError:
            print(f"Network file not found at {specific_path}")
            return None
    
    # Try multiple possible network files in order of preference
    network_paths = [
        "results/networks/base_s_1_elec_Co2L0.001.nc",
        "results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_co2_pricing.nc",
        "results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_scenario1_250co2.nc"
    ]
    
    for network_path in network_paths:
        try:
            print(f"Trying to load: {network_path}")
            n = pypsa.Network(network_path)
            print(f"Successfully loaded network from: {network_path}")
            return n
        except FileNotFoundError:
            print(f"Network file not found at {network_path}")
            continue
    
    print("No network files found in any of the expected locations.")
    return None

def calculate_co2_emissions(n):
    """Calculate CO2 emissions from generation"""
    print("="*60)
    print("CO2 EMISSIONS ANALYSIS")
    print("="*60)
    
    # CO2 emission factors (kg CO2/MWh_th) - thermal energy input
    co2_factors = {
        'lignite': 1054,  # kg CO2/MWh_th
        'coal': 820,      # kg CO2/MWh_th
        'oil': 736,       # kg CO2/MWh_th
        'CCGT': 490,      # kg CO2/MWh_th (natural gas)
        'OCGT': 490,      # kg CO2/MWh_th (natural gas)
        'nuclear': 0,     # No direct emissions
        'biomass': 0,     # Considered CO2 neutral
        'solar': 0,       # No emissions
        'solar-hsat': 0,  # No emissions
        'onwind': 0,      # No emissions
        'offwind-ac': 0,  # No emissions
        'offwind-dc': 0,  # No emissions
        'offwind-float': 0, # No emissions
        'hydro': 0,       # No emissions
        'ror': 0,         # No emissions
    }
    
    total_co2 = 0
    co2_by_carrier = {}
    
    print("\nCO2 Emissions by Technology:")
    print("-" * 50)
    
    for carrier in n.generators.carrier.unique():
        if carrier in co2_factors:
            # Get generators of this carrier
            carrier_gens = n.generators[n.generators.carrier == carrier]
            
            if len(carrier_gens) > 0 and co2_factors[carrier] > 0:
                # Get total generation for this carrier (MWh_el)
                total_gen_el = n.generators_t.p[carrier_gens.index].sum().sum()
                
                # Convert to thermal energy using efficiency
                efficiency = carrier_gens.efficiency.iloc[0] if len(carrier_gens) > 0 else 0.4
                total_gen_th = total_gen_el / efficiency if efficiency > 0 else total_gen_el
                
                # Calculate CO2 emissions (kg CO2)
                co2_emissions_kg = total_gen_th * co2_factors[carrier]
                co2_emissions_mt = co2_emissions_kg / 1e9  # Convert to Mt CO2
                
                co2_by_carrier[carrier] = co2_emissions_mt
                total_co2 += co2_emissions_mt
                
                print(f"{carrier:15s}: {co2_emissions_mt:8.2f} Mt CO2")
            else:
                co2_by_carrier[carrier] = 0
                if carrier in ['lignite', 'coal', 'oil', 'CCGT', 'OCGT']:
                    total_gen = n.generators_t.p[carrier_gens.index].sum().sum() if len(carrier_gens) > 0 else 0
                    print(f"{carrier:15s}: {0:8.2f} Mt CO2 (Generation: {total_gen:.1f} MWh)")
    
    print("-" * 50)
    print(f"{'TOTAL':15s}: {total_co2:8.2f} Mt CO2")
    
    # Check constraint
    print(f"\nCO2 Constraint Check:")
    print(f"- Total CO2 emissions: {total_co2:.2f} Mt")
    print(f"- CO2 limit configured: 0.0 Mt")
    if total_co2 > 0.01:  # Allow for small numerical errors
        print("❌ CO2 CONSTRAINT VIOLATED!")
        print("   The model did not achieve zero emissions.")
    else:
        print("✅ CO2 CONSTRAINT SATISFIED")
        print("   Zero emissions achieved.")
    
    return co2_by_carrier, total_co2

def check_co2_constraint_in_model(n):
    """Check if CO2 constraints are actually in the model"""
    print("\n" + "="*60)
    print("MODEL CONSTRAINT ANALYSIS")
    print("="*60)
    
    # Check if carriers have CO2 data
    print(f"\nCarriers in network: {len(n.carriers)}")
    if hasattr(n.carriers, 'co2_emissions'):
        print("\nCO2 emissions data in carriers:")
        for carrier, co2 in n.carriers.co2_emissions.items():
            if co2 != 0:
                print(f"  {carrier}: {co2} t CO2/MWh_th")
        
        if n.carriers.co2_emissions.sum() == 0:
            print("⚠️  WARNING: All carriers have zero CO2 emissions!")
            print("   This suggests CO2 data might not be loaded correctly.")
    else:
        print("⚠️  WARNING: No CO2 emissions data found in carriers!")
        print("   CO2 constraints cannot work without emission factors.")
    
    # Check if there are any CO2 related constraints
    constraints_info = []
    if hasattr(n, '_constraints'):
        for name, constraint in n._constraints.items():
            if 'co2' in name.lower() or 'emission' in name.lower():
                constraints_info.append(name)
    
    if constraints_info:
        print(f"\nCO2-related constraints found: {constraints_info}")
    else:
        print(f"\n⚠️  No CO2-related constraints found in the model!")

def main():
    """Main analysis function"""
    print("PyPSA CO2 Emissions Analysis")
    print("="*60)
    
    # Load network
    n = load_network()
    if n is None:
        return
    
    # Calculate emissions
    co2_by_carrier, total_co2 = calculate_co2_emissions(n)
    
    # Check model constraints
    check_co2_constraint_in_model(n)
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total CO2 emissions: {total_co2:.2f} Mt CO2/year")
    if total_co2 > 0.01:
        print("❌ ZERO EMISSIONS TARGET NOT MET")
        print("\nPossible issues:")
        print("1. CO2 emission factors not loaded correctly")
        print("2. CO2 constraint not properly enforced")
        print("3. Model configuration error")
    else:
        print("✅ ZERO EMISSIONS TARGET ACHIEVED")

if __name__ == "__main__":
    main()
