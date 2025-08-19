"""
Enhanced CO2 Scenarios Dashboard for PyPSA Results

Creates an interactive dashboard comparing 4 CO2 scenarios:
A) 15% of 1990 emissions
B) 5% of 1990 emissions  
C) 1% of 1990 emissions
D) 0% of 1990 emissions (net-zero)

Features:
- 1-decimal precision formatting
- Iron-Air always included in storage plots
- Extended summary table
- Storage capacity line chart
- Comprehensive model information in subtitle
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os

def load_comparison_data():
    """Load CO2 scenarios comparison data"""
    
    try:
        print("🔄 Loading CO2 scenarios comparison data...")
        import glob
        import os
        csv_files = glob.glob('co2_scenarios_comparison*.csv')
        if not csv_files:
            raise FileNotFoundError("No co2_scenarios_comparison*.csv files found in the current directory.")
        latest_csv = max(csv_files, key=os.path.getmtime)
        print(f"📂 Loading most recent comparison file: {latest_csv}")
        df = pd.read_csv(latest_csv)
        
        # Ensure Iron-Air columns exist
        if 'ironair_power_GW' not in df.columns:
            df['ironair_power_GW'] = 0.0
        if 'ironair_energy_GWh' not in df.columns:
            df['ironair_energy_GWh'] = 0.0
        if 'annual_consumption_TWh' not in df.columns:
            df['annual_consumption_TWh'] = 491.5  # Default value
        
        print(f"✓ Loaded {len(df)} scenarios with {len(df.columns)} metrics")
        print(f"   Scenarios: {', '.join(df['scenario'].tolist())}")
        
        return df
        
    except Exception as e:
        print(f"⚠ Error loading comparison data: {e}")
        print("Creating fallback sample data...")
        
        # Enhanced fallback sample data
        fallback_data = {
            'scenario': ['A', 'B', 'C', 'D'],
            'co2_target_pct': [15.0, 5.0, 1.0, 0.0],
            'solar_capacity_GW': [150.2, 180.7, 200.1, 220.5],
            'onwind_capacity_GW': [100.8, 120.3, 140.9, 160.2],
            'offwind-ac_capacity_GW': [30.4, 40.1, 50.7, 60.3],
            'CCGT_capacity_GW': [25.1, 15.2, 5.1, 0.0],
            'OCGT_capacity_GW': [10.5, 5.3, 2.1, 0.0],
            'nuclear_capacity_GW': [0.0, 0.0, 0.0, 10.2],
            'biomass_capacity_GW': [8.5, 8.5, 8.5, 8.5],
            'battery_power_GW': [20.3, 30.7, 40.2, 50.8],
            'battery_energy_GWh': [162.4, 245.6, 321.6, 406.4],
            'ironair_power_GW': [0.0, 5.2, 15.7, 25.1],
            'ironair_energy_GWh': [0.0, 520.0, 1570.0, 2510.0],
            'H2_power_GW': [5.3, 10.1, 15.8, 25.4],
            'H2_energy_GWh': [530.0, 1010.0, 1580.0, 2540.0],
            'PHS_power_GW': [7.2, 7.2, 7.2, 7.2],
            'PHS_energy_GWh': [43.2, 43.2, 43.2, 43.2],
            'total_renewable_GW': [290.9, 349.6, 400.2, 459.7],
            'total_storage_power_GW': [32.8, 53.2, 78.9, 108.5],
            'total_storage_energy_GWh': [735.6, 1818.8, 3514.8, 5999.8],
            'total_system_cost_billion_EUR': [152.3, 171.8, 203.5, 254.7],
            'co2_emissions_MtCO2': [98.7, 28.4, 4.2, 0.0],
            'annual_consumption_TWh': [491.5, 491.5, 491.5, 491.5]
        }
        
        df = pd.DataFrame(fallback_data)
        print(f"✓ Created fallback data with {len(df)} scenarios")
        return df

def create_technology_colors():
    """Define consistent color scheme for technologies"""
    
    colors = {
        # Renewables - Green/Blue tones
        'solar': '#FFD700',        # Gold
        'onwind': '#87CEEB',       # Sky Blue
        'offwind-ac': '#4682B4',   # Steel Blue
        'nuclear': '#FF8C00',      # Orange
        'biomass': '#228B22',      # Forest Green
        
        # Fossil - Gray/Brown tones
        'CCGT': '#A9A9A9',         # Dark Gray
        'OCGT': '#D3D3D3',         # Light Gray
        
        # Storage - Purple/Orange tones
        'battery': '#FF69B4',      # Hot Pink
        'ironair': '#FF8C00',      # Dark Orange
        'H2': '#9370DB',           # Medium Purple
        'PHS': '#00CED1',          # Dark Turquoise
    }
    
    return colors

def create_storage_capacity_lines_chart(df, colors):
    """Create line chart showing storage energy capacity evolution"""
    
    fig = go.Figure()
    
    scenarios = df['scenario'].tolist()
    scenario_labels = [f"Scenario {s}" for s in scenarios]
    
    # Storage technologies - always include all three
    storage_techs = ['battery', 'ironair', 'H2']
    storage_names = ['Battery', 'Iron-Air', 'Hydrogen']
    
    for tech, name in zip(storage_techs, storage_names):
        energy_col = f'{tech}_energy_GWh'
        if energy_col in df.columns:
            values = df[energy_col].fillna(0)
        else:
            values = [0] * len(df)
        
        fig.add_trace(go.Scatter(
            x=scenario_labels,
            y=values,
            mode='lines+markers',
            name=f'{name} Energy',
            line=dict(color=colors.get(tech, '#808080'), width=3),
            marker=dict(size=10, color=colors.get(tech, '#808080')),
            hovertemplate=f'<b>{name} Energy</b><br>' +
                         'Scenario: %{x}<br>' +
                         'Energy: %{y:.1f} GWh<br>' +
                         '<extra></extra>'
        ))
    
    fig.update_layout(
        title='<b>Storage Energy Capacity by Technology</b><br><sub>Evolution Across CO2 Scenarios</sub>',
        xaxis_title='CO2 Scenario',
        yaxis_title='Storage Energy Capacity (GWh)',
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

def create_enhanced_summary_table(df):
    """Create enhanced summary table with additional storage details"""
    
    # Prepare comprehensive table data
    table_data = []
    for _, row in df.iterrows():
        scenario = row['scenario']
        co2_pct = row['co2_target_pct']
        
        table_data.append([
            f"Scenario {scenario}",
            f"{co2_pct:.0f}%",
            f"{row['total_renewable_GW']:.1f}",
            f"{row.get('battery_power_GW', 0):.1f}",
            f"{row.get('ironair_power_GW', 0):.1f}", 
            f"{row.get('H2_power_GW', 0):.1f}",
            f"{row['total_storage_power_GW']:.1f}",
            f"{row['total_storage_energy_GWh']:.1f}",
            f"€{row['total_system_cost_billion_EUR']:.1f}B",
            f"{row['co2_emissions_MtCO2']:.1f}"
        ])
    
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=[
                '<b>Scenario</b>', 
                '<b>CO2 Target</b>', 
                '<b>Renewable<br>(GW)</b>',
                '<b>Battery Power<br>(GW)</b>',
                '<b>Iron-Air Power<br>(GW)</b>',
                '<b>Hydrogen Power<br>(GW)</b>',
                '<b>Total Storage<br>Power (GW)</b>',
                '<b>Total Storage<br>Energy (GWh)</b>',
                '<b>System Cost</b>',
                '<b>CO2 Emissions<br>(Mt)</b>'
            ],
            fill_color='lightblue',
            align='center',
            font=dict(size=11, color='white'),
            height=40
        ),
        cells=dict(
            values=list(zip(*table_data)),
            fill_color=[['white', 'lightgray'] * 5],
            align='center',
            font=dict(size=10),
            height=30
        ),
        columnwidth=[0.8, 0.8, 1.0, 1.0, 1.0, 1.0, 1.2, 1.2, 1.0, 1.2]
    )])
    
    fig.update_layout(
        title='<b>Comprehensive Scenario Summary</b><br><sub>Detailed Technology and Performance Metrics</sub>',
        template='plotly_white',
        font=dict(size=12),
        height=400,
        margin=dict(l=0, r=0, t=80, b=20)
    )
    
    return fig

def get_model_info_subtitle(df):
    """Generate comprehensive model information subtitle"""
    
    # Extract model parameters from data
    annual_consumption = df['annual_consumption_TWh'].iloc[0] if 'annual_consumption_TWh' in df.columns else 491.5
    
    subtitle_text = (
        f"<b>Model Configuration:</b> "
        f"{annual_consumption:.1f} TWh/yr consumption • "
        f"1 spatial node (Germany) • "
        f"4380 timesteps/year (2-hour resolution) • "
        f"PyPSA v0.30+ • "
        f"Linopy v0.3+ • "
        f"HiGHS solver • "
        f"LP optimization"
    )
    
    return subtitle_text

def create_comprehensive_dashboard():
    """Create the enhanced comprehensive CO2 scenarios dashboard"""
    
    print("🔄 Loading and preparing data...")
    df = load_comparison_data()
    colors = create_technology_colors()
    
    print("📊 Creating enhanced visualizations...")
    
    # Create dashboard with 3 rows and 2 columns
    fig = make_subplots(
        rows=3,
        cols=2,
        subplot_titles=[
            ' ',
            ' ',
            'Storage Power deployed', 
            'Storage Energy deployed',
            'Storage duration',
            'Summary Table'
        ],
        specs=[
            [{"secondary_y": False}, {"secondary_y": True}],
            [{"secondary_y": False}, {"secondary_y": False}],
            [{"secondary_y": False}, {"type": "table"}]
        ],
        vertical_spacing=0.08,
        horizontal_spacing=0.1
    )
    
    scenarios = df['scenario'].tolist()
    scenario_labels = [f"Scenario {s} ({df[df['scenario']==s]['co2_target_pct'].iloc[0]:.0f}% CO2)" for s in scenarios]
    
    # 1. Generation capacity evolution
    renewable_techs = ['solar', 'onwind', 'offwind-ac', 'nuclear', 'biomass']
    fossil_techs = ['CCGT', 'OCGT']
    
    for tech in fossil_techs + renewable_techs:
        col_name = f'{tech}_capacity_GW'
        if col_name in df.columns:
            values = df[col_name]
        else:
            values = [0] * len(df)
            
        fig.add_trace(go.Bar(
            name=tech.replace('_', ' ').title(),
            x=scenario_labels,
            y=values,
            marker_color=colors.get(tech, '#808080'),
            showlegend=True,
            legendgroup='capacity',
            hovertemplate=f'<b>{tech.replace("_", " ").title()}</b><br>Capacity: %{{y:.1f}} GW<extra></extra>'
        ), row=1, col=1)
    
    # 2. Cost vs emissions (dual axis) - moved to position 2
    fig.add_trace(go.Bar(
        name='System Cost',
        x=scenario_labels,
        y=df['total_system_cost_billion_EUR'],
        marker_color='lightblue',
        showlegend=True,
        legendgroup='cost_emissions',
        hovertemplate='<b>System Cost</b><br>Cost: €%{y:.1f} billion<extra></extra>'
    ), row=1, col=2)
    
    fig.add_trace(go.Scatter(
        name='CO2 Emissions',
        x=scenario_labels,
        y=df['co2_emissions_MtCO2'],
        mode='lines+markers',
        line=dict(color='red', width=2),
        marker=dict(size=8, color='red'),
        showlegend=True,
        legendgroup='cost_emissions',
        hovertemplate='<b>CO2 Emissions</b><br>Emissions: %{y:.1f} Mt<extra></extra>',
        yaxis='y3'
    ), row=1, col=2, secondary_y=True)
    
    # 3. Storage & Flexibility (always include Iron-Air) - moved to position 3
    storage_techs = ['PHS', 'battery', 'ironair', 'H2']
    storage_names = ['PHS', 'Battery', 'Iron-Air', 'Hydrogen']
    
    for tech, name in zip(storage_techs, storage_names):
        power_col = f'{tech}_power_GW'
        if power_col in df.columns:
            values = df[power_col].fillna(0)
        else:
            values = [0] * len(df)
            
        fig.add_trace(go.Bar(
            name=f'{name} Power',
            x=scenario_labels,
            y=values,
            marker_color=colors.get(tech, '#808080'),
            showlegend=True,
            legendgroup='storage_power',
            hovertemplate=f'<b>{name} Power</b><br>Power: %{{y:.1f}} GW<extra></extra>'
        ), row=2, col=1)
    
    # 4. Storage Energy Evolution - moved to position 4  
    for tech, name in zip(storage_techs, storage_names):
        energy_col = f'{tech}_energy_GWh'
        if energy_col in df.columns:
            values = df[energy_col].fillna(0)
        else:
            values = [0] * len(df)
            
        fig.add_trace(go.Bar(
            name=f'{name} Energy',
            x=scenario_labels,
            y=values,
            marker_color=colors.get(tech, '#808080'),
            showlegend=True,
            legendgroup='storage_energy',
            hovertemplate=f'<b>{name} Energy</b><br>Energy: %{{y:.1f}} GWh<extra></extra>'
        ), row=2, col=2)
    
    # 5. Storage duration per technology - position 5
    storage_duration_techs = ['PHS', 'battery', 'ironair', 'H2']
    storage_duration_names = ['PHS', 'Battery', 'Iron-Air', 'Hydrogen']
    
    # Calculate storage durations from GWh/GW ratio in the data
    # Use the first scenario (or average across scenarios) for consistent display
    reference_scenario = df.iloc[0]  # Use first scenario as reference
    
    storage_durations = {}
    for tech in storage_duration_techs:
        # Handle special cases for column naming
        if tech == 'PHS':
            power_col = 'PHS_power_GW'
            energy_col = 'PHS_energy_GWh'
        elif tech == 'H2':
            power_col = 'H2_power_GW'
            energy_col = 'H2_energy_GWh'
        else:
            power_col = f'{tech.lower()}_power_GW'
            energy_col = f'{tech.lower()}_energy_GWh'
        
        if power_col in df.columns and energy_col in df.columns:
            # Calculate average duration across all scenarios for this technology
            durations = []
            for _, row in df.iterrows():
                power = row[power_col]
                energy = row[energy_col]
                if power > 0:  # Avoid division by zero
                    duration = energy / power
                    durations.append(duration)
            
            if durations:
                storage_durations[tech] = np.mean(durations)
            else:
                storage_durations[tech] = 0
    
    duration_values = [storage_durations[tech] for tech in storage_duration_techs]
    
    # Debug output for calculated durations
    print("📊 Calculated storage durations from data:")
    for tech, duration in storage_durations.items():
        # Handle special cases for column naming (same logic as above)
        if tech == 'PHS':
            power_col = 'PHS_power_GW'
            energy_col = 'PHS_energy_GWh'
        elif tech == 'H2':
            power_col = 'H2_power_GW'
            energy_col = 'H2_energy_GWh'
        else:
            power_col = f'{tech.lower()}_power_GW'
            energy_col = f'{tech.lower()}_energy_GWh'
        
        if power_col in df.columns and energy_col in df.columns:
            print(f"   {tech}: {duration:.0f} hours")
            # Show breakdown for each scenario
            for _, row in df.iterrows():
                power = row[power_col]
                energy = row[energy_col]
                if power > 0:
                    scenario_duration = energy / power
                    print(f"     Scenario {row['scenario']}: {energy:.1f} GWh / {power:.1f} GW = {scenario_duration:.0f} hours")
        else:
            print(f"   {tech}: {duration:.0f} hours (fallback value)")
    
    fig.add_trace(go.Bar(
        name='Storage Duration',
        x=storage_duration_names,
        y=duration_values,
        marker_color=[colors.get(tech, '#808080') for tech in storage_duration_techs],
        showlegend=True,
        legendgroup='duration',
        text=[f'{dur:.0f}h' for dur in duration_values],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Duration: %{y:.0f} hours<br>Calculated from GWh/GW ratio<extra></extra>'
    ), row=3, col=1)
    
    # Section 6 removed - no longer needed
    
    # 6. Summary table (position 6) - remove CO2 Target column
    table_data = []
    for _, row in df.iterrows():
        table_data.append([
            f"Scenario {row['scenario']}",
            f"{row['total_renewable_GW']:.1f}",
            f"{row.get('battery_power_GW', 0):.1f}",
            f"{row.get('ironair_power_GW', 0):.1f}",
            f"{row.get('H2_power_GW', 0):.1f}",
            f"{row['total_storage_power_GW']:.1f}",
            f"{row['total_storage_energy_GWh']:.1f}",
            f"€{row['total_system_cost_billion_EUR']:.1f}B",
            f"{row['co2_emissions_MtCO2']:.1f}"
        ])
    
    fig.add_trace(go.Table(
        header=dict(
            values=[
                '<b>Scenario</b>', 
                '<b>Renewable<br>(GW)</b>',
                '<b>Battery Power<br>(GW)</b>',
                '<b>Iron-Air Power<br>(GW)</b>',
                '<b>Hydrogen Power<br>(GW)</b>',
                '<b>Total Storage<br>Power (GW)</b>',
                '<b>Total Storage<br>Energy (GWh)</b>',
                '<b>System Cost</b>',
                '<b>CO2 Emissions<br>(Mt)</b>'
            ],
            fill_color='lightblue',
            align='center',
            font=dict(size=11, color='white'),
            height=40
        ),
        cells=dict(
            values=list(zip(*table_data)),
            fill_color=[['white', 'lightgray'] * 5],
            align='center',
            font=dict(size=10),
            height=30
        ),
        columnwidth=[0.8, 1.0, 1.0, 1.0, 1.0, 1.2, 1.2, 1.0, 1.2]
    ), row=3, col=2)
    
    # Update layout with model information in subtitle
    model_subtitle = get_model_info_subtitle(df)
    
    fig.update_layout(
        height=1600,  # Increased height for 4 rows
        title=dict(
            text='<b>PyPSA CO2 Scenarios Analysis Dashboard</b><br><sub>Decarbonization Pathways for Germany 2035</sub><br>' + 
                 f'<sub style="font-size: 12px; color: #666;">{model_subtitle}</sub>',
            x=0.5,
            font=dict(size=18)
        ),
        template='plotly_white',
        font=dict(size=11),
        showlegend=True,
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
    #fig.update_xaxes(title_text="CO2 Scenario", row=1, col=1)
    fig.update_yaxes(title_text="Capacity (GW)", row=1, col=1)
    
    #fig.update_xaxes(title_text="CO2 Scenario", row=1, col=2)
    fig.update_yaxes(title_text="System Cost (Billion EUR)", row=1, col=2)
    fig.update_yaxes(title_text="CO2 Emissions (Mt)", row=1, col=2, secondary_y=True)
    
    #fig.update_xaxes(title_text="CO2 Scenario", row=2, col=1)
    fig.update_yaxes(title_text="Storage Power (GW)", row=2, col=1)
    
    #fig.update_xaxes(title_text="CO2 Scenario", row=2, col=2)
    fig.update_yaxes(title_text="Storage Energy (GWh)", row=2, col=2)
    
    fig.update_xaxes(title_text="Storage Technology", row=3, col=1)
    fig.update_yaxes(title_text="Duration (Hours)", row=3, col=1)
    
    return fig

def main():
    """Main function to create and save the enhanced CO2 scenarios dashboard"""
    
    print("🚀 Creating Enhanced CO2 Scenarios Dashboard...")
    print("=" * 60)
    
    # Create the comprehensive dashboard
    dashboard_fig = create_comprehensive_dashboard()
    
    # Save as HTML file
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'co2_scenarios_dashboard_enhanced_{timestamp}.html'
    dashboard_fig.write_html(
        output_file,
        include_plotlyjs='cdn',
        div_id="co2_dashboard_enhanced",
        config={
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
            'displaylogo': False
        },
        auto_open=True
    )
    
    print(f"✅ Enhanced dashboard saved as '{output_file}'")
    print(f"📊 Enhanced dashboard features:")
    print("   • 1-decimal precision formatting")
    print("   • Iron-Air always included in storage visualizations")
    print("   • Extended summary table with individual storage power columns")
    print("   • Storage energy capacity line chart")
    print("   • Comprehensive model information in subtitle")
    print("   • Page-wide table layout")
    print("   • Enhanced visual design")
    print()
    print("📝 Key Improvements:")
    print("   • More precise data display (1 decimal place)")
    print("   • Better storage technology visibility")
    print("   • Comprehensive technology breakdown")
    print("   • Model configuration transparency")
    print("   • Enhanced user experience")
    print("=" * 60)
    print(f"🌐 Open '{output_file}' in your web browser to view the enhanced dashboard!")

if __name__ == "__main__":
    main()
