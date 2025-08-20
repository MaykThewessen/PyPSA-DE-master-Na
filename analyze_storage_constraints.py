#!/usr/bin/env python3
"""
Analyze storage durations per scenario and iron-air deployment constraints.
"""

import pandas as pd
import numpy as np

def analyze_storage_constraints():
    """Analyze storage durations and iron-air constraints for each scenario."""
    
    # Load data
    df = pd.read_csv('co2_scenarios_readable_summary_20250819_203903.csv')
    
    print("🔋 Storage Duration Analysis by Scenario")
    print("=" * 60)
    
    scenarios = ['A', 'B', 'C', 'D']
    
    # Analyze each scenario
    for i, scenario in enumerate(scenarios):
        row = df.iloc[i]
        co2_limit = row['CO2 Limit']
        
        print(f"\n📊 Scenario {scenario} ({co2_limit}):")
        print("-" * 40)
        
        # PHS Duration
        phs_power = row.get('PHS Power (GW)', 0)
        phs_energy = row.get('PHS Energy (GWh)', 0)
        if phs_power > 0:
            phs_duration = phs_energy / phs_power
            print(f"   PHS:        {phs_energy:.1f} GWh / {phs_power:.1f} GW = {phs_duration:.1f} hours")
        else:
            print(f"   PHS:        No deployment")
        
        # Battery Duration
        battery_power = row.get('Battery Charger (GW)', 0)
        battery_energy = row.get('Battery Energy (GWh)', 0)
        if battery_power > 0:
            battery_duration = battery_energy / battery_power
            print(f"   Battery:    {battery_energy:.1f} GWh / {battery_power:.1f} GW = {battery_duration:.1f} hours")
        else:
            print(f"   Battery:    No deployment")
        
        # Iron-Air Duration with Constraint Analysis
        ironair_power = row.get('Iron-Air Charger (GW)', 0)
        ironair_energy = row.get('Iron-Air Energy (GWh)', 0)
        
        if ironair_power > 0 and ironair_energy > 0:
            ironair_duration = ironair_energy / ironair_power
            power_ratio = ironair_power / ironair_energy * 100  # Power as % of energy
            
            print(f"   Iron-Air:   {ironair_energy:.1f} GWh / {ironair_power:.1f} GW = {ironair_duration:.1f} hours")
            print(f"               Power ratio: {power_ratio:.2f}% of energy content")
            
            # Check constraints
            constraint_50h = ironair_duration >= 50
            constraint_2pct = power_ratio <= 2
            
            print(f"               Constraint checks:")
            print(f"                 ✓ Duration ≥ 50h: {'✅ PASS' if constraint_50h else '❌ FAIL'}")
            print(f"                 ✓ Power ≤ 2% of energy: {'✅ PASS' if constraint_2pct else '❌ FAIL'}")
            
            if constraint_50h or constraint_2pct:
                print(f"               ✅ MEETS 50H REQUIREMENT: Constraint satisfied")
            else:
                print(f"               ⚠️  BELOW 50H REQUIREMENT: Consider increasing duration")
        else:
            print(f"   Iron-Air:   No deployment")
        
        # Hydrogen Duration
        hydrogen_energy = row.get('Hydrogen Storage (GWh)', 0)
        if hydrogen_energy > 0:
            # Typical seasonal storage duration
            hydrogen_power = hydrogen_energy / 720
            print(f"   Hydrogen:   {hydrogen_energy:.1f} GWh / {hydrogen_power:.1f} GW = 720.0 hours (seasonal)")
        else:
            print(f"   Hydrogen:   No deployment")
    
    print(f"\n📋 Iron-Air Deployment Constraint Summary:")
    print("=" * 60)
    print("Constraint: Deploy iron-air ONLY if:")
    print("  - Duration ≥ 50 hours, OR")
    print("  - Power ≤ 2% of energy content")
    print()
    
    # Summary table
    constraint_summary = []
    for i, scenario in enumerate(scenarios):
        row = df.iloc[i]
        ironair_power = row.get('Iron-Air Charger (GW)', 0)
        ironair_energy = row.get('Iron-Air Energy (GWh)', 0)
        
        if ironair_power > 0 and ironair_energy > 0:
            duration = ironair_energy / ironair_power
            power_ratio = ironair_power / ironair_energy * 100
            constraint_met = duration >= 50 or power_ratio <= 2
            constraint_summary.append({
                'Scenario': scenario,
                'Duration (h)': f"{duration:.1f}",
                'Power Ratio (%)': f"{power_ratio:.2f}",
                'Constraint Met': '✅' if constraint_met else '❌',
                'Status': 'ALLOWED' if constraint_met else 'BLOCKED'
            })
        else:
            constraint_summary.append({
                'Scenario': scenario,
                'Duration (h)': 'N/A',
                'Power Ratio (%)': 'N/A',
                'Constraint Met': 'N/A',
                'Status': 'NO DEPLOYMENT'
            })
    
    summary_df = pd.DataFrame(constraint_summary)
    print(summary_df.to_string(index=False))
    
    print(f"\n🎯 Key Insights:")
    deployed_scenarios = [s for s in summary_df['Scenario'] if summary_df[summary_df['Scenario'] == s]['Status'].iloc[0] == 'ALLOWED']
    blocked_scenarios = [s for s in summary_df['Scenario'] if summary_df[summary_df['Scenario'] == s]['Status'].iloc[0] == 'BLOCKED']
    
    if deployed_scenarios:
        print(f"   ✅ Iron-air deployed in scenarios: {', '.join(deployed_scenarios)}")
    if blocked_scenarios:
        print(f"   🚫 Iron-air blocked in scenarios: {', '.join(blocked_scenarios)}")
    
    print(f"\n📈 Storage Technology Roles:")
    print(f"   Short-term (< 10h):    Battery, PHS")
    print(f"   Medium-term (10-100h): Iron-air (when constraints met)")
    print(f"   Long-term (> 100h):    Hydrogen (seasonal)")

if __name__ == "__main__":
    analyze_storage_constraints()
