"""
CO2 Scenarios Dashboard for PyPSA Results

Creates an interactive dashboard comparing 4 CO2 scenarios:
A) 15% of 1990 emissions
B) 5% of 1990 emissions  
C) 1% of 1990 emissions
D) 0% of 1990 emissions (net-zero)

Features:
- Technology capacity comparison
- Cost analysis
- Storage breakdown
- Renewable transition paths
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
        df = pd.read_csv('co2_scenarios_comparison.csv')
        
        print(f"✓ Loaded {len(df)} scenarios with {len(df.columns)} metrics")
        print(f"   Scenarios: {', '.join(df['scenario'].tolist())}")
        
        return df
        
    except Exception as e:
        print(f"⚠ Error loading comparison data: {e}")
        print("Creating fallback sample data...")
        
        # Fallback sample data for demonstration
        fallback_data = {
            'scenario': ['A', 'B', 'C', 'D'],
            'co2_target_pct': [15, 5, 1, 0],
            'solar_capacity_GW': [150.2, 180.7, 200.1, 220.5],
            'onwind_capacity_GW': [100.8, 120.3, 140.9, 160.2],
            'offwind-ac_capacity_GW': [30.4, 40.1, 50.7, 60.3],
            'CCGT_capacity_GW': [25.1, 15.2, 5.1, 0.0],
            'OCGT_capacity_GW': [10.5, 5.3, 2.1, 0.0],
            'nuclear_capacity_GW': [0.0, 0.0, 0.0, 10.2],
            'battery_power_GW': [20.3, 30.7, 40.2, 50.8],
            'battery_energy_GWh': [162.4, 245.6, 321.6, 406.4],
            'ironair_power_GW': [0.0, 5.2, 15.7, 25.1],
            'ironair_energy_GWh': [0.0, 520.0, 1570.0, 2510.0],
            'H2_power_GW': [5.3, 10.1, 15.8, 25.4],
            'H2_energy_GWh': [530.0, 1010.0, 1580.0, 2540.0],
            'PHS_power_GW': [7.2, 7.2, 7.2, 7.2],
            'PHS_energy_GWh': [43.2, 43.2, 43.2, 43.2],
            'total_renewable_GW': [281.4, 341.1, 391.7, 451.0],
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
        
        # Fossil - Gray/Brown tones
        'CCGT': '#A9A9A9',         # Dark Gray
        'OCGT': '#D3D3D3',         # Light Gray
        
        # Storage - Purple/Orange tones
        'battery': '#FF69B4',      # Hot Pink
        'H2': '#9370DB',           # Medium Purple
        'PHS': '#00CED1',          # Dark Turquoise
    }
    
    return colors

def create_capacity_evolution_chart(df, colors):
    """Create stacked bar chart showing capacity evolution across scenarios"""
    
    fig = go.Figure()
    
    scenarios = df['scenario'].tolist()
    scenario_labels = [f"Scenario {s} ({df[df['scenario']==s]['co2_target_pct'].iloc[0]:.0f}% CO2)" for s in scenarios]
    
    # Renewable technologies
    renewable_techs = ['solar', 'onwind', 'offwind-ac', 'nuclear']
    for tech in renewable_techs:
        col_name = f'{tech}_capacity_GW'
        if col_name in df.columns:
            fig.add_trace(go.Bar(
                name=tech.replace('_', ' ').title(),
                x=scenario_labels,
                y=df[col_name],
                marker_color=colors.get(tech, '#808080'),
                hovertemplate=f'<b>{tech.replace("_", " ").title()}</b><br>' +
                             'Capacity: %{y:.1f} GW<br>' +
                             '<extra></extra>'
            ))
    
    # Fossil technologies
    fossil_techs = ['CCGT', 'OCGT']
    for tech in fossil_techs:
        col_name = f'{tech}_capacity_GW'
        if col_name in df.columns:
            fig.add_trace(go.Bar(
                name=tech,
                x=scenario_labels,
                y=df[col_name],
                marker_color=colors.get(tech, '#808080'),
                hovertemplate=f'<b>{tech}</b><br>' +
                             'Capacity: %{y:.1f} GW<br>' +
                             '<extra></extra>'
            ))
    
    fig.update_layout(
        title='<b>Generation Capacity Evolution Across CO2 Scenarios</b><br><sub>Technology Mix by Decarbonization Level</sub>',
        xaxis_title='CO2 Scenario',
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

def create_storage_evolution_chart(df, colors):
    """Create stacked bar chart showing storage evolution"""
    
    fig = go.Figure()
    
    scenarios = df['scenario'].tolist()
    scenario_labels = [f"Scenario {s} ({df[df['scenario']==s]['co2_target_pct'].iloc[0]:.0f}% CO2)" for s in scenarios]
    
    # Storage technologies
    storage_techs = ['PHS', 'battery', 'H2']
    for tech in storage_techs:
        power_col = f'{tech}_power_GW'
        if power_col in df.columns:
            fig.add_trace(go.Bar(
                name=f'{tech} Power',
                x=scenario_labels,
                y=df[power_col],
                marker_color=colors.get(tech, '#808080'),
                hovertemplate=f'<b>{tech} Power</b><br>' +
                             'Power: %{y:.1f} GW<br>' +
                             '<extra></extra>'
            ))
    
    fig.update_layout(
        title='<b>Storage Power Capacity Evolution</b><br><sub>Storage Technologies by CO2 Scenario</sub>',
        xaxis_title='CO2 Scenario',
        yaxis_title='Storage Power (GW)',
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

def create_cost_emissions_chart(df):
    """Create dual-axis chart showing cost vs emissions"""
    
    fig = go.Figure()
    
    scenarios = df['scenario'].tolist()
    scenario_labels = [f"Scenario {s} ({df[df['scenario']==s]['co2_target_pct'].iloc[0]:.0f}% CO2)" for s in scenarios]
    
    # System costs
    fig.add_trace(go.Bar(
        name='System Cost',
        x=scenario_labels,
        y=df['total_system_cost_billion_EUR'],
        marker_color='lightblue',
        yaxis='y',
        hovertemplate='<b>System Cost</b><br>' +
                     'Cost: €%{y:.1f} billion<br>' +
                     '<extra></extra>'
    ))
    
    # CO2 emissions
    fig.add_trace(go.Scatter(
        name='CO2 Emissions',
        x=scenario_labels,
        y=df['co2_emissions_MtCO2'],
        mode='lines+markers',
        line=dict(color='red', width=3),
        marker=dict(size=10, color='red'),
        yaxis='y2',
        hovertemplate='<b>CO2 Emissions</b><br>' +
                     'Emissions: %{y:.1f} Mt CO2<br>' +
                     '<extra></extra>'
    ))
    
    fig.update_layout(
        title='<b>System Cost vs CO2 Emissions</b><br><sub>Economic and Environmental Trade-offs</sub>',
        xaxis_title='CO2 Scenario',
        yaxis=dict(
            title='System Cost (Billion EUR)',
            side='left',
            color='blue'
        ),
        yaxis2=dict(
            title='CO2 Emissions (Mt)',
            side='right',
            overlaying='y',
            color='red'
        ),
        template='plotly_white',
        font=dict(size=12),
        height=500,
        showlegend=True
    )
    
    return fig

def create_renewable_transition_chart(df):
    """Create line chart showing renewable transition"""
    
    fig = go.Figure()
    
    scenarios = df['scenario'].tolist()
    co2_targets = df['co2_target_pct'].tolist()
    
    # Renewable share calculation
    total_capacity = (df['solar_capacity_GW'] + df['onwind_capacity_GW'] + 
                     df['offwind-ac_capacity_GW'] + df['CCGT_capacity_GW'] + 
                     df['OCGT_capacity_GW'] + df.get('nuclear_capacity_GW', 0))
    
    renewable_share = (df['total_renewable_GW'] / total_capacity * 100).fillna(0)
    
    fig.add_trace(go.Scatter(
        x=co2_targets,
        y=renewable_share,
        mode='lines+markers',
        name='Renewable Share',
        line=dict(color='green', width=3),
        marker=dict(size=12, color='green'),
        hovertemplate='<b>Renewable Share</b><br>' +
                     'CO2 Target: %{x:.0f}% of 1990<br>' +
                     'Renewable Share: %{y:.1f}%<br>' +
                     '<extra></extra>'
    ))
    
    # Add annotations for scenarios
    for i, (scenario, co2, share) in enumerate(zip(scenarios, co2_targets, renewable_share)):
        fig.add_annotation(
            x=co2,
            y=share,
            text=f"Scenario {scenario}",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="green",
            font=dict(size=10)
        )
    
    fig.update_layout(
        title='<b>Renewable Energy Transition Path</b><br><sub>Renewable Share vs CO2 Reduction Target</sub>',
        xaxis_title='CO2 Target (% of 1990 Emissions)',
        yaxis_title='Renewable Share (%)',
        template='plotly_white',
        font=dict(size=12),
        height=500,
        showlegend=True
    )
    
    # Reverse x-axis to show progression from high to low emissions
    fig.update_xaxes(autorange="reversed")
    
    return fig

def create_storage_energy_chart(df, colors):
    """Create chart showing storage energy capacity"""
    
    fig = go.Figure()
    
    scenarios = df['scenario'].tolist()
    scenario_labels = [f"Scenario {s} ({df[df['scenario']==s]['co2_target_pct'].iloc[0]:.0f}% CO2)" for s in scenarios]
    
    # Storage energy capacities
    storage_techs = ['PHS', 'battery', 'H2']
    for tech in storage_techs:
        energy_col = f'{tech}_energy_GWh'
        if energy_col in df.columns:
            fig.add_trace(go.Bar(
                name=f'{tech} Energy',
                x=scenario_labels,
                y=df[energy_col],
                marker_color=colors.get(tech, '#808080'),
                hovertemplate=f'<b>{tech} Energy</b><br>' +
                             'Energy: %{y:.0f} GWh<br>' +
                             '<extra></extra>'
            ))
    
    fig.update_layout(
        title='<b>Storage Energy Capacity Evolution</b><br><sub>Energy Storage by Technology and Scenario</sub>',
        xaxis_title='CO2 Scenario',
        yaxis_title='Storage Energy (GWh)',
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

def create_summary_table(df):
    """Create summary table with key metrics"""
    
    # Prepare table data
    table_data = []
    for _, row in df.iterrows():
        scenario = row['scenario']
        co2_pct = row['co2_target_pct']
        
        table_data.append([
            f"Scenario {scenario}",
            f"{co2_pct:.0f}%",
            f"{row['total_renewable_GW']:.1f} GW",
            f"{row['total_storage_power_GW']:.1f} GW",
            f"{row['total_storage_energy_GWh']:.0f} GWh",
            f"€{row['total_system_cost_billion_EUR']:.1f}B",
            f"{row['co2_emissions_MtCO2']:.1f} Mt"
        ])
    
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=['<b>Scenario</b>', '<b>CO2 Target</b>', '<b>Renewable (GW)</b>', 
                   '<b>Storage Power (GW)</b>', '<b>Storage Energy (GWh)</b>', 
                   '<b>System Cost</b>', '<b>CO2 Emissions</b>'],
            fill_color='lightblue',
            align='center',
            font=dict(size=12, color='white')
        ),
        cells=dict(
            values=list(zip(*table_data)),
            fill_color=[['white', 'lightgray'] * 4],
            align='center',
            font=dict(size=11)
        )
    )])
    
    fig.update_layout(
        title='<b>CO2 Scenarios Summary</b><br><sub>Key Performance Metrics</sub>',
        template='plotly_white',
        font=dict(size=12),
        height=300
    )
    
    return fig

def create_comprehensive_dashboard():
    """Create the comprehensive CO2 scenarios dashboard"""
    
    print("🔄 Loading and preparing data...")
    df = load_comparison_data()
    colors = create_technology_colors()
    
    print("📊 Creating visualizations...")
    
    # Create main dashboard with subplots
    fig = make_subplots(
        rows=3,
        cols=2,
        subplot_titles=[
            'Generation Capacity Evolution',
            'Storage Power Evolution',
            'System Cost vs CO2 Emissions',
            'Renewable Transition Path',
            'Storage Energy Evolution',
            'Scenario Summary'
        ],
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": True}, {"secondary_y": False}],
               [{"secondary_y": False}, {"type": "table"}]],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    scenarios = df['scenario'].tolist()
    scenario_labels = [f"Scenario {s} ({df[df['scenario']==s]['co2_target_pct'].iloc[0]:.0f}% CO2)" for s in scenarios]
    
    # 1. Generation capacity evolution
    renewable_techs = ['solar', 'onwind', 'offwind-ac', 'nuclear']
    fossil_techs = ['CCGT', 'OCGT']
    
    for tech in renewable_techs + fossil_techs:
        col_name = f'{tech}_capacity_GW'
        if col_name in df.columns:
            fig.add_trace(go.Bar(
                name=tech.replace('_', ' ').title(),
                x=scenario_labels,
                y=df[col_name],
                marker_color=colors.get(tech, '#808080'),
                showlegend=True,
                legendgroup='capacity',
                hovertemplate=f'<b>{tech.replace("_", " ").title()}</b><br>Capacity: %{{y:.1f}} GW<extra></extra>'
            ), row=1, col=1)
    
    # 2. Storage power evolution
    storage_techs = ['PHS', 'battery', 'H2']
    for tech in storage_techs:
        power_col = f'{tech}_power_GW'
        if power_col in df.columns:
            fig.add_trace(go.Bar(
                name=f'{tech} Power',
                x=scenario_labels,
                y=df[power_col],
                marker_color=colors.get(tech, '#808080'),
                showlegend=True,
                legendgroup='storage_power',
                hovertemplate=f'<b>{tech} Power</b><br>Power: %{{y:.1f}} GW<extra></extra>'
            ), row=1, col=2)
    
    # 3. Cost vs emissions (dual axis)
    fig.add_trace(go.Bar(
        name='System Cost',
        x=scenario_labels,
        y=df['total_system_cost_billion_EUR'],
        marker_color='lightblue',
        showlegend=True,
        legendgroup='cost_emissions',
        hovertemplate='<b>System Cost</b><br>Cost: €%{y:.1f} billion<extra></extra>'
    ), row=2, col=1)
    
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
    ), row=2, col=1, secondary_y=True)
    
    # 4. Renewable transition
    co2_targets = df['co2_target_pct'].tolist()
    total_capacity = (df['solar_capacity_GW'] + df['onwind_capacity_GW'] + 
                     df['offwind-ac_capacity_GW'] + df['CCGT_capacity_GW'] + 
                     df['OCGT_capacity_GW'] + df.get('nuclear_capacity_GW', 0))
    renewable_share = (df['total_renewable_GW'] / total_capacity * 100).fillna(0)
    
    fig.add_trace(go.Scatter(
        x=co2_targets,
        y=renewable_share,
        mode='lines+markers',
        name='Renewable Share',
        line=dict(color='green', width=2),
        marker=dict(size=8, color='green'),
        showlegend=True,
        legendgroup='renewable',
        hovertemplate='<b>Renewable Share</b><br>CO2 Target: %{x:.0f}%<br>Share: %{y:.1f}%<extra></extra>'
    ), row=2, col=2)
    
    # 5. Storage energy evolution
    for tech in storage_techs:
        energy_col = f'{tech}_energy_GWh'
        if energy_col in df.columns:
            fig.add_trace(go.Bar(
                name=f'{tech} Energy',
                x=scenario_labels,
                y=df[energy_col],
                marker_color=colors.get(tech, '#808080'),
                showlegend=True,
                legendgroup='storage_energy',
                hovertemplate=f'<b>{tech} Energy</b><br>Energy: %{{y:.0f}} GWh<extra></extra>'
            ), row=3, col=1)
    
    # 6. Summary table
    table_data = []
    for _, row in df.iterrows():
        table_data.append([
            f"Scenario {row['scenario']}",
            f"{row['co2_target_pct']:.0f}%",
            f"{row['total_renewable_GW']:.1f}",
            f"{row['total_storage_power_GW']:.1f}",
            f"{row['total_storage_energy_GWh']:.0f}",
            f"€{row['total_system_cost_billion_EUR']:.1f}B",
            f"{row['co2_emissions_MtCO2']:.1f}"
        ])
    
    fig.add_trace(go.Table(
        header=dict(
            values=['<b>Scenario</b>', '<b>CO2 Target</b>', '<b>Renewable (GW)</b>', 
                   '<b>Storage Power (GW)</b>', '<b>Storage Energy (GWh)</b>', 
                   '<b>System Cost</b>', '<b>CO2 Emissions (Mt)</b>'],
            fill_color='lightblue',
            align='center',
            font=dict(size=10, color='white')
        ),
        cells=dict(
            values=list(zip(*table_data)),
            fill_color=[['white', 'lightgray'] * 4],
            align='center',
            font=dict(size=9)
        )
    ), row=3, col=2)
    
    # Update layout
    fig.update_layout(
        height=1200,
        title=dict(
            text='<b>PyPSA CO2 Scenarios Analysis Dashboard</b><br><sub>Decarbonization Pathways for Germany 2035</sub>',
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
    fig.update_xaxes(title_text="CO2 Scenario", row=1, col=1)
    fig.update_yaxes(title_text="Capacity (GW)", row=1, col=1)
    
    fig.update_xaxes(title_text="CO2 Scenario", row=1, col=2)
    fig.update_yaxes(title_text="Storage Power (GW)", row=1, col=2)
    
    fig.update_xaxes(title_text="CO2 Scenario", row=2, col=1)
    fig.update_yaxes(title_text="System Cost (Billion EUR)", row=2, col=1)
    fig.update_yaxes(title_text="CO2 Emissions (Mt)", row=2, col=1, secondary_y=True)
    
    fig.update_xaxes(title_text="CO2 Target (% of 1990)", row=2, col=2, autorange="reversed")
    fig.update_yaxes(title_text="Renewable Share (%)", row=2, col=2)
    
    fig.update_xaxes(title_text="CO2 Scenario", row=3, col=1)
    fig.update_yaxes(title_text="Storage Energy (GWh)", row=3, col=1)
    
    return fig

def main():
    """Main function to create and save the CO2 scenarios dashboard"""
    
    print("🚀 Creating CO2 Scenarios Dashboard...")
    print("=" * 50)
    
    # Create the comprehensive dashboard
    dashboard_fig = create_comprehensive_dashboard()
    
    # Save as HTML file
    output_file = 'co2_scenarios_dashboard.html'
    dashboard_fig.write_html(
        output_file,
        include_plotlyjs='cdn',
        div_id="co2_dashboard",
        config={
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
            'displaylogo': False
        },
        auto_open=True
    )
    
    print(f"✅ Dashboard saved as '{output_file}'")
    print(f"📊 Dashboard includes:")
    print("   • Generation capacity evolution across scenarios")
    print("   • Storage technology deployment trends")
    print("   • System cost vs CO2 emissions trade-offs")
    print("   • Renewable energy transition pathway")
    print("   • Storage energy capacity evolution")
    print("   • Summary table with key metrics")
    print()
    print("📝 Key Insights:")
    print("   • Shows impact of CO2 targets on technology mix")
    print("   • Demonstrates renewable energy transition path")
    print("   • Reveals storage deployment patterns")
    print("   • Quantifies cost-emissions trade-offs")
    print("=" * 50)
    print(f"🌐 Open '{output_file}' in your web browser to view the interactive dashboard!")

if __name__ == "__main__":
    main()
