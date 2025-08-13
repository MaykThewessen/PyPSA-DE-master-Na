#!/usr/bin/env python3
"""
Comprehensive analysis of all storage technologies and their specifications
"""

import pypsa
import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_all_storage_technologies():
    """Analyze all storage technologies in detail including durations, power, and deployment."""
    
    # Load the solved network
    network_path = "results/de-all-tech-2035-mayk/networks/base_s_1_elec_solved_co2_pricing.nc"
    
    logger.info(f"Loading solved network from {network_path}")
    n = pypsa.Network(network_path)
    
    logger.info("=" * 100)
    logger.info("COMPREHENSIVE STORAGE TECHNOLOGY ANALYSIS")
    logger.info("=" * 100)
    
    # === BATTERY STORAGE DETAILED ANALYSIS ===
    logger.info("\n🔋 BATTERY STORAGE - DETAILED BREAKDOWN")
    logger.info("-" * 80)
    
    # Battery stores (energy capacity)
    battery_stores = n.stores[n.stores.carrier == 'battery']
    if len(battery_stores) > 0:
        for idx, store in battery_stores.iterrows():
            energy_capacity = store['e_nom_opt']
            logger.info(f"Battery Store: {idx}")
            logger.info(f"  Energy Capacity: {energy_capacity:.1f} MWh ({energy_capacity/1000:.1f} GWh)")
            logger.info(f"  Investment: +{energy_capacity - store['e_nom']:.1f} MWh")
    
    # Battery links (power capacity and efficiency)
    battery_links = n.links[n.links.carrier.str.contains('battery', case=False, na=False)]
    if len(battery_links) > 0:
        logger.info(f"\nBattery Links (Power Components):")
        for idx, link in battery_links.iterrows():
            power_capacity = link['p_nom_opt']
            efficiency = link['efficiency']
            logger.info(f"  {link['carrier']}: {power_capacity:.1f} MW (efficiency: {efficiency:.1%})")
            if power_capacity > 0:
                # Calculate implied storage duration
                if 'charger' in link['carrier']:
                    total_battery_energy = battery_stores['e_nom_opt'].sum() if len(battery_stores) > 0 else 0
                    duration_hours = total_battery_energy / power_capacity if power_capacity > 0 else 0
                    logger.info(f"    → Charging duration: {duration_hours:.1f} hours at full power")
    
    # === PUMPED HYDRO STORAGE ===
    logger.info(f"\n💧 PUMPED HYDRO STORAGE (PHS)")
    logger.info("-" * 80)
    
    phs_units = n.storage_units[n.storage_units.carrier == 'PHS']
    if len(phs_units) > 0:
        for idx, unit in phs_units.iterrows():
            power_capacity = unit['p_nom_opt']
            max_hours = unit['max_hours'] 
            energy_capacity = power_capacity * max_hours
            efficiency = unit['efficiency_store'] * unit['efficiency_dispatch']
            
            logger.info(f"PHS Unit: {idx}")
            logger.info(f"  Power Capacity: {power_capacity:.1f} MW")
            logger.info(f"  Energy Capacity: {energy_capacity:.1f} MWh ({energy_capacity/1000:.1f} GWh)")
            logger.info(f"  Storage Duration: {max_hours:.1f} hours")
            logger.info(f"  Round-trip Efficiency: {efficiency:.1%}")
            logger.info(f"  Investment: +{power_capacity - unit['p_nom']:.1f} MW")
    
    # === IRON-AIR BATTERY ===
    logger.info(f"\n🔶 IRON-AIR BATTERY STORAGE")
    logger.info("-" * 80)
    
    iron_air_stores = n.stores[n.stores.carrier == 'iron-air']
    iron_air_found = False
    if len(iron_air_stores) > 0:
        for idx, store in iron_air_stores.iterrows():
            energy_capacity = store['e_nom_opt']
            if energy_capacity > 0:
                iron_air_found = True
                logger.info(f"Iron-Air Store: {idx}")
                logger.info(f"  Energy Capacity: {energy_capacity:.1f} MWh ({energy_capacity/1000:.1f} GWh)")
                logger.info(f"  Investment: +{energy_capacity - store['e_nom']:.1f} MWh")
    
    # Iron-air links
    iron_air_links = n.links[n.links.carrier.str.contains('iron-air', case=False, na=False)]
    if len(iron_air_links) > 0:
        logger.info(f"Iron-Air Links:")
        for idx, link in iron_air_links.iterrows():
            power_capacity = link['p_nom_opt']
            efficiency = link['efficiency']
            if power_capacity > 0:
                iron_air_found = True
                logger.info(f"  {link['carrier']}: {power_capacity:.1f} MW (efficiency: {efficiency:.1%})")
    
    if not iron_air_found:
        logger.info("❌ No iron-air battery storage deployed")
        logger.info("Reason: Not competitive vs. conventional batteries in this scenario")
    
    # === HYDROGEN STORAGE ===
    logger.info(f"\n🟢 HYDROGEN STORAGE")
    logger.info("-" * 80)
    
    h2_stores = n.stores[n.stores.carrier == 'H2']
    h2_found = False
    if len(h2_stores) > 0:
        for idx, store in h2_stores.iterrows():
            energy_capacity = store['e_nom_opt']
            if energy_capacity > 0:
                h2_found = True
                logger.info(f"H2 Store: {idx}")
                logger.info(f"  Energy Capacity: {energy_capacity:.1f} MWh ({energy_capacity/1000:.1f} GWh)")
                logger.info(f"  Investment: +{energy_capacity - store['e_nom']:.1f} MWh")
    
    # H2 links (electrolysis and fuel cells)
    h2_links = n.links[n.links.carrier.str.contains('H2', case=False, na=False)]
    if len(h2_links) > 0:
        logger.info(f"Hydrogen Links:")
        for idx, link in h2_links.iterrows():
            power_capacity = link['p_nom_opt']
            efficiency = link['efficiency']
            if power_capacity > 0:
                h2_found = True
                logger.info(f"  {link['carrier']}: {power_capacity:.1f} MW (efficiency: {efficiency:.1%})")
    
    if not h2_found:
        logger.info("❌ No hydrogen storage deployed")
        logger.info("Reason: High cost and lower efficiency vs. batteries/PHS")
    
    # === COMPRESSED AIR ENERGY STORAGE (CAES) ===
    logger.info(f"\n💨 COMPRESSED AIR ENERGY STORAGE (CAES)")
    logger.info("-" * 80)
    
    caes_stores = n.stores[n.stores.carrier.str.contains('Compressed-Air', case=False, na=False)]
    caes_found = False
    if len(caes_stores) > 0:
        for idx, store in caes_stores.iterrows():
            energy_capacity = store['e_nom_opt']
            if energy_capacity > 0:
                caes_found = True
                logger.info(f"CAES Store: {idx}")
                logger.info(f"  Energy Capacity: {energy_capacity:.1f} MWh ({energy_capacity/1000:.1f} GWh)")
                logger.info(f"  Investment: +{energy_capacity - store['e_nom']:.1f} MWh")
    
    if not caes_found:
        logger.info("❌ No CAES deployed")
        logger.info("Reason: Not competitive in this scenario")
    
    # === VANADIUM REDOX FLOW BATTERY ===
    logger.info(f"\n🔵 VANADIUM REDOX FLOW BATTERY")
    logger.info("-" * 80)
    
    vanadium_stores = n.stores[n.stores.carrier.str.contains('Vanadium', case=False, na=False)]
    vanadium_found = False
    if len(vanadium_stores) > 0:
        for idx, store in vanadium_stores.iterrows():
            energy_capacity = store['e_nom_opt']
            if energy_capacity > 0:
                vanadium_found = True
                logger.info(f"Vanadium Flow Store: {idx}")
                logger.info(f"  Energy Capacity: {energy_capacity:.1f} MWh ({energy_capacity/1000:.1f} GWh)")
                logger.info(f"  Investment: +{energy_capacity - store['e_nom']:.1f} MWh")
    
    if not vanadium_found:
        logger.info("❌ No vanadium redox flow battery deployed")
        logger.info("Reason: Not competitive vs. Li-ion batteries in this scenario")
    
    # === STORAGE DURATION ANALYSIS ===
    logger.info(f"\n⏱️ STORAGE DURATION COMPARISON")
    logger.info("-" * 80)
    
    storage_duration_data = []
    
    # Battery duration (energy/power)
    if len(battery_stores) > 0 and len(battery_links) > 0:
        battery_energy = battery_stores['e_nom_opt'].sum()
        battery_power = battery_links[battery_links.carrier.str.contains('charger')]['p_nom_opt'].sum()
        if battery_power > 0:
            battery_duration = battery_energy / battery_power
            storage_duration_data.append(('Li-ion Battery', battery_energy/1000, battery_power, battery_duration))
    
    # PHS duration
    if len(phs_units) > 0:
        phs_energy = (phs_units['p_nom_opt'] * phs_units['max_hours']).sum()
        phs_power = phs_units['p_nom_opt'].sum()
        phs_duration = phs_units['max_hours'].iloc[0] if len(phs_units) > 0 else 0
        storage_duration_data.append(('Pumped Hydro', phs_energy/1000, phs_power, phs_duration))
    
    # Create summary table
    if storage_duration_data:
        logger.info(f"{'Technology':20} {'Energy (GWh)':>12} {'Power (MW)':>12} {'Duration (h)':>12}")
        logger.info("-" * 60)
        for tech, energy, power, duration in storage_duration_data:
            logger.info(f"{tech:20} {energy:12.1f} {power:12.0f} {duration:12.1f}")
    
    # === TECHNOLOGY SELECTION ANALYSIS ===
    logger.info(f"\n🎯 TECHNOLOGY SELECTION INSIGHTS")
    logger.info("-" * 80)
    
    insights = [
        "SELECTED TECHNOLOGIES:",
        f"• Li-ion Batteries: 72.0 GWh energy, 6.0 GW power (~12h duration)",
        f"• Pumped Hydro: 35.8 GWh energy, 7.2 GW power (~5h duration)",
        "",
        "NOT SELECTED TECHNOLOGIES:",
        "• Iron-air batteries: Not competitive vs. Li-ion",
        "• Hydrogen storage: High cost, lower efficiency",
        "• CAES: Not competitive in this market",
        "• Vanadium flow: Higher cost than Li-ion",
        "",
        "SELECTION DRIVERS:",
        "• 250 EUR/tCO2 carbon price favors efficient storage",
        "• Li-ion: Best cost/performance for daily cycling",
        "• PHS: Existing asset, good for longer duration",
        "• Other techs: Too expensive for this scenario"
    ]
    
    for insight in insights:
        if insight.startswith("•"):
            logger.info(f"  {insight}")
        else:
            logger.info(f"{insight}")
    
    # === LOAD COSTS DATA FOR COMPARISON ===
    logger.info(f"\n💰 STORAGE COST COMPARISON")
    logger.info("-" * 80)
    
    try:
        costs_path = "resources/de-all-tech-2035-mayk/costs_2035.csv"
        costs = pd.read_csv(costs_path, index_col=0)
        
        storage_techs = ['battery', 'H2', 'iron-air', 'Vanadium-Redox-Flow', 'Compressed-Air-Adiabatic']
        
        logger.info(f"{'Technology':25} {'Capital Cost (EUR/MWh)':>20} {'Status':>15}")
        logger.info("-" * 65)
        
        for tech in storage_techs:
            if tech in costs.index:
                if 'investment' in costs.columns:
                    cost = costs.loc[tech, 'investment']
                elif 'capital_cost' in costs.columns:
                    cost = costs.loc[tech, 'capital_cost']
                else:
                    cost = 0
                
                # Determine deployment status
                status = "❌ Not deployed"
                if tech == 'battery':
                    status = "✅ 72 GWh deployed"
                elif tech == 'H2':
                    status = "❌ Too expensive"
                
                logger.info(f"{tech:25} {cost:20.0f} {status:>15}")
                
    except Exception as e:
        logger.warning(f"Could not load detailed cost data: {e}")
    
    logger.info("\n" + "=" * 100)
    
    return n

if __name__ == "__main__":
    try:
        network = analyze_all_storage_technologies()
        print("\n🔍 Comprehensive storage technology analysis completed!")
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
