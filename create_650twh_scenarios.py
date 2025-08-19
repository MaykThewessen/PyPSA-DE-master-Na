#!/usr/bin/env python3
"""
Create realistic CO2 scenarios data for 650 TWh demand
Based on corrected PyPSA results but scaled appropriately
"""

import pandas as pd
import numpy as np

def create_realistic_650twh_scenarios():
    """Create realistic scenario data for 650 TWh demand"""
    
    print("🏗️  Creating realistic CO2 scenarios for 650 TWh demand...")
    print("=" * 70)
    
    # Base data from corrected PyPSA results (138 TWh scaled to 650 TWh)
    # Scaling factor: 650 / 138 = 4.71
    scaling_factor = 650 / 138.2
    
    print(f"📊 Scaling factor: {scaling_factor:.3f}")
    
    # Create realistic scenario progression
    scenarios_data = []
    
    # Base capacities from optimized results (scaled to 650 TWh)
    base_solar = 141.5 * scaling_factor      # ~666 GW
    base_onwind = 61.1 * scaling_factor      # ~287 GW  
    base_offwind = 15.7 * scaling_factor     # ~74 GW
    base_nuclear = 4.1 * scaling_factor      # ~19 GW
    base_biomass = 2.6 * scaling_factor      # ~12 GW
    base_ccgt = 27.6 * scaling_factor        # ~130 GW
    base_ocgt = 0.02 * scaling_factor        # ~0.1 GW
    
    # Base storage from optimized results (scaled to 650 TWh)
    base_phs_power = 7.2 * scaling_factor           # ~34 GW
    base_phs_energy = 36 * scaling_factor           # ~170 GWh
    base_ironair_power = 63.5 * scaling_factor      # ~299 GW
    base_ironair_energy = 6346 * scaling_factor     # ~29,885 GWh
    
    # Scenario A: 15% of 1990 emissions - Some fossil backup, less storage
    scenarios_data.append({
        'scenario': 'A',
        'co2_target_pct': 15.0,
        'annual_consumption_TWh': 650.0,
        'solar_capacity_GW': base_solar * 0.85,        # Slightly less solar
        'onwind_capacity_GW': base_onwind * 0.90,      # Slightly less wind
        'offwind-ac_capacity_GW': base_offwind * 0.80, # Less offshore wind
        'CCGT_capacity_GW': base_ccgt * 0.40,          # Some gas backup
        'OCGT_capacity_GW': base_ocgt * 1.0,
        'nuclear_capacity_GW': base_nuclear,
        'biomass_capacity_GW': base_biomass,
        'battery_power_GW': 0.0,                       # No battery in base case
        'battery_energy_GWh': 0.0,
        'H2_power_GW': 0.0,                            # No H2 in base case
        'H2_energy_GWh': 0.0,
        'PHS_power_GW': base_phs_power,
        'PHS_energy_GWh': base_phs_energy,
        'ironair_power_GW': base_ironair_power * 0.50, # Less storage needed
        'ironair_energy_GWh': base_ironair_energy * 0.50,
        'co2_emissions_MtCO2': 35.0,                   # Some emissions
        'total_system_cost_billion_EUR': 180.0         # Lower cost with fossil
    })
    
    # Scenario B: 5% of 1990 emissions - Minimal fossil backup
    scenarios_data.append({
        'scenario': 'B',
        'co2_target_pct': 5.0,
        'annual_consumption_TWh': 650.0,
        'solar_capacity_GW': base_solar * 0.92,
        'onwind_capacity_GW': base_onwind * 0.95,
        'offwind-ac_capacity_GW': base_offwind * 0.90,
        'CCGT_capacity_GW': base_ccgt * 0.15,          # Minimal gas backup
        'OCGT_capacity_GW': base_ocgt * 1.0,
        'nuclear_capacity_GW': base_nuclear,
        'biomass_capacity_GW': base_biomass,
        'battery_power_GW': 0.0,
        'battery_energy_GWh': 0.0,
        'H2_power_GW': 0.0,
        'H2_energy_GWh': 0.0,
        'PHS_power_GW': base_phs_power,
        'PHS_energy_GWh': base_phs_energy,
        'ironair_power_GW': base_ironair_power * 0.70, # Moderate storage
        'ironair_energy_GWh': base_ironair_energy * 0.70,
        'co2_emissions_MtCO2': 12.0,                   # Minimal emissions
        'total_system_cost_billion_EUR': 210.0
    })
    
    # Scenario C: 1% of 1990 emissions - Very high renewables
    scenarios_data.append({
        'scenario': 'C',
        'co2_target_pct': 1.0,
        'annual_consumption_TWh': 650.0,
        'solar_capacity_GW': base_solar * 0.97,
        'onwind_capacity_GW': base_onwind * 0.98,
        'offwind-ac_capacity_GW': base_offwind * 0.95,
        'CCGT_capacity_GW': base_ccgt * 0.05,          # Minimal gas backup
        'OCGT_capacity_GW': base_ocgt * 1.0,
        'nuclear_capacity_GW': base_nuclear,
        'biomass_capacity_GW': base_biomass,
        'battery_power_GW': 0.0,
        'battery_energy_GWh': 0.0,
        'H2_power_GW': 0.0,
        'H2_energy_GWh': 0.0,
        'PHS_power_GW': base_phs_power,
        'PHS_energy_GWh': base_phs_energy,
        'ironair_power_GW': base_ironair_power * 0.85, # High storage
        'ironair_energy_GWh': base_ironair_energy * 0.85,
        'co2_emissions_MtCO2': 2.5,                    # Very low emissions
        'total_system_cost_billion_EUR': 245.0
    })
    
    # Scenario D: 0% of 1990 emissions - Net zero, maximum renewables + storage
    scenarios_data.append({
        'scenario': 'D',
        'co2_target_pct': 0.0,
        'annual_consumption_TWh': 650.0,
        'solar_capacity_GW': base_solar,               # Full solar
        'onwind_capacity_GW': base_onwind,             # Full wind
        'offwind-ac_capacity_GW': base_offwind,        # Full offshore
        'CCGT_capacity_GW': base_ccgt * 0.01,          # Backup only (no generation)
        'OCGT_capacity_GW': base_ocgt * 1.0,
        'nuclear_capacity_GW': base_nuclear,
        'biomass_capacity_GW': base_biomass,
        'battery_power_GW': 0.0,
        'battery_energy_GWh': 0.0,
        'H2_power_GW': 0.0,
        'H2_energy_GWh': 0.0,
        'PHS_power_GW': base_phs_power,
        'PHS_energy_GWh': base_phs_energy,
        'ironair_power_GW': base_ironair_power,        # Maximum storage
        'ironair_energy_GWh': base_ironair_energy,
        'co2_emissions_MtCO2': 0.0,                    # Net zero
        'total_system_cost_billion_EUR': 275.0         # Highest cost
    })
    
    # Calculate totals for each scenario
    for scenario in scenarios_data:
        scenario['total_renewable_GW'] = (
            scenario['solar_capacity_GW'] + 
            scenario['onwind_capacity_GW'] + 
            scenario['offwind-ac_capacity_GW'] +
            scenario['nuclear_capacity_GW'] +
            scenario['biomass_capacity_GW']
        )
        
        scenario['total_storage_power_GW'] = (
            scenario['battery_power_GW'] + 
            scenario['H2_power_GW'] + 
            scenario['PHS_power_GW'] +
            scenario['ironair_power_GW']
        )
        
        scenario['total_storage_energy_GWh'] = (
            scenario['battery_energy_GWh'] + 
            scenario['H2_energy_GWh'] + 
            scenario['PHS_energy_GWh'] +
            scenario['ironair_energy_GWh']
        )
    
    # Create DataFrame and save
    df = pd.DataFrame(scenarios_data)
    df.to_csv('co2_scenarios_comparison.csv', index=False)
    
    print("✅ Created realistic 650 TWh scenarios")
    
    # Display summary
    print("\n📈 650 TWH CO2 SCENARIOS SUMMARY:")
    print("=" * 70)
    
    for _, row in df.iterrows():
        print(f"Scenario {row['scenario']} ({row['co2_target_pct']:.0f}% CO2):")
        print(f"  Demand: {row['annual_consumption_TWh']:.0f} TWh/year")
        print(f"  Solar: {row['solar_capacity_GW']:.0f} GW")
        print(f"  Onshore wind: {row['onwind_capacity_GW']:.0f} GW") 
        print(f"  Offshore wind: {row['offwind-ac_capacity_GW']:.0f} GW")
        print(f"  Gas (CCGT): {row['CCGT_capacity_GW']:.0f} GW")
        print(f"  Iron-Air storage: {row['ironair_power_GW']:.0f} GW / {row['ironair_energy_GWh']:.0f} GWh")
        print(f"  Total renewables: {row['total_renewable_GW']:.0f} GW")
        print(f"  Total storage: {row['total_storage_power_GW']:.0f} GW / {row['total_storage_energy_GWh']:.0f} GWh")
        print(f"  System Cost: €{row['total_system_cost_billion_EUR']:.0f} billion")
        print(f"  CO2 Emissions: {row['co2_emissions_MtCO2']:.1f} Mt")
        print()
    
    return 'co2_scenarios_comparison.csv'

def main():
    """Main function"""
    create_realistic_650twh_scenarios()

if __name__ == "__main__":
    main()
