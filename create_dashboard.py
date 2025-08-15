#!/usr/bin/env python3
"""
Create a Plotly HTML dashboard for PyPSA electricity simulation results.
Shows installed capacity and storage deployment for Germany 2035 scenario.
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

def extract_generation_capacity(n):
    """Extract installed generation capacity by technology."""
    
    # Get generator capacities
    generators = n.generators.copy()
    generators = generators[generators.p_nom_opt > 0]  # Only built capacity
    
    # Aggregate by carrier
    gen_capacity = generators.groupby('carrier')['p_nom_opt'].sum() / 1000  # Convert to GW
    
    # Get storage unit capacities (like battery)
    storage_units = n.storage_units.copy()
    storage_units = storage_units[storage_units.p_nom_opt > 0]
    
    if not storage_units.empty:
        storage_capacity = storage_units.groupby('carrier')['p_nom_opt'].sum() / 1000  # Convert to GW
        # Combine with generators
        capacity_data = pd.concat([gen_capacity, storage_capacity]).groupby(level=0).sum()
    else:
        capacity_data = gen_capacity
    
    return capacity_data

def extract_storage_capacity(n):
    """Extract storage energy capacity by technology."""
    
    # Storage units (e.g., battery, H2)
    storage_units = n.storage_units.copy()
    storage_units = storage_units[storage_units.p_nom_opt > 0]
    
    storage_energy = pd.Series(dtype=float)
    
    if not storage_units.empty:
        # Calculate energy capacity in GWh
        storage_units['energy_capacity_gwh'] = (storage_units['p_nom_opt'] * storage_units['max_hours']) / 1000
        storage_energy = storage_units.groupby('carrier')['energy_capacity_gwh'].sum()
    
    # Stores (e.g., hydrogen stores, heat stores)
    stores = n.stores.copy()
    stores = stores[stores.e_nom_opt > 0]
    
    if not stores.empty:
        # Convert store capacity to GWh
        store_energy = stores.groupby('carrier')['e_nom_opt'].sum() / 1000  # Convert MWh to GWh
        storage_energy = pd.concat([storage_energy, store_energy]).groupby(level=0).sum()
    
    return storage_energy

def create_dashboard(capacity_data, storage_data):
    """Create the Plotly dashboard with subplots."""
    
    # Define colors for different technologies
    colors = {
        'solar': '#FFD700',  # Gold
        'onwind': '#1E90FF',  # DodgerBlue
        'offwind-ac': '#0000CD',  # MediumBlue
        'offwind-dc': '#000080',  # Navy
        'battery': '#32CD32',  # LimeGreen
        'home battery': '#90EE90',  # LightGreen
        'H2': '#FF69B4',  # HotPink
        'H2 Store': '#FF1493',  # DeepPink
        'IronAir': '#8B4513',  # SaddleBrown
        'CCGT': '#696969',  # DimGray
        'OCGT': '#A9A9A9',  # DarkGray
        'nuclear': '#FF6347',  # Tomato
        'coal': '#2F4F4F',  # DarkSlateGray
        'lignite': '#8B4513',  # SaddleBrown
        'PHS': '#4169E1',  # RoyalBlue
        'ror': '#87CEEB'  # SkyBlue
    }
    
    # Create subplots: 2 rows, 2 columns
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            'Renewable Generation Capacity (GW)',
            'All Generation Capacity (GW)', 
            'Storage Power Capacity (GW)',
            'Storage Energy Capacity (GWh)'
        ],
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "bar"}]]
    )
    
    # Subplot 1: Renewable Generation (PV, Wind)
    renewable_techs = ['solar', 'onwind', 'offwind-ac', 'offwind-dc']
    renewable_data = capacity_data.reindex(renewable_techs).fillna(0)
    
    fig.add_trace(
        go.Bar(
            x=renewable_data.index,
            y=renewable_data.values,
            name='Renewable Capacity',
            marker_color=[colors.get(tech, '#808080') for tech in renewable_data.index],
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Subplot 2: All Generation Capacity
    fig.add_trace(
        go.Bar(
            x=capacity_data.index,
            y=capacity_data.values,
            name='Total Generation',
            marker_color=[colors.get(tech, '#808080') for tech in capacity_data.index],
            showlegend=False
        ),
        row=1, col=2
    )
    
    # Subplot 3: Storage Power Capacity (from storage_units)
    storage_techs = ['battery', 'home battery', 'H2', 'IronAir', 'PHS']
    storage_power_data = capacity_data.reindex(storage_techs).fillna(0)
    storage_power_data = storage_power_data[storage_power_data > 0]  # Only show non-zero
    
    if not storage_power_data.empty:
        fig.add_trace(
            go.Bar(
                x=storage_power_data.index,
                y=storage_power_data.values,
                name='Storage Power',
                marker_color=[colors.get(tech, '#808080') for tech in storage_power_data.index],
                showlegend=False
            ),
            row=2, col=1
        )
    
    # Subplot 4: Storage Energy Capacity
    if not storage_data.empty:
        fig.add_trace(
            go.Bar(
                x=storage_data.index,
                y=storage_data.values,
                name='Storage Energy',
                marker_color=[colors.get(tech, '#808080') for tech in storage_data.index],
                showlegend=False
            ),
            row=2, col=2
        )
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'Germany 2035 Electricity System - PyPSA Results Dashboard',
            'x': 0.5,
            'font': {'size': 20}
        },
        height=800,
        showlegend=False,
        template='plotly_white'
    )
    
    # Update y-axis labels
    fig.update_yaxes(title_text="Capacity (GW)", row=1, col=1)
    fig.update_yaxes(title_text="Capacity (GW)", row=1, col=2)
    fig.update_yaxes(title_text="Power (GW)", row=2, col=1)
    fig.update_yaxes(title_text="Energy (GWh)", row=2, col=2)
    
    # Add value annotations on bars
    for i, trace in enumerate(fig.data):
        fig.update_traces(
            texttemplate='%{y:.1f}',
            textposition='outside',
            selector=dict(name=trace.name)
        )
    
    return fig

def create_summary_table(capacity_data, storage_data):
    """Create a summary table of key metrics."""
    
    summary = {
        'Metric': [],
        'Value': [],
        'Unit': []
    }
    
    # Generation metrics
    total_renewable = capacity_data.reindex(['solar', 'onwind', 'offwind-ac', 'offwind-dc']).fillna(0).sum()
    total_generation = capacity_data.sum()
    renewable_share = (total_renewable / total_generation * 100) if total_generation > 0 else 0
    
    summary['Metric'].extend([
        'Total Generation Capacity',
        'Total Renewable Capacity', 
        'Renewable Share',
        'Solar PV Capacity',
        'Onshore Wind Capacity',
        'Offshore Wind Capacity',
        'Total Storage Energy'
    ])
    
    summary['Value'].extend([
        f"{total_generation:.1f}",
        f"{total_renewable:.1f}",
        f"{renewable_share:.1f}",
        f"{capacity_data.get('solar', 0):.1f}",
        f"{capacity_data.get('onwind', 0):.1f}",
        f"{capacity_data.reindex(['offwind-ac', 'offwind-dc']).fillna(0).sum():.1f}",
        f"{storage_data.sum():.1f}" if not storage_data.empty else "0.0"
    ])
    
    summary['Unit'].extend([
        'GW', 'GW', '%', 'GW', 'GW', 'GW', 'GWh'
    ])
    
    return pd.DataFrame(summary)

def main():
    """Main function to create and save the dashboard."""
    
    try:
        print("Loading PyPSA network...")
        n = load_network()
        
        print("Extracting capacity data...")
        capacity_data = extract_generation_capacity(n)
        storage_data = extract_storage_capacity(n)
        
        print("\nInstalled Generation Capacity (GW):")
        print(capacity_data.sort_values(ascending=False))
        
        print("\nStorage Energy Capacity (GWh):")
        print(storage_data.sort_values(ascending=False))
        
        print("\nCreating dashboard...")
        fig = create_dashboard(capacity_data, storage_data)
        
        # Save dashboard
        output_file = "germany_2035_dashboard.html"
        fig.write_html(output_file)
        print(f"\nDashboard saved as: {output_file}")
        
        # Create summary table
        summary_table = create_summary_table(capacity_data, storage_data)
        print("\nKey Metrics Summary:")
        print(summary_table.to_string(index=False))
        
        # Save summary to CSV
        summary_table.to_csv("germany_2035_summary.csv", index=False)
        print(f"Summary table saved as: germany_2035_summary.csv")
        
        return fig
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the PyPSA simulation has completed successfully.")
        return None

if __name__ == "__main__":
    main()
