#!/usr/bin/env python3
"""
Comprehensive H2 Power-to-Gas-to-Power (P2G2P) cost and efficiency analysis.
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

def analyze_h2_p2g2p_costs(n):
    """Analyze complete H2 P2G2P system costs and efficiencies."""
    
    print("=" * 60)
    print("HYDROGEN POWER-TO-GAS-TO-POWER (P2G2P) COST ANALYSIS")
    print("=" * 60)
    
    # Find H2 system components
    h2_stores = n.stores[n.stores.carrier == 'H2 Store']
    h2_stores_opt = h2_stores[h2_stores.e_nom_opt > 0]
    
    h2_links = n.links[n.links.carrier.str.contains('H2', na=False)]
    h2_links_opt = h2_links[h2_links.p_nom_opt > 0]
    
    if h2_stores_opt.empty or h2_links_opt.empty:
        print("No H2 system components found.")
        return
    
    # === STEP 1: COMPONENT COSTS ===
    print("\n1. COMPONENT COSTS AND SPECIFICATIONS")
    print("-" * 40)
    
    # H2 Storage
    h2_energy_mwh = h2_stores_opt['e_nom_opt'].sum()
    h2_energy_cost_eur_mwh = h2_stores_opt['capital_cost'].iloc[0]
    h2_storage_capex = h2_energy_mwh * h2_energy_cost_eur_mwh
    
    print(f"H2 Energy Storage:")
    print(f"  Capacity: {h2_energy_mwh/1000:.1f} GWh")
    print(f"  Unit Cost: {h2_energy_cost_eur_mwh:.2f} EUR/MWh = {h2_energy_cost_eur_mwh/1000:.3f} EUR/kWh")
    print(f"  Total CAPEX: {h2_storage_capex/1e6:.1f} million EUR")
    
    # Electrolysis (Power-to-Gas)
    electrolyzer = h2_links_opt[h2_links_opt.carrier == 'H2 Electrolysis']
    if not electrolyzer.empty:
        elec_power_mw = electrolyzer['p_nom_opt'].iloc[0]
        elec_efficiency = electrolyzer['efficiency'].iloc[0]
        elec_cost_eur_mw = electrolyzer['capital_cost'].iloc[0]
        elec_capex = elec_power_mw * elec_cost_eur_mw
        
        print(f"\nH2 Electrolysis (Power-to-Gas):")
        print(f"  Capacity: {elec_power_mw/1000:.1f} GW")
        print(f"  Efficiency: {elec_efficiency:.1%}")
        print(f"  Unit Cost: {elec_cost_eur_mw/1000:.1f} EUR/kW")
        print(f"  Total CAPEX: {elec_capex/1e6:.1f} million EUR")
    
    # Fuel Cell (Gas-to-Power)
    fuel_cell = h2_links_opt[h2_links_opt.carrier == 'H2 Fuel Cell']
    if not fuel_cell.empty:
        fc_power_mw = fuel_cell['p_nom_opt'].iloc[0]
        fc_efficiency = fuel_cell['efficiency'].iloc[0]
        fc_cost_eur_mw = fuel_cell['capital_cost'].iloc[0]
        fc_capex = fc_power_mw * fc_cost_eur_mw
        
        print(f"\nH2 Fuel Cell (Gas-to-Power):")
        print(f"  Capacity: {fc_power_mw/1000:.1f} GW")
        print(f"  Efficiency: {fc_efficiency:.1%}")
        print(f"  Unit Cost: {fc_cost_eur_mw/1000:.1f} EUR/kW")
        print(f"  Total CAPEX: {fc_capex/1e6:.1f} million EUR")
    
    # === STEP 2: ROUND-TRIP EFFICIENCY ===
    print(f"\n2. ROUND-TRIP EFFICIENCY ANALYSIS")
    print("-" * 40)
    
    round_trip_efficiency = elec_efficiency * fc_efficiency
    energy_loss_factor = 1 - round_trip_efficiency
    
    print(f"Electrolysis Efficiency: {elec_efficiency:.1%}")
    print(f"Fuel Cell Efficiency: {fc_efficiency:.1%}")
    print(f"Round-Trip Efficiency: {round_trip_efficiency:.1%}")
    print(f"Energy Loss: {energy_loss_factor:.1%}")
    
    # === STEP 3: COST PER MWh ANALYSIS ===
    print(f"\n3. LEVELIZED COST ANALYSIS")
    print("-" * 40)
    
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
    
    # === STEP 4: P2G2P TOTAL COST ===
    print(f"\n4. POWER-TO-GAS-TO-POWER TOTAL COST")
    print("-" * 40)
    
    # Cost to store 1 MWh of electricity and get it back
    # Need to account for round-trip efficiency
    
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
    print(f"  Energy recovered: {electricity_recovered:.2f} MWh")
    print(f"  Cost per MWh output: {total_p2g2p_cost_per_mwh_output:.2f} EUR/MWh")
    
    # === STEP 5: SUMMARY ===
    print(f"\n5. SUMMARY")
    print("=" * 40)
    
    total_system_capex = h2_storage_capex + elec_capex + fc_capex
    
    print(f"Total H2 System CAPEX: {total_system_capex/1e9:.2f} billion EUR")
    print(f"Round-Trip Efficiency: {round_trip_efficiency:.1%}")
    print(f"P2G2P Cost (input basis): {total_p2g2p_cost_per_mwh_input:.1f} EUR/MWh")
    print(f"P2G2P Cost (output basis): {total_p2g2p_cost_per_mwh_output:.1f} EUR/MWh")
    print(f"P2G2P Cost (output basis): {total_p2g2p_cost_per_mwh_output/1000:.3f} EUR/kWh")
    
    # === STEP 6: DETAILED COST BREAKDOWN ===
    print(f"\n6. DETAILED COST SETTINGS")
    print("-" * 40)
    
    print("From PyPSA network cost parameters:")
    print(f"H2 Store capital_cost: {h2_energy_cost_eur_mwh:.2f} EUR/MWh")
    print(f"H2 Electrolysis capital_cost: {elec_cost_eur_mw:.2f} EUR/MW")
    print(f"H2 Fuel Cell capital_cost: {fc_cost_eur_mw:.2f} EUR/MW")
    
    # Check for marginal costs
    if 'marginal_cost' in electrolyzer.columns:
        elec_marginal = electrolyzer['marginal_cost'].iloc[0]
        print(f"H2 Electrolysis marginal_cost: {elec_marginal:.2f} EUR/MWh")
    
    if 'marginal_cost' in fuel_cell.columns:
        fc_marginal = fuel_cell['marginal_cost'].iloc[0]
        print(f"H2 Fuel Cell marginal_cost: {fc_marginal:.2f} EUR/MWh")
    
    return {
        'round_trip_efficiency': round_trip_efficiency,
        'p2g2p_cost_input': total_p2g2p_cost_per_mwh_input,
        'p2g2p_cost_output': total_p2g2p_cost_per_mwh_output,
        'total_capex': total_system_capex,
        'component_costs': {
            'storage': h2_energy_cost_eur_mwh,
            'electrolysis': elec_cost_eur_mw,
            'fuel_cell': fc_cost_eur_mw
        }
    }

def main():
    """Main function."""
    
    try:
        n = load_network()
        results = analyze_h2_p2g2p_costs(n)
        
        # Save results to file
        summary = f"""
H2 P2G2P Cost Analysis Summary
=============================

Round-Trip Efficiency: {results['round_trip_efficiency']:.1%}
P2G2P Cost (input): {results['p2g2p_cost_input']:.1f} EUR/MWh
P2G2P Cost (output): {results['p2g2p_cost_output']:.1f} EUR/MWh
Total System CAPEX: {results['total_capex']/1e9:.2f} billion EUR

Component Costs:
- H2 Storage: {results['component_costs']['storage']:.2f} EUR/MWh
- Electrolysis: {results['component_costs']['electrolysis']:.0f} EUR/MW
- Fuel Cell: {results['component_costs']['fuel_cell']:.0f} EUR/MW
"""
        
        with open("h2_p2g2p_cost_analysis.txt", "w") as f:
            f.write(summary)
        
        print(f"\nDetailed analysis saved to: h2_p2g2p_cost_analysis.txt")
        
        return results
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
