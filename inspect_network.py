#!/usr/bin/env python3
"""
Inspect PyPSA network to debug CO2 scenarios issues
"""

import pypsa
import pandas as pd

def inspect_network(network_file):
    """Detailed inspection of PyPSA network"""
    
    print(f"🔍 Inspecting network: {network_file}")
    print("=" * 80)
    
    # Load network
    n = pypsa.Network(network_file)
    
    print(f"📊 Network Overview:")
    print(f"   Buses: {len(n.buses)}")
    print(f"   Generators: {len(n.generators)}")
    print(f"   Storage Units: {len(n.storage_units)}")
    print(f"   Stores: {len(n.stores)}")
    print(f"   Loads: {len(n.loads)}")
    print(f"   Links: {len(n.links)}")
    
    print(f"\n📈 Load Analysis:")
    if not n.loads.empty:
        total_load = n.loads_t.p.sum().sum()
        print(f"   Total load: {total_load:.1f} MWh = {total_load/1e6:.1f} TWh")
        print(f"   Peak load: {n.loads_t.p.sum(axis=1).max():.1f} MW")
        print(f"   Average load: {n.loads_t.p.sum(axis=1).mean():.1f} MW")
        print(f"   Load factor: {(n.loads_t.p.sum(axis=1).mean() / n.loads_t.p.sum(axis=1).max()):.2f}")
    
    print(f"\n⚡ Generator Analysis:")
    if not n.generators.empty:
        print("   Generators by carrier:")
        gen_summary = n.generators.groupby('carrier').agg({
            'p_nom': 'sum',
            'p_nom_opt': 'sum',
            'capital_cost': 'mean'
        })
        gen_summary['p_nom_GW'] = gen_summary['p_nom'] / 1000
        gen_summary['p_nom_opt_GW'] = gen_summary['p_nom_opt'] / 1000
        print(gen_summary)
        
        # Check if optimization was performed
        if (n.generators.p_nom_opt == 0).all():
            print("   ⚠️  WARNING: All p_nom_opt values are 0 - optimization may not have run!")
        elif (n.generators.p_nom_opt == n.generators.p_nom).all():
            print("   ⚠️  WARNING: p_nom_opt equals p_nom - optimization may have used fixed capacities!")
    
    print(f"\n🔋 Storage Analysis:")
    if not n.storage_units.empty:
        print("   Storage units by carrier:")
        storage_summary = n.storage_units.groupby('carrier').agg({
            'p_nom': 'sum',
            'p_nom_opt': 'sum',
            'max_hours': 'mean',
            'capital_cost': 'mean'
        })
        storage_summary['p_nom_GW'] = storage_summary['p_nom'] / 1000
        storage_summary['p_nom_opt_GW'] = storage_summary['p_nom_opt'] / 1000
        print(storage_summary)
    
    if not n.stores.empty:
        print("   Stores by carrier:")
        store_summary = n.stores.groupby('carrier').agg({
            'e_nom': 'sum',
            'e_nom_opt': 'sum',
            'capital_cost': 'mean'
        })
        store_summary['e_nom_TWh'] = store_summary['e_nom'] / 1e6
        store_summary['e_nom_opt_TWh'] = store_summary['e_nom_opt'] / 1e6
        print(store_summary)
    
    print(f"\n💰 Cost Analysis:")
    if hasattr(n, 'objective'):
        print(f"   Total system cost: €{n.objective/1e9:.1f} billion")
    else:
        print("   No objective value found")
    
    print(f"\n🌍 CO2 Analysis:")
    if hasattr(n, 'global_constraints') and not n.global_constraints.empty:
        print("   Global constraints:")
        print(n.global_constraints)
    
    print(f"\n🔍 Time Series Analysis:")
    print(f"   Snapshots: {len(n.snapshots)}")
    print(f"   Start: {n.snapshots[0]}")
    print(f"   End: {n.snapshots[-1]}")
    
    # Check if time series data exists
    if hasattr(n, 'generators_t') and hasattr(n.generators_t, 'p'):
        total_generation = n.generators_t.p.sum().sum()
        print(f"   Total generation: {total_generation:.1f} MWh = {total_generation/1e6:.1f} TWh")
        
        print("   Generation by carrier:")
        for carrier in n.generators.carrier.unique():
            gen_idx = n.generators[n.generators.carrier == carrier].index
            if len(gen_idx) > 0:
                carrier_gen = n.generators_t.p[gen_idx].sum().sum()
                print(f"     {carrier}: {carrier_gen/1e6:.1f} TWh")
    else:
        print("   ⚠️  No generation time series found")
    
    return n

def main():
    """Main inspection function"""
    
    print("🔍 PyPSA Network Inspection")
    print("=" * 80)
    
    # Inspect one network file from each scenario
    network_files = [
        "results/de-co2-scenario-A-2035/networks/base_s_1_elec_Co2L0.15.nc",
        "results/de-co2-scenario-B-2035/networks/base_s_1_elec_Co2L0.05.nc"
    ]
    
    for network_file in network_files:
        try:
            inspect_network(network_file)
            print("\n" + "="*80 + "\n")
        except Exception as e:
            print(f"❌ Error inspecting {network_file}: {e}")

if __name__ == "__main__":
    main()
