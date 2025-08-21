#!/usr/bin/env python3
"""
Extract correct results from CO2 scenario networks and regenerate CSV
"""

import os
import pypsa
import pandas as pd
import numpy as np
import glob
from datetime import datetime

def extract_scenario_results(scenario_name, co2_target):
    """Extract results from a specific scenario network"""
    
    print(f"📊 Extracting Scenario {scenario_name} ({co2_target*100:.0f}% CO2)...")
    
    try:
        # Find the correct network file
        results_pattern = f"results/de-co2-scenario-{scenario_name}-2035/networks/base_s_1_elec_Co2L{co2_target:.2f}.nc"
        network_files = glob.glob(results_pattern)
        
        if not network_files:
            print(f"⚠️  No network file found for pattern: {results_pattern}")
            return None
        
        network_file = network_files[0]
        print(f"📂 Loading: {network_file}")
        
        # Load network
        n = pypsa.Network(network_file)
        
        # Initialize results dictionary
        results = {
            'scenario': scenario_name,
            'co2_target_pct': co2_target * 100,
            'annual_consumption_TWh': n.loads_t.p.sum().sum() / 1e6  # TWh
        }
        
        # Generator capacities
        generator_mapping = {
            'solar': 'solar_capacity_GW',
            'onwind': 'onwind_capacity_GW', 
            'offwind-ac': 'offwind-ac_capacity_GW',
            'CCGT': 'CCGT_capacity_GW',
            'OCGT': 'OCGT_capacity_GW',
            'nuclear': 'nuclear_capacity_GW',
            'biomass': 'biomass_capacity_GW'
        }
        
        for tech, col_name in generator_mapping.items():
            if tech in n.generators.carrier.values:
                capacity = n.generators[n.generators.carrier == tech].p_nom_opt.sum()
                results[col_name] = capacity / 1000  # Convert MW to GW
            else:
                results[col_name] = 0.0
        
        # Storage extraction - careful to get correct components
        
        # PHS (pumped hydro storage)
        if 'PHS' in n.storage_units.carrier.values:
            phs_units = n.storage_units[n.storage_units.carrier == 'PHS']
            phs_power = phs_units.p_nom_opt.sum()
            phs_energy = (phs_units.max_hours * phs_units.p_nom_opt).sum()
            results['PHS_power_GW'] = phs_power / 1000
            results['PHS_energy_GWh'] = phs_energy / 1000
        else:
            results['PHS_power_GW'] = 0.0
            results['PHS_energy_GWh'] = 0.0
        
        # Battery (store + charger/discharger links)
        battery_stores = n.stores[n.stores.index.str.contains('battery', case=False, na=False)]
        battery_chargers = n.links[n.links.index.str.contains('battery.*charger', case=False, na=False)]
        
        if len(battery_stores) > 0:
            results['battery_energy_GWh'] = battery_stores.e_nom_opt.sum() / 1000
        else:
            results['battery_energy_GWh'] = 0.0
            
        if len(battery_chargers) > 0:
            results['battery_power_GW'] = battery_chargers.p_nom_opt.sum() / 1000
        else:
            results['battery_power_GW'] = 0.0
        
        # Iron-air storage
        ironair_stores = n.stores[n.stores.index.str.contains('iron-air', case=False, na=False)]
        ironair_chargers = n.links[n.links.index.str.contains('iron-air.*charger', case=False, na=False)]
        
        if len(ironair_stores) > 0:
            results['iron-air_energy_GWh'] = ironair_stores.e_nom_opt.sum() / 1000
        else:
            results['iron-air_energy_GWh'] = 0.0
            
        if len(ironair_chargers) > 0:
            results['iron-air_power_GW'] = ironair_chargers.p_nom_opt.sum() / 1000
        else:
            results['iron-air_power_GW'] = 0.0
        
        # Hydrogen storage
        hydrogen_stores = n.stores[n.stores.index.str.contains('Hydrogen', case=False, na=False)]
        hydrogen_electrolysis = n.links[n.links.index.str.contains('Electrolysis', case=False, na=False)]
        
        if len(hydrogen_stores) > 0:
            results['Hydrogen_energy_GWh'] = hydrogen_stores.e_nom_opt.sum() / 1000
        else:
            results['Hydrogen_energy_GWh'] = 0.0
            
        if len(hydrogen_electrolysis) > 0:
            results['Hydrogen_power_GW'] = hydrogen_electrolysis.p_nom_opt.sum() / 1000
        else:
            results['Hydrogen_power_GW'] = 0.0
        
        # Calculate totals
        results['total_renewable_GW'] = (
            results.get('solar_capacity_GW', 0) + 
            results.get('onwind_capacity_GW', 0) + 
            results.get('offwind-ac_capacity_GW', 0)
        )
        
        results['total_storage_power_GW'] = (
            results.get('battery_power_GW', 0) + 
            results.get('Hydrogen_power_GW', 0) + 
            results.get('PHS_power_GW', 0) +
            results.get('iron-air_power_GW', 0)
        )
        
        results['total_storage_energy_GWh'] = (
            results.get('battery_energy_GWh', 0) + 
            results.get('Hydrogen_energy_GWh', 0) + 
            results.get('PHS_energy_GWh', 0) +
            results.get('iron-air_energy_GWh', 0)
        )
        
        # System costs
        results['total_system_cost_billion_EUR'] = n.objective / 1e9
        
        # CO2 emissions - check global constraints or calculate from generation
        results['co2_emissions_MtCO2'] = 0.0  # Will calculate properly if needed
        
        # Check if CO2 constraint is active
        if 'CO2Limit' in n.global_constraints.index:
            constraint = n.global_constraints.loc['CO2Limit']
            results['co2_constraint_active'] = True
            results['co2_limit_Mt'] = constraint.constant / 1e6 if constraint.constant > 0 else 0
        else:
            results['co2_constraint_active'] = False
            results['co2_limit_Mt'] = None
        
        print(f"✅ Scenario {scenario_name}: Cost={results['total_system_cost_billion_EUR']:.2f}B EUR, "
              f"Solar={results['solar_capacity_GW']:.1f}GW, "
              f"Battery={results['battery_energy_GWh']:.1f}GWh, "
              f"H2={results['Hydrogen_energy_GWh']:.1f}GWh")
        
        return results
        
    except Exception as e:
        print(f"❌ Error extracting Scenario {scenario_name}: {e}")
        return None

def main():
    """Extract all scenario results and create corrected CSV"""
    
    print("🔧 CORRECTED CO2 SCENARIOS EXTRACTION")
    print("=" * 60)
    
    # Define scenarios
    scenarios = [
        ('A', 0.15, "15% of 1990 emissions"),
        ('B', 0.05, "5% of 1990 emissions"),
        ('C', 0.01, "1% of 1990 emissions"),
        ('D', 0.00, "0% of 1990 emissions (net-zero)")
    ]
    
    all_results = []
    
    # Extract results for each scenario
    for scenario_name, co2_target, description in scenarios:
        print(f"\n{'='*40}")
        print(f"SCENARIO {scenario_name}: {description}")
        print(f"{'='*40}")
        
        results = extract_scenario_results(scenario_name, co2_target)
        if results:
            all_results.append(results)
        else:
            print(f"⚠️  Failed to extract results for Scenario {scenario_name}")
    
    # Create corrected CSV
    if all_results:
        df = pd.DataFrame(all_results)
        df = df.round(2)
        
        # Save corrected results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        corrected_file = f"co2_scenarios_corrected_{timestamp}.csv"
        df.to_csv(corrected_file, index=False)
        
        print(f"\n📊 CORRECTED RESULTS SUMMARY:")
        print("=" * 60)
        
        for _, row in df.iterrows():
            print(f"Scenario {row['scenario']} ({row['co2_target_pct']:.0f}% CO2):")
            print(f"  Cost: €{row['total_system_cost_billion_EUR']:.2f} billion")
            print(f"  Solar: {row['solar_capacity_GW']:.1f} GW")
            print(f"  Battery: {row['battery_energy_GWh']:.1f} GWh") 
            print(f"  Hydrogen: {row['Hydrogen_energy_GWh']:.1f} GWh")
            print(f"  Iron-Air: {row['iron-air_energy_GWh']:.1f} GWh")
            print()
        
        print(f"✅ Corrected results saved: {corrected_file}")
        return corrected_file
    else:
        print("❌ No results extracted!")
        return None

if __name__ == "__main__":
    main()
