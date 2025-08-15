#!/usr/bin/env python3
"""
Check for available storage technologies in the PyPSA network.
"""

import os
os.environ['PROJ_NETWORK'] = 'OFF'
import pypsa
import logging
import pandas as pd

logger = logging.getLogger(__name__)

def check_storage_technologies():
    """Load the network and print available storage carriers."""
    
    network_path = "resources/de-all-tech-2035-mayk/networks/base_s_1_elec_.nc"
    
    try:
        n = pypsa.Network(network_path)
        logger.info(f"Successfully loaded network from {network_path}")
        
        print("\n🔍 Analyzing storage technologies...")
        
        # Check n.stores
        if len(n.stores) > 0:
            print("\nCarriers in n.stores:")
            print(n.stores.carrier.unique())
        else:
            print("\nNo components in n.stores.")
            
        # Check n.storage_units
        if len(n.storage_units) > 0:
            print("\nCarriers in n.storage_units:")
            print(n.storage_units.carrier.unique())
        else:
            print("\nNo components in n.storage_units.")
            
    except Exception as e:
        logger.error(f"❌ Error loading or analyzing network: {e}")

if __name__ == "__main__":
    check_storage_technologies()

