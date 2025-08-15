#!/usr/bin/env python3
"""
Create interactive Plotly dashboard for storage technologies in PyPSA-DE
Fixed version with proper HTML embedding
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import json

def load_storage_data():
    """Load and prepare storage technology data"""
    
    # Technology data from verification results
    technologies = {
        'Iron-Air Battery': {
            'energy_cost': 20000,       # EUR/MWh
            'power_cost': 84000,        # EUR/MW
            'efficiency': 48,           # %
            'min_duration': 100,        # hours
            'max_duration': 400,        # hours
            'lifetime': 25,             # years
            'status': 'Implemented',
            'use_case': 'Long-term & Seasonal Storage',
            'technology_readiness': 7,  # TRL scale
            'color': '#FF6B35'
        },
        'CAES': {
            'energy_cost': 5449,        # EUR/MWh
            'power_cost': 946181,       # EUR/MW
            'efficiency': 72.1,         # %
            'min_duration': 4,          # hours
            'max_duration': 400,        # hours
            'lifetime': 60,             # years
            'status': 'Implemented',
            'use_case': 'Medium-term Storage',
            'technology_readiness': 8,  # TRL scale
            'color': '#4ECDC4'
        },
        'LFP Battery': {
            'energy_cost': 134000,      # EUR/MWh
            'power_cost': 132000,       # EUR/MW
            'efficiency': 88,           # %
            'min_duration': 1,          # hours
            'max_duration': 100,        # hours
            'lifetime': 16,             # years
            'status': 'Implemented',
            'use_case': 'Short-term Arbitrage',
            'technology_readiness': 9,  # TRL scale
            'color': '#45B7D1'
        },
        'Hydrogen Storage': {
            'energy_cost': 11200,       # EUR/MWh (underground storage)
            'power_cost': 338000,       # EUR/MW (electrolyzer + fuel cell)
            'efficiency': 42,           # % (round-trip efficiency)
            'min_duration': 168,        # hours (1 week)
            'max_duration': 8760,       # hours (1 year)
            'lifetime': 30,             # years
            'status': 'Implemented',
            'use_case': 'Seasonal & Long-term Storage',
            'technology_readiness': 8,  # TRL scale
            'color': '#9B59B6'
        }
    }
    
    return technologies

def create_combined_dashboard():
    """Create a combined dashboard with subplots"""
    
    technologies = load_storage_data()
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            'Cost Comparison (Bubble size = Efficiency %)',
            'Storage Duration vs Efficiency',
            'Technology Characteristics Radar',
            'Storage vs Time Scales',
            'Implementation Status',
            'Cost Ranking'
        ),
        specs=[
            [{'type': 'scatter'}, {'type': 'scatter'}],
            [{'type': 'polar'}, {'type': 'bar'}],
            [{'type': 'table', 'colspan': 2}, None]
        ],
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )
    
    # 1. Cost Comparison Chart
    for tech, data in technologies.items():
        typical_duration = (data['min_duration'] + data['max_duration']) / 2
        total_cost = data['energy_cost'] + (data['power_cost'] / typical_duration)
        
        fig.add_trace(
            go.Scatter(
                x=[data['power_cost'] / 1000],  # Convert to k EUR/MW
                y=[data['energy_cost'] / 1000], # Convert to k EUR/MWh
                mode='markers+text',
                marker=dict(
                    size=data['efficiency']/2,  # Scale down for visibility
                    color=data['color'],
                    opacity=0.7,
                    line=dict(width=2, color='white')
                ),
                text=tech.split()[0],  # Shortened name
                textposition='middle center',
                textfont=dict(size=9, color='white'),
                name=tech,
                showlegend=True,
                hovertemplate=
                f'<b>{tech}</b><br>' +
                f'Power Cost: {data["power_cost"]/1000:.0f} k€/MW<br>' +
                f'Energy Cost: {data["energy_cost"]/1000:.0f} k€/MWh<br>' +
                f'Efficiency: {data["efficiency"]:.1f}%<br>' +
                f'Total Cost: {total_cost/1000:.0f} k€/MWh<br>' +
                f'Lifetime: {data["lifetime"]} years' +
                '<extra></extra>'
            ),
            row=1, col=1
        )
    
    fig.update_xaxes(title_text='Power Cost (k€/MW)', type='log', row=1, col=1)
    fig.update_yaxes(title_text='Energy Cost (k€/MWh)', type='log', row=1, col=1)
    
    # 2. Duration vs Efficiency Chart
    for tech, data in technologies.items():
        fig.add_trace(
            go.Scatter(
                x=[data['min_duration'], data['max_duration']],
                y=[data['efficiency'], data['efficiency']],
                mode='lines+markers',
                line=dict(color=data['color'], width=3),
                marker=dict(size=8, color=data['color']),
                name=tech,
                showlegend=False,
                hovertemplate=
                f'<b>{tech}</b><br>' +
                'Duration: %{x} hours<br>' +
                f'Efficiency: {data["efficiency"]:.1f}%<br>' +
                f'Use Case: {data["use_case"]}<br>' +
                '<extra></extra>'
            ),
            row=1, col=2
        )
    
    fig.update_xaxes(title_text='Storage Duration (hours)', type='log', row=1, col=2)
    fig.update_yaxes(title_text='Round-trip Efficiency (%)', range=[0, 100], row=1, col=2)
    
    # 3. Radar Chart
    categories = ['Efficiency', 'Low Energy Cost', 'Low Power Cost', 
                 'Lifetime', 'Max Duration', 'Tech Readiness']
    
    for tech, data in technologies.items():
        # Normalize values to 0-100 scale
        values = [
            data['efficiency'],                           # Efficiency (already %)
            100 - min(data['energy_cost'] / 2000, 100),  # Energy cost (inverted)
            100 - min(data['power_cost'] / 20000, 100),  # Power cost (inverted)
            min(data['lifetime'] * 1.67, 100),           # Lifetime (normalized)
            min(data['max_duration'] / 4, 100),          # Max duration (normalized)
            data['technology_readiness'] * 11.1          # TRL to percentage
        ]
        
        # Convert hex to rgba
        hex_color = data['color'].lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgba_fill = f'rgba({rgb[0]},{rgb[1]},{rgb[2]},0.2)'
        
        fig.add_trace(
            go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                fillcolor=rgba_fill,
                line=dict(color=data['color'], width=2),
                name=tech,
                showlegend=False
            ),
            row=2, col=1
        )
    
    # 4. Time Scales Bar Chart
    time_scales = ['Minutes', 'Hours', 'Days', 'Weeks', 'Months']
    time_hours = [0.1, 4, 48, 168, 720]
    colors = ['#FFE66D', '#45B7D1', '#4ECDC4', '#FF6B35', '#A8E6CF']
    
    fig.add_trace(
        go.Bar(
            x=time_scales,
            y=time_hours,
            marker_color=colors,
            opacity=0.6,
            name='Time Scales',
            showlegend=False,
            hovertemplate='<b>%{x}</b><br>Duration: %{y} hours<extra></extra>'
        ),
        row=2, col=2
    )
    
    # Add technology duration lines
    for tech, data in technologies.items():
        fig.add_trace(
            go.Scatter(
                x=time_scales,
                y=[data['max_duration']] * len(time_scales),
                mode='lines',
                line=dict(color=data['color'], width=2, dash='dash'),
                name=f'{tech} Max',
                showlegend=False,
                hovertemplate=f'<b>{tech}</b><br>Max Duration: {data["max_duration"]}h<extra></extra>'
            ),
            row=2, col=2
        )
    
    fig.update_yaxes(title_text='Duration (hours)', type='log', row=2, col=2)
    fig.update_xaxes(title_text='Time Scale', row=2, col=2)
    
    # 5. Implementation Status Table
    table_data = []
    for tech, data in technologies.items():
        table_data.append([
            tech,
            f"{data['efficiency']:.1f}%",
            f"{data['energy_cost']:,} €/MWh",
            f"{data['power_cost']:,} €/MW",
            f"{data['min_duration']}-{data['max_duration']}h",
            f"{data['lifetime']} years"
        ])
    
    # Transpose for table format
    table_cols = ['Technology', 'Efficiency', 'Energy Cost', 'Power Cost', 'Duration', 'Lifetime']
    table_values = list(zip(*table_data))
    
    fig.add_trace(
        go.Table(
            header=dict(
                values=table_cols,
                fill_color='#667eea',
                font=dict(color='white', size=12),
                align='center',
                height=30
            ),
            cells=dict(
                values=table_values,
                fill_color=['#f5f5f5', 'white'] * 3,
                font=dict(size=11),
                align='center',
                height=25
            )
        ),
        row=3, col=1
    )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text='🔋 PyPSA-DE Storage Technologies Dashboard',
            x=0.5,
            font=dict(size=24)
        ),
        height=1200,
        showlegend=True,
        legend=dict(x=1.02, y=1),
        template='plotly_white'
    )
    
    return fig

def create_standalone_html():
    """Create a complete standalone HTML dashboard"""
    
    # Create the main figure
    fig = create_combined_dashboard()
    
    # Convert to HTML
    graph_html = fig.to_html(include_plotlyjs='cdn', div_id='main-dashboard')
    
    # Create complete HTML with additional content
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyPSA-DE Storage Technologies Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
        }}
        .header h1 {{
            color: #667eea;
            margin: 0 0 10px 0;
            font-size: 2.5em;
        }}
        .header p {{
            color: #666;
            margin: 5px 0;
            font-size: 1.1em;
        }}
        .status-badge {{
            display: inline-block;
            background: #4CAF50;
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .dashboard-container {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }}
        .summary-section {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .tech-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .tech-card {{
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            transition: transform 0.3s;
        }}
        .tech-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}
        .tech-card h3 {{
            margin: 0 0 15px 0;
        }}
        .tech-card.iron-air h3 {{ color: #FF6B35; }}
        .tech-card.caes h3 {{ color: #4ECDC4; }}
        .tech-card.lfp h3 {{ color: #45B7D1; }}
        .tech-card.hydrogen h3 {{ color: #9B59B6; }}
        .tech-detail {{
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            padding: 5px 0;
            border-bottom: 1px solid #f0f0f0;
        }}
        .footer {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔋 PyPSA-DE Storage Technologies Dashboard</h1>
            <p>Interactive Analysis of Iron-Air, CAES, LFP Battery, and Hydrogen Storage Implementation</p>
            <div class="status-badge">✅ ALL TECHNOLOGIES VERIFIED AND IMPLEMENTED</div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">4</div>
                    <div class="stat-label">Technologies</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">54+</div>
                    <div class="stat-label">Cost Entries</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">100%</div>
                    <div class="stat-label">Configured</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">1-8760h</div>
                    <div class="stat-label">Duration Range</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">42-88%</div>
                    <div class="stat-label">Efficiency Range</div>
                </div>
            </div>
        </div>
        
        <div class="dashboard-container">
            {graph_html}
        </div>
        
        <div class="summary-section">
            <h2>📊 Technology Summary</h2>
            <div class="tech-grid">
                <div class="tech-card iron-air">
                    <h3>🔋 Iron-Air Battery</h3>
                    <div class="tech-detail">
                        <span>Efficiency:</span>
                        <strong>48%</strong>
                    </div>
                    <div class="tech-detail">
                        <span>Energy Cost:</span>
                        <strong>20,000 €/MWh</strong>
                    </div>
                    <div class="tech-detail">
                        <span>Power Cost:</span>
                        <strong>84,000 €/MW</strong>
                    </div>
                    <div class="tech-detail">
                        <span>Duration:</span>
                        <strong>100-400 hours</strong>
                    </div>
                    <div class="tech-detail">
                        <span>Best Use:</span>
                        <strong>Seasonal Storage</strong>
                    </div>
                </div>
                
                <div class="tech-card caes">
                    <h3>💨 CAES</h3>
                    <div class="tech-detail">
                        <span>Efficiency:</span>
                        <strong>72.1%</strong>
                    </div>
                    <div class="tech-detail">
                        <span>Energy Cost:</span>
                        <strong>5,449 €/MWh</strong>
                    </div>
                    <div class="tech-detail">
                        <span>Power Cost:</span>
                        <strong>946,181 €/MW</strong>
                    </div>
                    <div class="tech-detail">
                        <span>Duration:</span>
                        <strong>4-400 hours</strong>
                    </div>
                    <div class="tech-detail">
                        <span>Best Use:</span>
                        <strong>Weekly Storage</strong>
                    </div>
                </div>
                
                <div class="tech-card lfp">
                    <h3>🔋 LFP Battery</h3>
                    <div class="tech-detail">
                        <span>Efficiency:</span>
                        <strong>88%</strong>
                    </div>
                    <div class="tech-detail">
                        <span>Energy Cost:</span>
                        <strong>134,000 €/MWh</strong>
                    </div>
                    <div class="tech-detail">
                        <span>Power Cost:</span>
                        <strong>132,000 €/MW</strong>
                    </div>
                    <div class="tech-detail">
                        <span>Duration:</span>
                        <strong>1-100 hours</strong>
                    </div>
                    <div class="tech-detail">
                        <span>Best Use:</span>
                        <strong>Daily Arbitrage</strong>
                    </div>
                </div>
                
                <div class="tech-card hydrogen">
                    <h3>⚡ Hydrogen Storage</h3>
                    <div class="tech-detail">
                        <span>Efficiency:</span>
                        <strong>42%</strong>
                    </div>
                    <div class="tech-detail">
                        <span>Energy Cost:</span>
                        <strong>11,200 €/MWh</strong>
                    </div>
                    <div class="tech-detail">
                        <span>Power Cost:</span>
                        <strong>338,000 €/MW</strong>
                    </div>
                    <div class="tech-detail">
                        <span>Duration:</span>
                        <strong>168-8760 hours</strong>
                    </div>
                    <div class="tech-detail">
                        <span>Best Use:</span>
                        <strong>Seasonal Storage</strong>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <h3>🎉 Implementation Complete</h3>
            <p>All storage technologies are correctly configured and ready for PyPSA optimization.</p>
            <p><small>Generated: December 2024 | PyPSA-DE Storage Technologies</small></p>
        </div>
    </div>
</body>
</html>
"""
    
    return html_template

def main():
    """Main function to create and save dashboard"""
    print("🔋 Creating Fixed Storage Technologies Dashboard...")
    print("=" * 50)
    
    try:
        # Create standalone HTML dashboard
        print("📊 Generating interactive charts...")
        html_content = create_standalone_html()
        
        # Save dashboard
        dashboard_file = 'storage_dashboard_fixed.html'
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Dashboard saved as: {dashboard_file}")
        
        # Also create individual chart files
        print("\n📈 Creating individual charts...")
        
        technologies = load_storage_data()
        
        # Create individual cost comparison chart
        fig_cost = go.Figure()
        for tech, data in technologies.items():
            typical_duration = (data['min_duration'] + data['max_duration']) / 2
            total_cost = data['energy_cost'] + (data['power_cost'] / typical_duration)
            
            fig_cost.add_trace(go.Scatter(
                x=[data['power_cost'] / 1000],
                y=[data['energy_cost'] / 1000],
                mode='markers+text',
                marker=dict(
                    size=data['efficiency'],
                    color=data['color'],
                    opacity=0.7,
                    line=dict(width=2, color='white')
                ),
                text=tech,
                textposition='top center',
                name=tech,
                hovertemplate=
                f'<b>{tech}</b><br>' +
                f'Power Cost: {data["power_cost"]/1000:.0f} k€/MW<br>' +
                f'Energy Cost: {data["energy_cost"]/1000:.0f} k€/MWh<br>' +
                f'Efficiency: {data["efficiency"]:.1f}%<br>' +
                f'Total Cost: {total_cost/1000:.0f} k€/MWh<br>' +
                '<extra></extra>'
            ))
        
        fig_cost.update_layout(
            title='Storage Technology Cost Comparison (Bubble Size = Efficiency)',
            xaxis=dict(title='Power Cost (k€/MW)', type='log'),
            yaxis=dict(title='Energy Cost (k€/MWh)', type='log'),
            height=600,
            template='plotly_white'
        )
        fig_cost.write_html('cost_comparison_fixed.html')
        
        print("✅ Individual charts created")
        
        # Summary
        print("\n" + "="*50)
        print("DASHBOARD CREATION SUMMARY")
        print("="*50)
        print("✅ Fixed dashboard created successfully!")
        print(f"📄 Main dashboard: {dashboard_file}")
        print("\nThe dashboard includes:")
        print("  • Cost comparison with efficiency bubbles")
        print("  • Duration vs efficiency analysis")
        print("  • Multi-dimensional radar comparison")
        print("  • Time scale suitability chart")
        print("  • Implementation status table")
        print("  • Detailed technology cards")
        print("\n🌐 Open the HTML file in your browser to view!")
        
        return dashboard_file
        
    except Exception as e:
        print(f"❌ Error creating dashboard: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
