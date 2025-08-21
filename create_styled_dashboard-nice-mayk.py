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
os.system('clear')


def load_data():
    """Load the latest scenario results."""
    # Use the latest readable summary with corrected storage data
    import glob

    # Find all matching CSV files in the current folder
    csv_files = glob.glob('co2_scenarios_comparison_*.csv')
    print("csv_files found:")
    #print(csv_files)
    if not csv_files:
        raise FileNotFoundError("No scenario summary CSV files found in the current directory.")
    # Sort by modification time, descending, and pick the most recent
    latest_csv = max(csv_files, key=os.path.getmtime)
    print(f"Using {latest_csv}")
    df = pd.read_csv(latest_csv)

    print("df:")
    print(df.round(0))


    # Move the last column to be the third column in the dataframe
    if len(df.columns) > 2:
        cols = df.columns.tolist()
        # Remove last column and insert at position 2 (third column, 0-based indexing)
        cols.insert(2, cols.pop(-1))
        cols.insert(3, cols.pop(-1))
        df = df[cols]

    print("Column headers:")
    for col in df.columns:
        print("--", col)


    return df

def create_styled_dashboard():
    """Create dashboard matching the exact style shown in the image."""
    
    # Load data
    df = load_data()
    
    # Create 6-panel dashboard with table as full-width bottom row (removed 4th subplot)
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=[
            '', '',  # Top row - no titles, will add manually
            'Storage Power deployed', 'Storage duration',  # Middle row
            '', ''  # Bottom row - table spans both columns
        ],
        specs=[
            [{"secondary_y": False}, {"secondary_y": True}],
            [{"secondary_y": False}, {"secondary_y": False}],
            [{"type": "table", "colspan": 2}, None]  # Table spans both columns
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.08
    )
    
    # Scenario data
    scenarios = ['A', 'B', 'C', 'D']
    # Extract just the percentage from CO2 Limit
    scenario_labels = []
    for i, s in enumerate(scenarios):
        co2_limit = df.iloc[i]['co2_target_pct']
        # Extract just the percentage part before 'of 1990'
        percentage = str(co2_limit).split(' of ')[0] if pd.notnull(co2_limit) and ' of ' in str(co2_limit) else str(co2_limit)
        scenario_labels.append(f"{s}: {percentage}")
    
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
    
    # Stack renewable technologies
    for i, tech in enumerate(renewable_techs):
        col_map = {
            'biomass': 'biomass_capacity_GW',
            'nuclear': 'nuclear_capacity_GW', 
            'offwind': 'offwind-ac_capacity_GW',
            'onwind': 'onwind_capacity_GW',
            'solar': 'solar_capacity_GW'
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
    if 'CCGT_capacity_GW' in df.columns:
        ccgt_cap = df['CCGT_capacity_GW']
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
        y=df['total_system_cost_billion_EUR'],
        marker_color='lightblue',
        showlegend=True,
        legendgroup='cost'
    ), row=1, col=2)
    
    fig.add_trace(go.Scatter(
        name='CO2 Emissions',
        x=scenario_labels,
        y=df['co2_emissions_MtCO2'],
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
    storage_power_cols = ['PHS_power_GW', 'battery_power_GW', 'iron-air_power_GW', 'Hydrogen_power_GW']
    
    for tech, name, col in zip(storage_power_techs, storage_power_names, storage_power_cols):
        if col in df.columns:
            values = df[col].fillna(0)
        else:
            # If column doesn't exist, show zeros - no fake calculations
            values = [0] * len(df)
        
        fig.add_trace(go.Bar(
            name=name,
            x=scenario_labels,
            y=values,
            marker_color=colors[tech],
            showlegend=True,
            legendgroup='storage_power'
        ), row=2, col=1)
    
    # 4. Bottom Left: Storage Duration (non-stacked bars by technology)
    # Calculate durations for each scenario and technology
    storage_techs = ['Battery LFP', 'PHS', 'Iron-Air', 'Hydrogen']
    storage_tech_colors = {
        'Battery LFP': colors['battery'],
        'PHS': colors['PHS'],
        'Iron-Air': colors['ironair'],
        'Hydrogen': colors['hydrogen']
    }
    
    # Calculate actual durations from data for each scenario
    tech_durations = {tech: [] for tech in storage_techs}
    
    for i, scenario in enumerate(scenarios):
        row = df.iloc[i]
        
        # Battery LFP duration - only calculate if both power and energy exist
        battery_power = row.get('battery_power_GW', 0)
        battery_energy = row.get('battery_energy_GWh', 0)
        if battery_power > 0 and battery_energy > 0:
            tech_durations['Battery LFP'].append(battery_energy / battery_power)
        else:
            tech_durations['Battery LFP'].append(0)
        
        # PHS duration - only calculate from actual data, no fallbacks
        phs_power = row.get('PHS_power_GW', 0)
        phs_energy = row.get('PHS_energy_GWh', 0)
        if phs_power > 0 and phs_energy > 0:
            tech_durations['PHS'].append(phs_energy / phs_power)
        else:
            tech_durations['PHS'].append(0)
        
        # Iron-Air duration - only calculate from actual data
        ironair_power = row.get('iron-air_power_GW', 0)
        ironair_energy = row.get('iron-air_energy_GWh', 0)
        if ironair_power > 0 and ironair_energy > 0:
            duration = ironair_energy / ironair_power
            tech_durations['Iron-Air'].append(duration)
        else:
            tech_durations['Iron-Air'].append(0)
        
        # Hydrogen duration - only calculate from actual data
        hydrogen_power = row.get('Hydrogen_power_GW', 0)
        hydrogen_energy = row.get('Hydrogen_energy_GWh', 0)
        if hydrogen_power > 0 and hydrogen_energy > 0:
            tech_durations['Hydrogen'].append(hydrogen_energy / hydrogen_power)
        else:
            tech_durations['Hydrogen'].append(0)
    
    # Create non-stacked bar chart - each technology gets its own trace across all scenarios
    for i, tech in enumerate(storage_techs):
        # Round values to 1 decimal place
        rounded_values = [round(val, 1) if val > 0 else 0 for val in tech_durations[tech]]
        
        fig.add_trace(go.Bar(
            name=tech,
            x=scenario_labels,
            y=rounded_values,
            marker_color=storage_tech_colors[tech],
            showlegend=True,
            legendgroup='duration',
            offsetgroup=i,  # This creates grouped (non-stacked) bars
            base=None       # Ensure no stacking
        ), row=2, col=2)
    
    # No reference lines - only show actual data
    
    # 5. Bottom: Summary Table - Display all CSV columns and rows
    table_data = []
    
    # Get all column names from the dataframe (excluding the first column)
    all_columns = df.columns.tolist()
    
    # Create short column header names mapping
    header_mapping = {
        'scenario': 'Scen ario',
        'co2_target_pct': 'CO2 %',
        'co2_emissions_MtCO2': 'Emiss Mt/y',
        'annual_consumption_TWh': 'Load TWh/y',
        'solar_capacity_GW': 'PV GWp',
        'onwind_capacity_GW': 'Onsho Wind',
        'offwind-ac_capacity_GW': 'Offsh Wind',
        'biomass_capacity_GW': 'Bio mass',
        'nuclear_capacity_GW': 'Nuc lear',
        'CCGT_capacity_GW': 'Gas CCGT',
        'OCGT_capacity_GW': 'Gas OCGT',
        'battery_power_GW': 'LFP GW',
        'battery_energy_GWh': 'LFP GWh',
        'iron-air_power_GW': 'Iron GW',
        'iron-air_energy_GWh': 'Iron GWh',
        'Hydrogen_power_GW': 'H2 GW',
        'Hydrogen_energy_GWh': 'H2 GWh',
        'PHS_power_GW': 'PHS GW',
        'PHS_energy_GWh': 'PHS GWh',
        'total_renewable_GW': 'Ren GW',
        'total_storage_power_GW': 'Stor GW',
        'total_storage_energy_GWh': 'Stor GWh',
        'total_system_cost_billion_EUR': 'Cost B€'
    }
    
    # Create header row with short names
    header_values = []
    for col in all_columns:
        if col in header_mapping:
            header_values.append(header_mapping[col])
        else:
            # For unmapped columns, use a shortened version
            short_name = col.replace('_', ' ').title()
            if len(short_name) > 10:
                short_name = short_name[:10] + '...'
            header_values.append(short_name)
    
    # Create data rows for each scenario
    for i, row in df.iterrows():
        # Create row data with all columns (excluding scenario column)
        row_data = []
        
        for col in all_columns:
            value = row[col]
            if pd.isna(value):
                row_data.append("")
            elif isinstance(value, (int, float)):
                # Apply specific rounding rules - convert to int to remove decimal places
                if 'cost' in col.lower() or 'billion' in col.lower():
                    # System costs: round to 2 decimal places and keep as float
                    row_data.append(f"{round(value, 2)}")
                elif 'co2' in col.lower() or 'emissions' in col.lower():
                    # Emissions: round to 0 decimal places
                    row_data.append(f"{int(round(value, 0))}")
                else:
                    # All other numeric values: round to 0 decimal places
                    row_data.append(f"{int(round(value, 0))}")
            else:
                # Keep non-numeric values as is
                row_data.append(str(value))
        
        table_data.append(row_data)
    
    fig.add_trace(go.Table(
        header=dict(
            values=header_values,
            fill_color='lightblue',
            align='center',
            font=dict(size=10, color='white'),
            height=35
        ),
        cells=dict(
            values=list(zip(*table_data)),
            fill_color=[['white', 'lightgray'] * (len(table_data) // 2 + 1)],
            align='center',
            font=dict(size=9),
            height=30
        )
    ), row=3, col=1)
    
    # Update layout to match the style
    fig.update_layout(
        height=1400,
        title=dict(
            text='PyPSA Germany 2035 - Analysis Dashboard',
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
        barmode='stack',
        # Set specific spacing for better grouped bars in duration subplot
        bargap=0.15,
        bargroupgap=0.05
    )
    
    # Update axis labels and formatting
    fig.update_yaxes(title_text="Capacity (GW)", row=1, col=1)
    fig.update_yaxes(title_text="System Cost (Billion EUR)", row=1, col=2)
    fig.update_yaxes(title_text="CO2 Emissions (Mt)", row=1, col=2, secondary_y=True)
    fig.update_yaxes(title_text="Storage Power (GW)", row=2, col=1)
    fig.update_yaxes(title_text="Duration (Hours)", row=3, col=1)
    fig.update_xaxes(title_text="Scenarios", row=3, col=1, tickangle=0)
    
    # Set non-stacked bars for the duration subplot specifically
    fig.update_layout(xaxis5=dict(type='category'), bargap=0.2, bargroupgap=0.1)
    
    # Remove x-axis labels for top and middle rows to match the image
    fig.update_xaxes(showticklabels=True, row=1, col=1)
    fig.update_xaxes(showticklabels=True, row=1, col=2)
    fig.update_xaxes(showticklabels=True, row=2, col=1)
    fig.update_xaxes(showticklabels=True, row=3, col=1)
    fig.update_xaxes(showticklabels=True, row=3, col=2)
    
    return fig

def main():
    """Create and save the styled dashboard."""
    
    print("🎨 Creating Styled PyPSA-DE Dashboard...")
    
    # Create dashboard
    fig = create_styled_dashboard()
    
    # Save with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H")
    filename = f'pypsa_germany_dashboard_{timestamp}h.html'
    
    fig.write_html(
        filename,
        include_plotlyjs='cdn',
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d']
        },
        auto_open=True
    )
    
    print(f"✅ Dashboard created: {filename}")

    
    return filename

if __name__ == "__main__":
    dashboard_file = main()
    print(f"\n🎉 Styled dashboard ready: {dashboard_file}")
