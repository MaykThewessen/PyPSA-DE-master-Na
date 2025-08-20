#!/usr/bin/env python3
"""
Create PyPSA-DE Dashboard matching the exact style and layout shown.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import webbrowser
import os

def load_data():
    """Load the latest scenario results."""
    # Use the latest readable summary
    df = pd.read_csv('co2_scenarios_readable_summary_20250819_203903.csv')
    return df

def create_styled_dashboard():
    """Create dashboard matching the exact style shown in the image."""
    
    # Load data
    df = load_data()
    
    # Create 6-panel dashboard with exact layout
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=[
            '', '',  # Top row - no titles, will add manually
            'Storage Power deployed', 'Storage Energy deployed',
            'Storage duration', 'Summary Table'
        ],
        specs=[
            [{"secondary_y": False}, {"secondary_y": True}],
            [{"secondary_y": False}, {"secondary_y": False}],
            [{"secondary_y": False}, {"type": "table"}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.08
    )
    
    # Scenario data
    scenarios = ['A', 'B', 'C', 'D']
    scenario_labels = [f"Scenario {s} ({df.iloc[i]['CO2 Limit']})" for i, s in enumerate(scenarios)]
    
    # Define exact colors matching the image
    colors = {
        'biomass': '#8B4513',      # Brown
        'nuclear': '#FF8C00',      # Orange  
        'offwind': '#4682B4',      # Steel Blue
        'onwind': '#87CEEB',       # Sky Blue
        'solar': '#FFD700',        # Gold
        'CCGT': '#A9A9A9',         # Gray
        'battery': '#FF69B4',      # Hot Pink
        'ironair': '#FF8C00',      # Orange
        'hydrogen': '#9370DB',     # Medium Purple
        'PHS': '#00CED1'           # Dark Turquoise
    }
    
    # 1. Top Left: Generation Capacity (stacked bars)
    renewable_techs = ['biomass', 'nuclear', 'offwind', 'onwind', 'solar']
    fossil_techs = ['CCGT']
    
    # Stack renewable technologies
    for i, tech in enumerate(renewable_techs):
        col_map = {
            'biomass': 'Biomass Capacity (GW)',
            'nuclear': 'Nuclear Capacity (GW)', 
            'offwind': 'Offshore Wind Capacity (GW)',
            'onwind': 'Onshore Wind Capacity (GW)',
            'solar': 'Solar Capacity (GW)'
        }
        
        col_name = col_map.get(tech)
        if col_name and col_name in df.columns:
            values = df[col_name]
            fig.add_trace(go.Bar(
                name=tech.title(),
                x=scenario_labels,
                y=values,
                marker_color=colors[tech],
                showlegend=True,
                legendgroup='generation'
            ), row=1, col=1)
    
    # Add CCGT at bottom
    if 'CCGT Generation (TWh)' in df.columns:
        # Convert generation to approximate capacity (assuming capacity factor)
        ccgt_gen = df['CCGT Generation (TWh)']
        ccgt_cap = ccgt_gen / (8.76 * 0.4)  # Rough conversion: TWh to GW
        fig.add_trace(go.Bar(
            name='CCGT',
            x=scenario_labels,
            y=ccgt_cap,
            marker_color=colors['CCGT'],
            showlegend=True,
            legendgroup='generation'
        ), row=1, col=1)
    
    # 2. Top Right: System Cost (bars) + CO2 Emissions (line)
    fig.add_trace(go.Bar(
        name='System Cost',
        x=scenario_labels,
        y=df['Total Cost (Billion EUR)'],
        marker_color='lightblue',
        showlegend=True,
        legendgroup='cost'
    ), row=1, col=2)
    
    fig.add_trace(go.Scatter(
        name='CO2 Emissions',
        x=scenario_labels,
        y=df['CO2 Emissions (Mt)'],
        mode='lines+markers',
        line=dict(color='red', width=3),
        marker=dict(size=8, color='red'),
        showlegend=True,
        legendgroup='cost',
        yaxis='y3'
    ), row=1, col=2, secondary_y=True)
    
    # 3. Middle Left: Storage Power (stacked bars)
    storage_power_techs = ['PHS', 'battery', 'ironair', 'hydrogen']
    storage_power_names = ['PHS Power', 'Battery Power', 'Iron-Air Power', 'Hydrogen Power']
    storage_power_cols = ['PHS Power (GW)', 'Battery Charger (GW)', 'Iron-Air Charger (GW)', 'H2 Power (GW)']
    
    for tech, name, col in zip(storage_power_techs, storage_power_names, storage_power_cols):
        if col in df.columns:
            values = df[col].fillna(0)
        else:
            # Calculate hydrogen power from energy (assume 720h duration)
            if tech == 'hydrogen' and 'Hydrogen Storage (GWh)' in df.columns:
                values = df['Hydrogen Storage (GWh)'] / 720
            else:
                values = [0] * len(df)
        
        fig.add_trace(go.Bar(
            name=name,
            x=scenario_labels,
            y=values,
            marker_color=colors[tech],
            showlegend=True,
            legendgroup='storage_power'
        ), row=2, col=1)
    
    # 4. Middle Right: Storage Energy (stacked bars)
    storage_energy_techs = ['PHS', 'battery', 'ironair', 'hydrogen']
    storage_energy_names = ['PHS Energy', 'Battery Energy', 'Iron-Air Energy', 'Hydrogen Energy']
    storage_energy_cols = ['PHS Energy (GWh)', 'Battery Energy (GWh)', 'Iron-Air Energy (GWh)', 'Hydrogen Storage (GWh)']
    
    for tech, name, col in zip(storage_energy_techs, storage_energy_names, storage_energy_cols):
        if col in df.columns:
            values = df[col].fillna(0)
        else:
            values = [0] * len(df)
        
        fig.add_trace(go.Bar(
            name=name,
            x=scenario_labels,
            y=values,
            marker_color=colors[tech],
            showlegend=True,
            legendgroup='storage_energy'
        ), row=2, col=2)
    
    # 5. Bottom Left: Storage Duration (grouped bars by technology)
    # Calculate durations for each scenario and technology
    storage_techs = ['Battery LFP', 'PHS', 'Iron-Air', 'Hydrogen']
    
    # Calculate actual durations from data for each scenario
    tech_durations = {tech: [] for tech in storage_techs}
    
    for i, scenario in enumerate(scenarios):
        row = df.iloc[i]
        
        # Battery LFP duration
        battery_power = row.get('Battery Charger (GW)', 0)
        battery_energy = row.get('Battery Energy (GWh)', 0)
        if battery_power > 0:
            tech_durations['Battery LFP'].append(battery_energy / battery_power)
        else:
            tech_durations['Battery LFP'].append(0)
        
        # PHS duration - assume typical 8h duration for pumped hydro
        phs_power = row.get('PHS Power (GW)', 0)
        phs_energy = row.get('PHS Energy (GWh)', 0)
        if phs_power > 0:
            tech_durations['PHS'].append(phs_energy / phs_power)
        else:
            tech_durations['PHS'].append(8)  # Typical PHS duration
        
        # Iron-Air duration
        ironair_power = row.get('Iron-Air Charger (GW)', 0)
        ironair_energy = row.get('Iron-Air Energy (GWh)', 0)
        if ironair_power > 0 and ironair_energy > 0:
            duration = ironair_energy / ironair_power
            tech_durations['Iron-Air'].append(duration)
        else:
            tech_durations['Iron-Air'].append(0)
        
        # Hydrogen duration - typical seasonal storage (720h)
        hydrogen_energy = row.get('Hydrogen Storage (GWh)', 0)
        if hydrogen_energy > 0:
            tech_durations['Hydrogen'].append(720)  # Typical seasonal storage duration
        else:
            tech_durations['Hydrogen'].append(0)
    
    # Create grouped bar chart - each scenario gets its own trace for each technology
    scenario_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']  # Blue, Orange, Green, Red
    
    for i, scenario in enumerate(scenarios):
        x_labels = [f'{tech}' for tech in storage_techs]
        scenario_values = [tech_durations[tech][i] for tech in storage_techs]
        
        fig.add_trace(go.Bar(
            name=f'Scenario {scenario}',
            x=x_labels,
            y=scenario_values,
            marker_color=scenario_colors[i],
            text=[f'{dur:.0f}h' if dur > 0 else '0h' for dur in scenario_values],
            textposition='outside',
            showlegend=True,
            legendgroup='duration'
        ), row=3, col=1)
    
    # Add 50-hour reference line for iron-air minimum requirement
    fig.add_trace(go.Scatter(
        x=storage_techs,
        y=[50] * len(storage_techs),
        mode='lines',
        name='Iron-Air 50h Min',
        line=dict(color='red', width=2, dash='dash'),
        showlegend=True,
        legendgroup='duration'
    ), row=3, col=1)
    
    # 6. Bottom Right: Summary Table
    table_data = []
    for i, row in df.iterrows():
        scenario_letter = scenarios[i]
        table_data.append([
            f"Scenario {scenario_letter}",
            f"{row['Total Cost (Billion EUR)']:.1f}",
            f"{row['Solar Capacity (GW)']:.1f}",
            f"{row['Iron-Air Charger (GW)']:.1f}",
            f"{row.get('H2 Power (GW)', row['Hydrogen Storage (GWh)']/720):.1f}",
            f"{row['Battery Charger (GW)'] + row['Iron-Air Charger (GW)'] + row.get('H2 Power (GW)', row['Hydrogen Storage (GWh)']/720):.1f}",
            f"{row['Total Cost (Billion EUR)']:.1f}",
            f"{row['CO2 Emissions (Mt)']:.1f}"
        ])
    
    fig.add_trace(go.Table(
        header=dict(
            values=['Scenario', 'Renewable<br>(GW)', 'Solar<br>(GW)', 'Iron-Air Power<br>(GW)', 
                   'Hydrogen Power<br>(GW)', 'Total Storage<br>(GW)', 'System<br>Cost', 'CO2 Emissions<br>(Mt)'],
            fill_color='lightblue',
            align='center',
            font=dict(size=10, color='white'),
            height=30
        ),
        cells=dict(
            values=list(zip(*table_data)),
            fill_color=[['white', 'lightgray'] * 4],
            align='center',
            font=dict(size=9),
            height=25
        )
    ), row=3, col=2)
    
    # Update layout to match the style
    fig.update_layout(
        height=1000,
        title=dict(
            text='<b>PyPSA Germany 2035 - Analysis Dashboard</b><br>' +
                 '<sub>Decarbonization Pathways for Germany 2035</sub><br>' +
                 '<sub style="font-size: 10px;">Model Configuration: 138.2 TWh/yr consumption • 1 spatial node (Germany) • 4380 timesteps/year (2-hour resolution) • PyPSA v0.30+ • Linopy v0.3+ • HiGHS solver • LP optimization</sub>',
            x=0.5,
            font=dict(size=16)
        ),
        template='plotly_white',
        font=dict(size=10),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left", 
            x=1.02,
            font=dict(size=9)
        ),
        barmode='stack'
    )
    
    # Update axis labels and formatting
    fig.update_yaxes(title_text="Capacity (GW)", row=1, col=1)
    fig.update_yaxes(title_text="System Cost (Billion EUR)", row=1, col=2)
    fig.update_yaxes(title_text="CO2 Emissions (Mt)", row=1, col=2, secondary_y=True)
    fig.update_yaxes(title_text="Storage Power (GW)", row=2, col=1)
    fig.update_yaxes(title_text="Storage Energy (GWh)", row=2, col=2)
    fig.update_yaxes(title_text="Duration (Hours)", row=3, col=1)
    fig.update_xaxes(title_text="Storage Technology", row=3, col=1, tickangle=45)
    
    # Set grouped bars for the duration subplot specifically
    fig.update_layout(xaxis5=dict(type='category'), bargap=0.2, bargroupgap=0.1)
    
    # Remove x-axis labels for top and middle rows to match the image
    fig.update_xaxes(showticklabels=True, row=1, col=1)
    fig.update_xaxes(showticklabels=True, row=1, col=2)
    fig.update_xaxes(showticklabels=True, row=2, col=1)
    fig.update_xaxes(showticklabels=True, row=2, col=2)
    
    return fig

def main():
    """Create and save the styled dashboard."""
    
    print("🎨 Creating Styled PyPSA-DE Dashboard...")
    
    # Create dashboard
    fig = create_styled_dashboard()
    
    # Save with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'pypsa_germany_dashboard_{timestamp}.html'
    
    fig.write_html(
        filename,
        include_plotlyjs='cdn',
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d']
        }
    )
    
    print(f"✅ Dashboard created: {filename}")
    
    # Auto-open
    try:
        full_path = os.path.abspath(filename)
        webbrowser.open(f'file://{full_path}')
        print(f"🌐 Dashboard opened in browser!")
    except Exception as e:
        print(f"⚠ Could not auto-open browser: {e}")
    
    return filename

if __name__ == "__main__":
    dashboard_file = main()
    print(f"\n🎉 Styled dashboard ready: {dashboard_file}")
