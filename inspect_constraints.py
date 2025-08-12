#!/usr/bin/env python3
"""
PyPSA Network Constraint Inspector
=================================

This script inspects the constraints and global constraints in the PyPSA network
"""

import pypsa
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

def inspect_network_constraints():
    """Inspect constraints in the PyPSA network"""
    network_path = "results/networks/base_s_1_elec_Co2L0.001.nc"
    print(f"Loading network from: {network_path}")
    
    try:
        n = pypsa.Network(network_path)
        print(f"Network loaded successfully!")
        
        print("\n" + "="*60)
        print("GLOBAL CONSTRAINTS")
        print("="*60)
        
        if hasattr(n, 'global_constraints') and len(n.global_constraints) > 0:
            print(f"Found {len(n.global_constraints)} global constraints:")
            print(n.global_constraints)
            
            # Check for CO2-related constraints
            co2_constraints = n.global_constraints[n.global_constraints.index.str.contains('CO2|co2|emission', case=False)]
            if len(co2_constraints) > 0:
                print(f"\nCO2-related global constraints:")
                for idx, row in co2_constraints.iterrows():
                    print(f"  {idx}: {row['sense']} {row['constant']}")
            else:
                print("\n⚠️  No CO2-related global constraints found!")
        else:
            print("⚠️  No global constraints found in the model!")
        
        print("\n" + "="*60)
        print("CARRIERS CO2 INFORMATION")
        print("="*60)
        
        if hasattr(n.carriers, 'co2_emissions'):
            co2_carriers = n.carriers[n.carriers.co2_emissions != 0]
            if len(co2_carriers) > 0:
                print("Carriers with CO2 emissions:")
                for carrier, data in co2_carriers.iterrows():
                    print(f"  {carrier}: {data['co2_emissions']:.4f} t CO2/MWh_th")
            else:
                print("No carriers with non-zero CO2 emissions found!")
        
        print("\n" + "="*60)
        print("GENERATION SUMMARY")
        print("="*60)
        
        # Get generation by carrier
        generation = n.generators_t.p.sum()
        generation_by_carrier = generation.groupby(n.generators.carrier).sum() / 1e3  # Convert to GWh
        
        print("Energy Production by Technology (GWh):")
        for carrier, energy in generation_by_carrier.sort_values(ascending=False).items():
            if energy > 0.1:  # Only show significant generation
                print(f"  {carrier:15s}: {energy:10.1f} GWh")
        
        print("\n" + "="*60)
        print("MODEL OBJECTIVE")
        print("="*60)
        print(f"Objective value: €{n.objective/1e9:.2f} billion")
        
        print("\n" + "="*60)
        print("DIAGNOSTIC")
        print("="*60)
        
        # Check if this is actually a CO2-constrained solution
        fossil_generation = 0
        for carrier in ['coal', 'lignite', 'CCGT', 'OCGT', 'oil']:
            if carrier in generation_by_carrier:
                fossil_generation += generation_by_carrier[carrier]
        
        print(f"Total fossil fuel generation: {fossil_generation:.1f} GWh")
        
        if fossil_generation > 1000:  # Significant fossil generation
            print("❌ HIGH FOSSIL FUEL USAGE - CO2 constraint likely NOT active")
        else:
            print("✅ LOW FOSSIL FUEL USAGE - CO2 constraint likely active")
            
    except FileNotFoundError:
        print(f"Network file not found at {network_path}")
    except Exception as e:
        print(f"Error loading network: {e}")

if __name__ == "__main__":
    inspect_network_constraints()
