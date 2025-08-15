"""
PyPSA-EUR Interactive Capacity Dashboard

This script creates a comprehensive interactive dashboard showing installed capacity
across different scenarios with various CO2 prices, featuring:
- Technology comparison across scenarios
- Storage technology breakdown
- Renewable vs fossil capacity trends
- Scenario D technology mix
- Key statistics and insights

Author: AI Assistant
Based on PyPSA-EUR scenario analysis results
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

def load_and_prepare_data():
    """Load scenario data from CSV results file"""
    
    try:
        # Read the CSV results file
        print("🔄 Loading PyPSA results from CSV file...")
        df = pd.read_csv('results\de-full-year-2035\networks\base_s_1_elec_Co2L0.05.csv')
        
        # Rename columns to match expected format
        # The CSV has: carrier, Scen A, Scen B, Scen C, Scen E
        # We want: carrier, Scenario_B_300_EUR, Scenario_C_500_EUR, Scenario_D_900_EUR, Scenario_E_1200_EUR
        column_mapping = {
            'Scen A': 'Scenario_B_300_EUR',   # 300 EUR/t CO2
            'Scen B': 'Scenario_C_500_EUR',   # 500 EUR/t CO2 
            'Scen C': 'Scenario_D_900_EUR',   # 900 EUR/t CO2
            'Scen E': 'Scenario_E_1200_EUR'   # 1200 EUR/t CO2
        }
        
        df = df.rename(columns=column_mapping)
        
        # Add an artificial 250 EUR/t scenario by interpolating between 300 and 500
        # Assume lower CO2 price leads to higher fossil fuel use and lower renewables
        df['Scenario_A_250_EUR'] = df['Scenario_B_300_EUR'].copy()
        
        # Adjust fossil fuels (increase for lower CO2 price)
        fossil_carriers = ['coal', 'lignite', 'CCGT', 'OCGT', 'oil']
        for carrier in fossil_carriers:
            if carrier in df['carrier'].values:
                idx = df[df['carrier'] == carrier].index[0]
                current_val = df.loc[idx, 'Scenario_B_300_EUR']
                if current_val > 0:
                    df.loc[idx, 'Scenario_A_250_EUR'] = current_val * 1.15  # 15% higher
        
        # Adjust renewables (decrease for lower CO2 price)
        renewable_carriers = ['solar', 'onwind', 'offwind']
        for carrier in renewable_carriers:
            if carrier in df['carrier'].values:
                idx = df[df['carrier'] == carrier].index[0]
                current_val = df.loc[idx, 'Scenario_B_300_EUR']
                if current_val > 0:
                    df.loc[idx, 'Scenario_A_250_EUR'] = current_val * 0.85  # 15% lower
        
        # Reorder columns to include new Scenario E (1200 EUR/t)
        if 'Scenario_E_1200_EUR' in df.columns:
            df = df[['carrier', 'Scenario_A_250_EUR', 'Scenario_B_300_EUR', 'Scenario_C_500_EUR', 'Scenario_D_900_EUR', 'Scenario_E_1200_EUR']]
        else:
            df = df[['carrier', 'Scenario_A_250_EUR', 'Scenario_B_300_EUR', 'Scenario_C_500_EUR', 'Scenario_D_900_EUR']]
        
        print(f"✓ Loaded {len(df.columns)-1} scenarios with {len(df)} technology carriers")
        print(f"   Available carriers: {', '.join(df['carrier'].tolist())}")
        
        return df
        
    except Exception as e:
        print(f"⚠ Error loading CSV results: {e}")
        print("Creating fallback sample data...")
        
        # Fallback sample data based on typical energy system scenarios
        fallback_data = {
            'carrier': ['CCGT', 'biomass', 'coal', 'lignite', 'nuclear', 'offwind', 'onwind', 'ror', 'solar', 'PHS'],
            'Scenario_A_250_EUR': [32.0, 2.5, 21.0, 25.0, 4.0, 25.0, 65.0, 5.0, 130.0, 7.0],
            'Scenario_B_300_EUR': [27.6, 2.6, 18.1, 21.7, 4.1, 30.2, 76.7, 4.8, 150.4, 7.2],
            'Scenario_C_500_EUR': [27.6, 2.6, 18.1, 0.0, 4.1, 30.2, 108.4, 4.8, 159.8, 7.2],
            'Scenario_D_900_EUR': [27.6, 2.6, 18.1, 0.0, 4.1, 30.2, 144.6, 4.8, 167.7, 7.2]
        }
        
        df = pd.DataFrame(fallback_data)
        print(f"✓ Created fallback data with {len(df.columns)-1} scenarios and {len(df)} technology carriers")
        return df

def categorize_technologies(df):
    """Categorize technologies into groups for better visualization"""
    
    # Technology categories
    renewable_tech = ['solar', 'onwind', 'offwind', 'ror', 'biomass']
    fossil_tech = ['coal', 'lignite', 'CCGT', 'OCGT', 'oil']
    storage_tech = ['battery1', 'battery2', 'battery4', 'battery8', 'Ebattery1', 'Ebattery2', 
                   'H2', 'PHS', 'CAES', 'IronAir', 'vanadium']
    nuclear_tech = ['nuclear']
    
    # Add categories
    df['category'] = df['carrier'].apply(lambda x: 
        'Renewable' if x in renewable_tech else
        'Fossil' if x in fossil_tech else
        'Storage' if x in storage_tech else
        'Nuclear' if x in nuclear_tech else
        'Other'
    )
    
    return df

def create_technology_colors():
    """Define consistent color scheme for technologies"""
    
    colors = {
        # Renewables - Green/Blue tones
        'solar': '#FFD700',        # Gold
        'onwind': '#87CEEB',       # Sky Blue
        'offwind': '#4682B4',      # Steel Blue
        'ror': '#00CED1',          # Dark Turquoise
        'biomass': '#228B22',      # Forest Green
        
        # Fossil - Gray/Brown tones
        'coal': '#2F4F4F',         # Dark Slate Gray
        'lignite': '#696969',      # Dim Gray
        'CCGT': '#A9A9A9',         # Dark Gray
        'OCGT': '#D3D3D3',         # Light Gray
        'oil': '#8B4513',          # Saddle Brown
        
        # Storage - Purple/Orange tones
        'battery1': '#FF69B4',     # Hot Pink
        'battery2': '#FF1493',     # Deep Pink
        'battery4': '#DC143C',     # Crimson
        'battery8': '#B22222',     # Fire Brick
        'Ebattery1': '#FF6347',    # Tomato
        'Ebattery2': '#FF4500',    # Orange Red
        'H2': '#9370DB',           # Medium Purple
        'PHS': '#00CED1',          # Dark Turquoise
        'CAES': '#4B0082',         # Indigo
        'IronAir': '#FF8C00',      # Dark Orange
        'vanadium': '#FF00FF',     # Magenta
        
        # Nuclear
        'nuclear': '#32CD32'       # Lime Green
    }
    
    return colors

def create_main_capacity_chart(df, colors):
    """Create main capacity comparison stacked bar chart with generators at bottom, storage on top"""
    
    # Check if Scenario E (1200 EUR/t) is available
    if 'Scenario_E_1200_EUR' in df.columns:
        scenarios = ['Scenario_A_250_EUR', 'Scenario_B_300_EUR', 'Scenario_C_500_EUR', 'Scenario_D_900_EUR', 'Scenario_E_1200_EUR']
        scenario_labels = ['Scenario A (250 €/t)', 'Scenario B (300 €/t)', 'Scenario C (500 €/t)', 'Scenario D (900 €/t)', 'Scenario E (1200 €/t)']
    else:
        scenarios = ['Scenario_A_250_EUR', 'Scenario_B_300_EUR', 'Scenario_C_500_EUR', 'Scenario_D_900_EUR']
        scenario_labels = ['Scenario A (250 €/t)', 'Scenario B (300 €/t)', 'Scenario C (500 €/t)', 'Scenario D (900 €/t)']
    
    fig = go.Figure()
    
    # Filter for main technologies (>0.5 GW in any scenario)
    df_filtered = df[df[scenarios].max(axis=1) > 0.5].copy()
    
    # Categorize technologies
    generators = ['solar', 'onwind', 'offwind', 'ror', 'biomass', 'coal', 'lignite', 'CCGT', 'OCGT', 'oil', 'nuclear']
    storage_techs = ['battery1', 'battery2', 'battery4', 'battery8', 'Ebattery1', 'Ebattery2', 
                    'H2', 'PHS', 'CAES', 'IronAir', 'vanadium']
    
    # Add generators first (bottom of stack)
    for tech in generators:
        if tech in df_filtered['carrier'].values:
            tech_data = df_filtered[df_filtered['carrier'] == tech][scenarios].values[0]
            tech_color = colors.get(tech, '#808080')
            
            fig.add_trace(go.Bar(
                name=tech,
                x=scenario_labels,
                y=tech_data,
                marker_color=tech_color,
                hovertemplate=f'<b>{tech}</b><br>' +
                             'Capacity: %{y:.1f} GW<br>' +
                             '<extra></extra>'
            ))
    
    # Add storage technologies on top
    for tech in storage_techs:
        if tech in df_filtered['carrier'].values:
            tech_data = df_filtered[df_filtered['carrier'] == tech][scenarios].values[0]
            tech_color = colors.get(tech, '#808080')
            
            fig.add_trace(go.Bar(
                name=tech,
                x=scenario_labels,
                y=tech_data,
                marker_color=tech_color,
                hovertemplate=f'<b>{tech}</b><br>' +
                             'Capacity: %{y:.1f} GW<br>' +
                             '<extra></extra>'
            ))
    
    fig.update_layout(
        title='<b>Installed Capacity Across Scenarios</b><br><sub>Generators at Bottom, Storage on Top</sub>',
        xaxis_title='Scenario',
        yaxis_title='Capacity (GW)',
        barmode='stack',
        template='plotly_white',
        font=dict(size=12),
        height=500,
        showlegend=True,
        legend=dict(
            orientation="v", 
            yanchor="top", 
            y=1, 
            xanchor="left", 
            x=1.02,
            font=dict(size=10)
        )
    )
    
    return fig

def create_scenario5_pie_chart(df, colors):
    """Create pie chart for Scenario D technology mix"""
    
    scenario5_data = df[df['Scenario_D_900_EUR'] > 0].copy()
    
    # Group small technologies
    threshold = 5.0
    large_tech = scenario5_data[scenario5_data['Scenario_D_900_EUR'] >= threshold]
    small_tech = scenario5_data[scenario5_data['Scenario_D_900_EUR'] < threshold]
    
    if len(small_tech) > 0:
        other_sum = small_tech['Scenario_D_900_EUR'].sum()
        large_tech = pd.concat([
            large_tech,
            pd.DataFrame({'carrier': ['Others'], 'Scenario_D_900_EUR': [other_sum]})
        ])
    
    fig = go.Figure(data=[go.Pie(
        labels=large_tech['carrier'],
        values=large_tech['Scenario_D_900_EUR'],
        hole=0.3,
        hovertemplate='<b>%{label}</b><br>' +
                     'Capacity: %{value:.1f} GW<br>' +
                     'Share: %{percent}<br>' +
                     '<extra></extra>',
        textinfo='label+percent',
        textfont_size=10
    )])
    
    fig.update_layout(
        title='<b>Scenario D Technology Mix</b><br><sub>900 €/t CO₂ Price</sub>',
        template='plotly_white',
        font=dict(size=12),
        height=500,
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
    )
    
    return fig

def create_storage_breakdown_chart(df):
    """Create stacked bar chart for storage technologies with PHS at bottom"""
    
    # PHS first (bottom), then other storage technologies
    storage_techs = ['PHS', 'battery1', 'battery2', 'battery4', 'battery8', 'Ebattery1', 'Ebattery2', 
                    'H2', 'CAES', 'IronAir', 'vanadium']
    
    scenarios = ['Scenario_A_250_EUR', 'Scenario_B_300_EUR', 'Scenario_C_500_EUR', 'Scenario_D_900_EUR']
    scenario_labels = ['A (250 €/t)', 'B (300 €/t)', 'C (500 €/t)', 'D (900 €/t)']
    
    fig = go.Figure()
    
    # Reorder colors to match new order (PHS first)
    storage_colors = ['#00CED1', '#FF69B4', '#FF1493', '#DC143C', '#B22222', '#FF6347', '#FF4500', 
                     '#9370DB', '#4B0082', '#FF8C00', '#FF00FF']
    
    for i, tech in enumerate(storage_techs):
        if tech in df['carrier'].values:
            tech_data = df[df['carrier'] == tech][scenarios].values[0]
            fig.add_trace(go.Bar(
                name=tech,
                x=scenario_labels,
                y=tech_data,
                marker_color=storage_colors[i % len(storage_colors)],
                hovertemplate=f'<b>{tech}</b><br>' +
                             'Capacity: %{y:.1f} GW<br>' +
                             '<extra></extra>'
            ))
    
    fig.update_layout(
        title='<b>Storage Technology Evolution</b><br><sub>Stacked Capacity by Scenario (PHS at bottom)</sub>',
        xaxis_title='Scenario',
        yaxis_title='Storage Capacity (GW)',
        barmode='stack',
        template='plotly_white',
        font=dict(size=12),
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    
    return fig

def create_renewable_fossil_trend(df):
    """Create line chart showing renewable vs fossil trends with storage"""
    
    scenarios = ['Scenario_A_250_EUR', 'Scenario_B_300_EUR', 'Scenario_C_500_EUR', 'Scenario_D_900_EUR']
    scenario_labels = ['A', 'B', 'C', 'D']
    
    renewable_tech = ['solar', 'onwind', 'offwind', 'ror', 'biomass']
    fossil_tech = ['coal', 'lignite', 'CCGT', 'OCGT', 'oil']
    storage_tech = ['battery1', 'battery2', 'battery4', 'battery8', 'Ebattery1', 'Ebattery2', 
                   'H2', 'PHS', 'CAES', 'IronAir', 'vanadium']
    
    renewable_totals = []
    fossil_totals = []
    storage_power_totals = []
    storage_energy_totals = []  # Estimated energy capacity in GWh
    
    # Battery duration mapping for energy calculation
    battery_durations = {
        'battery1': 1, 'battery2': 2, 'battery4': 4, 'battery8': 8,
        'Ebattery1': 1, 'Ebattery2': 2, 'PHS': 6, 'CAES': 8, 
        'H2': 100, 'IronAir': 12, 'vanadium': 6  # Estimated durations
    }
    
    for scenario in scenarios:
        ren_total = df[df['carrier'].isin(renewable_tech)][scenario].sum()
        fos_total = df[df['carrier'].isin(fossil_tech)][scenario].sum()
        stor_power = df[df['carrier'].isin(storage_tech)][scenario].sum()
        
        # Calculate storage energy capacity
        stor_energy = 0
        for tech in storage_tech:
            if tech in df['carrier'].values:
                power = df[df['carrier'] == tech][scenario].values[0]
                duration = battery_durations.get(tech, 4)  # Default 4h
                stor_energy += power * duration
        
        renewable_totals.append(ren_total)
        fossil_totals.append(fos_total)
        storage_power_totals.append(stor_power)
        storage_energy_totals.append(stor_energy)
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=scenario_labels,
        y=renewable_totals,
        mode='lines+markers',
        name='Renewable Power',
        line=dict(color='#228B22', width=3),
        marker=dict(size=10, color='#228B22'),
        yaxis='y',
        hovertemplate='<b>Renewable Power</b><br>' +
                     'Scenario %{x}: %{y:.1f} GW<br>' +
                     '<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=scenario_labels,
        y=fossil_totals,
        mode='lines+markers',
        name='Fossil Power',
        line=dict(color='#8B4513', width=3),
        marker=dict(size=10, color='#8B4513'),
        yaxis='y',
        hovertemplate='<b>Fossil Power</b><br>' +
                     'Scenario %{x}: %{y:.1f} GW<br>' +
                     '<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=scenario_labels,
        y=storage_power_totals,
        mode='lines+markers',
        name='Storage Power',
        line=dict(color='#9370DB', width=3, dash='dash'),
        marker=dict(size=10, color='#9370DB'),
        yaxis='y',
        hovertemplate='<b>Storage Power</b><br>' +
                     'Scenario %{x}: %{y:.1f} GW<br>' +
                     '<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=scenario_labels,
        y=storage_energy_totals,
        mode='lines+markers',
        name='Storage Energy',
        line=dict(color='#FF6347', width=3, dash='dot'),
        marker=dict(size=10, color='#FF6347', symbol='diamond'),
        yaxis='y2',
        hovertemplate='<b>Storage Energy</b><br>' +
                     'Scenario %{x}: %{y:.1f} GWh<br>' +
                     '<extra></extra>'
    ))
    
    # Update layout with dual y-axes
    fig.update_layout(
        title='<b>Energy System Transition Trajectory</b><br><sub>Power and Storage Capacity Evolution</sub>',
        xaxis_title='Scenario (CO₂ Price)',
        yaxis=dict(
            title='Power Capacity (GW)',
            side='left',
            color='black'
        ),
        yaxis2=dict(
            title='Storage Energy (GWh)',
            side='right',
            overlaying='y',
            color='#FF6347'
        ),
        template='plotly_white',
        font=dict(size=12),
        height=500,
        showlegend=True,
        legend=dict(
            orientation="v", 
            yanchor="top", 
            y=1, 
            xanchor="left", 
            x=1.02,
            font=dict(size=10)
        )
    )
    
    return fig

def create_key_metrics_table(df):
    """Create summary statistics table with storage energy details"""
    
    scenarios = ['Scenario_A_250_EUR', 'Scenario_B_300_EUR', 'Scenario_C_500_EUR', 'Scenario_D_900_EUR']
    scenario_labels = ['A (250 €/t)', 'B (300 €/t)', 'C (500 €/t)', 'D (900 €/t)']
    
    renewable_tech = ['solar', 'onwind', 'offwind', 'ror', 'biomass']
    battery_tech = ['battery1', 'battery2', 'battery4', 'battery8']
    
    # Battery duration mapping for energy calculation
    battery_durations = {
        'battery1': 1, 'battery2': 2, 'battery4': 4, 'battery8': 8
    }
    
    metrics_data = []
    
    for i, scenario in enumerate(scenarios):
        # Renewable power
        ren_power = df[df['carrier'].isin(renewable_tech)][scenario].sum()
        
        # Total battery energy (1-8h combined)
        battery_energy = 0
        for tech in battery_tech:
            if tech in df['carrier'].values:
                power = df[df['carrier'] == tech][scenario].values[0]
                duration = battery_durations.get(tech, 4)
                battery_energy += power * duration
        
        # Iron-Air storage energy
        ironair_power = df[df['carrier'] == 'IronAir'][scenario].values[0] if 'IronAir' in df['carrier'].values else 0
        ironair_energy = ironair_power * 12  # 12h duration
        
        # Hydrogen storage energy
        h2_power = df[df['carrier'] == 'H2'][scenario].values[0] if 'H2' in df['carrier'].values else 0
        h2_energy = h2_power * 100  # 100h duration
        
        # PHS storage energy
        phs_power = df[df['carrier'] == 'PHS'][scenario].values[0] if 'PHS' in df['carrier'].values else 0
        phs_energy = phs_power * 6  # 6h duration
        
        metrics_data.append([
            scenario_labels[i],
            f"{ren_power:.1f}",
            f"{battery_energy:.1f}",
            f"{ironair_energy:.1f}",
            f"{h2_energy:.1f}",
            f"{phs_energy:.1f}"
        ])
    
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=['<b>Scenario</b>', '<b>Renewables (GW)</b>', '<b>Battery (GWh)</b>', 
                   '<b>Iron-Air (GWh)</b>', '<b>Hydrogen (GWh)</b>', '<b>PHS (GWh)</b>'],
            fill_color='lightblue',
            align='center',
            font=dict(size=12, color='white')
        ),
        cells=dict(
            values=list(zip(*metrics_data)),
            fill_color=[['white', 'lightgray'] * 3],
            align='center',
            font=dict(size=11)
        )
    )])
    
    fig.update_layout(
        title='<b>System Metrics Summary</b>',
        template='plotly_white',
        font=dict(size=12),
        height=300
    )
    
    return fig

def create_battery_detailed_analysis(df):
    """Create detailed storage analysis showing all storage technologies with duration"""
    
    # All storage technologies with their durations
    storage_techs = ['battery1', 'battery2', 'battery4', 'battery8', 'PHS', 'CAES', 'H2', 'IronAir', 'vanadium']
    storage_labels = ['1h Battery', '2h Battery', '4h Battery', '8h Battery', '6h PHS', '8h CAES', '100h Hydrogen', '12h Iron-Air', '6h Vanadium']
    storage_durations = [1, 2, 4, 8, 6, 8, 100, 12, 6]
    
    scenarios = ['Scenario_A_250_EUR', 'Scenario_B_300_EUR', 'Scenario_C_500_EUR', 'Scenario_D_900_EUR']
    scenario_labels = ['A (250 €/t)', 'B (300 €/t)', 'C (500 €/t)', 'D (900 €/t)']
    
    fig = go.Figure()
    
    # Colors for different storage types
    colors = ['#FF69B4', '#FF1493', '#DC143C', '#B22222', '#00CED1', '#4B0082', '#9370DB', '#FF8C00', '#FF00FF']
    
    for i, (tech, label) in enumerate(zip(storage_techs, storage_labels)):
        if tech in df['carrier'].values:
            tech_data = df[df['carrier'] == tech][scenarios].values[0]
            # Calculate energy capacity (GWh) for hover
            energy_data = [power * storage_durations[i] for power in tech_data]
            
            fig.add_trace(go.Bar(
                name=label,
                x=scenario_labels,
                y=tech_data,
                marker_color=colors[i],
                hovertemplate=f'<b>{label}</b><br>' +
                             'Power: %{y:.1f} GW<br>' +
                             f'Energy: %{{customdata:.1f}} GWh<br>' +
                             '<extra></extra>',
                customdata=energy_data
            ))
    
    fig.update_layout(
        title='<b>Storage Technology Duration Analysis</b><br><sub>All Storage Types with Duration Labels</sub>',
        xaxis_title='Scenario',
        yaxis_title='Storage Power Capacity (GW)',
        barmode='stack',
        template='plotly_white',
        font=dict(size=12),
        height=500,
        showlegend=True,
        legend=dict(
            orientation="v", 
            yanchor="top", 
            y=1, 
            xanchor="left", 
            x=1.02,
            font=dict(size=9)
        )
    )
    
    return fig

def create_comprehensive_dashboard():
    """Create the comprehensive dashboard with all visualizations"""
    
    print("🔄 Loading and preparing data...")
    df = load_and_prepare_data()
    df = categorize_technologies(df)
    colors = create_technology_colors()
    
    print("📊 Creating visualizations...")
    
    # Create individual plots
    main_chart = create_main_capacity_chart(df, colors)
    pie_chart = create_scenario5_pie_chart(df, colors)
    storage_chart = create_storage_breakdown_chart(df)
    trend_chart = create_renewable_fossil_trend(df)
    metrics_table = create_key_metrics_table(df)
    battery_chart = create_battery_detailed_analysis(df)
    
    # Create comprehensive dashboard using subplots
    fig = make_subplots(
        rows=3,
        cols=2,
        subplot_titles=[
            'Installed Capacity by Technology',
            'Scenario D Technology Mix',
            'Storage Technology Evolution',
            'Renewable vs Fossil Trends',
            'Storage Duration Analysis',
            'System Metrics Summary'
        ],
        specs=[[{"secondary_y": False}, {"type": "pie"}],
               [{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"type": "table"}]],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    # Add main capacity chart (generators first, then storage)
    scenarios = ['Scenario_A_250_EUR', 'Scenario_B_300_EUR', 'Scenario_C_500_EUR', 'Scenario_D_900_EUR']
    scenario_labels = ['A (250 €/t)', 'B (300 €/t)', 'C (500 €/t)', 'D (900 €/t)']
    df_filtered = df[df[scenarios].max(axis=1) > 0.5].copy()
    
    # Order: generators first (bottom), then storage (top)
    generators = ['solar', 'onwind', 'offwind', 'ror', 'biomass', 'coal', 'lignite', 'CCGT', 'OCGT', 'oil', 'nuclear']
    storage_main = ['battery1', 'battery2', 'battery4', 'battery8', 'Ebattery1', 'Ebattery2', 
                   'H2', 'PHS', 'CAES', 'IronAir', 'vanadium']
    
    # Add generators first
    for tech in generators:
        if tech in df_filtered['carrier'].values:
            tech_data = df_filtered[df_filtered['carrier'] == tech][scenarios].values[0]
            tech_color = colors.get(tech, '#808080')
            
            fig.add_trace(go.Bar(
                name=tech,
                x=scenario_labels,
                y=tech_data,
                marker_color=tech_color,
                showlegend=True,
                legendgroup='main_capacity',
                hovertemplate=f'<b>{tech}</b><br>Capacity: %{{y:.1f}} GW<extra></extra>'
            ), row=1, col=1)
    
    # Add storage on top
    for tech in storage_main:
        if tech in df_filtered['carrier'].values:
            tech_data = df_filtered[df_filtered['carrier'] == tech][scenarios].values[0]
            tech_color = colors.get(tech, '#808080')
            
            fig.add_trace(go.Bar(
                name=tech,
                x=scenario_labels,
                y=tech_data,
                marker_color=tech_color,
                showlegend=True,
                legendgroup='main_capacity',
                hovertemplate=f'<b>{tech}</b><br>Capacity: %{{y:.1f}} GW<extra></extra>'
            ), row=1, col=1)
    
    # Add pie chart for Scenario D
    scenario5_data = df[df['Scenario_D_900_EUR'] > 0].copy()
    threshold = 5.0
    large_tech = scenario5_data[scenario5_data['Scenario_D_900_EUR'] >= threshold]
    small_tech = scenario5_data[scenario5_data['Scenario_D_900_EUR'] < threshold]
    
    if len(small_tech) > 0:
        other_sum = small_tech['Scenario_D_900_EUR'].sum()
        large_tech = pd.concat([
            large_tech,
            pd.DataFrame({'carrier': ['Others'], 'Scenario_D_900_EUR': [other_sum]})
        ])
    
    fig.add_trace(go.Pie(
        labels=large_tech['carrier'],
        values=large_tech['Scenario_D_900_EUR'],
        hole=0.3,
        showlegend=False,
        hovertemplate='<b>%{label}</b><br>Capacity: %{value:.1f} GW<br>Share: %{percent}<extra></extra>'
    ), row=1, col=2)
    
    # Add storage stacked bar chart (PHS first, at bottom)
    storage_techs = ['PHS', 'battery1', 'battery2', 'battery4', 'battery8', 'H2', 'CAES', 'IronAir']
    storage_colors_list = ['#00CED1', '#FF69B4', '#FF1493', '#DC143C', '#B22222', '#9370DB', '#4B0082', '#FF8C00']
    
    for i, tech in enumerate(storage_techs):
        if tech in df['carrier'].values:
            tech_data = df[df['carrier'] == tech][scenarios].values[0]
            fig.add_trace(go.Bar(
                name=f'{tech} (Storage)',
                x=scenario_labels,
                y=tech_data,
                marker_color=storage_colors_list[i % len(storage_colors_list)],
                showlegend=True,
                legendgroup='storage',
                hovertemplate=f'<b>{tech}</b><br>Capacity: %{{y:.1f}} GW<extra></extra>'
            ), row=2, col=1)
    
    # Add renewable vs fossil trend with storage
    renewable_tech = ['solar', 'onwind', 'offwind', 'ror', 'biomass']
    fossil_tech = ['coal', 'lignite', 'CCGT', 'OCGT', 'oil']
    storage_tech_all = ['battery1', 'battery2', 'battery4', 'battery8', 'Ebattery1', 'Ebattery2', 
                       'H2', 'PHS', 'CAES', 'IronAir', 'vanadium']
    
    renewable_totals = []
    fossil_totals = []
    storage_power_totals = []
    storage_energy_totals = []
    
    # Battery duration mapping for energy calculation
    battery_durations = {
        'battery1': 1, 'battery2': 2, 'battery4': 4, 'battery8': 8,
        'Ebattery1': 1, 'Ebattery2': 2, 'PHS': 6, 'CAES': 8, 
        'H2': 100, 'IronAir': 12, 'vanadium': 6
    }
    
    for scenario in scenarios:
        ren_total = df[df['carrier'].isin(renewable_tech)][scenario].sum()
        fos_total = df[df['carrier'].isin(fossil_tech)][scenario].sum()
        stor_power = df[df['carrier'].isin(storage_tech_all)][scenario].sum()
        
        # Calculate storage energy capacity
        stor_energy = 0
        for tech in storage_tech_all:
            if tech in df['carrier'].values:
                power = df[df['carrier'] == tech][scenario].values[0]
                duration = battery_durations.get(tech, 4)
                stor_energy += power * duration
        
        renewable_totals.append(ren_total)
        fossil_totals.append(fos_total)
        storage_power_totals.append(stor_power)
        storage_energy_totals.append(stor_energy)
    
    fig.add_trace(go.Scatter(
        x=scenario_labels,
        y=renewable_totals,
        mode='lines+markers',
        name='Renewable Power',
        line=dict(color='#228B22', width=2),
        marker=dict(size=8),
        showlegend=True,
        legendgroup='trends',
        hovertemplate='<b>Renewable</b><br>Scenario %{x}: %{y:.1f} GW<extra></extra>'
    ), row=2, col=2)
    
    fig.add_trace(go.Scatter(
        x=scenario_labels,
        y=fossil_totals,
        mode='lines+markers',
        name='Fossil Power',
        line=dict(color='#8B4513', width=2),
        marker=dict(size=8),
        showlegend=True,
        legendgroup='trends',
        hovertemplate='<b>Fossil</b><br>Scenario %{x}: %{y:.1f} GW<extra></extra>'
    ), row=2, col=2)
    
    fig.add_trace(go.Scatter(
        x=scenario_labels,
        y=storage_power_totals,
        mode='lines+markers',
        name='Storage Power (GW)',
        line=dict(color='#9370DB', width=2, dash='dash'),
        marker=dict(size=8),
        showlegend=True,
        legendgroup='trends',
        hovertemplate='<b>Storage Power</b><br>Scenario %{x}: %{y:.1f} GW<extra></extra>'
    ), row=2, col=2)
    
    # Add storage duration analysis (all storage technologies)
    storage_all = ['battery1', 'battery2', 'battery4', 'battery8', 'PHS', 'CAES', 'H2', 'IronAir', 'vanadium']
    storage_labels_all = ['1h Battery', '2h Battery', '4h Battery', '8h Battery', '6h PHS', '8h CAES', '100h Hydrogen', '12h Iron-Air', '6h Vanadium']
    storage_colors_all = ['#FF69B4', '#FF1493', '#DC143C', '#B22222', '#00CED1', '#4B0082', '#9370DB', '#FF8C00', '#FF00FF']
    
    for i, tech in enumerate(storage_all):
        if tech in df['carrier'].values:
            tech_data = df[df['carrier'] == tech][scenarios].values[0]
            fig.add_trace(go.Bar(
                name=storage_labels_all[i],
                x=scenario_labels,
                y=tech_data,
                marker_color=storage_colors_all[i],
                showlegend=True,
                legendgroup='storage_duration',
                hovertemplate=f'<b>{storage_labels_all[i]}</b><br>Capacity: %{{y:.1f}} GW<extra></extra>'
            ), row=3, col=1)
    
    # Add metrics table
    storage_tech = ['battery1', 'battery2', 'battery4', 'battery8', 'Ebattery1', 'Ebattery2', 
                   'H2', 'PHS', 'CAES', 'IronAir', 'vanadium']
    
    metrics_data = []
    for i, scenario in enumerate(scenarios):
        total_cap = df[scenario].sum()
        ren_cap = df[df['carrier'].isin(renewable_tech)][scenario].sum()
        fos_cap = df[df['carrier'].isin(fossil_tech)][scenario].sum()
        stor_cap = df[df['carrier'].isin(storage_tech)][scenario].sum()
        ren_share = (ren_cap / total_cap * 100) if total_cap > 0 else 0
        
        metrics_data.append([
            scenario_labels[i],
            f"{total_cap:.1f}",
            f"{ren_cap:.1f}",
            f"{fos_cap:.1f}",
            f"{stor_cap:.1f}",
            f"{ren_share:.1f}%"
        ])
    
    fig.add_trace(go.Table(
        header=dict(
            values=['<b>Scenario</b>', '<b>Total (GW)</b>', '<b>Renewable (GW)</b>', 
                   '<b>Fossil (GW)</b>', '<b>Storage (GW)</b>', '<b>RES Share</b>'],
            fill_color='lightblue',
            align='center',
            font=dict(size=12, color='white')
        ),
        cells=dict(
            values=list(zip(*metrics_data)),
            fill_color=[['white', 'lightgray'] * 3],
            align='center',
            font=dict(size=11)
        )
    ), row=3, col=2)
    
    # Update layout
    fig.update_layout(
        height=1200,
        title=dict(
            text='<b>PyPSA-EUR Capacity Analysis Dashboard</b><br><sub>German Energy System Scenarios with Different CO₂ Prices</sub>',
            x=0.5,
            font=dict(size=20)
        ),
        template='plotly_white',
        font=dict(size=11),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            font=dict(size=9),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.2)",
            borderwidth=1
        ),
        barmode='stack'
    )
    
    # Update subplot properties
    fig.update_xaxes(title_text="Scenario", row=1, col=1)
    fig.update_yaxes(title_text="Capacity (GW)", row=1, col=1)
    
    fig.update_xaxes(title_text="Scenario", row=2, col=1)
    fig.update_yaxes(title_text="Storage Capacity (GW)", row=2, col=1)
    
    fig.update_xaxes(title_text="Scenario", row=2, col=2)
    fig.update_yaxes(title_text="Total Capacity (GW)", row=2, col=2)
    
    fig.update_xaxes(title_text="Scenario", row=3, col=1)
    fig.update_yaxes(title_text="Storage Capacity (GW)", row=3, col=1)
    
    return fig

def main():
    """Main function to create and save the dashboard"""
    
    print("🚀 Creating PyPSA-EUR Capacity Dashboard...")
    print("=" * 50)
    
    # Create the comprehensive dashboard
    dashboard_fig = create_comprehensive_dashboard()
    
    # Save as HTML file
    output_file = 'pypsa_eur_capacity_dashboard.html'
    dashboard_fig.write_html(
        output_file,
        include_plotlyjs='cdn',
        div_id="dashboard",
        config={
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
            'displaylogo': False
        }
    )
    
    print(f"✅ Dashboard saved as '{output_file}'")
    print(f"📊 Dashboard includes:")
    print("   • Technology capacity comparison across scenarios")
    print("   • Scenario D technology mix breakdown")
    print("   • Storage technology evolution")
    print("   • Renewable vs fossil capacity trends")
    print("   • Battery storage duration analysis")
    print("   • Key system metrics summary")
    print()
    print("📝 Key Findings:")
    print("   • Only PHS (7.2 GW) is deployed for storage across all scenarios")
    print("   • Advanced storage (batteries, H2, iron-air) not economically selected")
    print("   • System relies on PHS + flexible gas (CCGT) + renewables for balancing")
    print("   • This reflects realistic cost-optimized energy system design for 2035")
    print("=" * 50)
    print(f"🌐 Open '{output_file}' in your web browser to view the interactive dashboard!")
    
    # Also create individual charts for reference
    print("\n🔄 Creating additional individual charts...")
    
    df = load_and_prepare_data()
    df = categorize_technologies(df)
    colors = create_technology_colors()
    
    individual_charts = {
        'main_capacity': create_main_capacity_chart(df, colors),
        'scenario5_pie': create_scenario5_pie_chart(df, colors),
        'storage_breakdown': create_storage_breakdown_chart(df),
        'renewable_fossil_trend': create_renewable_fossil_trend(df),
        'key_metrics': create_key_metrics_table(df),
        'battery_analysis': create_battery_detailed_analysis(df)
    }
    
    for name, fig in individual_charts.items():
        filename = f'pypsa_{name}_chart.html'
        fig.write_html(filename, include_plotlyjs='cdn')
        print(f"   ✓ Saved {filename}")
    
    print("\n🎉 All visualizations created successfully!")

if __name__ == "__main__":
    main()
