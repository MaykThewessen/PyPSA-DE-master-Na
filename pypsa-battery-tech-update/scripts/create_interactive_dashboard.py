#!/usr/bin/env python3
"""
Interactive PyPSA Dashboard Generator
=====================================

Creates an interactive Plotly HTML dashboard with:
1. Installed Technology Capacity by Scenario (Bar Chart)
2. Energy Storage Capacity by Technology (Bar Chart) 
3. System Costs vs CO2 Emissions Intensity (Scatter Plot)

Usage: python scripts/create_interactive_dashboard.py
"""

import pypsa
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_scenario_networks():
    """Load all three scenario networks."""
    
    logger.info("Loading scenario networks...")
    
    # Check for network files
    if os.path.exists('data/networks'):
        base_path = 'data/networks'
    else:
        base_path = 'results/de-all-tech-2035-mayk/networks'
    
    networks = {}
    network_files = {
        '250Mt CO₂': f'{base_path}/250Mt_CO2_Limit_solved_network.nc',
        '300Mt CO₂': f'{base_path}/300Mt_CO2_Limit_solved_network.nc', 
        '500Mt CO₂': f'{base_path}/500Mt_CO2_Limit_solved_network.nc'
    }
    
    for scenario, file_path in network_files.items():
        if os.path.exists(file_path):
            try:
                networks[scenario] = pypsa.Network(file_path)
                logger.info(f"✅ Loaded {scenario}")
            except Exception as e:
                logger.error(f"❌ Failed to load {scenario}: {e}")
        else:
            # Try alternative naming
            alt_files = {
                '250Mt CO₂': f'{base_path}/base_s_1_elec_solved_scenario1_250co2.nc',
                '300Mt CO₂': f'{base_path}/base_s_1_elec_solved_scenario2_300co2.nc',
                '500Mt CO₂': f'{base_path}/base_s_1_elec_solved_scenario3_500co2.nc'
            }
            alt_path = alt_files.get(scenario)
            if alt_path and os.path.exists(alt_path):
                try:
                    networks[scenario] = pypsa.Network(alt_path)
                    logger.info(f"✅ Loaded {scenario} (alternative path)")
                except Exception as e:
                    logger.error(f"❌ Failed to load {scenario}: {e}")
            else:
                logger.warning(f"⚠️  {scenario} network file not found")
    
    return networks

def get_installed_capacity_data(networks):
    """Extract installed capacity data for all technologies across scenarios."""
    
    capacity_data = []
    
    for scenario, network in networks.items():
        # Generators
        if len(network.generators) > 0:
            gen_capacity = network.generators.groupby('carrier')['p_nom_opt'].sum()
            for carrier, capacity in gen_capacity.items():
                if capacity > 0:
                    capacity_data.append({
                        'Scenario': scenario,
                        'Technology': carrier,
                        'Type': 'Generation',
                        'Capacity_GW': capacity / 1000  # Convert MW to GW
                    })
        
        # Storage Units
        if len(network.storage_units) > 0:
            storage_capacity = network.storage_units.groupby('carrier')['p_nom_opt'].sum()
            for carrier, capacity in storage_capacity.items():
                if capacity > 0:
                    capacity_data.append({
                        'Scenario': scenario,
                        'Technology': carrier,
                        'Type': 'Storage Power',
                        'Capacity_GW': capacity / 1000  # Convert MW to GW
                    })
        
        # Links (for batteries and other storage)
        if len(network.links) > 0:
            # Group links by carrier for charging/discharging capacity
            link_capacity = network.links.groupby('carrier')['p_nom_opt'].sum()
            for carrier, capacity in link_capacity.items():
                if capacity > 0 and 'battery' in carrier.lower():
                    capacity_data.append({
                        'Scenario': scenario,
                        'Technology': carrier.replace(' charger', '').replace(' discharger', ''),
                        'Type': 'Battery Power',
                        'Capacity_GW': capacity / 1000  # Convert MW to GW
                    })
    
    return pd.DataFrame(capacity_data)

def get_storage_energy_data(networks):
    """Extract energy storage capacity data for all storage technologies."""
    
    storage_data = []
    
    for scenario, network in networks.items():
        # Storage Units (energy capacity)
        if len(network.storage_units) > 0:
            storage_units = network.storage_units
            # Check for different possible column names
            energy_col = 'e_nom_opt' if 'e_nom_opt' in storage_units.columns else 'e_nom'
            power_col = 'p_nom_opt' if 'p_nom_opt' in storage_units.columns else 'p_nom'
            
            for idx, storage in storage_units.iterrows():
                energy_capacity = storage.get(energy_col, 0)
                power_capacity = storage.get(power_col, 0)
                
                if energy_capacity > 0:
                    storage_data.append({
                        'Scenario': scenario,
                        'Technology': storage['carrier'],
                        'Energy_Capacity_GWh': energy_capacity / 1000,  # Convert MWh to GWh
                        'Power_Capacity_GW': power_capacity / 1000       # Convert MW to GW
                    })
        
        # Stores (energy capacity)
        if len(network.stores) > 0:
            stores = network.stores
            # Check for different possible column names
            energy_col = 'e_nom_opt' if 'e_nom_opt' in stores.columns else 'e_nom'
            
            for idx, store in stores.iterrows():
                energy_capacity = store.get(energy_col, 0)
                
                if energy_capacity > 0:
                    storage_data.append({
                        'Scenario': scenario,
                        'Technology': store['carrier'],
                        'Energy_Capacity_GWh': energy_capacity / 1000,  # Convert MWh to GWh
                        'Power_Capacity_GW': 0  # Stores don't have power capacity
                    })
        
        # Battery links (estimate energy from power assuming 4h duration for now)
        if len(network.links) > 0:
            battery_links = network.links[network.links['carrier'].str.contains('battery', case=False, na=False)]
            for idx, link in battery_links.iterrows():
                if link['p_nom_opt'] > 0 and 'charger' in link['carrier']:
                    # Estimate energy capacity assuming typical duration
                    duration_h = 4  # Typical battery duration
                    storage_data.append({
                        'Scenario': scenario,
                        'Technology': 'battery',
                        'Energy_Capacity_GWh': (link['p_nom_opt'] * duration_h) / 1000,  # Convert MWh to GWh
                        'Power_Capacity_GW': link['p_nom_opt'] / 1000
                    })
    
    return pd.DataFrame(storage_data)

def get_system_metrics_data(networks):
    """Extract system-level metrics for cost and emissions analysis."""
    
    metrics_data = []
    
    # CO2 prices for each scenario (€/tCO2)
    co2_prices = {
        '250Mt CO₂': 250,
        '300Mt CO₂': 300,
        '500Mt CO₂': 500
    }
    
    for scenario, network in networks.items():
        metrics = {}
        metrics['Scenario'] = scenario
        
        # System cost
        if network.objective is not None:
            metrics['System_Cost_Billion_EUR'] = network.objective / 1e9
        else:
            metrics['System_Cost_Billion_EUR'] = 0
        
        # CO2 price for this scenario
        metrics['CO2_Price_EUR_per_tCO2'] = co2_prices.get(scenario, 0)
        
        # Total generation and CO2 emissions
        if hasattr(network, 'generators_t') and hasattr(network.generators_t, 'p'):
            gen_by_carrier = network.generators_t.p.sum().groupby(network.generators.carrier).sum()
            total_generation_mwh = gen_by_carrier.sum()
            
            # CO2 emissions calculation
            co2_factors = {
                'coal': 0.820,     # tCO2/MWh
                'lignite': 0.986,  # tCO2/MWh
                'CCGT': 0.350,     # tCO2/MWh
                'OCGT': 0.400,     # tCO2/MWh
                'oil': 0.650       # tCO2/MWh
            }
            
            total_co2_tons = 0
            for carrier, co2_factor in co2_factors.items():
                if carrier in gen_by_carrier.index:
                    total_co2_tons += gen_by_carrier[carrier] * co2_factor
            
            # CO2 intensity in gCO2/kWh
            if total_generation_mwh > 0:
                metrics['CO2_Intensity_gCO2_per_kWh'] = (total_co2_tons * 1000 * 1000) / (total_generation_mwh * 1000)  # Convert to g/kWh
            else:
                metrics['CO2_Intensity_gCO2_per_kWh'] = 0
            
            metrics['Total_Generation_TWh'] = total_generation_mwh / 1e6  # Convert to TWh
            metrics['Total_CO2_Mt'] = total_co2_tons / 1e6  # Convert to Mt
        else:
            metrics['CO2_Intensity_gCO2_per_kWh'] = 0
            metrics['Total_Generation_TWh'] = 0
            metrics['Total_CO2_Mt'] = 0
        
        metrics_data.append(metrics)
    
    return pd.DataFrame(metrics_data)

def create_installed_capacity_chart(capacity_df):
    """Create interactive bar chart for installed capacity by technology and scenario."""
    
    # Aggregate capacity by scenario and technology
    agg_df = capacity_df.groupby(['Scenario', 'Technology'])['Capacity_GW'].sum().reset_index()
    
    # Create bar chart
    fig = go.Figure()
    
    scenarios = agg_df['Scenario'].unique()
    technologies = agg_df['Technology'].unique()
    
    # Color palette for technologies
    colors = px.colors.qualitative.Set3
    
    for i, tech in enumerate(technologies):
        tech_data = agg_df[agg_df['Technology'] == tech]
        fig.add_trace(go.Bar(
            name=tech,
            x=tech_data['Scenario'],
            y=tech_data['Capacity_GW'],
            marker_color=colors[i % len(colors)],
            hovertemplate=f'<b>{tech}</b><br>' +
                         'Scenario: %{x}<br>' +
                         'Capacity: %{y:.1f} GW<br>' +
                         '<extra></extra>'
        ))
    
    fig.update_layout(
        title={
            'text': 'Installed Technology Capacity by Scenario',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title='Scenario',
        yaxis_title='Installed Capacity (GW)',
        barmode='group',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500
    )
    
    return fig

def create_storage_capacity_chart(storage_df):
    """Create interactive bar chart for energy storage capacity by technology."""
    
    # Filter out technologies with zero capacity
    storage_nonzero = storage_df[storage_df['Energy_Capacity_GWh'] > 0]
    
    if storage_nonzero.empty:
        # Create empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No storage technologies with capacity > 0 found",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        fig.update_layout(title="Energy Storage Capacity by Technology", height=400)
        return fig
    
    # Group by scenario and technology
    agg_storage = storage_nonzero.groupby(['Scenario', 'Technology'])['Energy_Capacity_GWh'].sum().reset_index()
    
    fig = go.Figure()
    
    scenarios = agg_storage['Scenario'].unique()
    technologies = agg_storage['Technology'].unique()
    
    # Color palette for storage technologies
    storage_colors = {
        'battery': '#FF6B35',
        'H2': '#34A0A4',
        'PHS': '#1A759F',
        'Compressed-Air': '#168AAD',
        'iron-air battery': '#FF6B35',
        'Lithium-Ion-LFP': '#004E89'
    }
    
    for tech in technologies:
        tech_data = agg_storage[agg_storage['Technology'] == tech]
        color = storage_colors.get(tech, '#7570b3')
        
        fig.add_trace(go.Bar(
            name=tech,
            x=tech_data['Scenario'],
            y=tech_data['Energy_Capacity_GWh'],
            marker_color=color,
            hovertemplate=f'<b>{tech}</b><br>' +
                         'Scenario: %{x}<br>' +
                         'Energy Capacity: %{y:.1f} GWh<br>' +
                         '<extra></extra>'
        ))
    
    fig.update_layout(
        title={
            'text': 'Energy Storage Capacity by Technology (Capacity > 0)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title='Scenario',
        yaxis_title='Energy Storage Capacity (GWh)',
        barmode='group',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500
    )
    
    return fig

def create_system_costs_co2price_chart(metrics_df):
    """Create scatter plot for system costs vs CO2 price."""
    
    fig = go.Figure()
    
    # Create scatter plot
    fig.add_trace(go.Scatter(
        x=metrics_df['System_Cost_Billion_EUR'],
        y=metrics_df['CO2_Price_EUR_per_tCO2'],
        mode='markers+text',
        text=metrics_df['Scenario'],
        textposition="top center",
        textfont=dict(size=12, color='black'),
        marker=dict(
            size=15,
            color=['#FF6B35', '#1A759F', '#34A0A4'],
            opacity=0.8,
            line=dict(width=2, color='DarkSlateGrey')
        ),
        hovertemplate='<b>%{text}</b><br>' +
                     'System Cost: %{x:.1f} Billion EUR<br>' +
                     'CO₂ Price: %{y:.0f} €/tCO₂<br>' +
                     '<extra></extra>',
        name='Scenarios'
    ))
    
    fig.update_layout(
        title={
            'text': 'System Costs vs CO₂ Price',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title='System Cost (Billion EUR)',
        yaxis_title='CO₂ Price (€/tCO₂)',
        hovermode='closest',
        height=500,
        showlegend=False
    )
    
    # Add trend line if more than 2 points
    if len(metrics_df) >= 2:
        # Simple linear trend
        from sklearn.linear_model import LinearRegression
        import numpy as np
        
        X = metrics_df['System_Cost_Billion_EUR'].values.reshape(-1, 1)
        y = metrics_df['CO2_Price_EUR_per_tCO2'].values
        
        try:
            model = LinearRegression().fit(X, y)
            x_trend = np.linspace(X.min(), X.max(), 100)
            y_trend = model.predict(x_trend.reshape(-1, 1))
            
            fig.add_trace(go.Scatter(
                x=x_trend.flatten(),
                y=y_trend,
                mode='lines',
                name='Trend',
                line=dict(color='red', width=2, dash='dash'),
                hovertemplate='Trend Line<extra></extra>'
            ))
        except:
            logger.info("Could not add trend line (sklearn not available)")
    
    return fig

def create_dashboard_html(networks):
    """Create complete interactive dashboard HTML file."""
    
    logger.info("Extracting data for dashboard...")
    
    # Extract data
    capacity_df = get_installed_capacity_data(networks)
    storage_df = get_storage_energy_data(networks)
    metrics_df = get_system_metrics_data(networks)
    
    logger.info(f"Capacity data: {len(capacity_df)} records")
    logger.info(f"Storage data: {len(storage_df)} records")  
    logger.info(f"Metrics data: {len(metrics_df)} records")
    
    # Create individual charts
    logger.info("Creating charts...")
    
    capacity_chart = create_installed_capacity_chart(capacity_df)
    storage_chart = create_storage_capacity_chart(storage_df)
    costs_co2price_chart = create_system_costs_co2price_chart(metrics_df)
    
    # Create combined dashboard using subplots
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=(
            'Installed Technology Capacity by Scenario',
            'Energy Storage Capacity by Technology (Capacity > 0)',
            'System Costs vs CO₂ Price'
        ),
        vertical_spacing=0.12,
        specs=[[{"secondary_y": False}],
               [{"secondary_y": False}],
               [{"secondary_y": False}]]
    )
    
    # Add capacity chart traces (keep legend for first subplot)
    for trace in capacity_chart.data:
        fig.add_trace(trace, row=1, col=1)
    
    # Add storage chart traces  
    for trace in storage_chart.data:
        trace.showlegend = False  # Avoid duplicate legends
        fig.add_trace(trace, row=2, col=1)
    
    # Add costs/CO2 price chart traces
    for trace in costs_co2price_chart.data:
        trace.showlegend = False  # Avoid duplicate legends
        fig.add_trace(trace, row=3, col=1)
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'PyPSA Scenario Analysis Dashboard - Battery Technology Study',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': 'darkblue'}
        },
        height=1400,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.95,  # Position within first subplot area
            xanchor="left",
            x=1.02,  # Position to the right of the first subplot
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.2)",
            borderwidth=1
        ),
        font=dict(size=11)
    )
    
    # Update axes labels
    fig.update_xaxes(title_text="Scenario", row=1, col=1)
    fig.update_yaxes(title_text="Capacity (GW)", row=1, col=1)
    
    fig.update_xaxes(title_text="Scenario", row=2, col=1)
    fig.update_yaxes(title_text="Energy Capacity (GWh)", row=2, col=1)
    
    fig.update_xaxes(title_text="System Cost (Billion EUR)", row=3, col=1)
    fig.update_yaxes(title_text="CO₂ Price (€/tCO₂)", row=3, col=1)
    
    return fig

def main():
    """Main function to create interactive dashboard."""
    
    logger.info("🚀 Starting PyPSA Interactive Dashboard Creation...")
    logger.info("=" * 60)
    
    # Load networks
    networks = load_scenario_networks()
    
    if len(networks) == 0:
        logger.error("❌ No networks loaded. Please check network file paths.")
        return
    
    logger.info(f"✅ Loaded {len(networks)} scenarios: {list(networks.keys())}")
    
    # Create dashboard
    logger.info("Creating interactive dashboard...")
    dashboard_fig = create_dashboard_html(networks)
    
    # Save HTML file
    output_dir = "outputs/plots"
    os.makedirs(output_dir, exist_ok=True)
    html_file = f"{output_dir}/pypsa_interactive_dashboard.html"
    
    dashboard_fig.write_html(html_file, 
                           include_plotlyjs=True,
                           config={'displayModeBar': True, 'displaylogo': False})
    
    logger.info(f"✅ Interactive dashboard saved: {html_file}")
    
    # Create summary stats
    logger.info("\n📊 Dashboard Summary:")
    logger.info("-" * 40)
    
    capacity_df = get_installed_capacity_data(networks)
    storage_df = get_storage_energy_data(networks)
    metrics_df = get_system_metrics_data(networks)
    
    logger.info(f"Scenarios analyzed: {len(networks)}")
    logger.info(f"Technologies tracked: {len(capacity_df['Technology'].unique())}")
    logger.info(f"Storage technologies: {len(storage_df['Technology'].unique())}")
    
    # Display key metrics
    logger.info("\nKey Metrics by Scenario:")
    for _, row in metrics_df.iterrows():
        logger.info(f"  {row['Scenario']}:")
        logger.info(f"    System Cost: {row['System_Cost_Billion_EUR']:.1f} B€")
        logger.info(f"    CO₂ Intensity: {row['CO2_Intensity_gCO2_per_kWh']:.1f} gCO₂/kWh")
        logger.info(f"    Total Generation: {row['Total_Generation_TWh']:.1f} TWh")
    
    logger.info(f"\n🎉 Dashboard creation completed successfully!")
    logger.info(f"📄 Open '{html_file}' in your web browser to view the interactive dashboard.")

if __name__ == "__main__":
    main()
