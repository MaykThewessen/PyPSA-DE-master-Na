#!/usr/bin/env python3
"""
H2 P2G2P analysis with updated realistic cost parameters.
"""

import pypsa
import pandas as pd
import numpy as np
import os

def load_network():
    """Load the solved PyPSA network."""
    network_file = "results/de-electricity-only-2035-mayk/networks/base_s_1___2035.nc"
    if not os.path.exists(network_file):
        raise FileNotFoundError(f"Network file not found: {network_file}")
    
    print(f"Loading network from: {network_file}")
    n = pypsa.Network(network_file)
    return n

def analyze_h2_updated_costs(n):
    """Analyze H2 P2G2P with updated cost parameters."""
    
    print("=" * 70)
    print("H2 P2G2P ANALYSIS WITH UPDATED REALISTIC COST PARAMETERS")
    print("=" * 70)
    
    # Find H2 system components to get capacities and efficiencies
    h2_stores = n.stores[n.stores.carrier == 'H2 Store']
    h2_stores_opt = h2_stores[h2_stores.e_nom_opt > 0]
    
    h2_links = n.links[n.links.carrier.str.contains('H2', na=False)]
    h2_links_opt = h2_links[h2_links.p_nom_opt > 0]
    
    if h2_stores_opt.empty or h2_links_opt.empty:
        print("No H2 system components found.")
        return
    
    # === UPDATED COST PARAMETERS ===
    print("\n1. UPDATED COST PARAMETERS")
    print("-" * 45)
    
    # Updated costs (your specifications)
    h2_energy_cost_eur_kwh = 5.0  # €5/kWh
    h2_energy_cost_eur_mwh = h2_energy_cost_eur_kwh * 1000  # €5000/MWh
    elec_cost_eur_kw = 1710.0  # €1710/kW
    elec_cost_eur_mw = elec_cost_eur_kw * 1000  # €1,710,000/MW
    fc_cost_eur_kw = 1510.0  # €1510/kW
    fc_cost_eur_mw = fc_cost_eur_kw * 1000  # €1,510,000/MW
    
    print(f"UPDATED COST PARAMETERS:")
    print(f"H2 Energy Storage: {h2_energy_cost_eur_kwh:.2f} EUR/kWh = {h2_energy_cost_eur_mwh:.0f} EUR/MWh")
    print(f"H2 Electrolysis: {elec_cost_eur_kw:.0f} EUR/kW = {elec_cost_eur_mw:.0f} EUR/MW")
    print(f"H2 Fuel Cell: {fc_cost_eur_kw:.0f} EUR/kW = {fc_cost_eur_mw:.0f} EUR/MW")
    
    # Get capacities and efficiencies from optimization results
    h2_energy_mwh = h2_stores_opt['e_nom_opt'].sum()
    h2_energy_gwh = h2_energy_mwh / 1000
    h2_energy_twh = h2_energy_mwh / 1e6
    
    electrolyzer = h2_links_opt[h2_links_opt.carrier == 'H2 Electrolysis']
    fuel_cell = h2_links_opt[h2_links_opt.carrier == 'H2 Fuel Cell']
    
    elec_power_mw = electrolyzer['p_nom_opt'].iloc[0]
    elec_power_gw = elec_power_mw / 1000
    elec_efficiency = electrolyzer['efficiency'].iloc[0]
    
    fc_power_mw = fuel_cell['p_nom_opt'].iloc[0]
    fc_power_gw = fc_power_mw / 1000
    fc_efficiency = fuel_cell['efficiency'].iloc[0]
    
    print(f"\nOPTIMIZED CAPACITIES (from PyPSA):")
    print(f"H2 Energy Storage: {h2_energy_gwh:.1f} GWh = {h2_energy_twh:.2f} TWh")
    print(f"H2 Electrolysis: {elec_power_gw:.1f} GW (Efficiency: {elec_efficiency:.1%})")
    print(f"H2 Fuel Cell: {fc_power_gw:.1f} GW (Efficiency: {fc_efficiency:.1%})")
    
    # === UPDATED CAPEX CALCULATIONS ===
    print(f"\n2. UPDATED CAPEX CALCULATIONS")
    print("-" * 45)
    
    h2_storage_capex = h2_energy_mwh * h2_energy_cost_eur_mwh
    elec_capex = elec_power_mw * elec_cost_eur_mw
    fc_capex = fc_power_mw * fc_cost_eur_mw
    total_capex = h2_storage_capex + elec_capex + fc_capex
    
    print(f"H2 Storage CAPEX: {h2_storage_capex/1e9:.2f} billion EUR")
    print(f"Electrolysis CAPEX: {elec_capex/1e9:.2f} billion EUR")
    print(f"Fuel Cell CAPEX: {fc_capex/1e9:.2f} billion EUR")
    print(f"TOTAL CAPEX: {total_capex/1e9:.2f} billion EUR")
    
    print(f"\nCAPEX Share:")
    print(f"H2 Storage: {h2_storage_capex/total_capex*100:.1f}%")
    print(f"Electrolysis: {elec_capex/total_capex*100:.1f}%")
    print(f"Fuel Cell: {fc_capex/total_capex*100:.1f}%")
    
    # === ROUND-TRIP EFFICIENCY ===
    print(f"\n3. ROUND-TRIP EFFICIENCY")
    print("-" * 45)
    
    round_trip_efficiency = elec_efficiency * fc_efficiency
    energy_loss_factor = 1 - round_trip_efficiency
    
    print(f"Electrolysis Efficiency: {elec_efficiency:.1%}")
    print(f"Fuel Cell Efficiency: {fc_efficiency:.1%}")
    print(f"Round-Trip Efficiency: {round_trip_efficiency:.1%}")
    print(f"Energy Loss: {energy_loss_factor:.1%}")
    
    # === UPDATED LEVELIZED COST ANALYSIS ===
    print(f"\n4. UPDATED LEVELIZED COST ANALYSIS")
    print("-" * 45)
    
    # Assumptions for levelized cost calculation
    lifetime_years = 25  # Standard assumption
    discount_rate = 0.05  # 5% discount rate
    capacity_factor_elec = 0.3  # 30% capacity factor for electrolysis
    capacity_factor_fc = 0.15  # 15% capacity factor for fuel cell (seasonal)
    
    # Calculate annualized costs
    annuity_factor = (discount_rate * (1 + discount_rate)**lifetime_years) / ((1 + discount_rate)**lifetime_years - 1)
    
    # Storage cost per MWh stored
    storage_annual_cost = h2_storage_capex * annuity_factor
    storage_mwh_per_year = h2_energy_mwh  # Energy capacity
    storage_cost_per_mwh = storage_annual_cost / storage_mwh_per_year
    
    # Electrolysis cost per MWh H2 produced
    elec_annual_cost = elec_capex * annuity_factor
    elec_mwh_per_year = elec_power_mw * 8760 * capacity_factor_elec * elec_efficiency
    elec_cost_per_mwh_h2 = elec_annual_cost / elec_mwh_per_year
    
    # Fuel cell cost per MWh electricity produced
    fc_annual_cost = fc_capex * annuity_factor
    fc_mwh_per_year = fc_power_mw * 8760 * capacity_factor_fc
    fc_cost_per_mwh_elec = fc_annual_cost / fc_mwh_per_year
    
    print(f"Storage Cost: {storage_cost_per_mwh:.2f} EUR/MWh stored")
    print(f"Electrolysis Cost: {elec_cost_per_mwh_h2:.2f} EUR/MWh H2 produced")
    print(f"Fuel Cell Cost: {fc_cost_per_mwh_elec:.2f} EUR/MWh electricity produced")
    
    # === UPDATED P2G2P TOTAL COST ===
    print(f"\n5. UPDATED POWER-TO-GAS-TO-POWER TOTAL COST")
    print("-" * 45)
    
    # Cost to store 1 MWh of electricity and get it back
    # For 1 MWh electricity input:
    h2_energy_produced = 1.0 * elec_efficiency  # MWh H2
    electricity_recovered = h2_energy_produced * fc_efficiency  # MWh electricity
    
    # Costs per 1 MWh input electricity:
    cost_electrolysis = elec_cost_per_mwh_h2 / elec_efficiency  # Cost per MWh input
    cost_storage = storage_cost_per_mwh  # Cost per MWh H2 stored
    cost_fuel_cell = fc_cost_per_mwh_elec / fc_efficiency  # Cost per MWh H2 input
    
    total_p2g2p_cost_per_mwh_input = cost_electrolysis + cost_storage + cost_fuel_cell
    total_p2g2p_cost_per_mwh_output = total_p2g2p_cost_per_mwh_input / round_trip_efficiency
    
    print(f"\nCost breakdown for 1 MWh electricity input:")
    print(f"  Electrolysis: {cost_electrolysis:.2f} EUR/MWh")
    print(f"  Storage: {cost_storage:.2f} EUR/MWh")
    print(f"  Fuel Cell: {cost_fuel_cell:.2f} EUR/MWh")
    print(f"  Total: {total_p2g2p_cost_per_mwh_input:.2f} EUR/MWh input")
    print(f"  Energy recovered: {electricity_recovered:.3f} MWh")
    print(f"  Cost per MWh output: {total_p2g2p_cost_per_mwh_output:.2f} EUR/MWh")
    
    # === COMPARISON WITH ORIGINAL COSTS ===
    print(f"\n6. COMPARISON WITH ORIGINAL PYPSA COSTS")
    print("-" * 45)
    
    # Original costs from PyPSA
    orig_storage_cost = 93.76  # EUR/MWh
    orig_elec_cost = 149786  # EUR/MW
    orig_fc_cost = 97352  # EUR/MW
    
    # Original CAPEX
    orig_storage_capex = h2_energy_mwh * orig_storage_cost
    orig_elec_capex = elec_power_mw * orig_elec_cost
    orig_fc_capex = fc_power_mw * orig_fc_cost
    orig_total_capex = orig_storage_capex + orig_elec_capex + orig_fc_capex
    
    print(f"CAPEX COMPARISON:")
    print(f"                    Original      Updated       Change")
    print(f"H2 Storage:     {orig_storage_capex/1e9:8.2f} B€  {h2_storage_capex/1e9:8.2f} B€  {(h2_storage_capex/orig_storage_capex-1)*100:+6.1f}%")
    print(f"Electrolysis:   {orig_elec_capex/1e9:8.2f} B€  {elec_capex/1e9:8.2f} B€  {(elec_capex/orig_elec_capex-1)*100:+6.1f}%")
    print(f"Fuel Cell:      {orig_fc_capex/1e9:8.2f} B€  {fc_capex/1e9:8.2f} B€  {(fc_capex/orig_fc_capex-1)*100:+6.1f}%")
    print(f"TOTAL:          {orig_total_capex/1e9:8.2f} B€  {total_capex/1e9:8.2f} B€  {(total_capex/orig_total_capex-1)*100:+6.1f}%")
    
    # === FINAL SUMMARY ===
    print(f"\n7. UPDATED COST SUMMARY")
    print("=" * 45)
    
    print(f"Total H2 System CAPEX: {total_capex/1e9:.2f} billion EUR")
    print(f"Round-Trip Efficiency: {round_trip_efficiency:.1%}")
    print(f"P2G2P Cost (input basis): {total_p2g2p_cost_per_mwh_input:.1f} EUR/MWh")
    print(f"P2G2P Cost (output basis): {total_p2g2p_cost_per_mwh_output:.1f} EUR/MWh")
    print(f"P2G2P Cost (output basis): {total_p2g2p_cost_per_mwh_output/1000:.3f} EUR/kWh")
    
    print(f"\nCost per Energy Capacity: {total_capex/h2_energy_mwh:.2f} EUR/MWh = {total_capex/(h2_energy_mwh*1000):.3f} EUR/kWh")
    print(f"Storage Duration: {h2_energy_mwh/fc_power_mw:.1f} hours = {h2_energy_mwh/fc_power_mw/24:.1f} days")
    
    return {
        'updated_costs': {
            'storage': h2_energy_cost_eur_kwh,
            'electrolysis': elec_cost_eur_kw,
            'fuel_cell': fc_cost_eur_kw
        },
        'updated_capex': {
            'storage': h2_storage_capex,
            'electrolysis': elec_capex,
            'fuel_cell': fc_capex,
            'total': total_capex
        },
        'round_trip_efficiency': round_trip_efficiency,
        'p2g2p_cost_input': total_p2g2p_cost_per_mwh_input,
        'p2g2p_cost_output': total_p2g2p_cost_per_mwh_output,
        'capacities': {
            'energy_gwh': h2_energy_gwh,
            'power_elec_gw': elec_power_gw,
            'power_fc_gw': fc_power_gw
        }
    }

def main():
    """Main function."""
    
    try:
        n = load_network()
        results = analyze_h2_updated_costs(n)
        
        # Save results to file
        summary = f"""
H2 P2G2P Updated Cost Analysis Summary
=====================================

UPDATED COST PARAMETERS:
- H2 Storage: {results['updated_costs']['storage']:.2f} EUR/kWh
- Electrolysis: {results['updated_costs']['electrolysis']:.0f} EUR/kW
- Fuel Cell: {results['updated_costs']['fuel_cell']:.0f} EUR/kW

UPDATED CAPEX:
- H2 Storage: {results['updated_capex']['storage']/1e9:.2f} billion EUR
- Electrolysis: {results['updated_capex']['electrolysis']/1e9:.2f} billion EUR
- Fuel Cell: {results['updated_capex']['fuel_cell']/1e9:.2f} billion EUR
- TOTAL: {results['updated_capex']['total']/1e9:.2f} billion EUR

PERFORMANCE:
- Round-Trip Efficiency: {results['round_trip_efficiency']:.1%}
- P2G2P Cost (input): {results['p2g2p_cost_input']:.1f} EUR/MWh
- P2G2P Cost (output): {results['p2g2p_cost_output']:.1f} EUR/MWh

CAPACITIES:
- Energy Storage: {results['capacities']['energy_gwh']:.1f} GWh
- Electrolysis Power: {results['capacities']['power_elec_gw']:.1f} GW
- Fuel Cell Power: {results['capacities']['power_fc_gw']:.1f} GW
"""
        
        with open("h2_p2g2p_updated_cost_analysis.txt", "w") as f:
            f.write(summary)
        
        print(f"\nDetailed analysis saved to: h2_p2g2p_updated_cost_analysis.txt")
        
        return results
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
