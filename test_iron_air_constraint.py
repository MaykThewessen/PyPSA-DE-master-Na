#!/usr/bin/env python3
"""
Test script to verify the iron-air minimum duration constraint.

This script creates a minimal PyPSA network with iron-air storage and tests
that the minimum 50-hour duration constraint is properly enforced.
"""

import numpy as np
import pandas as pd
import pypsa
import tempfile
import os

def create_test_network():
    """Create a minimal test network with iron-air storage."""
    
    # Create basic network
    n = pypsa.Network()
    
    # Add buses
    n.add("Bus", "bus1", carrier="AC")
    
    # Add minimal load
    n.add("Load", "load1", bus="bus1", p_set=100)  # 100 MW load
    
    # Add iron-air storage components (mimicking the structure in add_electricity.py)
    
    # Add iron-air bus
    n.add("Bus", "bus1 iron-air", carrier="iron-air", location="bus1")
    
    # Add iron-air store (make it very cheap to incentivize deployment)
    n.add(
        "Store",
        "bus1 iron-air",
        bus="bus1 iron-air",
        carrier="iron-air",
        e_cyclic=True,
        e_nom_extendable=True,
        capital_cost=5,  # €/MWh - very cheap energy storage
        marginal_cost=0.001,
    )
    
    # Add charger link (also cheap)
    n.add(
        "Link", 
        "bus1 iron-air charger",
        bus0="bus1",
        bus1="bus1 iron-air",
        carrier="iron-air charger",
        efficiency=0.9,
        capital_cost=50,  # €/MW - cheap power capacity
        p_nom_extendable=True,
        marginal_cost=0.001,
    )
    
    # Add discharger link  
    n.add(
        "Link",
        "bus1 iron-air discharger", 
        bus0="bus1 iron-air",
        bus1="bus1",
        carrier="iron-air discharger",
        efficiency=0.9,
        p_nom_extendable=True,
        marginal_cost=0.001,
    )
    
    # Add expensive conventional generation to incentivize storage
    n.add(
        "Generator",
        "gen1",
        bus="bus1", 
        carrier="CCGT",
        p_nom_extendable=True,
        capital_cost=1500,  # €/MW - expensive
        marginal_cost=100,  # €/MWh - very expensive
        efficiency=0.6,
    )
    
    # Set snapshots for a longer period to better test duration constraints
    n.set_snapshots(pd.date_range('2023-01-01', periods=168, freq='h'))  # 1 week
    
    # Create highly variable load pattern that incentivizes long-duration storage
    # Peak during day, low at night, with weekly pattern
    hours = np.arange(168)
    daily_pattern = 1 + 0.8 * np.sin(2 * np.pi * hours / 24 + np.pi/2)  # Daily cycle
    weekly_pattern = 1 + 0.3 * np.sin(2 * np.pi * hours / (24*7))  # Weekly cycle
    load_profile = daily_pattern * weekly_pattern
    n.loads_t.p_set.loc[:, "load1"] = 100 * load_profile
    
    return n

def test_iron_air_constraint():
    """Test that the iron-air constraint is properly enforced."""
    
    print("🔧 Creating test network...")
    n = create_test_network()
    
    # Import the constraint function
    import sys
    sys.path.append('/Users/m/PyPSA-DE-master-Na/scripts')
    from solve_network import add_iron_air_constraints
    
    print("🔬 Building optimization model...")
    n.optimize.create_model()
    
    print("➕ Adding iron-air constraints...")
    add_iron_air_constraints(n)
    
    print("🎯 Solving optimization...")
    status, condition = n.optimize.solve_model()
    
    print(f"📊 Solution status: {status}")
    print(f"📊 Termination condition: {condition}")
    
    if status == 'ok':
        # Check the results
        charger_capacity = n.links.loc["bus1 iron-air charger", "p_nom_opt"]
        discharger_capacity = n.links.loc["bus1 iron-air discharger", "p_nom_opt"] 
        energy_capacity = n.stores.loc["bus1 iron-air", "e_nom_opt"]
        
        print(f"\n📈 Results:")
        print(f"   Charger capacity: {charger_capacity:.2f} MW")
        print(f"   Discharger capacity: {discharger_capacity:.2f} MW")
        print(f"   Energy capacity: {energy_capacity:.2f} MWh")
        
        if charger_capacity > 0:
            duration = energy_capacity / charger_capacity
            print(f"   Duration: {duration:.1f} hours")
            
            # Check constraints
            print(f"\n🔍 Constraint verification:")
            
            # Check charger/discharger ratio constraint  
            expected_discharger = 0.5 * charger_capacity / 0.9  # efficiency correction
            ratio_ok = abs(discharger_capacity - expected_discharger) < 1e-3
            print(f"   ✅ Discharger = 50% charger: {ratio_ok} ({discharger_capacity:.3f} ≈ {expected_discharger:.3f})")
            
            # Check minimum duration constraint
            min_energy = 50.0 * charger_capacity
            duration_ok = energy_capacity >= min_energy - 1e-3
            print(f"   ✅ Duration ≥ 50h: {duration_ok} ({energy_capacity:.1f} ≥ {min_energy:.1f} MWh)")
            
            if duration_ok and ratio_ok:
                print(f"\n🎉 SUCCESS: All iron-air constraints are properly enforced!")
            else:
                print(f"\n❌ FAILURE: Some constraints are violated!")
                
        else:
            print(f"\n💡 No iron-air capacity deployed (not cost-effective in this test case)")
            
    else:
        print(f"\n❌ Optimization failed: {status} - {condition}")
        
    return n

if __name__ == "__main__":
    print("🚀 Testing iron-air minimum duration constraint...")
    print("=" * 60)
    
    n = test_iron_air_constraint()
    
    print("=" * 60)
    print("✅ Test completed!")
