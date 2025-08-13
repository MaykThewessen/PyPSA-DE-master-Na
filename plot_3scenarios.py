#!/usr/bin/env python3
"""
Enhanced 3-Scenario Comparison Plotting Script
==============================================

This script creates publication-quality plots for the 3 PyPSA scenarios:
- All Tech
- No Iron-Air
- No MDS

Based on the results-analysis-3scenarios.ipynb notebook structure.

Usage:
    python plot_3scenarios.py [results_folder]
    
Example:
    python plot_3scenarios.py results-de-2030-white-paper-v3
"""

import os
import sys
import glob
import logging
from datetime import datetime
from pathlib import Path
import warnings

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pypsa
from tabulate import tabulate

warnings.filterwarnings('ignore')

# Configuration
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
PLOTS_DIR = Path("plots")
PLOTS_DIR.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use the bmh style like in the notebook
plt.style.use("bmh")

def get_capacity_data(network):
    """Extract capacity data from network, similar to notebook function"""
    # List of all possible carriers
    all_storage_carriers = ['vanadium', 'IronAir', 'H2', 'CAES', 'battery1', 'battery2', 'battery4', 'battery8', 
                    'Ebattery1', 'Ebattery2']
    
    # Step 1: Identify generators that actually generated power (sum over all time steps)
    generators_used = network.generators_t.p.sum().groupby(network.generators.carrier).sum()

    # Step 2: Filter out carriers that never generated power
    active_carriers = generators_used[generators_used > 0].index

    # Step 3: Get the installed capacity (`p_nom_opt`) of only the active generators
    generators = network.generators[network.generators.carrier.isin(active_carriers)].groupby("carrier").p_nom_opt.sum() / 1e3

    # calculate the total installed capacity for storage units by carrier, converting from MW to GW
    storage_units = network.storage_units.groupby("carrier").p_nom_opt.sum() / 1e3
  
    # Convert storage unit capacity data to a DataFrame
    df_storage_units = storage_units.reset_index()
    # Convert generator optimal capacity data to a DataFrame
    df_generators = pd.DataFrame(generators).reset_index()

    # Rename the columns for consistency
    df_generators.columns = ['carrier', 'capacity']
    df_storage_units.columns = ['carrier', 'capacity']

    # Combine storage unit and generator capacity data
    df_combined = pd.concat([df_storage_units.set_index('carrier'), df_generators.set_index('carrier')])

    # Group multiple offshore wind categories under "offwind" (offwind-ac, offwind-dc, offwind-float)
    df_combined = df_combined.groupby(df_combined.index.map(lambda x: 'offwind' if x in ['offwind-ac', 'offwind-dc', 'offwind-float'] else x)).sum()
    # Group "solar" and "solar-hsat" under "solar"
    df_combined = df_combined.groupby(df_combined.index.map(lambda x: 'solar' if x in ['solar', 'solar-hsat'] else x)).sum()

    df_combined = df_combined.groupby(df_combined.index.map(lambda x: 'battery1' if x in ['Ebattery1', 'battery1'] else x)).sum()
    df_combined = df_combined.groupby(df_combined.index.map(lambda x: 'battery2' if x in ['Ebattery2', 'battery2'] else x)).sum()

    # Ensure all carriers from the list are present, add with 0 capacity if missing
    for carrier in all_storage_carriers:
        if carrier not in df_combined.index:
            df_combined.loc[carrier] = 0

    # Reset the index
    df_combined = df_combined.reset_index()

    # Return the final DataFrame
    return df_combined.reset_index(drop=True)


def calculate_emissions(network):
    """Calculate CO2 emissions from network"""
    try:
        emissions = (
            network.generators_t.p
            / network.generators.efficiency
            * network.generators.carrier.map(network.carriers.co2_emissions)
        )  # t/h

        # calculate total emission, and transform to Mt 
        total_emissions = network.snapshot_weightings.generators @ emissions.sum(axis=1).div(1e6)  # Mt
        return total_emissions
    except Exception as e:
        logger.warning(f"Could not calculate emissions: {e}")
        return 0


def add_network_identifier(df, identifier):
    """Adds a 'network' column to the DataFrame, containing the identifier for the network"""
    df['network'] = identifier
    return df


def get_carrier_color(carrier):
    """Get color for a specific carrier"""
    color_map = {
        'CAES': '#1f77b4',        # Medium Blue
        'Ebattery1': '#aec7e8',   # Light Blue
        'Ebattery2': '#c6dbef',   # Very Light Blue
        'H2': '#ff7f0e',          # Bright Orange
        'IronAir': '#2ca02c',     # Fresh Green
        'PHS': '#9467bd',         # Purple
        'battery1': '#8c564b',    # Earth Brown
        'battery2': '#e377c2',    # Pink
        'battery4': '#7f7f7f',    # Neutral Grey
        'battery8': '#bcbd22',    # Olive
        'biomass': '#17becf',     # Cyan
        'hydro': '#1f9e89',       # Teal Green
        'nuclear': '#c5b0d5',     # Light Lavender
        'offwind': '#98df8a',     # Light Green
        'onwind': '#66c2a5',      # Strong Green
        'ror': '#f7b6d2',         # Soft Pink
        'solar': '#fdae61',       # Golden Orange
        'vanadium': '#80b1d3',    # Light Steel Blue
    }
    return color_map.get(carrier, '#333333')  # default: dark grey


def prepare_dataframes(networks):
    """Prepares dataframes for different networks"""
    dfs = []
    # Iterates over networks and their identifiers
    for network, identifier in networks:
        # Retrieves capacity data for each network
        df = get_capacity_data(network)
        # Adds a 'network' column to identify each network
        df = add_network_identifier(df, identifier)
        # Concatenates all DataFrames into a single DataFrame
        dfs.append(df)
    return pd.concat(dfs)


def pivot_and_reorder(df_all, carrier_order, network_order):
    """Pivots the DataFrame to prepare it for plotting and reorders by carrier and network"""
    # Pivots the DataFrame to have carriers as rows and networks as columns
    df_pivot = df_all.pivot_table(index='carrier', columns='network', values='capacity', fill_value=0)
    # Reorders the rows (carriers) according to the carrier_order list
    df_pivot = df_pivot.loc[carrier_order]
    # Reorders the columns (networks) according to the network_order list
    df_pivot = df_pivot[network_order]
    return df_pivot


def plot_stacked_bar(df_pivot, colors, output_file):
    """Plots a stacked bar chart with capacity"""
    # Create a figure and axis for plotting
    fig, ax1 = plt.subplots(figsize=(10, 6))
    # Plot a stacked bar chart using the transposed pivot table
    df_pivot.T.plot(kind='bar', stacked=True, ax=ax1, width=0.5, color=colors)
    
    # Label the y-axis for capacity
    ax1.set_ylabel('Capacity (GW)', fontsize=14)
    ax1.set_xlabel('')
    ax1.set_title('Installed capacity by carrier', fontsize=14)

    ax1.legend(title='Carrier', bbox_to_anchor=(1.03, 1), loc='upper left', fontsize=12, title_fontsize=12)

    # Custom x-tick labels for the network order
    custom_xticks = ['All Tech', 'No Iron-Air', 'No MDS']

    # Set x-ticks to match the number of custom labels
    ax1.set_xticks(range(len(custom_xticks)))
    ax1.set_xticklabels(custom_xticks, rotation=0, fontsize=12)

    ax1.set_xlabel('Scenarios', fontsize=14)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Capacity plot saved to: {output_file}")


def create_emissions_table(networks_data, output_file):
    """Create and save emissions comparison table"""
    emissions_data = {
        'Network': ['All Tech', 'No Iron-Air', 'No MDS'],
        'CO2 Emissions (Mt)': []
    }
    
    for network_name in ['All Tech', 'No Iron-Air', 'No MDS']:
        if network_name in networks_data:
            emissions = calculate_emissions(networks_data[network_name]['network'])
            emissions_data['CO2 Emissions (Mt)'].append(f'{emissions:.6g}')
        else:
            emissions_data['CO2 Emissions (Mt)'].append('N/A')
    
    emissions_df = pd.DataFrame(emissions_data)
    
    # Save to CSV
    emissions_df.to_csv(output_file, index=False)
    
    # Print table
    print("\nCO2 Emissions for Different Networks")
    print(tabulate(emissions_df, headers='keys', tablefmt='grid', showindex=False, disable_numparse=True))
    
    logger.info(f"Emissions table saved to: {output_file}")


def create_capacity_table(df_pivot, output_file):
    """Create and save capacity comparison table"""
    # Save pivot_capacity_df in a csv file
    df_pivot.to_csv(output_file, index=True)
    
    print("\nCapacity Data (Rows: Carriers, Columns: Networks)")
    print(tabulate(df_pivot, headers='keys', tablefmt='grid', showindex=True, disable_numparse=True))
    
    logger.info(f"Capacity table saved to: {output_file}")


def load_networks(results_folder):
    """Load the three scenario networks"""
    # Define the grid names like in the notebook
    networks = {
        'All Tech': 'de-2030-all-technologies-elec_s_1_ec_lcopt_.nc',
        'No Iron-Air': 'de-2030-no-ironair-elec_s_1_ec_lcopt_.nc',
        'No MDS': 'de-2030-no-mds-elec_s_1_ec_lcopt_.nc',
    }
    
    network_objects = {}
    
    for name, file in networks.items():
        filepath = os.path.join(results_folder, file)
        if os.path.exists(filepath):
            try:
                logger.info(f"Loading network: {name} from {filepath}")
                network = pypsa.Network(filepath)
                network_objects[name] = network
                logger.info(f"Network '{name}' loaded with {len(network.buses)} buses.")
            except MemoryError:
                logger.warning(f"MemoryError loading {name}, trying optimized loading...")
                try:
                    network = pypsa.Network()
                    network.import_from_netcdf(filepath)
                    # Downcast to save memory
                    _downcast_network_dtypes(network)
                    network_objects[name] = network
                    logger.info(f"Network '{name}' loaded with optimization.")
                except Exception as e:
                    logger.error(f"Failed to load {name} even with optimization: {e}")
            except Exception as e:
                logger.error(f"Failed to load network {name}: {e}")
        else:
            logger.warning(f"Network file not found: {filepath}")
    
    return network_objects


def _downcast_network_dtypes(network):
    """Downcast numeric dtypes to reduce memory usage"""
    components = ['buses', 'generators', 'loads', 'lines', 'links', 'transformers', 'storage_units']
    
    for component in components:
        if hasattr(network, component):
            df = getattr(network, component)
            if not df.empty:
                for col in df.columns:
                    if df[col].dtype == 'float64':
                        df[col] = pd.to_numeric(df[col], downcast='float')
                    elif df[col].dtype == 'int64':
                        df[col] = pd.to_numeric(df[col], downcast='integer')


def main():
    """Main function"""
    print("Enhanced 3-Scenario Comparison Plotting Script")
    print("=" * 50)
    
    # Get results folder from command line or use default
    if len(sys.argv) > 1:
        results_folder = sys.argv[1]
    else:
        # Try to find results folder automatically
        possible_folders = [
            "results-de-2030-white-paper-v3",
            "results/networks",
            "results",
            "runs"
        ]
        
        results_folder = None
        for folder in possible_folders:
            if os.path.exists(folder):
                results_folder = folder
                break
        
        if results_folder is None:
            logger.error("No results folder found. Please specify one as argument.")
            print("\nUsage: python plot_3scenarios.py [results_folder]")
            sys.exit(1)
    
    logger.info(f"Using results folder: {results_folder}")
    
    # Load networks
    network_objects = load_networks(results_folder)
    
    if not network_objects:
        logger.error("No networks could be loaded!")
        sys.exit(1)
    
    logger.info(f"Successfully loaded {len(network_objects)} networks")
    
    # Store network data for easy access
    networks_data = {}
    for name, network in network_objects.items():
        networks_data[name] = {'network': network}
    
    # Create emissions table
    emissions_file = PLOTS_DIR / f"{TIMESTAMP}_emissions_comparison.csv"
    create_emissions_table(networks_data, emissions_file)
    
    # Prepare data for capacity plotting (like in the notebook)
    network_list = [
        (network_objects["All Tech"], 'All Tech'),
        (network_objects["No Iron-Air"], 'No Iron-Air'), 
        (network_objects["No MDS"], 'No MDS'),
    ]
    
    # Prepare the combined DataFrame for all networks
    df_all = prepare_dataframes(network_list)
    
    # Define the order of carriers and networks for the plot
    carrier_order = [
        'PHS', 'H2', 'IronAir', 'battery1', 'battery2', 'battery4', 'battery8',
        'vanadium', 'CAES', 'Ebattery1', 'Ebattery2',
        'nuclear', 'biomass', 'hydro', 'ror', 'onwind', 'offwind', 'solar'
    ]
    
    network_order = ['All Tech', 'No Iron-Air', 'No MDS']
    
    # Pivot and reorder the data
    df_pivot = pivot_and_reorder(df_all, carrier_order, network_order)
    
    # Create capacity table
    capacity_file = PLOTS_DIR / f"{TIMESTAMP}_installed_capacity_comparison.csv"
    create_capacity_table(df_pivot, capacity_file)
    
    # Define colors for each carrier
    colors = [get_carrier_color(carrier) for carrier in carrier_order]
    
    # Create the stacked bar plot
    plot_file = PLOTS_DIR / f"{TIMESTAMP}_capacity_by_scenario.png"
    plot_stacked_bar(df_pivot, colors, plot_file)
    
    print(f"\nResults saved to:")
    print(f"  - Capacity plot: {plot_file}")
    print(f"  - Capacity table: {capacity_file}")
    print(f"  - Emissions table: {emissions_file}")
    
    logger.info("Analysis completed successfully!")


if __name__ == "__main__":
    main()
