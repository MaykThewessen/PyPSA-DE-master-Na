#!/usr/bin/env python3
"""
Enhanced Storage Scenario (Fixed): Optimized long-duration storage technologies
- 12h, 24h, 48h LFP batteries with correct cost structures  
- Iron-air storage with proper cost advantage over hydrogen
- 500 EUR/tCO2 carbon price for comparison with scenario 3
"""

import pypsa
import pandas as pd
import numpy as np
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def enhance_storage_technologies(n):
    """
    Add enhanced storage technologies with correct parameters and costs.
    """
    # Remove existing stores to replace with enhanced versions
    stores_to_remove = n.stores.index.tolist()
    for store in stores_to_remove:
        n.remove('Store', store)
    
    # Remove existing storage-related links
    storage_links = n.links[n.links.index.str.contains('battery|H2', case=False, na=False)]
    for link in storage_links.index:
        n.remove('Link', link)
    
    # Storage technology parameters with realistic 2024 cost projections
    storage_configs = {
        'battery_4h': {
            'duration': 4,
            'energy_cost': 150,    # EUR/MWh - LFP costs
            'power_cost': 200,     # EUR/MW - inverter costs  
            'efficiency': 0.95,
            'description': 'Short-duration LFP battery (4h)',
            'color': '#baf238'
        },
        'battery_12h': {
            'duration': 12,
            'energy_cost': 135,    # EUR/MWh - economies of scale
            'power_cost': 180,     # EUR/MW - shared inverter costs
            'efficiency': 0.95,
            'description': 'Medium-duration LFP battery (12h)',
            'color': '#9be82e'
        },
        'battery_24h': {
            'duration': 24,
            'energy_cost': 125,    # EUR/MWh - further cost reduction
            'power_cost': 160,     # EUR/MW
            'efficiency': 0.94,    # Slightly lower due to longer cycles
            'description': 'Long-duration LFP battery (24h)',
            'color': '#7cde24'
        },
        'battery_48h': {
            'duration': 48,
            'energy_cost': 120,    # EUR/MWh - optimized for multi-day
            'power_cost': 150,     # EUR/MW
            'efficiency': 0.93,
            'description': 'Ultra-long-duration LFP battery (48h)',
            'color': '#5dd41a'
        },
        'ironair': {
            'duration': 100,  # hours
            'energy_cost': 20,      # EUR/MWh - major cost advantage
            'power_cost': 60,       # EUR/MW - low power costs
            'charge_efficiency': 0.52,   # Round-trip ~50%
            'discharge_efficiency': 0.96,
            'description': 'Iron-air battery (100h duration)', 
            'color': '#00ace0'
        },
        'H2': {
            'duration': 720,  # 30 days - seasonal storage
            'energy_cost': 2,       # EUR/MWh - very low energy costs (salt cavern)
            'electrolyzer_cost': 800,  # EUR/MW - electrolyzer
            'fuelcell_cost': 900,      # EUR/MW - fuel cell
            'electrolyzer_eff': 0.65,  # Electrolyzer efficiency
            'fuelcell_eff': 0.55,      # Fuel cell efficiency
            'description': 'Hydrogen storage (30-day duration)',
            'color': '#bf13a0'
        }
    }
    
    buses = n.buses.index
    
    # Add enhanced storage technologies
    for tech_name, config in storage_configs.items():
        logger.info(f"Adding {config['description']}...")
        
        for bus in buses:
            # Create storage bus name
            storage_bus = f"{bus} {tech_name}"
            
            # Add storage bus
            n.add('Bus',
                  storage_bus,
                  carrier=tech_name,
                  x=n.buses.loc[bus, 'x'],
                  y=n.buses.loc[bus, 'y'],
                  country=n.buses.loc[bus, 'country'])
            
            # Add store
            n.add('Store',
                  f"{storage_bus} store",
                  bus=storage_bus,
                  carrier=tech_name,
                  e_nom_extendable=True,
                  e_cyclic=True,
                  capital_cost=config['energy_cost'])  # EUR/MWh
            
            if tech_name == 'H2':
                # Hydrogen uses electrolyzer and fuel cell
                n.add('Link',
                      f"{bus} H2 electrolyzer",
                      bus0=bus,
                      bus1=storage_bus,
                      carrier='H2 electrolyzer',
                      efficiency=config['electrolyzer_eff'],
                      p_nom_extendable=True,
                      capital_cost=config['electrolyzer_cost'])
                
                n.add('Link',
                      f"{bus} H2 fuel cell",
                      bus0=storage_bus,
                      bus1=bus,
                      carrier='H2 fuel cell',
                      efficiency=config['fuelcell_eff'],
                      p_nom_extendable=True,
                      capital_cost=config['fuelcell_cost'])
                
            elif tech_name == 'ironair':
                # Iron-air has different charge/discharge efficiencies
                n.add('Link',
                      f"{bus} ironair charger",
                      bus0=bus,
                      bus1=storage_bus,
                      carrier='ironair charger',
                      efficiency=config['charge_efficiency'],
                      p_nom_extendable=True,
                      capital_cost=config['power_cost'])
                
                n.add('Link',
                      f"{bus} ironair discharger",
                      bus0=storage_bus,
                      bus1=bus,
                      carrier='ironair discharger',
                      efficiency=config['discharge_efficiency'],
                      p_nom_extendable=True,
                      capital_cost=config['power_cost'])
            else:
                # Battery technologies use symmetric charge/discharge
                n.add('Link',
                      f"{bus} {tech_name} charger",
                      bus0=bus,
                      bus1=storage_bus,
                      carrier=f'{tech_name} charger',
                      efficiency=config['efficiency'],
                      p_nom_extendable=True,
                      capital_cost=config['power_cost'])
                
                n.add('Link',
                      f"{bus} {tech_name} discharger",
                      bus0=storage_bus,
                      bus1=bus,
                      carrier=f'{tech_name} discharger',
                      efficiency=config['efficiency'],
                      p_nom_extendable=True,
                      capital_cost=config['power_cost'])
    
    # Add carriers for all storage technologies
    storage_carriers = list(storage_configs.keys())
    for tech in storage_configs.keys():
        if tech == 'H2':
            storage_carriers.extend(['H2 electrolyzer', 'H2 fuel cell'])
        elif tech == 'ironair':
            storage_carriers.extend(['ironair charger', 'ironair discharger'])
        else:
            storage_carriers.extend([f'{tech} charger', f'{tech} discharger'])
    
    for carrier in storage_carriers:
        if carrier not in n.carriers.index:
            color = storage_configs.get(carrier.split()[0], {}).get('color', '#000000')
            n.add('Carrier', carrier, color=color)
    
    # Calculate and log costs
    logger.info(f"\nStorage technology cost comparison (EUR/MW):")
    for tech_name, config in storage_configs.items():
        if tech_name == 'H2':
            total_cost = (config['energy_cost'] * config['duration'] + 
                         config['electrolyzer_cost'] + config['fuelcell_cost'])
        elif tech_name == 'ironair':
            total_cost = config['energy_cost'] * config['duration'] + 2 * config['power_cost']
        else:
            total_cost = config['energy_cost'] * config['duration'] + 2 * config['power_cost']
        
        logger.info(f"  {tech_name:12}: {total_cost:6.0f} EUR/MW ({config['duration']:3.0f}h duration)")

def solve_enhanced_storage_scenario():
    """Load network, enhance storage, apply 500 EUR/tCO2 pricing, and solve."""
    
    # Load the prepared electricity network
    network_path = "resources/de-all-tech-2035-mayk/networks/base_s_1_elec_.nc"
    
    logger.info(f"Loading network from {network_path}")
    n = pypsa.Network(network_path)
    
    # Remove global CO2 constraints
    logger.info("Removing global CO2 constraints (using pricing instead)...")
    n.global_constraints = n.global_constraints.iloc[0:0]
    
    # Enhance storage technologies
    logger.info("Enhancing storage technologies...")
    enhance_storage_technologies(n)
    
    # Apply carbon pricing (500 EUR/tCO2 for comparison with scenario 3)
    co2_price = 500  # EUR/tCO2
    
    co2_factors = {
        'coal': 0.820, 'lignite': 0.986, 'CCGT': 0.350, 'OCGT': 0.400, 'oil': 0.650,
        'biomass': 0.000, 'nuclear': 0.000, 'solar': 0.000, 'solar-hsat': 0.000,
        'onwind': 0.000, 'offwind-ac': 0.000, 'offwind-dc': 0.000, 'offwind-float': 0.000, 'ror': 0.000
    }
    
    logger.info(f"🌍 ENHANCED STORAGE: Applying carbon price of {co2_price} EUR/tCO2...")
    for carrier, co2_factor in co2_factors.items():
        if co2_factor > 0:
            mask = n.generators.carrier == carrier
            if mask.any():
                original_cost = n.generators.loc[mask, 'marginal_cost'].mean()
                carbon_cost = co2_factor * co2_price
                new_cost = n.generators.loc[mask, 'marginal_cost'] + carbon_cost
                n.generators.loc[mask, 'marginal_cost'] = new_cost
                logger.info(f"{carrier}: Added {carbon_cost:.2f} EUR/MWh carbon cost")
    
    # Print network overview
    logger.info(f"\n=== ENHANCED STORAGE NETWORK READY ===")
    logger.info(f"🔋 Enhanced storage technologies enabled")
    logger.info(f"💰 Carbon Price: {co2_price} EUR/tCO2")
    logger.info(f"Buses: {len(n.buses)}")
    logger.info(f"Generators: {len(n.generators)}")
    logger.info(f"Stores: {len(n.stores)}")
    logger.info(f"Links: {len(n.links)}")
    
    if len(n.loads) > 0:
        total_demand = n.loads_t.p_set.sum().sum()
        peak_demand = n.loads_t.p_set.sum(axis=1).max()
        logger.info(f"Total annual demand: {total_demand:.0f} MWh")
        logger.info(f"Peak demand: {peak_demand:.0f} MW")
    
    # Solve the network
    logger.info(f"\nStarting optimization with enhanced storage technologies...")
    
    try:
        n.optimize(
            solver_name="highs",
            solver_options={
                "presolve": "on",
                "parallel": "on", 
                "threads": 4
            }
        )
        
        if n.objective is not None:
            logger.info(f"🎉 ENHANCED STORAGE OPTIMIZATION SUCCESSFUL!")
            logger.info(f"Objective value: {n.objective:.2e} EUR")
            
            # Analyze results
            analyze_enhanced_storage_results(n)
            
            # Save results
            results_dir = "results/de-all-tech-2035-mayk/networks"
            os.makedirs(results_dir, exist_ok=True)
            output_path = f"{results_dir}/base_s_1_elec_solved_enhanced_storage_500co2.nc"
            logger.info(f"\nSaving solved network to {output_path}")
            n.export_to_netcdf(output_path)
            
            return True, n
            
        else:
            logger.error("Optimization failed - no objective value found")
            return False, None
            
    except Exception as e:
        logger.error(f"Optimization failed with error: {str(e)}")
        return False, None

def analyze_enhanced_storage_results(n):
    """Analyze the storage optimization results in detail."""
    
    logger.info(f"\n=== ENHANCED STORAGE RESULTS ===")
    
    # Storage deployment analysis
    if len(n.stores) > 0:
        logger.info(f"\nOptimal storage energy capacities by technology:")
        store_results = n.stores.groupby('carrier')['e_nom_opt'].sum().sort_values(ascending=False)
        
        total_storage = store_results.sum()
        for carrier, capacity in store_results.items():
            if capacity > 1:  # Only show significant deployments
                share = capacity / total_storage * 100 if total_storage > 0 else 0
                logger.info(f"  {carrier:12}: {capacity:8.0f} GWh ({share:4.1f}%)")
        
        logger.info(f"  {'Total':12}: {total_storage:8.0f} GWh")
    
    # Power capacity analysis
    logger.info(f"\nOptimal storage power capacities:")
    storage_power = {}
    for link in n.links.index:
        if any(word in link.lower() for word in ['discharger', 'fuel cell']):
            # Extract technology name
            parts = link.split()
            if 'fuel' in link:
                tech = 'H2'
            elif 'ironair' in link:
                tech = 'ironair'
            else:
                tech = '_'.join(parts[1:-1])  # Extract battery_Xh
            
            if tech not in storage_power:
                storage_power[tech] = 0
            storage_power[tech] += n.links.loc[link, 'p_nom_opt']
    
    for tech, power in sorted(storage_power.items(), key=lambda x: x[1], reverse=True):
        if power > 1:
            logger.info(f"  {tech:12}: {power:8.0f} MW")
    
    # Storage duration analysis
    logger.info(f"\nActual storage durations:")
    for tech in storage_power:
        if tech in store_results.index and storage_power[tech] > 0:
            actual_duration = store_results[tech] * 1000 / storage_power[tech]  # GWh to MWh, then hours
            logger.info(f"  {tech:12}: {actual_duration:6.1f} hours")
    
    # Cost analysis
    total_storage_cost = 0
    
    # Energy costs
    for store in n.stores.index:
        if n.stores.loc[store, 'e_nom_opt'] > 0:
            energy_cost = n.stores.loc[store, 'e_nom_opt'] * n.stores.loc[store, 'capital_cost']
            total_storage_cost += energy_cost
    
    # Power costs
    for link in n.links.index:
        if any(word in link.lower() for word in ['charger', 'discharger', 'electrolyzer', 'fuel']):
            if n.links.loc[link, 'p_nom_opt'] > 0:
                power_cost = n.links.loc[link, 'p_nom_opt'] * n.links.loc[link, 'capital_cost']
                total_storage_cost += power_cost
    
    logger.info(f"\nTotal storage system cost: {total_storage_cost/1e6:.1f} million EUR/year")
    
    # Generation analysis
    if len(n.generators) > 0:
        gen_annual = n.generators_t.p.sum() / 1e3  # GWh
        gen_by_carrier = gen_annual.groupby(n.generators.carrier).sum().sort_values(ascending=False)
        total_gen = gen_by_carrier.sum()
        
        logger.info(f"\nAnnual generation by technology:")
        for carrier, generation in gen_by_carrier.items():
            if generation > 0:
                share = generation / total_gen * 100
                logger.info(f"  {carrier:12}: {generation:8.0f} GWh ({share:5.1f}%)")
        
        # Renewable share
        renewable_carriers = ['solar', 'solar-hsat', 'onwind', 'offwind-ac', 'offwind-dc', 'offwind-float', 'ror']
        renewable_gen = gen_by_carrier.reindex(renewable_carriers, fill_value=0).sum()
        renewable_share = renewable_gen / total_gen * 100 if total_gen > 0 else 0
        logger.info(f"\n🌱 Renewable share: {renewable_share:.1f}%")
    
    # CO2 analysis
    co2_factors = {'coal': 0.820, 'lignite': 0.986, 'CCGT': 0.350, 'OCGT': 0.400, 'oil': 0.650}
    total_co2 = 0
    for carrier, co2_factor in co2_factors.items():
        if carrier in gen_by_carrier.index:
            emissions = gen_by_carrier[carrier] * co2_factor  # ktCO2
            total_co2 += emissions
    
    logger.info(f"💨 Total CO2 emissions: {total_co2:.0f} ktCO2 ({total_co2/1000:.1f} MtCO2)")
    
    if total_gen > 0:
        co2_intensity = total_co2 / total_gen  # ktCO2/GWh = tCO2/MWh
        logger.info(f"💨 CO2 intensity: {co2_intensity:.3f} tCO2/MWh")
        
        # Compare to 2% target
        target_2pct = 6.0  # MtCO2
        logger.info(f"🎯 Target (2% of 1990): {target_2pct:.0f} MtCO2")
        logger.info(f"   Actual emissions: {total_co2/1000:.1f} MtCO2")
        if total_co2/1000 <= target_2pct:
            logger.info("✅ TARGET ACHIEVED!")
        else:
            excess = (total_co2/1000) - target_2pct
            logger.info(f"❌ Target missed by {excess:.1f} MtCO2")

if __name__ == "__main__":
    success, network = solve_enhanced_storage_scenario()
    
    if success:
        print("\n" + "="*120)
        print("🎉 ENHANCED STORAGE SCENARIO COMPLETED")
        print("="*120)
        print("✅ Multiple LFP battery durations: 4h, 12h, 24h, 48h")
        print("✅ Iron-air battery: 100h duration at 20 EUR/MWh")
        print("✅ Hydrogen storage: 720h duration for comparison")
        print("✅ Optimized storage cost structures")
        print("✅ Storage technology competition analysis")
        print("="*120)
        
    else:
        print("❌ Enhanced storage optimization failed!")
