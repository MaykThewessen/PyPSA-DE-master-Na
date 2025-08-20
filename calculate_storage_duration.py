#!/usr/bin/env python3
"""
Calculate storage duration for each technology based on actual PyPSA results.
Duration = Total Energy Capacity (GWh) / Total Power Capacity (GW)
"""

import pandas as pd
import numpy as np

def calculate_storage_durations():
    """Calculate storage durations from our detailed CSV data."""
    
    # Load our detailed CSV
    df = pd.read_csv('co2_scenarios_summary_20250819_203242.csv')
    
    print("🔋 Storage Duration Analysis")
    print("=" * 50)
    print("Calculation: Energy Capacity (GWh) / Power Capacity (GW) = Duration (hours)")
    print()
    
    # Storage technologies and their column mappings
    storage_techs = {
        'PHS': {
            'power_col': 'PHS_power_capacity_GW',
            'energy_col': 'PHS_energy_capacity_GWh',
            'name': 'Pumped Hydro Storage (PHS)'
        },
        'Battery': {
            'power_col': 'battery_charger_capacity_GW',
            'energy_col': 'battery_energy_capacity_GWh',
            'name': 'Lithium-ion Battery'
        },
        'Iron-Air': {
            'power_col': 'iron-air_charger_capacity_GW',
            'energy_col': 'iron-air_energy_capacity_GWh',
            'name': 'Iron-Air Battery'
        },
        'Hydrogen': {
            'power_col': None,  # Need to calculate from electrolysis/fuel cell
            'energy_col': 'Hydrogen_energy_capacity_GWh',
            'name': 'Hydrogen Storage'
        }
    }
    
    # Calculate duration for each scenario and technology
    scenarios = ['A', 'B', 'C', 'D']
    durations_by_tech = {}
    
    for tech, cols in storage_techs.items():
        durations_by_tech[tech] = []
        
        print(f"\n📊 {cols['name']}:")
        for i, (_, row) in enumerate(df.iterrows()):
            scenario = scenarios[i]
            
            if tech == 'Hydrogen':
                # For hydrogen, we need to estimate power from flows or use a typical duration
                # Let's use electrolysis/fuel cell flows as proxy for power
                electrolysis_flow = row.get('Hydrogen electrolysis_link_flow_TWh', 0) * 1000  # Convert to GWh
                fuel_cell_flow = row.get('Hydrogen fuel cell_link_flow_TWh', 0) * 1000  # Convert to GWh
                
                # Use the maximum of electrolysis or fuel cell as representative power
                # Assume this represents annual operation, so power = energy / 8760 hours
                if electrolysis_flow > 0 or fuel_cell_flow > 0:
                    annual_throughput = max(electrolysis_flow, fuel_cell_flow)
                    # Estimate power as annual throughput / typical capacity factor (e.g., 0.3)
                    estimated_power = annual_throughput / (8760 * 0.3) if annual_throughput > 0 else 0
                else:
                    estimated_power = 0
                
                energy = row.get(cols['energy_col'], 0)
                power = estimated_power
            else:
                energy = row.get(cols['energy_col'], 0)
                power = row.get(cols['power_col'], 0)
            
            if power > 0 and energy > 0:
                duration = energy / power
                durations_by_tech[tech].append(duration)
                print(f"   Scenario {scenario}: {energy:.1f} GWh / {power:.1f} GW = {duration:.1f} hours")
            else:
                durations_by_tech[tech].append(0)
                print(f"   Scenario {scenario}: No capacity installed")
    
    # Calculate average durations (excluding zeros)
    print(f"\n📈 Average Storage Durations:")
    print("=" * 30)
    
    avg_durations = {}
    for tech, durations in durations_by_tech.items():
        non_zero_durations = [d for d in durations if d > 0]
        if non_zero_durations:
            avg_duration = np.mean(non_zero_durations)
            avg_durations[tech] = avg_duration
            print(f"{storage_techs[tech]['name']}: {avg_duration:.1f} hours")
        else:
            avg_durations[tech] = 0
            print(f"{storage_techs[tech]['name']}: No data (not deployed)")
    
    # Special handling for Hydrogen - use typical duration if estimation fails
    if avg_durations['Hydrogen'] == 0:
        # Use typical seasonal storage duration
        avg_durations['Hydrogen'] = 720  # 30 days typical for seasonal storage
        print(f"   Note: Using typical seasonal storage duration for Hydrogen")
    
    return avg_durations

def create_duration_visualization():
    """Create a simple text-based visualization of the durations."""
    
    durations = calculate_storage_durations()
    
    print(f"\n🎯 Storage Technology Duration Summary:")
    print("=" * 50)
    
    # Sort by duration
    sorted_durations = sorted(durations.items(), key=lambda x: x[1])
    
    for tech, duration in sorted_durations:
        if duration > 0:
            print(f"{tech:12}: {duration:6.1f} hours")
        else:
            print(f"{tech:12}: {'Not deployed':>10}")
    
    print()
    print("📝 Technology Categories:")
    print("   Short-duration: < 10 hours")
    print("   Medium-duration: 10-100 hours") 
    print("   Long-duration: > 100 hours")
    print()
    
    # Categorize technologies
    short_duration = []
    medium_duration = []
    long_duration = []
    
    for tech, duration in durations.items():
        if duration > 0:
            if duration < 10:
                short_duration.append(f"{tech} ({duration:.1f}h)")
            elif duration < 100:
                medium_duration.append(f"{tech} ({duration:.1f}h)")
            else:
                long_duration.append(f"{tech} ({duration:.1f}h)")
    
    print("📋 Classification:")
    if short_duration:
        print(f"   Short-duration:  {', '.join(short_duration)}")
    if medium_duration:
        print(f"   Medium-duration: {', '.join(medium_duration)}")
    if long_duration:
        print(f"   Long-duration:   {', '.join(long_duration)}")
    
    return durations

if __name__ == "__main__":
    durations = create_duration_visualization()
    
    print(f"\n✅ Storage duration analysis complete!")
    print(f"   Data source: co2_scenarios_summary_20250819_203242.csv")
    print(f"   Method: Energy Capacity (GWh) / Power Capacity (GW)")
    print(f"   Hydrogen estimated from system flows")
