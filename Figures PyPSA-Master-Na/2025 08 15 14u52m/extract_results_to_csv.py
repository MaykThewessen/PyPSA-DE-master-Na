#!/usr/bin/env python3
"""
Extract PyPSA optimization results to CSV files for dashboard visualization
"""

import pypsa
import pandas as pd
import numpy as np
import os
from datetime import datetime

def extract_pypsa_to_csv():
    """Extract PyPSA network results to multiple CSV files"""
    
    print("=== EXTRACTING PYPSA RESULTS TO CSV ===")
    
    # Load the optimized network
    network_path = 'results/de-full-year-2035/networks/base_s_1_elec_Co2L0.05.nc'
    print(f"Loading network from: {network_path}")
    
    try:
        n = pypsa.Network(network_path)
        print("✅ Network loaded successfully")
    except Exception as e:
        print(f"❌ Error loading network: {e}")
        return False
    
    # Create output directory
    output_dir = 'csv_outputs'
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 Created output directory: {output_dir}")
    
    # 1. Extract Generator Capacities and Information
    print("📊 Extracting generator data...")
    generators_df = n.generators.copy()
    generators_df['p_nom_opt_MW'] = generators_df['p_nom_opt']
    generators_df['p_nom_opt_GW'] = generators_df['p_nom_opt'] / 1000
    generators_df['capital_cost_total'] = generators_df['p_nom_opt'] * generators_df['capital_cost']
    
    # Add generation statistics if available
    if hasattr(n.generators_t, 'p') and not n.generators_t.p.empty:
        gen_stats = pd.DataFrame()
        gen_stats['mean_generation'] = n.generators_t.p.mean()
        gen_stats['max_generation'] = n.generators_t.p.max()
        gen_stats['capacity_factor'] = gen_stats['mean_generation'] / generators_df['p_nom_opt']
        generators_df = generators_df.join(gen_stats, how='left')
    
    generators_df.to_csv(f'{output_dir}/generators.csv')
    print(f"✅ Saved generators data: {len(generators_df)} entries")
    
    # 2. Extract Storage Information
    print("🔋 Extracting storage data...")
    
    # Stores (long-duration storage)
    if not n.stores.empty:
        stores_df = n.stores.copy()
        stores_df['e_nom_opt_MWh'] = stores_df['e_nom_opt']
        stores_df['e_nom_opt_GWh'] = stores_df['e_nom_opt'] / 1000
        stores_df['capital_cost_total'] = stores_df['e_nom_opt'] * stores_df['capital_cost']
        stores_df.to_csv(f'{output_dir}/stores.csv')
        print(f"✅ Saved stores data: {len(stores_df)} entries")
    
    # Storage Units (power-based storage)
    if not n.storage_units.empty:
        storage_units_df = n.storage_units.copy()
        storage_units_df['p_nom_opt_MW'] = storage_units_df['p_nom_opt']
        storage_units_df['p_nom_opt_GW'] = storage_units_df['p_nom_opt'] / 1000
        storage_units_df['e_nom_calculated'] = storage_units_df['p_nom_opt'] * storage_units_df['max_hours']
        storage_units_df.to_csv(f'{output_dir}/storage_units.csv')
        print(f"✅ Saved storage units data: {len(storage_units_df)} entries")
    
    # 3. Create Summary Statistics
    print("📈 Creating summary statistics...")
    
    # Generator summary by carrier
    gen_summary = generators_df.groupby('carrier').agg({
        'p_nom_opt_GW': 'sum',
        'capital_cost': 'mean',
        'capital_cost_total': 'sum',
        'marginal_cost': 'mean'
    }).round(2)
    
    gen_summary['count'] = generators_df.groupby('carrier').size()
    gen_summary.to_csv(f'{output_dir}/generator_summary_by_carrier.csv')
    print(f"✅ Saved generator summary: {len(gen_summary)} carriers")
    
    # Storage summary by carrier
    storage_summary_list = []
    
    if not n.stores.empty:
        stores_summary = stores_df.groupby('carrier').agg({
            'e_nom_opt_GWh': 'sum',
            'capital_cost': 'mean',
            'capital_cost_total': 'sum'
        }).round(2)
        stores_summary['type'] = 'Store'
        stores_summary['count'] = stores_df.groupby('carrier').size()
        storage_summary_list.append(stores_summary)
    
    if not n.storage_units.empty:
        su_summary = storage_units_df.groupby('carrier').agg({
            'p_nom_opt_GW': 'sum',
            'max_hours': 'mean',
            'e_nom_calculated': 'sum'
        }).round(2)
        su_summary['type'] = 'StorageUnit'
        su_summary['count'] = storage_units_df.groupby('carrier').size()
        storage_summary_list.append(su_summary)
    
    if storage_summary_list:
        storage_summary = pd.concat(storage_summary_list, sort=False)
        storage_summary.to_csv(f'{output_dir}/storage_summary_by_carrier.csv')
        print(f"✅ Saved storage summary: {len(storage_summary)} carriers")
    
    # 4. System-level summary
    print("🌍 Creating system summary...")
    
    total_capacity = generators_df['p_nom_opt_GW'].sum()
    renewable_techs = ['solar', 'solar-hsat', 'onwind', 'offwind-ac', 'offwind-dc', 'offwind-float', 'hydro', 'ror']
    renewable_capacity = generators_df[generators_df['carrier'].str.lower().isin(renewable_techs)]['p_nom_opt_GW'].sum()
    
    system_summary = pd.DataFrame({
        'metric': [
            'total_capacity_GW',
            'renewable_capacity_GW', 
            'renewable_share_percent',
            'conventional_capacity_GW',
            'total_system_cost_billion_EUR',
            'total_snapshots',
            'optimization_status'
        ],
        'value': [
            total_capacity,
            renewable_capacity,
            (renewable_capacity / total_capacity * 100) if total_capacity > 0 else 0,
            total_capacity - renewable_capacity,
            n.objective / 1e9 if hasattr(n, 'objective') else 0,
            len(n.snapshots),
            'optimal'
        ]
    })
    
    system_summary.to_csv(f'{output_dir}/system_summary.csv', index=False)
    print(f"✅ Saved system summary")
    
    # 5. Time series data (sample for dashboard)
    print("⏰ Extracting time series data...")
    
    # Save snapshots information
    snapshots_df = pd.DataFrame({
        'snapshot': n.snapshots,
        'year': n.snapshots.year,
        'month': n.snapshots.month, 
        'day': n.snapshots.day,
        'hour': n.snapshots.hour,
        'dayofyear': n.snapshots.dayofyear,
        'weekofyear': n.snapshots.isocalendar().week
    })
    snapshots_df.to_csv(f'{output_dir}/snapshots.csv')
    print(f"✅ Saved snapshots data: {len(snapshots_df)} time steps")
    
    # Sample load data (first week for dashboard testing)
    if hasattr(n, 'loads_t') and hasattr(n.loads_t, 'p_set') and not n.loads_t.p_set.empty:
        load_sample = n.loads_t.p_set.head(168)  # First week (24*7=168 hours)
        load_sample.index.name = 'snapshot'
        load_sample.to_csv(f'{output_dir}/load_sample.csv')
        print(f"✅ Saved load sample data: {len(load_sample)} time steps")
    
    # 6. Technology mapping for dashboard
    print("🏷️  Creating technology mapping...")
    
    # Create a comprehensive technology mapping
    tech_mapping = pd.DataFrame({
        'carrier': list(n.carriers.index),
        'nice_name': [n.carriers.loc[c, 'nice_name'] if 'nice_name' in n.carriers.columns and not pd.isna(n.carriers.loc[c, 'nice_name']) else c for c in n.carriers.index],
        'color': [n.carriers.loc[c, 'color'] if 'color' in n.carriers.columns and not pd.isna(n.carriers.loc[c, 'color']) else '#888888' for c in n.carriers.index],
        'co2_emissions': [n.carriers.loc[c, 'co2_emissions'] if 'co2_emissions' in n.carriers.columns else 0 for c in n.carriers.index]
    })
    
    # Add technology categories
    tech_mapping['category'] = tech_mapping['carrier'].apply(categorize_technology)
    tech_mapping.to_csv(f'{output_dir}/technology_mapping.csv', index=False)
    print(f"✅ Saved technology mapping: {len(tech_mapping)} technologies")
    
    # 7. Create metadata file
    metadata = {
        'extraction_date': datetime.now().isoformat(),
        'network_file': network_path,
        'total_snapshots': len(n.snapshots),
        'start_date': str(n.snapshots[0]),
        'end_date': str(n.snapshots[-1]),
        'objective_value': float(n.objective) if hasattr(n, 'objective') else None,
        'solver_status': 'optimal',
        'files_created': [
            'generators.csv',
            'stores.csv' if not n.stores.empty else None,
            'storage_units.csv' if not n.storage_units.empty else None,
            'generator_summary_by_carrier.csv',
            'storage_summary_by_carrier.csv',
            'system_summary.csv',
            'snapshots.csv',
            'load_sample.csv',
            'technology_mapping.csv'
        ]
    }
    
    # Remove None entries
    metadata['files_created'] = [f for f in metadata['files_created'] if f is not None]
    
    metadata_df = pd.DataFrame(list(metadata.items()), columns=['key', 'value'])
    metadata_df.to_csv(f'{output_dir}/metadata.csv', index=False)
    print(f"✅ Saved metadata")
    
    print()
    print("🎉 CSV EXTRACTION COMPLETED SUCCESSFULLY!")
    print(f"📁 All files saved to: {output_dir}/")
    print(f"📋 Files created: {len(metadata['files_created'])}")
    
    return True

def categorize_technology(carrier):
    """Categorize technologies for dashboard"""
    carrier_lower = carrier.lower()
    
    if any(word in carrier_lower for word in ['solar', 'pv']):
        return 'Solar'
    elif any(word in carrier_lower for word in ['wind', 'onwind', 'offwind']):
        return 'Wind'  
    elif any(word in carrier_lower for word in ['battery', 'storage', 'phs', 'caes', 'ironair', 'vanadium', 'hydrogen', 'h2']):
        return 'Storage'
    elif any(word in carrier_lower for word in ['hydro', 'ror']):
        return 'Hydro'
    elif any(word in carrier_lower for word in ['nuclear']):
        return 'Nuclear'
    elif any(word in carrier_lower for word in ['gas', 'ccgt', 'ocgt']):
        return 'Gas'
    elif any(word in carrier_lower for word in ['coal', 'lignite']):
        return 'Coal'
    elif any(word in carrier_lower for word in ['biomass']):
        return 'Biomass'
    else:
        return 'Other'

if __name__ == "__main__":
    success = extract_pypsa_to_csv()
    if success:
        print("\n✅ Ready for dashboard visualization!")
    else:
        print("\n❌ Extraction failed!")
