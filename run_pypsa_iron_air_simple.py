#!/usr/bin/env python3
"""
Simplified PyPSA run with Iron-Air Battery Storage
Avoids projection issues by creating a basic network
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path

# Delay pypsa import and handle projection issue
import os
os.environ['PROJ_NETWORK'] = 'OFF'
os.environ['PYPROJ_GLOBAL_CONTEXT'] = 'ON'
os.environ['PROJ_LIB'] = ''

import warnings
warnings.filterwarnings('ignore', category=UserWarning)

# Now import pypsa with a workaround
try:
    import pypsa
    # Monkey-patch to avoid CRS issues
    pypsa.Network._crs = None
except Exception as e:
    print(f"Warning: PyPSA import issue - {e}")
    import pypsa

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def create_simple_network_with_iron_air():
    """Create a simple test network with Iron-Air storage."""
    
    logger.info("🔨 Creating simplified network with Iron-Air storage...")
    
    # Create network without CRS
    n = pypsa.Network()
    n._crs = None  # Explicitly set to None to avoid projection issues
    
    # Set time series (one year, hourly resolution)
    n.set_snapshots(pd.date_range("2023-01-01", periods=8760, freq="h"))
    
    # Add main bus
    n.add("Bus", "DE", v_nom=380)
    
    # Create realistic load profile (Germany-like)
    hours = np.arange(8760)
    # Base load + daily variation + seasonal variation
    daily_pattern = 1 + 0.3 * np.sin(2 * np.pi * hours / 24 - np.pi/2)
    seasonal_pattern = 1 + 0.2 * np.cos(2 * np.pi * hours / 8760)
    random_variation = 1 + 0.05 * np.random.randn(8760)
    
    base_load = 60000  # 60 GW average
    load_profile = base_load * daily_pattern * seasonal_pattern * random_variation
    load_profile = np.maximum(load_profile, 30000)  # Minimum 30 GW
    load_profile = np.minimum(load_profile, 85000)  # Maximum 85 GW
    
    n.add("Load", "DE_load", 
          bus="DE", 
          p_set=pd.Series(load_profile, index=n.snapshots))
    
    logger.info(f"  Added load: avg={load_profile.mean()/1000:.1f} GW, peak={load_profile.max()/1000:.1f} GW")
    
    # Add renewable generators with realistic profiles
    
    # Solar PV
    solar_profile = np.zeros(8760)
    for h in range(8760):
        hour_of_day = h % 24
        day_of_year = h // 24
        # Daily solar pattern (peaks at noon)
        if 6 <= hour_of_day <= 18:
            solar_intensity = np.sin((hour_of_day - 6) * np.pi / 12)
        else:
            solar_intensity = 0
        # Seasonal variation (stronger in summer)
        seasonal_factor = 0.5 + 0.5 * np.cos(2 * np.pi * (day_of_year - 172) / 365)
        # Cloud cover variation
        cloud_factor = 0.7 + 0.3 * np.random.random()
        solar_profile[h] = solar_intensity * seasonal_factor * cloud_factor
    
    n.add("Generator", "solar", 
          bus="DE", 
          carrier="solar",
          p_nom_extendable=True, 
          p_nom=0,
          p_nom_min=0,
          p_nom_max=200000,  # 200 GW max
          capital_cost=370000,  # EUR/MW
          marginal_cost=0,
          p_max_pu=pd.Series(solar_profile, index=n.snapshots))
    
    logger.info("  Added solar generator (max 200 GW)")
    
    # Wind power
    wind_profile = np.zeros(8760)
    for h in range(8760):
        # Base wind speed with daily and seasonal patterns
        base_wind = 0.4
        daily_var = 0.1 * np.sin(2 * np.pi * h / 24)
        seasonal_var = 0.2 * np.cos(2 * np.pi * h / 8760)
        random_var = 0.3 * np.random.random()
        wind_profile[h] = np.clip(base_wind + daily_var + seasonal_var + random_var, 0, 1)
    
    n.add("Generator", "onwind", 
          bus="DE", 
          carrier="onwind",
          p_nom_extendable=True,
          p_nom=0,
          p_nom_min=0,
          p_nom_max=150000,  # 150 GW max
          capital_cost=910000,  # EUR/MW
          marginal_cost=0,
          p_max_pu=pd.Series(wind_profile, index=n.snapshots))
    
    logger.info("  Added onshore wind generator (max 150 GW)")
    
    # Add backup gas generator (limited use for grid stability)
    n.add("Generator", "OCGT",
          bus="DE",
          carrier="OCGT",
          p_nom_extendable=False,
          p_nom=5000,  # 5 GW fixed capacity
          marginal_cost=200,  # High cost to minimize use
          efficiency=0.39)
    
    logger.info("  Added 5 GW backup gas generator")
    
    # Add Iron-Air Battery Storage with correct parameters
    logger.info("\n🔋 Adding Iron-Air Battery Storage...")
    
    iron_air_params = {
        'carrier': 'iron_air',
        'bus': 'DE',
        'p_nom_extendable': True,
        'p_nom': 0,
        'p_nom_min': 0,
        'p_nom_max': 50000,  # 50 GW max power
        'efficiency_store': 0.693,  # sqrt(0.48) for 48% round-trip
        'efficiency_dispatch': 0.693,
        'standing_loss': 0.00001,  # 0.001% per hour
        'max_hours': 250,  # 250 hours typical duration
        'marginal_cost': 0.01,
        'capital_cost': 164000,  # Combined: 84k EUR/MW + 20k EUR/MWh * 250h
        'cyclic_state_of_charge': True,
        'state_of_charge_initial': 0.5,
    }
    
    n.add("StorageUnit", "iron_air_DE", **iron_air_params)
    
    energy_capacity_max = iron_air_params['p_nom_max'] * iron_air_params['max_hours'] / 1000
    logger.info(f"  Iron-Air: max {iron_air_params['p_nom_max']/1000:.0f} GW power, "
                f"{energy_capacity_max:.0f} GWh energy")
    logger.info(f"  Efficiency: {iron_air_params['efficiency_store']**2*100:.1f}% round-trip")
    logger.info(f"  Capital cost: {iron_air_params['capital_cost']/1000:.0f} k€/MW")
    
    # Also add a short-duration battery for comparison
    n.add("StorageUnit", "battery_DE",
          carrier="battery",
          bus="DE",
          p_nom_extendable=True,
          p_nom=0,
          p_nom_min=0,
          p_nom_max=30000,  # 30 GW max
          efficiency_store=0.95,
          efficiency_dispatch=0.95,
          standing_loss=0.00001,
          max_hours=4,  # 4-hour battery
          marginal_cost=0.01,
          capital_cost=150000,  # EUR/MW for 4-hour battery
          cyclic_state_of_charge=True,
          state_of_charge_initial=0.5)
    
    logger.info("  Added 4-hour Li-ion battery for comparison (max 30 GW)")
    
    return n

def solve_and_analyze(n):
    """Solve the network and analyze results."""
    
    logger.info("\n🚀 Starting optimization...")
    logger.info(f"  Network has {len(n.buses)} buses, {len(n.generators)} generators, "
                f"{len(n.storage_units)} storage units")
    logger.info(f"  Time period: {len(n.snapshots)} hours")
    
    # Solve with HiGHS
    try:
        n.optimize(
            solver_name='highs',
            solver_options={
                'threads': 4,
                'solver': 'ipm',  # Interior point method
                'run_crossover': 'off',  # Faster without crossover
                'time_limit': 600,  # 10 minutes max
            }
        )
        
        if n.objective is None or n.objective <= 0:
            logger.error("❌ Optimization failed - no valid objective")
            return False
            
    except Exception as e:
        logger.error(f"❌ Optimization error: {e}")
        return False
    
    logger.info(f"\n✅ Optimization successful!")
    logger.info(f"💰 Total system cost: {n.objective/1e9:.2f} billion EUR/year")
    
    # Analyze generation
    logger.info("\n⚡ Optimal Capacities:")
    
    # Generators
    for gen in n.generators.index:
        carrier = n.generators.at[gen, 'carrier']
        p_nom = n.generators.at[gen, 'p_nom']
        p_nom_opt = n.generators.at[gen, 'p_nom_opt']
        if p_nom_opt > 0:
            logger.info(f"  {carrier:12}: {p_nom_opt/1000:8.1f} GW "
                       f"(was {p_nom/1000:.1f} GW)")
    
    # Storage
    logger.info("\n🔋 Storage Capacities:")
    for storage in n.storage_units.index:
        carrier = n.storage_units.at[storage, 'carrier']
        p_nom_opt = n.storage_units.at[storage, 'p_nom_opt']
        max_hours = n.storage_units.at[storage, 'max_hours']
        if p_nom_opt > 0:
            energy = p_nom_opt * max_hours / 1000
            logger.info(f"  {carrier:12}: {p_nom_opt/1000:8.1f} GW power, "
                       f"{energy:8.1f} GWh energy")
    
    # Generation statistics
    if hasattr(n, 'generators_t') and hasattr(n.generators_t, 'p'):
        logger.info("\n📊 Annual Generation:")
        total_gen = 0
        gen_by_tech = {}
        
        for gen in n.generators.index:
            carrier = n.generators.at[gen, 'carrier']
            annual_gen = n.generators_t.p[gen].sum() / 1e6  # TWh
            if carrier not in gen_by_tech:
                gen_by_tech[carrier] = 0
            gen_by_tech[carrier] += annual_gen
            total_gen += annual_gen
        
        for carrier, gen in sorted(gen_by_tech.items(), key=lambda x: -x[1]):
            if gen > 0:
                share = gen / total_gen * 100
                logger.info(f"  {carrier:12}: {gen:8.1f} TWh ({share:5.1f}%)")
        
        logger.info(f"  {'TOTAL':12}: {total_gen:8.1f} TWh")
        
        # Renewable share
        renewable = sum(gen_by_tech.get(c, 0) for c in ['solar', 'onwind', 'offwind'])
        renewable_share = renewable / total_gen * 100 if total_gen > 0 else 0
        logger.info(f"\n🌱 Renewable share: {renewable_share:.1f}%")
    
    # Storage utilization
    if hasattr(n, 'storage_units_t') and hasattr(n.storage_units_t, 'p'):
        logger.info("\n📈 Storage Utilization:")
        
        for storage in n.storage_units.index:
            if n.storage_units.at[storage, 'p_nom_opt'] > 0:
                carrier = n.storage_units.at[storage, 'carrier']
                dispatch = n.storage_units_t.p[storage]
                charge = dispatch[dispatch > 0].sum() / 1e6  # TWh charged
                discharge = -dispatch[dispatch < 0].sum() / 1e6  # TWh discharged
                
                p_nom_opt = n.storage_units.at[storage, 'p_nom_opt']
                max_hours = n.storage_units.at[storage, 'max_hours']
                energy_capacity = p_nom_opt * max_hours / 1e6  # TWh
                
                cycles = discharge / energy_capacity if energy_capacity > 0 else 0
                
                logger.info(f"\n  {carrier}:")
                logger.info(f"    Charged: {charge:.2f} TWh")
                logger.info(f"    Discharged: {discharge:.2f} TWh")
                logger.info(f"    Full cycles: {cycles:.1f}")
                logger.info(f"    Peak charge: {dispatch.max()/1000:.1f} GW")
                logger.info(f"    Peak discharge: {-dispatch.min()/1000:.1f} GW")
    
    return True

def main():
    """Main execution function."""
    
    logger.info("=" * 60)
    logger.info("🔋 PYPSA WITH IRON-AIR BATTERY STORAGE")
    logger.info("=" * 60)
    
    # Create network
    n = create_simple_network_with_iron_air()
    
    # Solve and analyze
    success = solve_and_analyze(n)
    
    if success:
        # Save results
        output_dir = Path("results/iron_air_simple")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save network
        try:
            output_file = output_dir / "network_iron_air.nc"
            n.export_to_netcdf(str(output_file))
            logger.info(f"\n💾 Network saved to {output_file}")
        except Exception as e:
            logger.warning(f"Could not save network file: {e}")
        
        # Save summary
        summary_file = output_dir / "iron_air_results.txt"
        with open(summary_file, 'w') as f:
            f.write("IRON-AIR BATTERY STORAGE RESULTS\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("Optimal Capacities:\n")
            for gen in n.generators.index:
                if n.generators.at[gen, 'p_nom_opt'] > 0:
                    f.write(f"  {n.generators.at[gen, 'carrier']}: "
                           f"{n.generators.at[gen, 'p_nom_opt']/1000:.1f} GW\n")
            
            f.write("\nStorage:\n")
            for storage in n.storage_units.index:
                if n.storage_units.at[storage, 'p_nom_opt'] > 0:
                    power = n.storage_units.at[storage, 'p_nom_opt'] / 1000
                    hours = n.storage_units.at[storage, 'max_hours']
                    f.write(f"  {n.storage_units.at[storage, 'carrier']}: "
                           f"{power:.1f} GW, {power*hours:.1f} GWh\n")
            
            f.write(f"\nTotal Cost: {n.objective/1e9:.2f} billion EUR/year\n")
        
        logger.info(f"📄 Summary saved to {summary_file}")
        logger.info("\n✅ SUCCESS! Iron-Air battery storage optimization complete.")
        
        # Print key takeaways
        logger.info("\n🎯 KEY RESULTS:")
        iron_air_power = n.storage_units.at['iron_air_DE', 'p_nom_opt'] / 1000
        iron_air_energy = iron_air_power * 250  # 250h duration
        logger.info(f"  • Iron-Air deployed: {iron_air_power:.1f} GW / {iron_air_energy:.0f} GWh")
        logger.info(f"  • Provides long-duration storage for renewable integration")
        logger.info(f"  • Enables high renewable penetration with grid stability")
        
    else:
        logger.error("\n❌ Optimization failed. Check solver settings or constraints.")

if __name__ == "__main__":
    main()
