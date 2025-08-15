#!/usr/bin/env python3

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def theoretical_optimization_analysis():
    """
    Theoretical analysis of how realistic hydrogen costs would change the optimization
    """
    print("🔬 THEORETICAL OPTIMIZATION WITH REALISTIC HYDROGEN COSTS")
    print("=" * 70)
    
    # Load original optimized results
    storage_df = pd.read_csv("germany_2035_storage_details.csv")
    
    print("📊 ORIGINAL SYSTEM (PyPSA Optimized Costs):")
    print("-" * 50)
    for idx, row in storage_df.iterrows():
        print(f"  {row['technology']:15s}: {row['power_gw']:6.1f} GW, {row['energy_gwh']:8.1f} GWh")
    
    # Technology costs per kWh
    tech_costs = {
        'H2 Store': 5.00,           # €5.00/kWh (realistic)
        'battery': 0.132,           # €0.132/kWh 
        'home battery': 0.132,      # €0.132/kWh
        'PHS': 0.020,              # €0.020/kWh (pumped hydro)
        'IronAir': 0.027           # €0.027/kWh (Iron-Air)
    }
    
    # Technology power costs per kW
    power_costs = {
        'H2 Store': 1510,          # €1510/kW (fuel cell)
        'battery': 132,            # €132/kW
        'home battery': 132,       # €132/kW  
        'PHS': 2.0,               # €2/kW (pumped hydro)
        'IronAir': 84             # €84/kW (Iron-Air)
    }
    
    # Calculate costs for original system
    print("\n💰 COST ANALYSIS WITH REALISTIC PRICES:")
    print("-" * 50)
    
    total_original_cost = 0
    tech_costs_breakdown = {}
    
    for idx, row in storage_df.iterrows():
        tech = row['technology']
        energy_gwh = row['energy_gwh']
        power_gw = row['power_gw']
        
        if tech == 'H2 Store':
            cost_key = 'H2 Store'
        elif 'battery' in tech.lower():
            cost_key = 'battery'
        elif tech == 'PHS':
            cost_key = 'PHS'
        else:
            cost_key = 'battery'  # default
        
        # Calculate costs (energy + power)
        energy_cost = energy_gwh * 1000 * tech_costs[cost_key] / 1000  # Million EUR
        power_cost = power_gw * 1000 * power_costs[cost_key] / 1000   # Million EUR
        total_cost = energy_cost + power_cost
        
        tech_costs_breakdown[tech] = {
            'energy_cost_meur': energy_cost,
            'power_cost_meur': power_cost,
            'total_cost_meur': total_cost,
            'energy_gwh': energy_gwh,
            'power_gw': power_gw
        }
        
        total_original_cost += total_cost
        
        print(f"  {tech:15s}: {total_cost:8.0f} million EUR (E: {energy_cost:6.0f} + P: {power_cost:6.0f})")
    
    print(f"\n  TOTAL STORAGE:   {total_original_cost:8.0f} million EUR ({total_original_cost/1000:.1f} billion EUR)")
    
    # Now calculate optimal allocation with realistic costs
    print("\n🎯 THEORETICAL OPTIMAL ALLOCATION (Realistic Costs):")
    print("-" * 50)
    
    # Target storage energy (same as original)
    target_energy_gwh = storage_df['energy_gwh'].sum()
    print(f"Target storage energy: {target_energy_gwh:.1f} GWh")
    
    # Sort technologies by cost efficiency (EUR/kWh)
    cost_ranking = [
        ('PHS', tech_costs['PHS'], 'Pumped Hydro'),
        ('IronAir', tech_costs['IronAir'], 'Iron-Air Battery'),
        ('battery', tech_costs['battery'], 'Li-ion Battery'),
        ('H2 Store', tech_costs['H2 Store'], 'Hydrogen Storage')
    ]
    
    # Realistic constraints
    max_phs_gwh = 50      # Limited by geography
    max_ironair_gwh = 20000  # Large potential for long-duration
    max_battery_gwh = 2000   # Limited by duration/economics
    
    print("\nCost-optimal allocation strategy:")
    optimal_allocation = []
    remaining_energy = target_energy_gwh
    
    # 1. Use cheapest (PHS) first
    phs_allocation = min(max_phs_gwh, remaining_energy)
    if phs_allocation > 0:
        optimal_allocation.append(('PHS', phs_allocation, tech_costs['PHS']))
        remaining_energy -= phs_allocation
        print(f"  1. PHS:           {phs_allocation:8.1f} GWh @ €{tech_costs['PHS']:.3f}/kWh")
    
    # 2. Use Iron-Air for long-duration
    ironair_allocation = min(max_ironair_gwh, remaining_energy)
    if ironair_allocation > 0:
        optimal_allocation.append(('Iron-Air', ironair_allocation, tech_costs['IronAir']))
        remaining_energy -= ironair_allocation
        print(f"  2. Iron-Air:      {ironair_allocation:8.1f} GWh @ €{tech_costs['IronAir']:.3f}/kWh")
    
    # 3. Use batteries for remaining short-duration
    battery_allocation = min(max_battery_gwh, remaining_energy)
    if battery_allocation > 0:
        optimal_allocation.append(('Battery', battery_allocation, tech_costs['battery']))
        remaining_energy -= battery_allocation
        print(f"  3. Battery:       {battery_allocation:8.1f} GWh @ €{tech_costs['battery']:.3f}/kWh")
    
    # 4. Any remaining would need hydrogen (very expensive)
    if remaining_energy > 0:
        optimal_allocation.append(('H2 Store', remaining_energy, tech_costs['H2 Store']))
        print(f"  4. H2 Storage:    {remaining_energy:8.1f} GWh @ €{tech_costs['H2 Store']:.3f}/kWh")
    
    # Calculate optimal costs
    optimal_total_cost = 0
    print(f"\nOptimal cost breakdown:")
    
    for tech, energy_gwh, cost_per_kwh in optimal_allocation:
        # Estimate power requirements (duration-based)
        if tech == 'PHS':
            duration_hours = 6
            power_cost_per_kw = power_costs['PHS']
        elif tech == 'Iron-Air':
            duration_hours = 100
            power_cost_per_kw = power_costs['IronAir']
        elif tech == 'Battery':
            duration_hours = 4
            power_cost_per_kw = power_costs['battery']
        else:  # H2
            duration_hours = 400
            power_cost_per_kw = power_costs['H2 Store']
        
        power_gw = energy_gwh / duration_hours * 1000 / 1000  # Convert to GW
        
        energy_cost = energy_gwh * 1000 * cost_per_kwh / 1000  # Million EUR
        power_cost = power_gw * 1000 * power_cost_per_kw / 1000  # Million EUR
        total_cost = energy_cost + power_cost
        
        optimal_total_cost += total_cost
        
        print(f"  {tech:12s}: {total_cost:8.0f} million EUR ({energy_gwh:6.0f} GWh, {power_gw:5.1f} GW)")
    
    print(f"\n  OPTIMAL TOTAL:   {optimal_total_cost:8.0f} million EUR ({optimal_total_cost/1000:.1f} billion EUR)")
    
    # Comparison
    cost_savings = total_original_cost - optimal_total_cost
    savings_percent = (cost_savings / total_original_cost) * 100
    
    print(f"\n📈 ECONOMIC IMPACT COMPARISON:")
    print("-" * 50)
    print(f"Original H2-dominated system:  {total_original_cost/1000:6.1f} billion EUR")
    print(f"Optimal realistic-cost system: {optimal_total_cost/1000:6.1f} billion EUR")
    print(f"COST SAVINGS:                  {cost_savings/1000:6.1f} billion EUR ({savings_percent:.1f}%)")
    
    # Technology mix comparison
    print(f"\n🔄 TECHNOLOGY MIX COMPARISON:")
    print("-" * 50)
    print("Original system (H2-dominated):")
    h2_share = tech_costs_breakdown['H2 Store']['energy_gwh'] / target_energy_gwh * 100
    print(f"  H2 Storage:     {tech_costs_breakdown['H2 Store']['energy_gwh']:7.1f} GWh ({h2_share:.1f}%)")
    print(f"  Other storage:  {target_energy_gwh - tech_costs_breakdown['H2 Store']['energy_gwh']:7.1f} GWh ({100-h2_share:.1f}%)")
    
    print("\nOptimal system (cost-efficient):")
    for tech, energy_gwh, _ in optimal_allocation:
        share = energy_gwh / target_energy_gwh * 100
        print(f"  {tech:12s}: {energy_gwh:7.1f} GWh ({share:5.1f}%)")
    
    # Key insights
    print(f"\n🎯 KEY INSIGHTS:")
    print("-" * 50)
    print(f"1. With realistic costs, hydrogen storage becomes prohibitively expensive")
    print(f"2. Iron-Air batteries emerge as the optimal long-duration storage solution")
    print(f"3. Total system cost could be reduced by {savings_percent:.0f}% with realistic technology mix")
    print(f"4. Hydrogen would only be used if absolutely necessary (>22 TWh storage needed)")
    print(f"5. The PyPSA model's H2-dominated solution reflects unrealistic cost assumptions")
    
    return {
        'original_cost_billion': total_original_cost/1000,
        'optimal_cost_billion': optimal_total_cost/1000,
        'savings_billion': cost_savings/1000,
        'savings_percent': savings_percent,
        'optimal_allocation': optimal_allocation
    }

if __name__ == "__main__":
    results = theoretical_optimization_analysis()
    print(f"\n✅ Analysis complete!")
    print(f"Potential savings: €{results['savings_billion']:.1f} billion ({results['savings_percent']:.0f}%)")
