#!/usr/bin/env python3
"""
Enhanced Plotly dashboard for PyPSA results with storage duration analysis.
"""

import pypsa
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os

def load_network():
    """Load the solved PyPSA network."""
    network_file = "results/de-electricity-only-2035-mayk/networks/base_s_1___2035.nc"
    if not os.path.exists(network_file):
        raise FileNotFoundError(f"Network file not found: {network_file}")
    
    print(f"Loading network from: {network_file}")
    n = pypsa.Network(network_file)
    return n

def extract_detailed_storage_data(n):
    """Extract detailed storage characteristics including duration."""
    
    storage_details = []
    
    # Storage units (battery, PHS, etc.)
    storage_units = n.storage_units[n.storage_units.p_nom_opt > 0].copy()
    
    for idx, storage in storage_units.iterrows():
        power_mw = storage['p_nom_opt']
        energy_mwh = power_mw * storage['max_hours']
        duration_hours = storage['max_hours']
        
        storage_details.append({
            'technology': storage['carrier'],
            'type': 'Storage Unit',
            'power_gw': power_mw / 1000,
            'energy_gwh': energy_mwh / 1000,
            'duration_hours': duration_hours,
            'bus': storage['bus']
        })
    
    # Stores (hydrogen, heat, etc.)
    stores = n.stores[n.stores.e_nom_opt > 0].copy()
    
    for idx, store in stores.iterrows():
        energy_mwh = store['e_nom_opt']
        # For stores, we need to find associated links for power rating
        # This is approximate - looking for related charger/discharger links
        
        store_links = n.links[
            (n.links.bus1 == store['bus']) | (n.links.bus0 == store['bus'])
        ]
        
        if not store_links.empty:
            # Use the maximum link capacity as power rating
            power_mw = store_links['p_nom_opt'].max()
            duration_hours = energy_mwh / power_mw if power_mw > 0 else np.inf
        else:
            power_mw = 0
            duration_hours = np.inf
        
        storage_details.append({
            'technology': store['carrier'],
            'type': 'Store',
            'power_gw': power_mw / 1000,
            'energy_gwh': energy_mwh / 1000,
            'duration_hours': duration_hours,
            'bus': store['bus']
        })
    
    return pd.DataFrame(storage_details)

def create_enhanced_dashboard(n):
    """Create enhanced dashboard with multiple visualizations."""
    
    # Get basic capacity data
    generators = n.generators[n.generators.p_nom_opt > 0].copy()
    gen_capacity = generators.groupby('carrier')['p_nom_opt'].sum() / 1000
    
    storage_units = n.storage_units[n.storage_units.p_nom_opt > 0].copy()
    if not storage_units.empty:
        storage_capacity = storage_units.groupby('carrier')['p_nom_opt'].sum() / 1000
        capacity_data = pd.concat([gen_capacity, storage_capacity]).groupby(level=0).sum()
    else:
        capacity_data = gen_capacity
    
    # Get detailed storage data
    storage_details = extract_detailed_storage_data(n)
    
    # Colors
    colors = {
        'solar': '#FFD700',
        'onwind': '#1E90FF',
        'offwind-ac': '#0000CD',
        'offwind-dc': '#000080',
        'battery': '#32CD32',
        'home battery': '#90EE90',
        'H2 Store': '#FF1493',
        'PHS': '#4169E1',
        'nuclear': '#FF6347',
        'ror': '#87CEEB',
        'IronAir': '#8B4513'  # Add IronAir with a brown color
    }
    
    # Create subplots: 1 row, 3 columns (removed bottom row)
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=[
            'Generation Capacity by Technology (GW)',
            'Storage Power Capacity (GW)',
            'Storage Energy Capacity (GWh)'
        ],
        specs=[
            [{"type": "bar"}, {"type": "bar"}, {"type": "bar"}]
        ]
    )
    
    # Plot 1: Generation Capacity
    fig.add_trace(
        go.Bar(
            x=capacity_data.index,
            y=capacity_data.values,
            name='Generation',
            marker_color=[colors.get(tech, '#808080') for tech in capacity_data.index],
            showlegend=False,
            text=[f"{val:.1f} GW" for val in capacity_data.values],
            textposition='outside'
        ),
        row=1, col=1
    )
    
    # Plot 2: Storage Power Capacity
    if not storage_details.empty:
        storage_power = storage_details.groupby('technology')['power_gw'].sum()
        
        # Always include IronAir storage even when 0 capacity
        if 'IronAir' not in storage_power.index:
            storage_power['IronAir'] = 0
        
        # Only show non-zero storage technologies except for IronAir
        storage_power = pd.concat([storage_power[storage_power > 0], 
                                 pd.Series([storage_power.get('IronAir', 0)], index=['IronAir'])])
        storage_power = storage_power[~storage_power.index.duplicated()]
        
        fig.add_trace(
            go.Bar(
                x=storage_power.index,
                y=storage_power.values,
                name='Storage Power',
                marker_color=[colors.get(tech, '#808080') for tech in storage_power.index],
                showlegend=False,
                text=[f"{val:.1f} GW" for val in storage_power.values],
                textposition='outside'
            ),
            row=1, col=2
        )
    
    # Plot 3: Storage Energy Capacity
    if not storage_details.empty:
        storage_energy = storage_details.groupby('technology')['energy_gwh'].sum()
        
        # Always include IronAir storage even when 0 capacity
        if 'IronAir' not in storage_energy.index:
            storage_energy['IronAir'] = 0
        
        # Only show non-zero storage technologies except for IronAir
        storage_energy = pd.concat([storage_energy[storage_energy > 0], 
                                  pd.Series([storage_energy.get('IronAir', 0)], index=['IronAir'])])
        storage_energy = storage_energy[~storage_energy.index.duplicated()]
        
        fig.add_trace(
            go.Bar(
                x=storage_energy.index,
                y=storage_energy.values,
                name='Storage Energy',
                marker_color=[colors.get(tech, '#808080') for tech in storage_energy.index],
                showlegend=False,
                text=[f"{val:.1f} GWh" for val in storage_energy.values],
                textposition='outside'
            ),
            row=1, col=3
        )
    
    # Removed bottom two subplots as requested
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'Germany 2035 Electricity System - Enhanced Analysis Dashboard',
            'x': 0.5,
            'font': {'size': 18}
        },
        height=600,  # Reduced height since we removed bottom row
        showlegend=False,
        template='plotly_white'
    )
    
    # Update axis labels
    # Row 1, Col 1: Generation Capacity
    fig.update_yaxes(title_text="Capacity (GW)", row=1, col=1)
    fig.update_xaxes(title_text="Technology", row=1, col=1)
    
    # Row 1, Col 2: Storage Power Capacity
    fig.update_yaxes(title_text="Power (GW)", row=1, col=2)
    fig.update_xaxes(title_text="Storage Technology", row=1, col=2)
    
    # Row 1, Col 3: Storage Energy Capacity
    fig.update_yaxes(title_text="Energy (GWh)", row=1, col=3)
    fig.update_xaxes(title_text="Storage Technology", row=1, col=3)
    
    return fig, storage_details

def create_summary_report(n, storage_details):
    """Create a comprehensive summary report."""
    
    generators = n.generators[n.generators.p_nom_opt > 0].copy()
    gen_capacity = generators.groupby('carrier')['p_nom_opt'].sum() / 1000
    
    storage_units = n.storage_units[n.storage_units.p_nom_opt > 0].copy()
    if not storage_units.empty:
        storage_capacity = storage_units.groupby('carrier')['p_nom_opt'].sum() / 1000
        total_capacity = pd.concat([gen_capacity, storage_capacity]).groupby(level=0).sum()
    else:
        total_capacity = gen_capacity
    
    # Calculate key metrics
    renewable_capacity = total_capacity.reindex(['solar', 'onwind', 'offwind-ac', 'offwind-dc', 'ror']).fillna(0).sum()
    total_gen_capacity = total_capacity.sum()
    renewable_share = (renewable_capacity / total_gen_capacity * 100) if total_gen_capacity > 0 else 0
    
    total_storage_energy = storage_details['energy_gwh'].sum() if not storage_details.empty else 0
    total_storage_power = storage_details['power_gw'].sum() if not storage_details.empty else 0
    
    report = f"""
    ================================================================
    GERMANY 2035 ELECTRICITY SYSTEM - OPTIMIZATION RESULTS SUMMARY
    ================================================================
    
    GENERATION CAPACITY:
    -------------------
    Total Generation:        {total_gen_capacity:.1f} GW
    Renewable Capacity:      {renewable_capacity:.1f} GW  ({renewable_share:.1f}%)
    
    Solar PV:               {total_capacity.get('solar', 0):.1f} GW
    Onshore Wind:           {total_capacity.get('onwind', 0):.1f} GW
    Offshore Wind AC:       {total_capacity.get('offwind-ac', 0):.1f} GW
    Offshore Wind DC:       {total_capacity.get('offwind-dc', 0):.1f} GW
    Nuclear:                {total_capacity.get('nuclear', 0):.1f} GW
    Run-of-river Hydro:     {total_capacity.get('ror', 0):.1f} GW
    
    STORAGE SYSTEMS:
    ---------------
    Total Storage Power:     {total_storage_power:.1f} GW
    Total Storage Energy:    {total_storage_energy:.1f} GWh
    
    """
    
    if not storage_details.empty:
        report += "Storage by Technology:\n"
        for tech in storage_details['technology'].unique():
            tech_data = storage_details[storage_details['technology'] == tech]
            power = tech_data['power_gw'].sum()
            energy = tech_data['energy_gwh'].sum()
            avg_duration = tech_data['duration_hours'].mean()
            
            report += f"  {tech:15s}: {power:6.1f} GW, {energy:8.1f} GWh, {avg_duration:6.1f}h duration\n"
    
    report += f"""
    
    KEY INSIGHTS:
    ------------
    • System is {renewable_share:.1f}% renewable
    • Solar dominates with {total_capacity.get('solar', 0):.1f} GW ({total_capacity.get('solar', 0)/total_gen_capacity*100:.1f}% of total)
    • Wind provides {total_capacity.reindex(['onwind', 'offwind-ac', 'offwind-dc']).fillna(0).sum():.1f} GW
    • Storage provides {total_storage_energy:.0f} GWh of energy storage
    • Hydrogen storage dominates long-duration storage needs
    
    ================================================================
    """
    
    return report

def main():
    """Main function."""
    
    try:
        print("Loading PyPSA network...")
        n = load_network()
        
        print("Creating enhanced dashboard...")
        fig, storage_details = create_enhanced_dashboard(n)
        
        # Save dashboard
        output_file = "germany_2035_enhanced_dashboard.html"
        fig.write_html(output_file)
        print(f"Enhanced dashboard saved as: {output_file}")
        
        # Create and save detailed report
        report = create_summary_report(n, storage_details)
        print(report)
        
        with open("germany_2035_detailed_report.txt", "w") as f:
            f.write(report)
        print("Detailed report saved as: germany_2035_detailed_report.txt")
        
        # Save detailed storage data
        if not storage_details.empty:
            storage_details.to_csv("germany_2035_storage_details.csv", index=False)
            print("Storage details saved as: germany_2035_storage_details.csv")
        
        return fig
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    main()
