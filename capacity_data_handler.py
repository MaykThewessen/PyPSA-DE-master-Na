#!/usr/bin/env python3
"""
Capacity data handler for storage technologies
Handles the updated battery technology naming conventions
"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)

def get_capacity_data(network):
    """
    Extract capacity data for storage technologies with updated battery technology names.
    
    Updated to handle new battery technology naming conventions:
    - 'iron-air battery', 'Lithium-Ion-LFP-bicharger', 'Lithium-Ion-LFP-store', 
      'battery storage', 'battery inverter'
    - Removed old names: 'battery1', 'battery2', 'battery4', 'battery8', 
      'Ebattery1', 'Ebattery2'
    """
    
    # Updated list of all storage carriers with new battery technology names
    all_storage_carriers = [
        'iron-air battery',
        'Lithium-Ion-LFP-bicharger', 
        'Lithium-Ion-LFP-store',
        'battery storage',
        'battery inverter',
        'H2',
        'PHS',
        'battery_4h',
        'battery_12h', 
        'battery_24h',
        'battery_48h',
        'ironair',
        'Compressed-Air-Adiabatic',
        'Vanadium-Redox-Flow'
    ]
    
    # Initialize capacity data structure
    capacity_data = {
        'stores': {},
        'storage_units': {},
        'links': {}
    }
    
    # Extract store capacities
    if hasattr(network, 'stores') and len(network.stores) > 0:
        for carrier in all_storage_carriers:
            store_mask = network.stores.carrier == carrier
            if store_mask.any():
                total_capacity = network.stores.loc[store_mask, 'e_nom_opt'].sum()
                capacity_data['stores'][carrier] = total_capacity
                logger.info(f"Store {carrier}: {total_capacity:.1f} MWh")
    
    # Extract storage unit capacities  
    if hasattr(network, 'storage_units') and len(network.storage_units) > 0:
        for carrier in all_storage_carriers:
            unit_mask = network.storage_units.carrier == carrier
            if unit_mask.any():
                total_power = network.storage_units.loc[unit_mask, 'p_nom_opt'].sum()
                total_energy = (network.storage_units.loc[unit_mask, 'p_nom_opt'] * 
                               network.storage_units.loc[unit_mask, 'max_hours']).sum()
                capacity_data['storage_units'][carrier] = {
                    'power': total_power,
                    'energy': total_energy
                }
                logger.info(f"Storage Unit {carrier}: {total_power:.1f} MW, {total_energy:.1f} MWh")
    
    # Extract link capacities with updated carrier grouping logic
    if hasattr(network, 'links') and len(network.links) > 0:
        for idx, link in network.links.iterrows():
            carrier = link['carrier']
            power_capacity = link['p_nom_opt']
            
            # Updated carrier grouping logic for new battery technology naming
            grouped_carrier = group_storage_carrier(carrier)
            
            if grouped_carrier in all_storage_carriers:
                if grouped_carrier not in capacity_data['links']:
                    capacity_data['links'][grouped_carrier] = []
                
                capacity_data['links'][grouped_carrier].append({
                    'name': idx,
                    'carrier': carrier,
                    'power': power_capacity,
                    'efficiency': link.get('efficiency', 1.0)
                })
    
    return capacity_data

def group_storage_carrier(carrier_name):
    """
    Group storage carrier names according to new naming conventions.
    Handles bicharger/store separation for Lithium-Ion-LFP technology.
    
    Parameters
    ----------
    carrier_name : str
        Original carrier name
        
    Returns
    -------
    str
        Grouped carrier name
    """
    
    # Handle Lithium-Ion-LFP bicharger/store separation
    if 'Lithium-Ion-LFP' in carrier_name:
        if 'bicharger' in carrier_name:
            return 'Lithium-Ion-LFP-bicharger'
        elif 'store' in carrier_name:
            return 'Lithium-Ion-LFP-store'
        else:
            # Default to store for other LFP variants
            return 'Lithium-Ion-LFP-store'
    
    # Handle iron-air battery variations
    if 'iron-air' in carrier_name.lower() or 'ironair' in carrier_name.lower():
        return 'iron-air battery'
    
    # Handle generic battery storage
    if 'battery' in carrier_name.lower() and 'storage' in carrier_name.lower():
        return 'battery storage'
    
    # Handle battery inverter
    if 'battery' in carrier_name.lower() and 'inverter' in carrier_name.lower():
        return 'battery inverter'
    
    # Handle specific duration batteries
    if 'battery_4h' in carrier_name:
        return 'battery_4h'
    elif 'battery_12h' in carrier_name:
        return 'battery_12h'
    elif 'battery_24h' in carrier_name:
        return 'battery_24h'
    elif 'battery_48h' in carrier_name:
        return 'battery_48h'
    
    # Handle hydrogen storage
    if 'H2' in carrier_name:
        return 'H2'
    
    # Handle pumped hydro storage
    if 'PHS' in carrier_name:
        return 'PHS'
    
    # Handle other technologies
    if 'Compressed-Air' in carrier_name:
        return 'Compressed-Air-Adiabatic'
    
    if 'Vanadium' in carrier_name:
        return 'Vanadium-Redox-Flow'
    
    # Return original name if no grouping rule matches
    return carrier_name

def analyze_storage_capacity_data(capacity_data):
    """
    Analyze the extracted capacity data and provide insights.
    
    Parameters
    ----------
    capacity_data : dict
        Capacity data from get_capacity_data function
    """
    
    logger.info("\n=== STORAGE CAPACITY ANALYSIS ===")
    
    # Analyze stores
    if capacity_data['stores']:
        logger.info("\nEnergy Storage Capacities (Stores):")
        total_store_energy = 0
        for carrier, capacity in capacity_data['stores'].items():
            if capacity > 0:
                logger.info(f"  {carrier}: {capacity:.1f} MWh")
                total_store_energy += capacity
        logger.info(f"  Total Store Energy: {total_store_energy:.1f} MWh")
    
    # Analyze storage units
    if capacity_data['storage_units']:
        logger.info("\nStorage Unit Capacities:")
        total_unit_power = 0
        total_unit_energy = 0
        for carrier, data in capacity_data['storage_units'].items():
            power = data['power']
            energy = data['energy'] 
            if power > 0:
                logger.info(f"  {carrier}: {power:.1f} MW, {energy:.1f} MWh")
                total_unit_power += power
                total_unit_energy += energy
        logger.info(f"  Total Unit Power: {total_unit_power:.1f} MW")
        logger.info(f"  Total Unit Energy: {total_unit_energy:.1f} MWh")
    
    # Analyze links
    if capacity_data['links']:
        logger.info("\nStorage Link Capacities:")
        for carrier, links in capacity_data['links'].items():
            total_link_power = sum(link['power'] for link in links)
            if total_link_power > 0:
                logger.info(f"  {carrier}: {total_link_power:.1f} MW ({len(links)} links)")
                
                # Show bicharger vs store breakdown for Lithium-Ion-LFP
                if carrier == 'Lithium-Ion-LFP-bicharger':
                    logger.info(f"    → Bicharger technology for bidirectional operation")
                elif carrier == 'Lithium-Ion-LFP-store':
                    logger.info(f"    → Store technology for energy storage")
    
    logger.info("\n" + "="*50)

if __name__ == "__main__":
    # Example usage
    import pypsa
    
    # This would normally load a solved network
    # network_path = "path/to/solved/network.nc"  
    # n = pypsa.Network(network_path)
    # capacity_data = get_capacity_data(n)
    # analyze_storage_capacity_data(capacity_data)
    
    print("Capacity data handler with updated battery technology names ready!")
    print("New battery technologies supported:")
    print("  - iron-air battery")
    print("  - Lithium-Ion-LFP-bicharger")
    print("  - Lithium-Ion-LFP-store") 
    print("  - battery storage")
    print("  - battery inverter")
    print("Old battery names removed:")
    print("  - battery1, battery2, battery4, battery8")
    print("  - Ebattery1, Ebattery2")
