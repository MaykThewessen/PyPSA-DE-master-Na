#!/usr/bin/env python3
"""
PyPSA Results Comparison and Analysis Script
==========================================

This script discovers all run folders containing network.nc files,
extracts KPIs, generates comparative visualizations, and produces
summary reports.

Features:
- Automatic discovery of network files in results/, runs/, outputs/
- KPI extraction: total system cost, generation & storage capacities, 
  energy shares, storage energy & power, line expansion, capacity factors
- Comparative visualizations (bar charts, cost breakdowns, radar charts)
- Error handling with logging - continues with remaining networks if errors occur
- CSV export of summary data to reports/summary_<timestamp>.csv
- Plots saved to plots/<timestamp>_<topic>.png
- Detailed logging to logs/analysis_<timestamp>.log

Usage:
    python compare_results.py

Requirements:
    - pypsa
    - pandas
    - numpy
    - matplotlib
    - seaborn

Output files:
    - reports/summary_<timestamp>.csv: Complete KPI summary
    - plots/<timestamp>_capacity_comparison.png: Generation capacity by technology
    - plots/<timestamp>_cost_breakdown.png: Total system cost by scenario
    - plots/<timestamp>_storage_radar.png: Storage mix radar chart
    - plots/<timestamp>_residual_load.png: Hourly residual load comparison
    - logs/analysis_<timestamp>.log: Detailed execution log
"""

import os
import sys
import glob
import logging
import warnings
from datetime import datetime
from pathlib import Path
import traceback

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pypsa

warnings.filterwarnings('ignore')

# Configuration
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
PLOTS_DIR = Path("plots")
REPORTS_DIR = Path("reports") 
LOGS_DIR = Path("logs")

# Create directories if they don't exist
for directory in [PLOTS_DIR, REPORTS_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# Set up logging
log_file = LOGS_DIR / f"analysis_{TIMESTAMP}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


class NetworkAnalyzer:
    """Analyzes PyPSA networks and extracts KPIs"""
    
    def __init__(self):
        self.networks_data = {}
        self.summary_data = []
        
    def discover_networks(self, base_dirs=None):
        """Discover all network.nc files in the specified directories"""
        if base_dirs is None:
            base_dirs = ["results", "runs", "outputs"]
        
        network_files = []
        
        for base_dir in base_dirs:
            if os.path.exists(base_dir):
                logger.info(f"Searching for network files in: {base_dir}")
                
                # Search for network.nc files specifically in networks subdirectories
                # and other common PyPSA output patterns
                patterns = [
                    os.path.join(base_dir, "**", "network.nc"),
                    os.path.join(base_dir, "networks", "*.nc"),
                    os.path.join(base_dir, "**", "networks", "*.nc"),
                    os.path.join(base_dir, "**", "*elec*.nc"),
                    os.path.join(base_dir, "**", "solved_*.nc"),
                    os.path.join(base_dir, "**", "optimized_*.nc")
                ]
                
                for pattern in patterns:
                    files = glob.glob(pattern, recursive=True)
                    for f in files:
                        # Filter out non-network files
                        filename = os.path.basename(f).lower()
                        path_lower = f.lower()
                        
                        # Skip input data files
                        if any(skip in path_lower for skip in [
                            'availability_matrix', 'profile_', 'demand', 'cop_profiles',
                            'temperature_profiles', 'heat_demand', 'solar_thermal',
                            'ptes_', 'temp_', 'pop_layout', 'cutouts', 'bundle', 'gebco'
                        ]):
                            continue
                            
                        # Include files that look like solved networks
                        if (filename.startswith('network') or 
                            'elec' in filename or
                            any(indicator in filename for indicator in ['solved', 'optimized', 'base_s'])):
                            network_files.append(f)
                        
        # Remove duplicates and sort
        network_files = sorted(list(set(network_files)))
        logger.info(f"Found {len(network_files)} potential network files")
        
        # Log found files for debugging
        for f in network_files:
            logger.debug(f"  - {f}")
        
        return network_files
    
    def load_network(self, filepath):
        """Load a PyPSA network with error handling and memory optimization"""
        try:
            logger.info(f"Loading network: {filepath}")
            network = pypsa.Network(filepath)
            logger.info(f"Successfully loaded network with {len(network.buses)} buses, "
                       f"{len(network.generators)} generators")
            return network
        except MemoryError:
            logger.warning(f"MemoryError loading {filepath}, attempting with optimized settings...")
            try:
                # Attempt to load with memory optimization
                network = self._load_network_optimized(filepath)
                if network is not None:
                    logger.info(f"Successfully loaded optimized network with {len(network.buses)} buses")
                return network
            except Exception as e:
                logger.error(f"Failed to load network even with optimization {filepath}: {str(e)}")
                return None
        except Exception as e:
            logger.error(f"Failed to load network {filepath}: {str(e)}")
            return None
    
    def _load_network_optimized(self, filepath):
        """Load network with memory optimization techniques"""
        try:
            # Load network
            network = pypsa.Network()
            network.import_from_netcdf(filepath)
            
            # Downcast numeric dtypes to save memory
            self._downcast_network_dtypes(network)
            
            return network
        except Exception as e:
            logger.error(f"Optimized loading failed: {e}")
            return None
    
    def _downcast_network_dtypes(self, network):
        """Downcast numeric dtypes in network to reduce memory usage"""
        logger.info("Downcasting network dtypes to reduce memory usage...")
        
        # Components to optimize
        components_to_optimize = [
            'buses', 'generators', 'loads', 'lines', 'links', 'transformers', 'storage_units'
        ]
        
        for component in components_to_optimize:
            if hasattr(network, component):
                df = getattr(network, component)
                if not df.empty:
                    # Downcast numeric columns
                    for col in df.columns:
                        if df[col].dtype == 'float64':
                            df[col] = pd.to_numeric(df[col], downcast='float')
                        elif df[col].dtype == 'int64':
                            df[col] = pd.to_numeric(df[col], downcast='integer')
        
        # Also downcast time series data if present
        time_series_components = [
            'generators_t', 'loads_t', 'lines_t', 'links_t', 'storage_units_t'
        ]
        
        for ts_component in time_series_components:
            if hasattr(network, ts_component):
                ts_obj = getattr(network, ts_component)
                for attr in ['p', 'q', 'p0', 'p1', 'state_of_charge']:
                    if hasattr(ts_obj, attr):
                        ts_df = getattr(ts_obj, attr)
                        if not ts_df.empty and ts_df.dtype == 'float64':
                            setattr(ts_obj, attr, pd.to_numeric(ts_df, downcast='float'))
    
    def extract_kpis(self, network, scenario_name):
        """Extract key performance indicators from a network"""
        logger.info(f"Extracting KPIs for scenario: {scenario_name}")
        
        kpis = {
            'scenario': scenario_name,
            'timestamp': datetime.now(),
            'num_buses': len(network.buses),
            'num_generators': len(network.generators),
            'num_lines': len(network.lines) if hasattr(network, 'lines') else 0,
            'num_storage': len(network.storage_units) if hasattr(network, 'storage_units') else 0,
        }
        
        try:
            # Total system cost
            kpis['total_system_cost_eur'] = network.objective if hasattr(network, 'objective') else np.nan
            kpis['total_system_cost_billion_eur'] = kpis['total_system_cost_eur'] / 1e9 if not pd.isna(kpis['total_system_cost_eur']) else np.nan
            
            # Generation capacities by carrier
            if not network.generators.empty:
                gen_capacity = network.generators.groupby('carrier')['p_nom_opt'].sum() / 1e3  # GW
                for carrier, capacity in gen_capacity.items():
                    kpis[f'gen_capacity_{carrier}_GW'] = capacity
                
                kpis['total_gen_capacity_GW'] = gen_capacity.sum()
            
            # Storage capacities
            if hasattr(network, 'storage_units') and not network.storage_units.empty:
                storage_energy = network.storage_units.groupby('carrier')['p_nom_opt'].sum() / 1e3  # GW
                storage_power = network.storage_units.groupby('carrier')['p_nom_opt'].sum() / 1e3  # GW
                
                for carrier, power in storage_power.items():
                    kpis[f'storage_power_{carrier}_GW'] = power
                    
                if hasattr(network.storage_units, 'state_of_charge_set'):
                    for carrier, energy in storage_energy.items():
                        kpis[f'storage_energy_{carrier}_GWh'] = energy
                
                kpis['total_storage_power_GW'] = storage_power.sum()
                kpis['total_storage_energy_GWh'] = storage_energy.sum()
            
            # Energy generation shares
            if hasattr(network, 'generators_t') and hasattr(network.generators_t, 'p'):
                if not network.generators_t.p.empty:
                    total_gen = network.generators_t.p.sum()
                    gen_by_carrier = total_gen.groupby(network.generators.carrier).sum()
                    total_energy = gen_by_carrier.sum()
                    
                    for carrier, energy in gen_by_carrier.items():
                        share = energy / total_energy * 100 if total_energy > 0 else 0
                        kpis[f'energy_share_{carrier}_percent'] = share
                        kpis[f'energy_generation_{carrier}_GWh'] = energy / 1e3
                    
                    kpis['total_energy_generation_GWh'] = total_energy / 1e3
            
            # Line expansion (if available)
            if hasattr(network, 'lines') and not network.lines.empty:
                if 's_nom_opt' in network.lines.columns and 's_nom' in network.lines.columns:
                    line_expansion = (network.lines['s_nom_opt'] - network.lines['s_nom']).sum()
                    kpis['line_expansion_MVA'] = line_expansion
                    kpis['line_expansion_GVA'] = line_expansion / 1e3
            
            # Capacity factors
            if (hasattr(network, 'generators_t') and hasattr(network.generators_t, 'p') 
                and not network.generators_t.p.empty and not network.generators.empty):
                
                for carrier in network.generators.carrier.unique():
                    carrier_gens = network.generators[network.generators.carrier == carrier]
                    if len(carrier_gens) > 0:
                        total_capacity = carrier_gens.p_nom_opt.sum()
                        if total_capacity > 0:
                            total_generation = network.generators_t.p[carrier_gens.index].sum().sum()
                            hours_in_period = len(network.snapshots)
                            max_possible = total_capacity * hours_in_period
                            cf = total_generation / max_possible if max_possible > 0 else 0
                            kpis[f'capacity_factor_{carrier}'] = cf
            
            logger.info(f"Extracted {len(kpis)} KPIs for {scenario_name}")
            
        except Exception as e:
            logger.error(f"Error extracting KPIs for {scenario_name}: {str(e)}")
            logger.error(traceback.format_exc())
        
        return kpis
    
    def analyze_all_networks(self):
        """Analyze all discovered networks"""
        network_files = self.discover_networks()
        
        if not network_files:
            logger.warning("No network files found!")
            return
        
        for filepath in network_files:
            # Create scenario name from filepath
            scenario_name = self._get_scenario_name(filepath)
            
            # Load network
            network = self.load_network(filepath)
            if network is None:
                continue
                
            # Extract KPIs
            kpis = self.extract_kpis(network, scenario_name)
            self.summary_data.append(kpis)
            
            # Store network data for plotting
            self.networks_data[scenario_name] = {
                'network': network,
                'filepath': filepath,
                'kpis': kpis
            }
            
            logger.info(f"Completed analysis for {scenario_name}")
    
    def _get_scenario_name(self, filepath):
        """Extract scenario name from filepath"""
        path_parts = Path(filepath).parts
        filename = Path(filepath).stem
        
        # Try to extract meaningful name
        if len(path_parts) >= 2:
            scenario = f"{path_parts[-2]}_{filename}"
        else:
            scenario = filename
            
        # Clean up scenario name
        scenario = scenario.replace('.nc', '').replace('network', '').replace('_', '-')
        return scenario or "unknown"
    
    def create_summary_dataframe(self):
        """Create summary DataFrame from all KPIs"""
        if not self.summary_data:
            logger.warning("No data available for summary")
            return pd.DataFrame()
        
        df = pd.DataFrame(self.summary_data)
        
        # Save to CSV
        csv_file = REPORTS_DIR / f"summary_{TIMESTAMP}.csv"
        df.to_csv(csv_file, index=False)
        logger.info(f"Summary data saved to: {csv_file}")
        
        return df
    
    def create_capacity_comparison(self, df):
        """Create bar chart comparing new capacity by technology"""
        logger.info("Creating capacity comparison chart")
        
        try:
            # Extract capacity columns
            capacity_cols = [col for col in df.columns if col.startswith('gen_capacity_') and col.endswith('_GW')]
            
            if not capacity_cols:
                logger.warning("No generation capacity data found")
                return
            
            # Prepare data for plotting
            capacity_data = df[['scenario'] + capacity_cols].set_index('scenario')
            capacity_data.columns = [col.replace('gen_capacity_', '').replace('_GW', '') for col in capacity_data.columns]
            
            # Create plot
            fig, ax = plt.subplots(figsize=(12, 8))
            capacity_data.plot(kind='bar', ax=ax, width=0.8)
            
            ax.set_title('Generation Capacity by Technology and Scenario', fontsize=14, fontweight='bold')
            ax.set_ylabel('Capacity (GW)', fontsize=12)
            ax.set_xlabel('Scenario', fontsize=12)
            ax.legend(title='Technology', bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.grid(True, alpha=0.3)
            
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Save plot
            plot_file = PLOTS_DIR / f"{TIMESTAMP}_capacity_comparison.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            logger.info(f"Capacity comparison saved to: {plot_file}")
            plt.close()
            
        except Exception as e:
            logger.error(f"Error creating capacity comparison: {str(e)}")
    
    def create_cost_breakdown(self, df):
        """Create stacked bar chart of cost breakdown"""
        logger.info("Creating cost breakdown chart")
        
        try:
            if 'total_system_cost_billion_eur' not in df.columns:
                logger.warning("No cost data available for breakdown")
                return
            
            # Create a simplified cost breakdown (could be enhanced with more detailed cost data)
            fig, ax = plt.subplots(figsize=(10, 6))
            
            scenarios = df['scenario'].tolist()
            costs = df['total_system_cost_billion_eur'].tolist()
            
            bars = ax.bar(scenarios, costs, color='steelblue', alpha=0.8)
            
            ax.set_title('Total System Cost by Scenario', fontsize=14, fontweight='bold')
            ax.set_ylabel('Cost (Billion EUR)', fontsize=12)
            ax.set_xlabel('Scenario', fontsize=12)
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for bar, cost in zip(bars, costs):
                if not pd.isna(cost):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                           f'€{cost:.1f}B', ha='center', va='bottom')
            
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Save plot
            plot_file = PLOTS_DIR / f"{TIMESTAMP}_cost_breakdown.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            logger.info(f"Cost breakdown saved to: {plot_file}")
            plt.close()
            
        except Exception as e:
            logger.error(f"Error creating cost breakdown: {str(e)}")
    
    def create_storage_radar_chart(self, df):
        """Create spider/radar chart of storage mix"""
        logger.info("Creating storage radar chart")
        
        try:
            # Extract storage power columns
            storage_cols = [col for col in df.columns if col.startswith('storage_power_') and col.endswith('_GW')]
            
            if not storage_cols or len(storage_cols) < 2:
                logger.warning("Insufficient storage data for radar chart")
                return
            
            # Prepare data
            storage_data = df[['scenario'] + storage_cols].set_index('scenario')
            storage_data.columns = [col.replace('storage_power_', '').replace('_GW', '') for col in storage_data.columns]
            storage_data = storage_data.fillna(0)
            
            if storage_data.empty:
                logger.warning("No storage data available")
                return
            
            # Create radar chart
            fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
            
            categories = list(storage_data.columns)
            N = len(categories)
            
            # Compute angle for each category
            angles = [n / float(N) * 2 * np.pi for n in range(N)]
            angles += angles[:1]  # Complete the circle
            
            # Plot each scenario
            colors = plt.cm.Set3(np.linspace(0, 1, len(storage_data)))
            
            for (scenario, row), color in zip(storage_data.iterrows(), colors):
                values = row.tolist()
                values += values[:1]  # Complete the circle
                
                ax.plot(angles, values, 'o-', linewidth=2, label=scenario, color=color)
                ax.fill(angles, values, alpha=0.25, color=color)
            
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories)
            ax.set_title('Storage Power Mix by Scenario', fontsize=14, fontweight='bold', pad=20)
            ax.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
            ax.grid(True)
            
            plt.tight_layout()
            
            # Save plot
            plot_file = PLOTS_DIR / f"{TIMESTAMP}_storage_radar.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            logger.info(f"Storage radar chart saved to: {plot_file}")
            plt.close()
            
        except Exception as e:
            logger.error(f"Error creating storage radar chart: {str(e)}")
    
    def create_residual_load_comparison(self, df):
        """Create hourly residual load comparison (optional)"""
        logger.info("Creating residual load comparison")
        
        try:
            if not self.networks_data:
                logger.warning("No network data available for residual load analysis")
                return
            
            fig, ax = plt.subplots(figsize=(15, 8))
            
            colors = plt.cm.tab10(np.linspace(0, 1, len(self.networks_data)))
            
            for (scenario, data), color in zip(self.networks_data.items(), colors):
                network = data['network']
                
                if (hasattr(network, 'loads_t') and hasattr(network.loads_t, 'p') 
                    and hasattr(network, 'generators_t') and hasattr(network.generators_t, 'p')):
                    
                    # Calculate residual load (load - variable generation)
                    total_load = network.loads_t.p.sum(axis=1) if not network.loads_t.p.empty else None
                    total_gen = network.generators_t.p.sum(axis=1) if not network.generators_t.p.empty else None
                    
                    if total_load is not None and total_gen is not None:
                        residual_load = total_load - total_gen
                        
                        # Plot first week (168 hours)
                        hours_to_plot = min(168, len(residual_load))
                        time_range = range(hours_to_plot)
                        
                        ax.plot(time_range, residual_load.iloc[:hours_to_plot] / 1e3, 
                               label=scenario, color=color, linewidth=2)
            
            ax.set_title('Residual Load Comparison - First Week', fontsize=14, fontweight='bold')
            ax.set_xlabel('Hours', fontsize=12)
            ax.set_ylabel('Residual Load (GW)', fontsize=12)
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            plot_file = PLOTS_DIR / f"{TIMESTAMP}_residual_load.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            logger.info(f"Residual load comparison saved to: {plot_file}")
            plt.close()
            
        except Exception as e:
            logger.error(f"Error creating residual load comparison: {str(e)}")
    
    def generate_all_plots(self, df):
        """Generate all visualization plots"""
        logger.info("Generating all visualization plots")
        
        self.create_capacity_comparison(df)
        self.create_cost_breakdown(df)
        self.create_storage_radar_chart(df)
        self.create_residual_load_comparison(df)
    
    def run_analysis(self):
        """Run the complete analysis workflow"""
        logger.info("Starting PyPSA results comparison analysis")
        logger.info(f"Timestamp: {TIMESTAMP}")
        
        try:
            # Analyze all networks
            self.analyze_all_networks()
            
            if not self.summary_data:
                logger.error("No data was successfully analyzed. Exiting.")
                return
            
            # Create summary DataFrame
            df = self.create_summary_dataframe()
            
            # Generate plots
            self.generate_all_plots(df)
            
            logger.info("Analysis completed successfully!")
            logger.info(f"Results saved to:")
            logger.info(f"  - Summary CSV: {REPORTS_DIR}/summary_{TIMESTAMP}.csv")
            logger.info(f"  - Plots: {PLOTS_DIR}/{TIMESTAMP}_*.png")
            logger.info(f"  - Log: {LOGS_DIR}/analysis_{TIMESTAMP}.log")
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            logger.error(traceback.format_exc())


def main():
    """Main function"""
    print("PyPSA Results Comparison and Analysis")
    print("=" * 50)
    
    analyzer = NetworkAnalyzer()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
