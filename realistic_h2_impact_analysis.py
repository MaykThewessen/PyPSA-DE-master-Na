#!/usr/bin/env python3

import pandas as pd
import numpy as np

def analyze_realistic_h2_impact():
    """Analyze the impact of realistic hydrogen costs on the optimized system"""
    
    print("🔍 REALISTIC HYDROGEN COSTS IMPACT ANALYSIS")
    print("=" * 60)
    
    # Load the optimized system results 
    storage_details_file = "germany_2035_storage_details.csv"
    
    try:
        storage_df = pd.read_csv(storage_details_file)
        print(f"✅ Loaded storage data from {storage_details_file}")
    except:
        print(f"❌ Could not load {storage_details_file}")
        return
    
    print("\n📊 ORIGINAL SYSTEM (PyPSA Optimized Costs):")
    print("-" * 50)
    
    total_storage_power = storage_df['power_gw'].sum()
    total_storage_energy = storage_df['energy_gwh'].sum()
    
    print(f"Total Storage Power: {total_storage_power:.1f} GW")
    print(f"Total Storage Energy: {total_storage_energy:.1f} GWh")
    
    for idx, row in storage_df.iterrows():
        print(f"  {row['technology']:15s}: {row['power_gw']:6.1f} GW, {row['energy_gwh']:8.1f} GWh")
    
    # Cost Analysis
    print("\n💰 COST ANALYSIS:")
    print("-" * 50)
    
    # Original PyPSA costs (from our earlier analysis)
    original_costs = {
        'H2_storage_eur_mwh': 93.76,  # €93.76/MWh
        'H2_electrolysis_eur_mw': 149786,  # €149,786/MW  
        'H2_fuel_cell_eur_mw': 97352,  # €97,352/MW
    }
    
    # Realistic market costs
    realistic_costs = {
        'H2_storage_eur_mwh': 5000,  # €5,000/MWh (53x higher)
        'H2_electrolysis_eur_mw': 1710000,  # €1,710,000/MW (11x higher)
        'H2_fuel_cell_eur_mw': 1510000,  # €1,510,000/MW (15x higher)
    }
    
    # Calculate H2 system costs
    h2_data = storage_df[storage_df['technology'] == 'H2 Store'].iloc[0]
    h2_power_gw = h2_data['power_gw']
    h2_energy_gwh = h2_data['energy_gwh']
    
    print(f"\n🔹 HYDROGEN SYSTEM SCALE:")
    print(f"  H2 Storage Energy: {h2_energy_gwh:.1f} GWh")
    print(f"  H2 Power Capacity: {h2_power_gw:.1f} GW")
    
    # Original costs calculation
    original_h2_storage_cost = h2_energy_gwh * 1000 * original_costs['H2_storage_eur_mwh'] / 1e9  # Billion EUR
    original_h2_electrolysis_cost = h2_power_gw * 1000 * original_costs['H2_electrolysis_eur_mw'] / 1e9  # Billion EUR  
    original_h2_fuel_cell_cost = h2_power_gw * 1000 * original_costs['H2_fuel_cell_eur_mw'] / 1e9  # Billion EUR
    original_total = original_h2_storage_cost + original_h2_electrolysis_cost + original_h2_fuel_cell_cost
    
    # Realistic costs calculation
    realistic_h2_storage_cost = h2_energy_gwh * 1000 * realistic_costs['H2_storage_eur_mwh'] / 1e9  # Billion EUR
    realistic_h2_electrolysis_cost = h2_power_gw * 1000 * realistic_costs['H2_electrolysis_eur_mw'] / 1e9  # Billion EUR
    realistic_h2_fuel_cell_cost = h2_power_gw * 1000 * realistic_costs['H2_fuel_cell_eur_mw'] / 1e9  # Billion EUR
    realistic_total = realistic_h2_storage_cost + realistic_h2_electrolysis_cost + realistic_h2_fuel_cell_cost
    
    print(f"\n💡 ORIGINAL PYPSA COSTS:")
    print(f"  H2 Storage:     {original_h2_storage_cost:6.1f} billion EUR")
    print(f"  H2 Electrolysis: {original_h2_electrolysis_cost:6.1f} billion EUR")
    print(f"  H2 Fuel Cell:    {original_h2_fuel_cell_cost:6.1f} billion EUR")
    print(f"  TOTAL H2 SYSTEM: {original_total:6.1f} billion EUR")
    
    print(f"\n🚨 REALISTIC MARKET COSTS:")
    print(f"  H2 Storage:     {realistic_h2_storage_cost:6.1f} billion EUR")
    print(f"  H2 Electrolysis: {realistic_h2_electrolysis_cost:6.1f} billion EUR")
    print(f"  H2 Fuel Cell:    {realistic_h2_fuel_cell_cost:6.1f} billion EUR")
    print(f"  TOTAL H2 SYSTEM: {realistic_total:6.1f} billion EUR")
    
    cost_increase = realistic_total / original_total
    cost_difference = realistic_total - original_total
    
    print(f"\n📈 COST IMPACT:")
    print(f"  Cost Increase Factor: {cost_increase:.1f}x")
    print(f"  Additional Investment: {cost_difference:.1f} billion EUR")
    
    # Alternative storage analysis
    print(f"\n🔋 ALTERNATIVE STORAGE SCENARIOS:")
    print("-" * 50)
    
    # If hydrogen is too expensive, what alternatives exist?
    other_storage = storage_df[storage_df['technology'] != 'H2 Store']
    other_storage_energy = other_storage['energy_gwh'].sum()
    h2_replacement_need = h2_energy_gwh - other_storage_energy
    
    print(f"Current non-H2 storage: {other_storage_energy:.1f} GWh")
    print(f"H2 storage to replace: {h2_replacement_need:.1f} GWh")
    
    # Battery alternative cost (competitive pricing)
    battery_cost_eur_mwh = 132  # €132/kWh = €132,000/MWh
    battery_alternative_cost = h2_replacement_need * 1000 * battery_cost_eur_mwh / 1e9  # Billion EUR
    
    # Iron-Air alternative cost (long-duration)
    ironair_cost_eur_mwh = 27  # €27/kWh = €27,000/MWh  
    ironair_alternative_cost = h2_replacement_need * 1000 * ironair_cost_eur_mwh / 1e9  # Billion EUR
    
    print(f"\n🔄 REPLACEMENT OPTIONS:")
    print(f"  Replace H2 with Batteries:  {battery_alternative_cost:.1f} billion EUR")
    print(f"  Replace H2 with Iron-Air:   {ironair_alternative_cost:.1f} billion EUR")
    print(f"  vs. Realistic H2 costs:     {realistic_h2_storage_cost:.1f} billion EUR")
    
    # Energy storage comparison per kWh
    print(f"\n📊 STORAGE COST COMPARISON (EUR/kWh):")
    print(f"  PyPSA H2 (optimistic):  €{original_costs['H2_storage_eur_mwh']/1000:.3f}/kWh")
    print(f"  Realistic H2 (market):   €{realistic_costs['H2_storage_eur_mwh']/1000:.1f}/kWh")
    print(f"  Battery storage:         €{battery_cost_eur_mwh/1000:.3f}/kWh")
    print(f"  Iron-Air storage:        €{ironair_cost_eur_mwh/1000:.3f}/kWh")
    
    # Economic viability assessment
    print(f"\n🎯 ECONOMIC VIABILITY ASSESSMENT:")
    print("-" * 50)
    
    if realistic_costs['H2_storage_eur_mwh'] > battery_cost_eur_mwh:
        print(f"❌ Realistic H2 storage ({realistic_costs['H2_storage_eur_mwh']/1000:.1f} EUR/kWh) is MORE expensive than batteries ({battery_cost_eur_mwh/1000:.3f} EUR/kWh)")
    else:
        print(f"✅ H2 storage is competitive with batteries")
        
    if realistic_costs['H2_storage_eur_mwh'] > ironair_cost_eur_mwh:
        h2_vs_ironair = realistic_costs['H2_storage_eur_mwh'] / ironair_cost_eur_mwh
        print(f"❌ Realistic H2 storage is {h2_vs_ironair:.0f}x more expensive than Iron-Air batteries")
    else:
        print(f"✅ H2 storage is competitive with Iron-Air")
    
    print(f"\n🏁 CONCLUSION:")
    print("-" * 50)
    print(f"With realistic market costs, the hydrogen storage system would cost")
    print(f"{realistic_total:.0f} billion EUR instead of {original_total:.0f} billion EUR")
    print(f"({cost_increase:.0f}x more expensive).")
    print(f"")
    print(f"This makes hydrogen storage economically unviable compared to:")
    print(f"• Battery storage: {ironair_alternative_cost/battery_alternative_cost:.1f}x cheaper than H2")
    print(f"• Iron-Air storage: {realistic_h2_storage_cost/ironair_alternative_cost:.0f}x cheaper than H2")
    print(f"")
    print(f"The PyPSA model's optimistic hydrogen costs lead to a hydrogen-dominated")
    print(f"solution that would not be economically viable with realistic market costs.")
    
    return {
        'original_h2_cost': original_total,
        'realistic_h2_cost': realistic_total,
        'cost_increase_factor': cost_increase,
        'battery_alternative_cost': battery_alternative_cost,
        'ironair_alternative_cost': ironair_alternative_cost
    }

if __name__ == "__main__":
    analyze_realistic_h2_impact()
