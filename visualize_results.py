#!/usr/bin/env python3
"""
Simple PyPSA Results Visualization Script
=========================================

This script loads the solved PyPSA-Eur network and creates visualizations
"""

import pypsa
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

# Style settings
plt.style.use('bmh')

def load_network():
    """Load the solved PyPSA network"""
    network_path = "results/networks/base_s_1_elec_Co2L0.001.nc"
    print(f"Loading network from: {network_path}")
    
    try:
        n = pypsa.Network(network_path)
        print(f"Network loaded successfully!")
        print(f"Network has {len(n.buses)} buses, {len(n.generators)} generators")
        return n
    except FileNotFoundError:
        print(f"Network file not found at {network_path}")
        return None

def analyze_generation_capacity(n):
    """Analyze generation capacity by technology"""
    print("\n" + "="*50)
    print("GENERATION CAPACITY ANALYSIS")
    print("="*50)
    
    # Get capacity by generator type
    capacity_by_carrier = n.generators.groupby('carrier')['p_nom_opt'].sum() / 1e3  # Convert to GW
    
    print("\nInstalled Capacity by Technology (GW):")
    print("-" * 40)
    for carrier, capacity in capacity_by_carrier.sort_values(ascending=False).items():
        print(f"{carrier:15s}: {capacity:8.2f} GW")
    
    total_capacity = capacity_by_carrier.sum()
    print(f"{'Total':15s}: {total_capacity:8.2f} GW")
    
    return capacity_by_carrier

def analyze_energy_production(n):
    """Analyze energy production by technology"""
    print("\n" + "="*50)
    print("ENERGY PRODUCTION ANALYSIS")
    print("="*50)
    
    # Get energy production by carrier
    generation = n.generators_t.p.sum()
    generation_by_carrier = generation.groupby(n.generators.carrier).sum() / 1e3  # Convert to GWh
    
    print("\nEnergy Production by Technology (GWh):")
    print("-" * 40)
    for carrier, energy in generation_by_carrier.sort_values(ascending=False).items():
        print(f"{carrier:15s}: {energy:10.1f} GWh")
    
    total_energy = generation_by_carrier.sum()
    print(f"{'Total':15s}: {total_energy:10.1f} GWh")
    
    return generation_by_carrier

def calculate_capacity_factors(n):
    """Calculate capacity factors by technology"""
    print("\n" + "="*50)
    print("CAPACITY FACTOR ANALYSIS")
    print("="*50)
    
    capacity_factors = {}
    
    for carrier in n.generators.carrier.unique():
        carrier_gens = n.generators[n.generators.carrier == carrier]
        if len(carrier_gens) > 0:
            total_capacity = carrier_gens.p_nom_opt.sum()
            if total_capacity > 0:
                total_generation = n.generators_t.p[carrier_gens.index].sum().sum()
                hours_in_year = len(n.snapshots)
                max_possible = total_capacity * hours_in_year
                cf = total_generation / max_possible if max_possible > 0 else 0
                capacity_factors[carrier] = cf
    
    print("\nCapacity Factors by Technology:")
    print("-" * 40)
    for carrier, cf in sorted(capacity_factors.items(), key=lambda x: x[1], reverse=True):
        print(f"{carrier:15s}: {cf:8.1%}")
    
    return capacity_factors

def analyze_system_costs(n):
    """Analyze system costs"""
    print("\n" + "="*50)
    print("SYSTEM COST ANALYSIS")
    print("="*50)
    
    # Calculate total system cost (objective value)
    total_cost = n.objective / 1e9  # Convert to billion €
    print(f"\nTotal System Cost: €{total_cost:.2f} billion")
    
    # Calculate costs by component if possible
    try:
        # Generator costs
        gen_costs = {}
        for carrier in n.generators.carrier.unique():
            carrier_gens = n.generators[n.generators.carrier == carrier]
            if len(carrier_gens) > 0:
                # Capital costs
                capital_cost = (carrier_gens.p_nom_opt * carrier_gens.capital_cost).sum() / 1e6
                # Marginal costs 
                if carrier in n.generators_t.p.columns:
                    marginal_cost = (n.generators_t.p[carrier_gens.index].sum() * 
                                   carrier_gens.marginal_cost).sum().sum() / 1e6
                else:
                    marginal_cost = 0
                
                total_carrier_cost = capital_cost + marginal_cost
                if total_carrier_cost > 0:
                    gen_costs[carrier] = total_carrier_cost
        
        if gen_costs:
            print("\nCosts by Technology (Million €):")
            print("-" * 40)
            for carrier, cost in sorted(gen_costs.items(), key=lambda x: x[1], reverse=True):
                print(f"{carrier:15s}: €{cost:8.1f}M")
        
    except Exception as e:
        print(f"Detailed cost analysis not available: {e}")

def create_visualizations(n, capacity_by_carrier, generation_by_carrier, capacity_factors):
    """Create visualizations"""
    print("\n" + "="*50)
    print("CREATING VISUALIZATIONS")
    print("="*50)
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('PyPSA-Eur Results Analysis', fontsize=16, fontweight='bold')
    
    # 1. Capacity pie chart
    ax1 = axes[0, 0]
    capacity_by_carrier.plot(kind='pie', ax=ax1, autopct='%1.1f%%')
    ax1.set_title('Installed Capacity by Technology')
    ax1.set_ylabel('')
    
    # 2. Generation bar chart  
    ax2 = axes[0, 1]
    generation_by_carrier.plot(kind='bar', ax=ax2, color='steelblue')
    ax2.set_title('Energy Production by Technology')
    ax2.set_ylabel('Energy Production (GWh)')
    ax2.tick_params(axis='x', rotation=45)
    
    # 3. Capacity factors
    ax3 = axes[1, 0]
    cf_series = pd.Series(capacity_factors)
    cf_series.plot(kind='bar', ax=ax3, color='forestgreen')
    ax3.set_title('Capacity Factors by Technology')
    ax3.set_ylabel('Capacity Factor')
    ax3.tick_params(axis='x', rotation=45)
    ax3.set_ylim(0, 1)
    
    # 4. Generation time series (sample)
    ax4 = axes[1, 1]
    # Show first week of generation
    sample_hours = n.snapshots[:168]  # First week (168 hours)
    total_gen = n.generators_t.p.loc[sample_hours].sum(axis=1) / 1e3  # Convert to GW
    total_gen.plot(ax=ax4, color='darkred')
    ax4.set_title('Total Generation - First Week')
    ax4.set_ylabel('Generation (GW)')
    ax4.set_xlabel('Time')
    
    plt.tight_layout()
    
    # Save the plot
    output_path = 'pypsa_results_analysis.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nVisualization saved as: {output_path}")
    
    # Show the plot (if display available)
    try:
        plt.show()
    except:
        print("Display not available, but plot saved to file.")

def main():
    """Main analysis function"""
    print("PyPSA-Eur Results Analysis")
    print("=" * 50)
    
    # Load the network
    n = load_network()
    if n is None:
        print("Cannot proceed without network data.")
        return
    
    # Perform analyses
    capacity_by_carrier = analyze_generation_capacity(n)
    generation_by_carrier = analyze_energy_production(n)
    capacity_factors = calculate_capacity_factors(n)
    analyze_system_costs(n)
    
    # Create visualizations
    create_visualizations(n, capacity_by_carrier, generation_by_carrier, capacity_factors)
    
    print("\n" + "="*50)
    print("ANALYSIS COMPLETE!")
    print("="*50)
    print("Key Insights:")
    print(f"- Network optimized with {len(n.buses)} bus(es)")
    print(f"- Total capacity: {capacity_by_carrier.sum():.1f} GW")
    print(f"- Total energy: {generation_by_carrier.sum():.1f} GWh")
    print(f"- System cost: €{n.objective/1e9:.2f} billion")
    
    # Dominant technology
    dominant_tech = capacity_by_carrier.idxmax()
    dominant_share = capacity_by_carrier.max() / capacity_by_carrier.sum() * 100
    print(f"- Dominant technology: {dominant_tech} ({dominant_share:.1f}%)")

if __name__ == "__main__":
    main()
