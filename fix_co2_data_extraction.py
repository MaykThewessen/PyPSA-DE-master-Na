#!/usr/bin/env python3
"""
Fixed CO2 Scenarios Data Extraction
Corrects unit conversions and data extraction issues
"""

import pandas as pd
import pypsa
import glob
import os

def extract_results_fixed(scenario_name, co2_target):
    """Extract key results from scenario network file with proper unit conversions"""
    
    print(f"📊 Extracting results for Scenario {scenario_name}...")
    
    try:
        # Find the network file in multiple possible locations
        patterns = [
            f"results/de-co2-scenario-{scenario_name}-2035/networks/base_s_1_elec_Co2L*.nc",
            f"resources/de-co2-scenario-{scenario_name}-2035/networks/base_s_1_elec_Co2L*.nc"
        ]
        
        network_file = None
        for pattern in patterns:
            network_files = glob.glob(pattern)
            if network_files:
                network_file = network_files[0]
                break
        
        if not network_file:
            print(f"⚠️  No network file found for Scenario {scenario_name}")
            return None
        
        print(f"📂 Loading network: {network_file}")
        
        # Load network
        n = pypsa.Network(network_file)
        
        # Extract capacity data
        results = {
            'scenario': scenario_name,
            'co2_target_pct': co2_target * 100,
            'annual_consumption_TWh': n.loads_t.p.sum().sum() / 1e6 # Convert MWh to TWh
        }
        
        # Generator capacities (convert MW to GW)
        for tech in ['solar', 'onwind', 'offwind-ac', 'CCGT', 'OCGT', 'nuclear', 'biomass']:
            if tech in n.generators.carrier.values:
                capacity = n.generators[n.generators.carrier == tech].p_nom_opt.sum() / 1000  # MW to GW
                results[f'{tech}_capacity_GW'] = capacity
            else:
                results[f'{tech}_capacity_GW'] = 0.0
        
        # Storage capacities - check both storage_units and stores
        storage_techs = ['battery', 'Hydrogen', 'PHS', 'iron-air']
        
        for tech in storage_techs:
            power_gw = 0.0
            energy_gwh = 0.0
            
            # Check storage_units
            if hasattr(n, 'storage_units') and not n.storage_units.empty:
                storage_mask = n.storage_units.carrier == tech
                if storage_mask.any():
                    power_gw = n.storage_units[storage_mask].p_nom_opt.sum() / 1000  # MW to GW
                    # For energy, use max_hours * power if available
                    if 'max_hours' in n.storage_units.columns:
                        energy_gwh = (n.storage_units[storage_mask].p_nom_opt * 
                                    n.storage_units[storage_mask].max_hours).sum() / 1000  # MWh to GWh
                    else:
                        # Fallback: estimate energy capacity
                        energy_gwh = power_gw * {'battery': 4, 'PHS': 6, 'iron-air': 100, 'Hydrogen': 720}.get(tech, 4)
            
            # Check stores (especially for Hydrogen)
            if hasattr(n, 'stores') and not n.stores.empty:
                store_mask = n.stores.carrier == tech
                if store_mask.any():
                    store_energy = n.stores[store_mask].e_nom_opt.sum() / 1000  # MWh to GWh
                    energy_gwh = max(energy_gwh, store_energy)
            
            results[f'{tech}_power_GW'] = power_gw
            results[f'{tech}_energy_GWh'] = energy_gwh
        
        # Handle iron-air specifically (might be named differently)
        if results.get('iron-air_power_GW', 0) == 0:
            # Check for alternative names
            alt_names = ['ironair', 'iron_air', 'iron air']
            for alt_name in alt_names:
                if hasattr(n, 'storage_units') and not n.storage_units.empty:
                    mask = n.storage_units.carrier == alt_name
                    if mask.any():
                        results['iron-air_power_GW'] = n.storage_units[mask].p_nom_opt.sum() / 1000
                        if 'max_hours' in n.storage_units.columns:
                            results['iron-air_energy_GWh'] = (n.storage_units[mask].p_nom_opt * 
                                                            n.storage_units[mask].max_hours).sum() / 1000
                        else:
                            results['iron-air_energy_GWh'] = results['iron-air_power_GW'] * 100
                        break
        
        # Rename iron-air to ironair for consistency with dashboard
        results['ironair_power_GW'] = results.pop('iron-air_power_GW', 0.0)
        results['ironair_energy_GWh'] = results.pop('iron-air_energy_GWh', 0.0)
        
        # System totals
        results['total_renewable_GW'] = (
            results.get('solar_capacity_GW', 0) + 
            results.get('onwind_capacity_GW', 0) + 
            results.get('offwind-ac_capacity_GW', 0) +
            results.get('nuclear_capacity_GW', 0) +
            results.get('biomass_capacity_GW', 0)
        )
        
        results['total_storage_power_GW'] = (
            results.get('battery_power_GW', 0) + 
            results.get('Hydrogen_power_GW', 0) + 
            results.get('PHS_power_GW', 0) +
            results.get('ironair_power_GW', 0)
        )
        
        results['total_storage_energy_GWh'] = (
            results.get('battery_energy_GWh', 0) + 
            results.get('Hydrogen_energy_GWh', 0) + 
            results.get('PHS_energy_GWh', 0) +
            results.get('ironair_energy_GWh', 0)
        )
        
        # System costs (convert from EUR to billion EUR)
        if hasattr(n, 'objective'):
            results['total_system_cost_billion_EUR'] = n.objective / 1e9
        else:
            # Estimate from component costs
            total_cost = 0
            if hasattr(n, 'generators'):
                total_cost += (n.generators.p_nom_opt * n.generators.capital_cost).sum()
            if hasattr(n, 'storage_units'):
                total_cost += (n.storage_units.p_nom_opt * n.storage_units.capital_cost).sum()
            results['total_system_cost_billion_EUR'] = total_cost / 1e9
        
        # CO2 emissions calculation
        co2_emissions = 0
        if hasattr(n, 'generators_t') and hasattr(n.generators_t, 'p'):
            for carrier in ['CCGT', 'OCGT', 'coal', 'lignite']:
                if carrier in n.generators.carrier.values:
                    gen_idx = n.generators[n.generators.carrier == carrier].index
                    if len(gen_idx) > 0:
                        generation = n.generators_t.p[gen_idx].sum().sum() / 1e6  # Convert to TWh
                        co2_intensity = {'CCGT': 0.35, 'OCGT': 0.45, 'coal': 0.82, 'lignite': 0.95}.get(carrier, 0)
                        co2_emissions += generation * co2_intensity  # Mt CO2
        
        results['co2_emissions_MtCO2'] = co2_emissions
        
        print(f"✅ Results extracted for Scenario {scenario_name}")
        print(f"   Renewable capacity: {results['total_renewable_GW']:.1f} GW")
        print(f"   Storage capacity: {results['total_storage_power_GW']:.1f} GW")
        print(f"   System cost: €{results['total_system_cost_billion_EUR']:.1f} billion")
        
        return results
        
    except Exception as e:
        print(f"❌ Error extracting results for Scenario {scenario_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Re-extract all scenario results with proper unit conversions"""
    
    print("🔧 Fixing CO2 Scenarios Data Extraction...")
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
        
        results = extract_results_fixed(scenario_name, co2_target)
        if results:
            all_results.append(results)
    
    if all_results:
        # Create corrected comparison CSV
        df = pd.DataFrame(all_results)
        
        # Save to CSV
        comparison_file = "co2_scenarios_comparison.csv"
        df.to_csv(comparison_file, index=False)
        
        print(f"\n✅ Corrected comparison saved: {comparison_file}")
        
        # Display summary
        print("\n📈 CORRECTED SCENARIO COMPARISON SUMMARY:")
        print("=" * 60)
        
        for _, row in df.iterrows():
            print(f"Scenario {row['scenario']} ({row['co2_target_pct']:.0f}% CO2):")
            print(f"  Consumption: {row['annual_consumption_TWh']:.1f} TWh/year")
            print(f"  Renewables: {row['total_renewable_GW']:.1f} GW")
            print(f"  Storage: {row['total_storage_power_GW']:.1f} GW / {row['total_storage_energy_GWh']:.1f} GWh")
            print(f"  System Cost: €{row['total_system_cost_billion_EUR']:.1f} billion")
            print(f"  CO2 Emissions: {row['co2_emissions_MtCO2']:.1f} Mt")
            print()
        
        return comparison_file
    else:
        print("\n❌ No results could be extracted")
        return None

if __name__ == "__main__":
    main()
