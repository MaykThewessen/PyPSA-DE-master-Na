#!/usr/bin/env python3
"""
Run PyPSA-DE with Iron-Air Battery Storage correctly configured
Based on verified technology data from the dashboard
"""

import os
os.environ['PROJ_NETWORK'] = 'OFF'
os.environ['PYPROJ_GLOBAL_CONTEXT'] = 'ON'

import pypsa
import pandas as pd
import numpy as np
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_iron_air_storage(n):
    """
    Add Iron-Air battery storage to the network with correct parameters.
    
    Iron-Air Battery specifications:
    - Round-trip efficiency: 48%
    - Energy cost: 20,000 EUR/MWh
    - Power cost: 84,000 EUR/MW
    - Duration: 100-400 hours (using 250h typical)
    - Lifetime: 25 years
    """
    
    logger.info("\n🔋 Adding Iron-Air Battery Storage to the network...")
    
    # Iron-Air parameters from verified data
    iron_air_params = {
        'efficiency_store': 0.693,      # sqrt(0.48) for symmetric efficiency
        'efficiency_dispatch': 0.693,   # sqrt(0.48) for symmetric efficiency
        'standing_loss': 0.00001,       # Very low self-discharge (0.001%/hour)
        'capital_cost_energy': 20000,   # EUR/MWh energy capacity
        'capital_cost_power': 84000,    # EUR/MW power capacity
        'marginal_cost': 0.01,          # Near-zero marginal cost
        'lifetime': 25,                 # years
        'max_hours': 400,               # Maximum duration
        'min_hours': 100,               # Minimum duration
        'typical_hours': 250,           # Typical duration for optimization
    }
    
    # Get all buses in the network
    buses = n.buses.index
    
    # Add Iron-Air storage units to each bus
    for bus in buses:
        storage_id = f"iron_air_{bus}"
        
        # Check if this storage unit already exists
        if storage_id not in n.storage_units.index:
            n.add(
                "StorageUnit",
                storage_id,
                bus=bus,
                carrier="iron_air",
                p_nom_extendable=True,
                p_nom=0,  # Start with zero, let optimizer decide
                p_nom_min=0,
                p_nom_max=10000,  # Max 10 GW per node
                efficiency_store=iron_air_params['efficiency_store'],
                efficiency_dispatch=iron_air_params['efficiency_dispatch'],
                standing_loss=iron_air_params['standing_loss'],
                marginal_cost=iron_air_params['marginal_cost'],
                capital_cost=iron_air_params['capital_cost_power'] + 
                            iron_air_params['capital_cost_energy'] / iron_air_params['typical_hours'],
                max_hours=iron_air_params['max_hours'],
                cyclic_state_of_charge=True,
                state_of_charge_initial=0.5,  # Start at 50% charge
            )
            logger.info(f"  Added Iron-Air storage at bus: {bus}")
    
    # Add carrier if it doesn't exist
    if 'iron_air' not in n.carriers.index:
        n.add("Carrier", "iron_air", 
              color='#FF6B35',
              nice_name="Iron-Air Battery")
    
    logger.info(f"✅ Added {len(buses)} Iron-Air storage units to the network")
    return n

def prepare_network_for_renewable_scenario(n):
    """Prepare network for high renewable scenario with storage."""
    
    logger.info("\n📊 Preparing network for renewable + storage scenario...")
    
    # Remove or limit fossil fuel generation
    fossil_carriers = ['coal', 'lignite', 'CCGT', 'OCGT', 'oil', 'gas']
    
    for carrier in fossil_carriers:
        mask = n.generators.carrier.isin([carrier])
        if mask.any():
            # Option 1: Remove fossil generators completely
            # n.generators = n.generators[~mask]
            
            # Option 2: Set fossil capacity to zero (keep for reference)
            n.generators.loc[mask, 'p_nom'] = 0
            n.generators.loc[mask, 'p_nom_max'] = 0
            n.generators.loc[mask, 'p_nom_extendable'] = False
            logger.info(f"  Disabled {carrier} generators")
    
    # Increase renewable capacity limits
    renewable_params = {
        'solar': {'p_nom_max': 200000, 'capital_cost': 370000},      # 200 GW max
        'onwind': {'p_nom_max': 150000, 'capital_cost': 910000},     # 150 GW max
        'offwind-ac': {'p_nom_max': 50000, 'capital_cost': 1370000}, # 50 GW max
        'offwind-dc': {'p_nom_max': 50000, 'capital_cost': 1940000}, # 50 GW max
    }
    
    for carrier, params in renewable_params.items():
        mask = n.generators.carrier == carrier
        if mask.any():
            n.generators.loc[mask, 'p_nom_extendable'] = True
            n.generators.loc[mask, 'p_nom_max'] = params['p_nom_max']
            if 'capital_cost' in params:
                n.generators.loc[mask, 'capital_cost'] = params['capital_cost']
            logger.info(f"  Set {carrier} max capacity to {params['p_nom_max']/1000:.0f} GW")
    
    return n

def solve_network(n, solver='highs', time_limit=3600):
    """Solve the network optimization problem."""
    
    logger.info("\n🔧 Starting network optimization...")
    logger.info(f"  Solver: {solver}")
    logger.info(f"  Time limit: {time_limit} seconds")
    
    # Optimization settings
    solver_options = {
        'highs': {
            'presolve': 'on',
            'parallel': 'on',
            'threads': 4,
            'time_limit': time_limit,
            'mip_feasibility_tolerance': 1e-6,
            'dual_feasibility_tolerance': 1e-6,
            'primal_feasibility_tolerance': 1e-6,
            'log_to_console': True,
        },
        'gurobi': {
            'threads': 4,
            'method': 2,  # Barrier method
            'crossover': 0,
            'BarConvTol': 1e-6,
            'FeasibilityTol': 1e-6,
            'TimeLimit': time_limit,
        }
    }
    
    try:
        # Run optimization
        n.optimize(
            solver_name=solver,
            solver_options=solver_options.get(solver, {})
        )
        
        if n.objective is not None and n.objective > 0:
            logger.info(f"✅ Optimization successful!")
            logger.info(f"  Objective value: {n.objective/1e9:.2f} billion EUR")
            return True
        else:
            logger.warning("⚠️ Optimization completed but no valid objective found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Optimization failed: {e}")
        return False

def analyze_results(n):
    """Analyze and print optimization results."""
    
    logger.info("\n📈 OPTIMIZATION RESULTS")
    logger.info("=" * 60)
    
    # Total system cost
    if hasattr(n, 'objective') and n.objective is not None:
        logger.info(f"\n💰 Total System Cost: {n.objective/1e9:.2f} billion EUR/year")
    
    # Generation capacity results
    logger.info("\n⚡ Optimal Generation Capacities:")
    gen_capacity = n.generators.groupby('carrier')[['p_nom', 'p_nom_opt']].sum()
    gen_capacity['new_capacity'] = gen_capacity['p_nom_opt'] - gen_capacity['p_nom']
    
    for carrier in gen_capacity.index:
        if gen_capacity.loc[carrier, 'p_nom_opt'] > 0:
            logger.info(f"  {carrier:15}: {gen_capacity.loc[carrier, 'p_nom_opt']/1000:8.1f} GW "
                       f"(+{gen_capacity.loc[carrier, 'new_capacity']/1000:6.1f} GW new)")
    
    # Storage capacity results
    logger.info("\n🔋 Optimal Storage Capacities:")
    
    if len(n.storage_units) > 0:
        storage_capacity = n.storage_units.groupby('carrier')[['p_nom', 'p_nom_opt']].sum()
        
        for carrier in storage_capacity.index:
            if storage_capacity.loc[carrier, 'p_nom_opt'] > 0:
                power = storage_capacity.loc[carrier, 'p_nom_opt']
                
                # Calculate energy capacity based on max_hours
                if carrier == 'iron_air':
                    energy = power * 250  # Typical duration
                else:
                    # Get average max_hours for this carrier
                    mask = n.storage_units.carrier == carrier
                    avg_hours = n.storage_units.loc[mask, 'max_hours'].mean()
                    energy = power * avg_hours if not pd.isna(avg_hours) else power * 4
                
                logger.info(f"  {carrier:15}: {power/1000:8.1f} GW power, "
                           f"{energy/1000:8.1f} GWh energy")
    
    # Annual generation by technology
    if hasattr(n, 'generators_t') and hasattr(n.generators_t, 'p'):
        logger.info("\n📊 Annual Generation by Technology:")
        gen_annual = n.generators_t.p.sum() / 1e6  # Convert to TWh
        gen_by_carrier = gen_annual.groupby(n.generators.carrier).sum().sort_values(ascending=False)
        total_gen = gen_by_carrier.sum()
        
        for carrier, generation in gen_by_carrier.items():
            if generation > 0:
                share = generation / total_gen * 100
                logger.info(f"  {carrier:15}: {generation:8.1f} TWh ({share:5.1f}%)")
        
        logger.info(f"  {'TOTAL':15}: {total_gen:8.1f} TWh")
        
        # Calculate renewable share
        renewable_carriers = ['solar', 'onwind', 'offwind-ac', 'offwind-dc', 
                            'hydro', 'ror', 'biomass']
        renewable_gen = gen_by_carrier.reindex(renewable_carriers, fill_value=0).sum()
        renewable_share = renewable_gen / total_gen * 100 if total_gen > 0 else 0
        logger.info(f"\n🌱 Renewable Share: {renewable_share:.1f}%")
    
    # Iron-Air storage statistics
    iron_air_mask = n.storage_units.carrier == 'iron_air'
    if iron_air_mask.any():
        iron_air_units = n.storage_units[iron_air_mask]
        total_iron_air_power = iron_air_units.p_nom_opt.sum()
        total_iron_air_energy = total_iron_air_power * 250  # Typical duration
        
        logger.info("\n🔋 Iron-Air Battery Storage Details:")
        logger.info(f"  Total Power Capacity: {total_iron_air_power/1000:.2f} GW")
        logger.info(f"  Total Energy Capacity: {total_iron_air_energy/1000:.2f} GWh")
        logger.info(f"  Number of Units: {len(iron_air_units)}")
        logger.info(f"  Average Unit Size: {total_iron_air_power/len(iron_air_units):.1f} MW")
        
        # Storage utilization
        if hasattr(n, 'storage_units_t') and hasattr(n.storage_units_t, 'p'):
            iron_air_dispatch = n.storage_units_t.p[iron_air_units.index].sum(axis=1)
            logger.info(f"  Peak Discharge: {iron_air_dispatch.min()/1000:.2f} GW")
            logger.info(f"  Peak Charge: {iron_air_dispatch.max()/1000:.2f} GW")
            
            # Calculate cycles
            total_discharge = iron_air_dispatch[iron_air_dispatch < 0].sum()
            avg_cycles = abs(total_discharge) / total_iron_air_energy if total_iron_air_energy > 0 else 0
            logger.info(f"  Annual Cycles: {avg_cycles:.1f}")

def main():
    """Main function to run PyPSA with Iron-Air storage."""
    
    logger.info("=" * 60)
    logger.info("🔋 PyPSA-DE with Iron-Air Battery Storage")
    logger.info("=" * 60)
    
    # Try to load existing network or create a simple test network
    network_path = "resources/de-all-tech-2035-mayk/networks/base_s_1_elec_.nc"
    
    try:
        # Try loading existing network
        logger.info(f"\n📂 Loading network from {network_path}...")
        n = pypsa.Network(network_path)
        logger.info("✅ Network loaded successfully")
        
    except Exception as e:
        logger.warning(f"⚠️ Could not load network: {e}")
        logger.info("Creating a simple test network instead...")
        
        # Create a simple test network
        n = pypsa.Network()
        n.set_snapshots(pd.date_range("2023-01-01", periods=8760, freq="h"))
        
        # Add a single bus
        n.add("Bus", "DE", v_nom=380)
        
        # Add load
        load_profile = pd.Series(
            50000 + 10000 * np.sin(np.arange(8760) * 2 * np.pi / 8760),
            index=n.snapshots
        )
        n.add("Load", "DE_load", bus="DE", p_set=load_profile)
        
        # Add renewable generators
        n.add("Generator", "solar", bus="DE", carrier="solar",
              p_nom_extendable=True, p_nom_max=100000,
              capital_cost=370000, marginal_cost=0,
              p_max_pu=pd.Series(np.maximum(0, np.sin(np.arange(8760) * 2 * np.pi / 24)), 
                                index=n.snapshots))
        
        n.add("Generator", "wind", bus="DE", carrier="onwind",
              p_nom_extendable=True, p_nom_max=100000,
              capital_cost=910000, marginal_cost=0,
              p_max_pu=pd.Series(0.3 + 0.4 * np.random.random(8760), 
                               index=n.snapshots))
    
    # Add Iron-Air storage
    n = add_iron_air_storage(n)
    
    # Prepare network for renewable scenario
    n = prepare_network_for_renewable_scenario(n)
    
    # Print network summary
    logger.info("\n📋 Network Summary:")
    logger.info(f"  Buses: {len(n.buses)}")
    logger.info(f"  Generators: {len(n.generators)}")
    logger.info(f"  Storage Units: {len(n.storage_units)}")
    logger.info(f"  Snapshots: {len(n.snapshots)}")
    
    # Solve the network
    success = solve_network(n, solver='highs', time_limit=3600)
    
    if success:
        # Analyze results
        analyze_results(n)
        
        # Save results
        output_dir = Path("results/iron_air_scenario")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / "network_solved_iron_air.nc"
        n.export_to_netcdf(str(output_file))
        logger.info(f"\n💾 Results saved to {output_file}")
        
        # Save summary to CSV
        summary_file = output_dir / "iron_air_summary.csv"
        summary_data = {
            'Technology': [],
            'Capacity_GW': [],
            'Generation_TWh': [],
            'Share_%': []
        }
        
        if hasattr(n, 'generators_t') and hasattr(n.generators_t, 'p'):
            gen_annual = n.generators_t.p.sum() / 1e6
            gen_by_carrier = gen_annual.groupby(n.generators.carrier).sum()
            total_gen = gen_by_carrier.sum()
            
            for carrier, generation in gen_by_carrier.items():
                if generation > 0:
                    summary_data['Technology'].append(carrier)
                    summary_data['Capacity_GW'].append(
                        n.generators[n.generators.carrier == carrier].p_nom_opt.sum() / 1000
                    )
                    summary_data['Generation_TWh'].append(generation)
                    summary_data['Share_%'].append(generation / total_gen * 100)
            
            # Add Iron-Air storage
            iron_air_power = n.storage_units[n.storage_units.carrier == 'iron_air'].p_nom_opt.sum()
            if iron_air_power > 0:
                summary_data['Technology'].append('iron_air_storage')
                summary_data['Capacity_GW'].append(iron_air_power / 1000)
                summary_data['Generation_TWh'].append(0)  # Storage doesn't generate
                summary_data['Share_%'].append(0)
            
            pd.DataFrame(summary_data).to_csv(summary_file, index=False)
            logger.info(f"📊 Summary saved to {summary_file}")
        
        logger.info("\n✅ SUCCESS: PyPSA optimization with Iron-Air storage completed!")
        
    else:
        logger.error("\n❌ FAILED: Optimization did not converge")
        logger.info("Try adjusting capacity limits or solver settings")

if __name__ == "__main__":
    main()
