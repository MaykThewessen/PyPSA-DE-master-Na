"""
Realistic Hydrogen Cost Comparison Dashboard

This script creates an interactive dashboard comparing:
1. Original PyPSA optimization results (optimistic H2 costs)
2. Theoretical optimization with realistic hydrogen costs

Shows the dramatic shift from hydrogen-dominated to Iron-Air battery-dominated storage system.

Author: AI Assistant
Based on PyPSA theoretical analysis with realistic H2 costs
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

def create_comparison_data():
    """Create data comparing original PyPSA results with realistic H2 cost optimization"""
    
    # Original PyPSA Results (Optimistic H2 Costs)
    original_data = {
        'technology': ['H2 Storage', 'Battery', 'Home Battery', 'PHS'],
        'power_gw': [75.1, 40.2, 5.7, 7.2],
        'energy_gwh': [31121, 393, 21, 36],
        'cost_billion_eur': [268.9, 5.4, 0.8, 0.0],
        'share_energy': [98.6, 1.2, 0.1, 0.1]
    }
    
    # Theoretical Optimal Results (Realistic H2 Costs)
    optimal_data = {
        'technology': ['Iron-Air Battery', 'H2 Storage', 'Battery', 'PHS'],
        'power_gw': [200.0, 23.8, 500.0, 8.3],
        'energy_gwh': [20000, 9520, 2000, 50],
        'cost_billion_eur': [17.3, 83.5, 66.3, 0.0],
        'share_energy': [63.4, 30.2, 6.3, 0.2]
    }
    
    original_df = pd.DataFrame(original_data)
    optimal_df = pd.DataFrame(optimal_data)
    
    return original_df, optimal_df

def create_technology_colors():
    """Define consistent color scheme for storage technologies"""
    
    colors = {
        'H2 Storage': '#9370DB',      # Medium Purple
        'Battery': '#FF69B4',         # Hot Pink  
        'Home Battery': '#FF1493',    # Deep Pink
        'PHS': '#00CED1',            # Dark Turquoise
        'Iron-Air Battery': '#FF8C00' # Dark Orange
    }
    
    return colors

def create_energy_capacity_comparison(original_df, optimal_df, colors):
    """Create side-by-side comparison of energy storage capacity"""
    
    fig = go.Figure()
    
    # Original scenario
    fig.add_trace(go.Bar(
        name='Original (Optimistic H2)',
        x=['Original PyPSA'],
        y=[original_df['energy_gwh'].sum()],
        marker_color='lightcoral',
        text=[f"{original_df['energy_gwh'].sum():.0f} GWh"],
        textposition='inside',
        textfont=dict(size=14, color='white'),
        hovertemplate='<b>Original PyPSA</b><br>' +
                     'Total Energy: %{y:.0f} GWh<br>' +
                     '<extra></extra>',
        width=0.4
    ))
    
    # Optimal scenario  
    fig.add_trace(go.Bar(
        name='Optimal (Realistic H2)',
        x=['Optimal System'],
        y=[optimal_df['energy_gwh'].sum()],
        marker_color='lightgreen',
        text=[f"{optimal_df['energy_gwh'].sum():.0f} GWh"],
        textposition='inside',
        textfont=dict(size=14, color='white'),
        hovertemplate='<b>Optimal System</b><br>' +
                     'Total Energy: %{y:.0f} GWh<br>' +
                     '<extra></extra>',
        width=0.4
    ))
    
    fig.update_layout(
        title='<b>Total Energy Storage Capacity Comparison</b><br><sub>Same Total Energy, Different Technology Mix</sub>',
        xaxis_title='System Configuration',
        yaxis_title='Total Energy Capacity (GWh)',
        template='plotly_white',
        font=dict(size=12),
        height=400,
        showlegend=True,
        xaxis=dict(categoryorder='array', categoryarray=['Original PyPSA', 'Optimal System'])
    )
    
    return fig

def create_technology_breakdown_comparison(original_df, optimal_df, colors):
    """Create stacked bar chart comparing technology breakdown"""
    
    fig = go.Figure()
    
    # Original system breakdown
    for _, row in original_df.iterrows():
        tech = row['technology']
        fig.add_trace(go.Bar(
            name=f"{tech} (Original)",
            x=['Original PyPSA'],
            y=[row['energy_gwh']],
            marker_color=colors.get(tech, '#808080'),
            hovertemplate=f'<b>{tech}</b><br>' +
                         'Energy: %{y:.0f} GWh<br>' +
                         f'Share: {row["share_energy"]:.1f}%<br>' +
                         '<extra></extra>'
        ))
    
    # Optimal system breakdown
    for _, row in optimal_df.iterrows():
        tech = row['technology']
        fig.add_trace(go.Bar(
            name=f"{tech} (Optimal)",
            x=['Optimal System'],
            y=[row['energy_gwh']],
            marker_color=colors.get(tech, '#808080'),
            hovertemplate=f'<b>{tech}</b><br>' +
                         'Energy: %{y:.0f} GWh<br>' +
                         f'Share: {row["share_energy"]:.1f}%<br>' +
                         '<extra></extra>'
        ))
    
    fig.update_layout(
        title='<b>Storage Technology Mix Comparison</b><br><sub>Energy Capacity by Technology Type</sub>',
        xaxis_title='System Configuration',
        yaxis_title='Energy Capacity (GWh)',
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

def create_cost_comparison(original_df, optimal_df):
    """Create cost comparison chart"""
    
    original_total = original_df['cost_billion_eur'].sum()
    optimal_total = optimal_df['cost_billion_eur'].sum()
    savings = original_total - optimal_total
    savings_pct = (savings / original_total) * 100
    
    fig = go.Figure()
    
    # Cost bars
    fig.add_trace(go.Bar(
        name='System Cost',
        x=['Original PyPSA', 'Optimal System', 'Savings'],
        y=[original_total, optimal_total, savings],
        marker_color=['lightcoral', 'lightgreen', 'gold'],
        text=[f'€{original_total:.1f}B', f'€{optimal_total:.1f}B', f'€{savings:.1f}B<br>({savings_pct:.1f}%)'],
        textposition='inside',
        textfont=dict(size=12, color='white'),
        hovertemplate='<b>%{x}</b><br>' +
                     'Cost: €%{y:.1f} billion<br>' +
                     '<extra></extra>'
    ))
    
    fig.update_layout(
        title='<b>Total System Cost Comparison</b><br><sub>Capital Investment Required</sub>',
        xaxis_title='System Configuration',
        yaxis_title='Total Cost (Billion EUR)',
        template='plotly_white',
        font=dict(size=12),
        height=400,
        showlegend=False
    )
    
    return fig

def create_technology_shift_analysis(original_df, optimal_df):
    """Create analysis showing technology shifts"""
    
    # Prepare data for shift analysis
    tech_changes = []
    
    # H2 Storage comparison
    h2_original = original_df[original_df['technology'] == 'H2 Storage']['energy_gwh'].values[0]
    h2_optimal = optimal_df[optimal_df['technology'] == 'H2 Storage']['energy_gwh'].values[0]
    h2_change = ((h2_optimal - h2_original) / h2_original) * 100
    
    # Battery comparison (combine all battery types)
    battery_original = original_df[original_df['technology'].isin(['Battery', 'Home Battery'])]['energy_gwh'].sum()
    battery_optimal = optimal_df[optimal_df['technology'] == 'Battery']['energy_gwh'].values[0]
    battery_change = ((battery_optimal - battery_original) / battery_original) * 100
    
    # Iron-Air (new technology)
    ironair_optimal = optimal_df[optimal_df['technology'] == 'Iron-Air Battery']['energy_gwh'].values[0]
    
    # PHS comparison
    phs_original = original_df[original_df['technology'] == 'PHS']['energy_gwh'].values[0]
    phs_optimal = optimal_df[optimal_df['technology'] == 'PHS']['energy_gwh'].values[0]
    phs_change = ((phs_optimal - phs_original) / phs_original) * 100
    
    # Create waterfall-style chart
    fig = go.Figure()
    
    technologies = ['H2 Storage', 'Li-ion Battery', 'Iron-Air Battery', 'PHS']
    changes = [h2_change, battery_change, 100, phs_change]  # Iron-Air is 100% new
    original_vals = [h2_original, battery_original, 0, phs_original]
    optimal_vals = [h2_optimal, battery_optimal, ironair_optimal, phs_optimal]
    
    colors_change = ['red' if x < 0 else 'green' if x > 0 else 'gray' for x in changes]
    colors_change[2] = 'orange'  # Iron-Air is new technology
    
    fig.add_trace(go.Bar(
        name='Change in Deployment',
        x=technologies,
        y=changes,
        marker_color=colors_change,
        text=[f'{c:+.0f}%' if c != 100 else 'NEW' for c in changes],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>' +
                     'Change: %{y:+.1f}%<br>' +
                     '<extra></extra>'
    ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="black", line_width=1)
    
    fig.update_layout(
        title='<b>Technology Deployment Changes</b><br><sub>Percentage Change from Original to Optimal System</sub>',
        xaxis_title='Storage Technology',
        yaxis_title='Change in Deployment (%)',
        template='plotly_white',
        font=dict(size=12),
        height=400,
        showlegend=False,
        annotations=[
            dict(
                x=0, y=h2_change-10,
                text=f"From {h2_original:.0f} to {h2_optimal:.0f} GWh",
                showarrow=False, font=dict(size=10, color='red')
            ),
            dict(
                x=1, y=battery_change+20,
                text=f"From {battery_original:.0f} to {battery_optimal:.0f} GWh",
                showarrow=False, font=dict(size=10, color='green')
            ),
            dict(
                x=2, y=120,
                text=f"New: {ironair_optimal:.0f} GWh",
                showarrow=False, font=dict(size=10, color='orange')
            ),
            dict(
                x=3, y=phs_change+5,
                text=f"From {phs_original:.0f} to {phs_optimal:.0f} GWh",
                showarrow=False, font=dict(size=10, color='green')
            )
        ]
    )
    
    return fig

def create_power_vs_energy_analysis(original_df, optimal_df):
    """Create scatter plot showing power vs energy characteristics"""
    
    fig = go.Figure()
    
    # Original system
    fig.add_trace(go.Scatter(
        x=original_df['power_gw'],
        y=original_df['energy_gwh'],
        mode='markers+text',
        name='Original System',
        marker=dict(size=15, color='lightcoral', line=dict(width=2, color='darkred')),
        text=original_df['technology'],
        textposition='top center',
        hovertemplate='<b>%{text}</b> (Original)<br>' +
                     'Power: %{x:.1f} GW<br>' +
                     'Energy: %{y:.0f} GWh<br>' +
                     'Duration: %{customdata:.1f} hours<br>' +
                     '<extra></extra>',
        customdata=original_df['energy_gwh'] / original_df['power_gw']
    ))
    
    # Optimal system
    fig.add_trace(go.Scatter(
        x=optimal_df['power_gw'],
        y=optimal_df['energy_gwh'],
        mode='markers+text',
        name='Optimal System',
        marker=dict(size=15, color='lightgreen', line=dict(width=2, color='darkgreen')),
        text=optimal_df['technology'],
        textposition='bottom center',
        hovertemplate='<b>%{text}</b> (Optimal)<br>' +
                     'Power: %{x:.1f} GW<br>' +
                     'Energy: %{y:.0f} GWh<br>' +
                     'Duration: %{customdata:.1f} hours<br>' +
                     '<extra></extra>',
        customdata=optimal_df['energy_gwh'] / optimal_df['power_gw']
    ))
    
    # Add diagonal lines showing duration
    x_max = max(original_df['power_gw'].max(), optimal_df['power_gw'].max()) * 1.1
    y_max = max(original_df['energy_gwh'].max(), optimal_df['energy_gwh'].max()) * 1.1
    
    # Duration lines (1h, 10h, 100h, 1000h)
    durations = [1, 10, 100, 1000]
    for duration in durations:
        x_line = np.linspace(0, min(x_max, y_max/duration), 100)
        y_line = x_line * duration
        fig.add_trace(go.Scatter(
            x=x_line,
            y=y_line,
            mode='lines',
            line=dict(dash='dot', color='gray', width=1),
            name=f'{duration}h duration',
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Add duration labels
        if y_max > duration * x_max / 2:
            fig.add_annotation(
                x=x_max/2,
                y=(x_max/2) * duration,
                text=f'{duration}h',
                showarrow=False,
                font=dict(size=10, color='gray'),
                bgcolor='white',
                bordercolor='gray',
                borderwidth=1
            )
    
    fig.update_layout(
        title='<b>Power vs Energy Characteristics</b><br><sub>Technology Performance and Duration Analysis</sub>',
        xaxis_title='Power Capacity (GW)',
        yaxis_title='Energy Capacity (GWh)',
        template='plotly_white',
        font=dict(size=12),
        height=500,
        showlegend=True,
        xaxis=dict(range=[0, x_max]),
        yaxis=dict(range=[0, y_max])
    )
    
    return fig

def create_cost_breakdown_comparison(original_df, optimal_df, colors):
    """Create stacked bar chart showing cost breakdown by technology"""
    
    fig = go.Figure()
    
    # Original system cost breakdown
    for _, row in original_df.iterrows():
        tech = row['technology']
        fig.add_trace(go.Bar(
            name=f"{tech} (Original)",
            x=['Original PyPSA'],
            y=[row['cost_billion_eur']],
            marker_color=colors.get(tech, '#808080'),
            hovertemplate=f'<b>{tech}</b><br>' +
                         'Cost: €%{y:.1f} billion<br>' +
                         f'Share: {(row["cost_billion_eur"]/original_df["cost_billion_eur"].sum()*100):.1f}%<br>' +
                         '<extra></extra>'
        ))
    
    # Optimal system cost breakdown
    for _, row in optimal_df.iterrows():
        tech = row['technology']
        fig.add_trace(go.Bar(
            name=f"{tech} (Optimal)",
            x=['Optimal System'],
            y=[row['cost_billion_eur']],
            marker_color=colors.get(tech, '#808080'),
            hovertemplate=f'<b>{tech}</b><br>' +
                         'Cost: €%{y:.1f} billion<br>' +
                         f'Share: {(row["cost_billion_eur"]/optimal_df["cost_billion_eur"].sum()*100):.1f}%<br>' +
                         '<extra></extra>'
        ))
    
    fig.update_layout(
        title='<b>System Cost Breakdown by Technology</b><br><sub>Capital Investment by Storage Type</sub>',
        xaxis_title='System Configuration',
        yaxis_title='Cost (Billion EUR)',
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

def create_summary_metrics_table(original_df, optimal_df):
    """Create summary table with key metrics"""
    
    # Calculate summary metrics
    original_total_energy = original_df['energy_gwh'].sum()
    optimal_total_energy = optimal_df['energy_gwh'].sum()
    original_total_power = original_df['power_gw'].sum()
    optimal_total_power = optimal_df['power_gw'].sum()
    original_total_cost = original_df['cost_billion_eur'].sum()
    optimal_total_cost = optimal_df['cost_billion_eur'].sum()
    
    cost_savings = original_total_cost - optimal_total_cost
    cost_savings_pct = (cost_savings / original_total_cost) * 100
    
    h2_original_share = original_df[original_df['technology'] == 'H2 Storage']['share_energy'].values[0]
    h2_optimal_share = optimal_df[optimal_df['technology'] == 'H2 Storage']['share_energy'].values[0]
    
    # Create table data
    metrics_data = [
        ['Total Energy Capacity', f'{original_total_energy:.0f} GWh', f'{optimal_total_energy:.0f} GWh', 'Same total energy requirement'],
        ['Total Power Capacity', f'{original_total_power:.1f} GW', f'{optimal_total_power:.1f} GW', f'+{((optimal_total_power-original_total_power)/original_total_power*100):.0f}% (more flexible)'],
        ['Total System Cost', f'€{original_total_cost:.1f}B', f'€{optimal_total_cost:.1f}B', f'€{cost_savings:.1f}B savings ({cost_savings_pct:.1f}%)'],
        ['H2 Storage Dominance', f'{h2_original_share:.1f}% of energy', f'{h2_optimal_share:.1f}% of energy', f'{h2_optimal_share-h2_original_share:.1f} pp reduction'],
        ['Iron-Air Battery Share', '0% (not deployed)', '63.4% of energy', 'Becomes dominant technology'],
        ['Technology Diversity', '4 technologies', '4 technologies', 'Better duration matching'],
        ['Investment Risk', 'H2-dependent (98.6%)', 'Diversified portfolio', 'Lower technology risk'],
        ['Deployment Readiness', 'H2 infrastructure needed', 'Commercial technologies', 'Earlier deployment possible']
    ]
    
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=['<b>Metric</b>', '<b>Original PyPSA</b>', '<b>Optimal System</b>', '<b>Impact</b>'],
            fill_color='lightblue',
            align='center',
            font=dict(size=12, color='white')
        ),
        cells=dict(
            values=list(zip(*metrics_data)),
            fill_color=[['white', 'lightgray'] * 4],
            align=['left', 'center', 'center', 'left'],
            font=dict(size=11)
        )
    )])
    
    fig.update_layout(
        title='<b>System Comparison Summary</b><br><sub>Key Performance Metrics</sub>',
        template='plotly_white',
        font=dict(size=12),
        height=400
    )
    
    return fig

def create_comprehensive_dashboard():
    """Create the comprehensive comparison dashboard"""
    
    print("🔄 Loading comparison data...")
    original_df, optimal_df = create_comparison_data()
    colors = create_technology_colors()
    
    print("📊 Creating comparison visualizations...")
    
    # Create main dashboard with subplots
    fig = make_subplots(
        rows=3,
        cols=2,
        subplot_titles=[
            'Total Energy Storage Capacity',
            'Technology Mix Comparison',
            'System Cost Analysis',
            'Technology Deployment Changes',
            'Power vs Energy Characteristics',
            'Cost Breakdown by Technology'
        ],
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    # 1. Total capacity comparison
    original_total = original_df['energy_gwh'].sum()
    optimal_total = optimal_df['energy_gwh'].sum()
    
    fig.add_trace(go.Bar(
        name='Total Energy Capacity',
        x=['Original PyPSA', 'Optimal System'],
        y=[original_total, optimal_total],
        marker_color=['lightcoral', 'lightgreen'],
        text=[f'{original_total:.0f} GWh', f'{optimal_total:.0f} GWh'],
        textposition='inside',
        showlegend=True,
        legendgroup='capacity',
        hovertemplate='<b>%{x}</b><br>Total Energy: %{y:.0f} GWh<extra></extra>'
    ), row=1, col=1)
    
    # 2. Technology mix comparison
    # Original system
    for _, row in original_df.iterrows():
        tech = row['technology']
        fig.add_trace(go.Bar(
            name=f"{tech} (Original)",
            x=['Original PyPSA'],
            y=[row['energy_gwh']],
            marker_color=colors.get(tech, '#808080'),
            showlegend=True,
            legendgroup='tech_original',
            hovertemplate=f'<b>{tech}</b><br>Energy: %{{y:.0f}} GWh<br>Share: {row["share_energy"]:.1f}%<extra></extra>'
        ), row=1, col=2)
    
    # Optimal system
    for _, row in optimal_df.iterrows():
        tech = row['technology']
        fig.add_trace(go.Bar(
            name=f"{tech} (Optimal)",
            x=['Optimal System'],
            y=[row['energy_gwh']],
            marker_color=colors.get(tech, '#808080'),
            showlegend=True,
            legendgroup='tech_optimal',
            hovertemplate=f'<b>{tech}</b><br>Energy: %{{y:.0f}} GWh<br>Share: {row["share_energy"]:.1f}%<extra></extra>'
        ), row=1, col=2)
    
    # 3. Cost comparison
    original_cost = original_df['cost_billion_eur'].sum()
    optimal_cost = optimal_df['cost_billion_eur'].sum()
    savings = original_cost - optimal_cost
    savings_pct = (savings / original_cost) * 100
    
    fig.add_trace(go.Bar(
        name='System Cost',
        x=['Original PyPSA', 'Optimal System', 'Savings'],
        y=[original_cost, optimal_cost, savings],
        marker_color=['lightcoral', 'lightgreen', 'gold'],
        text=[f'€{original_cost:.1f}B', f'€{optimal_cost:.1f}B', f'€{savings:.1f}B<br>({savings_pct:.1f}%)'],
        textposition='inside',
        showlegend=True,
        legendgroup='cost',
        hovertemplate='<b>%{x}</b><br>Cost: €%{y:.1f} billion<extra></extra>'
    ), row=2, col=1)
    
    # 4. Technology changes
    # Calculate changes
    h2_original = original_df[original_df['technology'] == 'H2 Storage']['energy_gwh'].values[0]
    h2_optimal = optimal_df[optimal_df['technology'] == 'H2 Storage']['energy_gwh'].values[0]
    h2_change = ((h2_optimal - h2_original) / h2_original) * 100
    
    battery_original = original_df[original_df['technology'].isin(['Battery', 'Home Battery'])]['energy_gwh'].sum()
    battery_optimal = optimal_df[optimal_df['technology'] == 'Battery']['energy_gwh'].values[0]
    battery_change = ((battery_optimal - battery_original) / battery_original) * 100
    
    ironair_optimal = optimal_df[optimal_df['technology'] == 'Iron-Air Battery']['energy_gwh'].values[0]
    
    phs_original = original_df[original_df['technology'] == 'PHS']['energy_gwh'].values[0]
    phs_optimal = optimal_df[optimal_df['technology'] == 'PHS']['energy_gwh'].values[0]
    phs_change = ((phs_optimal - phs_original) / phs_original) * 100
    
    technologies = ['H2 Storage', 'Li-ion Battery', 'Iron-Air Battery', 'PHS']
    changes = [h2_change, battery_change, 100, phs_change]
    colors_change = ['red', 'green', 'orange', 'green']
    
    fig.add_trace(go.Bar(
        name='Change in Deployment',
        x=technologies,
        y=changes,
        marker_color=colors_change,
        text=[f'{c:+.0f}%' if c != 100 else 'NEW' for c in changes],
        textposition='outside',
        showlegend=True,
        legendgroup='changes',
        hovertemplate='<b>%{x}</b><br>Change: %{y:+.1f}%<extra></extra>'
    ), row=2, col=2)
    
    # 5. Power vs Energy scatter
    # Original system
    fig.add_trace(go.Scatter(
        x=original_df['power_gw'],
        y=original_df['energy_gwh'],
        mode='markers+text',
        name='Original System',
        marker=dict(size=12, color='lightcoral'),
        text=original_df['technology'],
        textposition='top center',
        showlegend=True,
        legendgroup='scatter',
        hovertemplate='<b>%{text}</b> (Original)<br>Power: %{x:.1f} GW<br>Energy: %{y:.0f} GWh<extra></extra>'
    ), row=3, col=1)
    
    fig.add_trace(go.Scatter(
        x=optimal_df['power_gw'],
        y=optimal_df['energy_gwh'],
        mode='markers+text',
        name='Optimal System',
        marker=dict(size=12, color='lightgreen'),
        text=optimal_df['technology'],
        textposition='bottom center',
        showlegend=True,
        legendgroup='scatter',
        hovertemplate='<b>%{text}</b> (Optimal)<br>Power: %{x:.1f} GW<br>Energy: %{y:.0f} GWh<extra></extra>'
    ), row=3, col=1)
    
    # 6. Cost breakdown
    # Original cost breakdown
    for _, row in original_df.iterrows():
        tech = row['technology']
        fig.add_trace(go.Bar(
            name=f"{tech} Cost (Original)",
            x=['Original PyPSA'],
            y=[row['cost_billion_eur']],
            marker_color=colors.get(tech, '#808080'),
            showlegend=True,
            legendgroup='cost_breakdown',
            hovertemplate=f'<b>{tech}</b><br>Cost: €%{{y:.1f}} billion<extra></extra>'
        ), row=3, col=2)
    
    # Optimal cost breakdown
    for _, row in optimal_df.iterrows():
        tech = row['technology']
        fig.add_trace(go.Bar(
            name=f"{tech} Cost (Optimal)",
            x=['Optimal System'],
            y=[row['cost_billion_eur']],
            marker_color=colors.get(tech, '#808080'),
            showlegend=True,
            legendgroup='cost_breakdown',
            hovertemplate=f'<b>{tech}</b><br>Cost: €%{{y:.1f}} billion<extra></extra>'
        ), row=3, col=2)
    
    # Update layout
    fig.update_layout(
        height=1200,
        title=dict(
            text='<b>PyPSA Optimization: Original vs Realistic Hydrogen Costs</b><br><sub>Impact of Cost Assumptions on Optimal Energy Storage Technology Mix</sub>',
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
            font=dict(size=9)
        ),
        barmode='stack'
    )
    
    # Update subplot properties
    fig.update_xaxes(title_text="System Configuration", row=1, col=1)
    fig.update_yaxes(title_text="Energy Capacity (GWh)", row=1, col=1)
    
    fig.update_xaxes(title_text="System Configuration", row=1, col=2)
    fig.update_yaxes(title_text="Energy Capacity (GWh)", row=1, col=2)
    
    fig.update_xaxes(title_text="Cost Category", row=2, col=1)
    fig.update_yaxes(title_text="Cost (Billion EUR)", row=2, col=1)
    
    fig.update_xaxes(title_text="Storage Technology", row=2, col=2)
    fig.update_yaxes(title_text="Change in Deployment (%)", row=2, col=2)
    
    fig.update_xaxes(title_text="Power Capacity (GW)", row=3, col=1)
    fig.update_yaxes(title_text="Energy Capacity (GWh)", row=3, col=1)
    
    fig.update_xaxes(title_text="System Configuration", row=3, col=2)
    fig.update_yaxes(title_text="Cost (Billion EUR)", row=3, col=2)
    
    return fig, original_df, optimal_df

def main():
    """Main function to create and save the comparison dashboard"""
    
    print("🚀 Creating Realistic Hydrogen Cost Comparison Dashboard...")
    print("=" * 60)
    
    # Create the comprehensive dashboard
    dashboard_fig, original_df, optimal_df = create_comprehensive_dashboard()
    
    # Save main dashboard
    output_file = 'realistic_h2_comparison_dashboard.html'
    dashboard_fig.write_html(
        output_file,
        include_plotlyjs='cdn',
        div_id="comparison_dashboard",
        config={
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
            'displaylogo': False
        }
    )
    
    print(f"✅ Main dashboard saved as '{output_file}'")
    
    # Create additional individual charts
    print("\n🔄 Creating individual comparison charts...")
    
    colors = create_technology_colors()
    
    individual_charts = {
        'energy_capacity_comparison': create_energy_capacity_comparison(original_df, optimal_df, colors),
        'technology_breakdown': create_technology_breakdown_comparison(original_df, optimal_df, colors),
        'cost_comparison': create_cost_comparison(original_df, optimal_df),
        'technology_shifts': create_technology_shift_analysis(original_df, optimal_df),
        'power_vs_energy': create_power_vs_energy_analysis(original_df, optimal_df),
        'cost_breakdown': create_cost_breakdown_comparison(original_df, optimal_df, colors),
        'summary_metrics': create_summary_metrics_table(original_df, optimal_df)
    }
    
    for name, fig in individual_charts.items():
        filename = f'h2_comparison_{name}.html'
        fig.write_html(filename, include_plotlyjs='cdn')
        print(f"   ✓ Saved {filename}")
    
    # Print summary insights
    original_cost = original_df['cost_billion_eur'].sum()
    optimal_cost = optimal_df['cost_billion_eur'].sum()
    savings = original_cost - optimal_cost
    savings_pct = (savings / original_cost) * 100
    
    h2_original_share = original_df[original_df['technology'] == 'H2 Storage']['share_energy'].values[0]
    h2_optimal_share = optimal_df[optimal_df['technology'] == 'H2 Storage']['share_energy'].values[0]
    
    print(f"\n📊 Dashboard Analysis Summary:")
    print(f"   • Total system cost savings: €{savings:.1f} billion ({savings_pct:.1f}%)")
    print(f"   • H2 storage reduced from {h2_original_share:.1f}% to {h2_optimal_share:.1f}% of energy")
    print(f"   • Iron-Air batteries become dominant: 63.4% of total energy capacity")
    print(f"   • Li-ion batteries expand 5x: from 414 GWh to 2,000 GWh")
    print(f"   • System becomes more diverse and less dependent on hydrogen")
    print(f"   • Higher power capacity (732 GW vs 128 GW) enables more flexible operation")
    
    print(f"\n📝 Key Findings:")
    print(f"   • Realistic H2 costs fundamentally change optimal technology mix")
    print(f"   • Iron-Air batteries emerge as cost-effective long-duration storage")
    print(f"   • Hydrogen relegated to niche role for extreme seasonal storage")
    print(f"   • More diverse portfolio reduces technology and investment risks")
    print(f"   • Earlier deployment possible with commercial technologies")
    
    print("=" * 60)
    print(f"🌐 Open '{output_file}' in your web browser to view the interactive dashboard!")
    
    print("\n🎉 All comparison visualizations created successfully!")

if __name__ == "__main__":
    main()
