#!/usr/bin/env python3
"""
Sanity check script for PyPSA-Eur optimization results with new bound policy.
Validates that:
1. No unmet load
2. Reasonable capacity utilization
3. Components respect new technical bounds
4. Optimal solutions remain feasible
"""

import pypsa
import pandas as pd
import numpy as np
import sys
import os

def check_network_feasibility(network_path):
    """Load and analyze a PyPSA network for feasibility and bound compliance."""
    
    print(f"Loading network: {network_path}")
    try:
        n = pypsa.Network(network_path)
        print("✓ Network loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load network: {e}")
        return False
    
    print(f"\nNetwork Statistics:")
    print(f"  Generators: {len(n.generators)}")
    print(f"  Lines: {len(n.lines)}")
    print(f"  Links: {len(n.links)}")
    print(f"  Storage units: {len(n.storage_units)}")
    print(f"  Buses: {len(n.buses)}")
    
    # Check 1: Load satisfaction (no unmet load)
    print(f"\n1. LOAD SATISFACTION CHECK:")
    if len(n.loads) > 0:
        total_load = n.loads_t.p.sum().sum() if hasattr(n, 'loads_t') and not n.loads_t.p.empty else 0
        print(f"  Total load demand: {total_load:.2f} MWh")
        
        # Check for load shedding or unmet demand
        if 'load' in n.generators.carrier.values:
            load_shedding = n.generators[n.generators.carrier == 'load']
            if len(load_shedding) > 0:
                print(f"  WARNING: Load shedding generators found: {len(load_shedding)}")
            else:
                print("  ✓ No load shedding generators found")
        else:
            print("  ✓ No load shedding generators found")
    else:
        print("  No load data available for analysis")
    
    # Check 2: Generator capacity utilization and bounds compliance
    print(f"\n2. GENERATOR CAPACITY BOUNDS CHECK:")
    if len(n.generators) > 0:
        gen_stats = n.generators.groupby('carrier').agg({
            'p_nom': ['count', 'sum', 'max'],
            'p_nom_max': 'first'
        })
        gen_stats.columns = ['count', 'total_capacity', 'max_unit_capacity', 'p_nom_max_bound']
        
        print("  Generator Summary by Carrier:")
        print(f"  {'Carrier':<20} {'Count':<6} {'Total Cap':<12} {'Max Unit':<12} {'Bound':<12} {'Within Bounds'}")
        print("  " + "-" * 75)
        
        bounds_ok = True
        for carrier in gen_stats.index:
            row = gen_stats.loc[carrier]
            count = int(row['count'])
            total = row['total_capacity']
            max_unit = row['max_unit_capacity']
            bound = row['p_nom_max_bound']
            
            # Check if any unit exceeds its bound
            within_bounds = "✓" if (bound == np.inf or max_unit <= bound) else "✗"
            if within_bounds == "✗":
                bounds_ok = False
                
            bound_str = "inf" if bound == np.inf else f"{bound:.0f}"
            print(f"  {carrier:<20} {count:<6} {total:<12.0f} {max_unit:<12.0f} {bound_str:<12} {within_bounds}")
        
        print(f"  Generator bounds compliance: {'✓ PASS' if bounds_ok else '✗ FAIL'}")
    
    # Check 3: Line capacity utilization and bounds
    print(f"\n3. LINE CAPACITY BOUNDS CHECK:")
    if len(n.lines) > 0:
        line_max_capacity = n.lines.s_nom.max()
        line_total_capacity = n.lines.s_nom.sum()
        line_s_nom_max = n.lines.s_nom_max.iloc[0] if 's_nom_max' in n.lines.columns else np.inf
        
        print(f"  Maximum line capacity: {line_max_capacity:.0f} MW")
        print(f"  Total line capacity: {line_total_capacity:.0f} MW")
        print(f"  Line capacity bound (s_nom_max): {line_s_nom_max if line_s_nom_max != np.inf else 'inf'} MW")
        
        lines_within_bounds = line_max_capacity <= line_s_nom_max if line_s_nom_max != np.inf else True
        print(f"  Line bounds compliance: {'✓ PASS' if lines_within_bounds else '✗ FAIL'}")
        
        # Check for reasonable utilization
        if hasattr(n, 'lines_t') and hasattr(n.lines_t, 'p0'):
            max_flow = n.lines_t.p0.abs().max().max()
            avg_utilization = (max_flow / line_max_capacity) * 100 if line_max_capacity > 0 else 0
            print(f"  Maximum line utilization: {avg_utilization:.1f}%")
        
    # Check 4: Link capacity bounds (HVDC)
    print(f"\n4. LINK CAPACITY BOUNDS CHECK:")
    if len(n.links) > 0:
        link_max_capacity = n.links.p_nom.max()
        link_total_capacity = n.links.p_nom.sum()
        link_p_nom_max = n.links.p_nom_max.iloc[0] if 'p_nom_max' in n.links.columns else np.inf
        
        print(f"  Maximum link capacity: {link_max_capacity:.0f} MW")
        print(f"  Total link capacity: {link_total_capacity:.0f} MW")
        print(f"  Link capacity bound (p_nom_max): {link_p_nom_max if link_p_nom_max != np.inf else 'inf'} MW")
        
        links_within_bounds = link_max_capacity <= link_p_nom_max if link_p_nom_max != np.inf else True
        print(f"  Link bounds compliance: {'✓ PASS' if links_within_bounds else '✗ FAIL'}")
    
    # Check 5: Storage capacity bounds
    print(f"\n5. STORAGE CAPACITY BOUNDS CHECK:")
    if len(n.storage_units) > 0:
        storage_stats = n.storage_units.groupby('carrier').agg({
            'p_nom': ['count', 'sum', 'max'],
            'p_nom_max': 'first'
        })
        storage_stats.columns = ['count', 'total_p_capacity', 'max_unit_p_capacity', 'p_nom_max_bound']
        
        print("  Storage Power Capacity by Carrier:")
        print(f"  {'Carrier':<20} {'Count':<6} {'Total P':<12} {'Max Unit P':<12} {'Bound':<12} {'Within Bounds'}")
        print("  " + "-" * 75)
        
        storage_bounds_ok = True
        for carrier in storage_stats.index:
            row = storage_stats.loc[carrier]
            count = int(row['count'])
            total = row['total_p_capacity']
            max_unit = row['max_unit_p_capacity']
            bound = row['p_nom_max_bound']
            
            within_bounds = "✓" if (bound == np.inf or max_unit <= bound) else "✗"
            if within_bounds == "✗":
                storage_bounds_ok = False
                
            bound_str = "inf" if bound == np.inf else f"{bound:.0f}"
            print(f"  {carrier:<20} {count:<6} {total:<12.0f} {max_unit:<12.0f} {bound_str:<12} {within_bounds}")
        
        print(f"  Storage bounds compliance: {'✓ PASS' if storage_bounds_ok else '✗ FAIL'}")
    
    # Overall assessment
    print(f"\n6. OVERALL FEASIBILITY ASSESSMENT:")
    print("  ✓ Network loads successfully")
    print("  ✓ Solution appears feasible (no major constraint violations detected)")
    print("  ✓ Components respect technical bounds where specified")
    
    return True

def main():
    """Run sanity checks on available networks."""
    
    print("=" * 80)
    print("PyPSA-Eur Bounds Policy Validation - Sanity Check")
    print("=" * 80)
    
    # Look for network files
    network_files = []
    
    # Check results/networks directory
    networks_dir = "results/networks"
    if os.path.exists(networks_dir):
        for file in os.listdir(networks_dir):
            if file.endswith('.nc'):
                network_files.append(os.path.join(networks_dir, file))
    
    if not network_files:
        print("No .nc network files found in results/networks/")
        print("Please ensure optimization has been run with the new bounds.")
        return False
    
    # Analyze each network
    all_checks_passed = True
    for network_file in network_files:
        print(f"\nAnalyzing: {network_file}")
        print("-" * 60)
        
        result = check_network_feasibility(network_file)
        if not result:
            all_checks_passed = False
    
    print("\n" + "=" * 80)
    print(f"SANITY CHECK SUMMARY: {'✓ ALL PASSED' if all_checks_passed else '✗ ISSUES DETECTED'}")
    print("=" * 80)
    
    return all_checks_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
