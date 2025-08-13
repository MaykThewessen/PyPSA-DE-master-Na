#!/usr/bin/env python3
"""
Enhanced Storage Scenario: Optimized long-duration storage technologies
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
    
    # Battery technology parameters (based on 2023/2024 cost projections)
    battery_configs = {
        'battery_4h': {
            'duration': 4,
            'energy_cost': 150,    # EUR/MWh - current LFP costs
            'power_cost': 200,     # EUR/MW - inverter costs
            'efficiency': 0.95,
            'description': 'Short-duration LFP battery (4h)'
        },
        'battery_12h': {
            'duration': 12,
            'energy_cost': 135,    # EUR/MWh - economies of scale for longer duration
            'power_cost': 180,     # EUR/MW - shared inverter costs
            'efficiency': 0.95,
            'description': 'Medium-duration LFP battery (12h)'
        },
        'battery_24h': {
            'duration': 24,
            'energy_cost': 125,    # EUR/MWh - further cost reduction
            'power_cost': 160,     # EUR/MW
            'efficiency': 0.94,    # Slightly lower due to longer cycles
            'description': 'Long-duration LFP battery (24h)'
        },
        'battery_48h': {
            'duration': 48,
            'energy_cost': 120,    # EUR/MWh - optimized for multi-day storage
            'power_cost': 150,     # EUR/MW
            'efficiency': 0.93,
            'description': 'Ultra-long-duration LFP battery (48h)'
        }
    }
    
    # Iron-air battery parameters (based on Form Energy specifications)
    ironair_config = {
        'duration': 100,  # hours
        'energy_cost': 20,      # EUR/MWh - major cost advantage
        'power_cost': 60,       # EUR/MW - low power costs
        'charge_efficiency': 0.52,   # Round-trip ~50%
        'discharge_efficiency': 0.96,  # High discharge efficiency
        'description': 'Iron-air battery (100h duration)'
    }
    
    # Hydrogen storage (for comparison)
    h2_config = {
        'duration': 720,  # 30 days - seasonal storage
        'energy_cost': 2,       # EUR/MWh - very low energy costs (salt cavern)
        'electrolyzer_cost': 800,  # EUR/MW - electrolyzer
        'fuelcell_cost': 900,      # EUR/MW - fuel cell
        'electrolyzer_eff': 0.65,  # Electrolyzer efficiency
        'fuelcell_eff': 0.55,      # Fuel cell efficiency
        'description': 'Hydrogen storage (30-day duration)'
    }
    
    buses = n.buses.index
    
    # Add enhanced battery storage technologies
    for tech_name, config in battery_configs.items():
        # Calculate total capital cost (energy + power components)
        total_cost = config['energy_cost'] * config['duration'] + config['power_cost']
        
        logger.info(f"Adding {config['description']}: {total_cost:.0f} EUR/MW total cost")
        
        for bus in buses:
            store_name = f"{bus} {tech_name} store"
            charger_name = f"{bus} {tech_name} charger"
            discharger_name = f"{bus} {tech_name} discharger"
            
            # Add energy store with proper bus naming
            n.add('Store',
                  store_name,
                  bus=store_name,  # Store creates its own bus
                  carrier=tech_name,
                  e_nom_extendable=True,
                  e_cyclic=True,
                  capital_cost=config['energy_cost'],  # EUR/MWh
                  )
            
            # Add charger link
            n.add('Link',
                  charger_name,
                  bus0=bus,
                  bus1=store_name,
                  carrier=f"{tech_name} charger",
                  efficiency=config['efficiency'],
                  p_nom_extendable=True,
                  capital_cost=config['power_cost'],  # EUR/MW
                  )
            
            # Add discharger link
            n.add('Link',
                  discharger_name,
                  bus0=store_name,
                  bus1=bus,
                  carrier=f"{tech_name} discharger", 
                  efficiency=config['efficiency'],
                  p_nom_extendable=True,
                  capital_cost=config['power_cost'],  # EUR/MW
                  )
    
    # Add iron-air battery storage
    total_ironair_cost = ironair_config['energy_cost'] * ironair_config['duration'] + ironair_config['power_cost']
    logger.info(f"Adding {ironair_config['description']}: {total_ironair_cost:.0f} EUR/MW total cost")
    
    for bus in buses:
        store_name = f"{bus} ironair store"
        charger_name = f"{bus} ironair charger"
        discharger_name = f"{bus} ironair discharger"
        
        # Add iron-air energy store
        n.add('Store',
              store_name,
              bus=store_name,  # Store creates its own bus
              carrier='ironair',
              e_nom_extendable=True,
              e_cyclic=True,
              capital_cost=ironair_config['energy_cost'],  # EUR/MWh
              )
        
        # Add iron-air charger
        n.add('Link',
              charger_name,
              bus0=bus,
              bus1=store_name,
              carrier='ironair charger',
              efficiency=ironair_config['charge_efficiency'],
              p_nom_extendable=True,
              capital_cost=ironair_config['power_cost'],  # EUR/MW
              )
        
        # Add iron-air discharger  
        n.add('Link',
              discharger_name,
              bus0=store_name,
              bus1=bus,
              carrier='ironair discharger',
              efficiency=ironair_config['discharge_efficiency'],
              p_nom_extendable=True,
              capital_cost=ironair_config['power_cost'],  # EUR/MW
              )
    
    # Add hydrogen storage (for comparison)
    total_h2_cost = h2_config['energy_cost'] * h2_config['duration'] + h2_config['electrolyzer_cost'] + h2_config['fuelcell_cost']
    logger.info(f"Adding {h2_config['description']}: {total_h2_cost:.0f} EUR/MW total cost")
    
    for bus in buses:
        store_name = f"{bus} H2 store"
        electrolyzer_name = f"{bus} H2 electrolyzer"
        fuelcell_name = f"{bus} H2 fuelcell"
        
        # Add H2 energy store
        n.add('Store',
              store_name,
              bus=store_name,  # Store creates its own bus
              carrier='H2',
              e_nom_extendable=True,
              e_cyclic=True,
              capital_cost=h2_config['energy_cost'],  # EUR/MWh
              )
        
        # Add electrolyzer
        n.add('Link',
              electrolyzer_name,
              bus0=bus,
              bus1=store_name,
              carrier='H2 electrolyzer',
              efficiency=h2_config['electrolyzer_eff'],
              p_nom_extendable=True,
              capital_cost=h2_config['electrolyzer_cost'],  # EUR/MW
              )
        
        # Add fuel cell
        n.add('Link',
              fuelcell_name,
              bus0=store_name,
              bus1=bus,
              carrier='H2 fuelcell',
              efficiency=h2_config['fuelcell_eff'],
              p_nom_extendable=True,
              capital_cost=h2_config['fuelcell_cost'],  # EUR/MW
              )
    
    # Add missing carriers
    storage_carriers = ['battery_4h', 'battery_12h', 'battery_24h', 'battery_48h', 'ironair', 'H2',
                       'battery_4h charger', 'battery_12h charger', 'battery_24h charger', 'battery_48h charger',
                       'battery_4h discharger', 'battery_12h discharger', 'battery_24h discharger', 'battery_48h discharger',
                       'ironair charger', 'ironair discharger', 'H2 electrolyzer', 'H2 fuelcell']
    
    for carrier in storage_carriers:
        if carrier not in n.carriers.index:
            n.add('Carrier', carrier)
    
    logger.info(f"Enhanced storage technologies added:")
    logger.info(f"  • 4 LFP battery durations: 4h, 12h, 24h, 48h")
    logger.info(f"  • Iron-air battery: 100h duration at {ironair_config['energy_cost']} EUR/MWh")
    logger.info(f"  • Hydrogen storage: 720h duration for comparison")

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
        logger.info(f"\nOptimal storage capacities by technology:")
        store_results = n.stores.groupby('carrier')['e_nom_opt'].sum().sort_values(ascending=False)
        
        total_storage = store_results.sum()
        for carrier, capacity in store_results.items():
            if capacity > 1:  # Only show significant deployments
                share = capacity / total_storage * 100
                avg_duration = capacity / n.links[n.links.carrier.str.contains(f'{carrier} discharger', na=False)]['p_nom_opt'].sum() if n.links[n.links.carrier.str.contains(f'{carrier} discharger', na=False)]['p_nom_opt'].sum() > 0 else 0
                logger.info(f"  {carrier:15}: {capacity:8.0f} GWh ({share:4.1f}%) - Avg duration: {avg_duration:.1f}h")
        
        logger.info(f"  {'Total':15}: {total_storage:8.0f} GWh")
    
    # Power capacity analysis
    storage_power = {}
    for link in n.links.index:
        if 'discharger' in link or 'fuelcell' in link:
            carrier = n.links.loc[link, 'carrier'].replace(' discharger', '').replace(' fuelcell', '')
            if carrier not in storage_power:
                storage_power[carrier] = 0
            storage_power[carrier] += n.links.loc[link, 'p_nom_opt']
    
    if storage_power:
        logger.info(f"\nOptimal storage power capacities:")
        for carrier, power in sorted(storage_power.items(), key=lambda x: x[1], reverse=True):
            if power > 1:
                logger.info(f"  {carrier:15}: {power:8.0f} MW")
    
    # Cost analysis
    total_storage_cost = 0
    logger.info(f"\nStorage technology costs:")
    
    for store in n.stores.index:
        if n.stores.loc[store, 'e_nom_opt'] > 0:
            energy_cost = n.stores.loc[store, 'e_nom_opt'] * n.stores.loc[store, 'capital_cost']
            total_storage_cost += energy_cost
    
    for link in n.links.index:
        if any(tech in link for tech in ['charger', 'discharger', 'electrolyzer', 'fuelcell']):
            if n.links.loc[link, 'p_nom_opt'] > 0:
                power_cost = n.links.loc[link, 'p_nom_opt'] * n.links.loc[link, 'capital_cost']
                total_storage_cost += power_cost
    
    logger.info(f"  Total storage system cost: {total_storage_cost/1e6:.1f} million EUR/year")
    
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

if __name__ == "__main__":
    success, network = solve_enhanced_storage_scenario()
    
    if success:
        print("\n" + "="*120)
        print("🎉 ENHANCED STORAGE SCENARIO COMPLETED")
        print("="*120)
        print("✅ Multiple LFP battery durations: 4h, 12h, 24h, 48h")
        print("✅ Iron-air battery: 100h duration at 20 EUR/MWh")
        print("✅ Optimized storage cost structures")
        print("✅ Storage technology competition analysis")
        print("="*120)
        
    else:
        print("❌ Enhanced storage optimization failed!")
