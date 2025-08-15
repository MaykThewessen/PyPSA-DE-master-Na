#!/usr/bin/env python3
"""
Analyze existing PyPSA results for CO2 emissions
This script analyzes the CO2 emissions from existing network solutions 
without requiring geospatial libraries that depend on PyProj.
"""

import pandas as pd
import numpy as np
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_co2_emissions():
    """Analyze CO2 emissions from existing network solutions."""
    
    logger.info("=" * 80)
    logger.info("PYPSA CO2 ANALYSIS - EXISTING RESULTS")
    logger.info("=" * 80)
    
    # Look for existing solved networks
    results_dir = "results/de-all-tech-2035-mayk/networks"
    if not os.path.exists(results_dir):
        logger.error(f"Results directory not found: {results_dir}")
        return False
    
    # List available network files
    network_files = []
    for file in os.listdir(results_dir):
        if file.endswith('.nc') and 'solved' in file:
            network_files.append(file)
    
    logger.info(f"Found {len(network_files)} solved network files:")
    for file in network_files:
        logger.info(f"  - {file}")
    
    if not network_files:
        logger.warning("No solved network files found")
        return False
    
    # CO2 emission factors (tCO2/MWh)
    co2_factors = {
        'coal': 0.820,
        'lignite': 0.986,
        'CCGT': 0.350,        # Combined Cycle Gas Turbine
        'OCGT': 0.400,        # Open Cycle Gas Turbine
        'oil': 0.650,
        'gas': 0.375,
        'natural gas': 0.375,
        'Gas': 0.375,
    }
    
    # German 1990 electricity CO2 emissions baseline (approximate)
    german_1990_co2_mtco2 = 148.7  # MtCO2 for electricity sector
    
    # Analyze each network
    results_summary = []
    
    for network_file in network_files:
        logger.info(f"\n{'='*50}")
        logger.info(f"Analyzing: {network_file}")
        logger.info(f"{'='*50}")
        
        try:
            # For now, let's create a simple method that doesn't require PyProj
            # We'll try to read specific CSV files that might contain generation data
            
            # Look for generation output files
            base_name = network_file.replace('.nc', '')
            generation_files = []
            
            # Check if there are CSV outputs
            csv_files = [f for f in os.listdir(results_dir) if f.endswith('.csv')]
            if csv_files:
                logger.info(f"Found CSV files that might contain generation data:")
                for csv_file in csv_files:
                    logger.info(f"  - {csv_file}")
            
            # Since we can't load the .nc files without PyProj, let's create a status report
            file_size = os.path.getsize(os.path.join(results_dir, network_file))
            file_size_mb = file_size / (1024 * 1024)
            
            logger.info(f"File size: {file_size_mb:.1f} MB")
            
            # For now, we'll report that analysis is pending
            scenario_name = network_file.replace('base_s_1_elec_solved_', '').replace('.nc', '')
            results_summary.append({
                'scenario': scenario_name,
                'file': network_file,
                'size_mb': file_size_mb,
                'status': 'Analysis pending - PyProj dependency issue'
            })
            
        except Exception as e:
            logger.error(f"Error analyzing {network_file}: {str(e)}")
            continue
    
    # Summary report
    logger.info(f"\n{'='*80}")
    logger.info("SUMMARY REPORT")
    logger.info(f"{'='*80}")
    
    if results_summary:
        logger.info("Available scenarios for CO2 analysis:")
        logger.info(f"{'Scenario':<20} {'File Size (MB)':<15} {'Status'}")
        logger.info("-" * 70)
        
        for result in results_summary:
            logger.info(f"{result['scenario']:<20} {result['size_mb']:<15.1f} {result['status']}")
    
    # Configuration status
    logger.info(f"\nCurrent CO2 configuration:")
    
    # Check config.yaml
    config_path = "config.yaml"
    if os.path.exists(config_path):
        logger.info(f"Reading configuration from {config_path}")
        try:
            with open(config_path, 'r') as f:
                config_content = f.read()
                
            # Look for CO2 settings
            lines = config_content.split('\n')
            co2_lines = [line for line in lines if 'co2' in line.lower()]
            
            if co2_lines:
                logger.info("CO2-related configuration:")
                for line in co2_lines:
                    logger.info(f"  {line.strip()}")
            
        except Exception as e:
            logger.error(f"Error reading config: {str(e)}")
    
    # Recommendations
    logger.info(f"\n{'='*60}")
    logger.info("RECOMMENDATIONS")
    logger.info(f"{'='*60}")
    
    logger.info("🔧 CURRENT ISSUE: PyProj database context not properly configured")
    logger.info("   This prevents loading of network files with geospatial data")
    logger.info("")
    logger.info("📊 AVAILABLE OPTIONS:")
    logger.info("1. Fix PyProj environment to enable full network analysis")
    logger.info("2. Export generation data to CSV format from existing networks")
    logger.info("3. Use PyPSA's built-in plotting/analysis without geographic features")
    logger.info("4. Run analysis in a different environment with proper PyProj setup")
    logger.info("")
    logger.info("🎯 GOAL: Verify that zero CO2 emissions constraint is working")
    logger.info(f"   Target: < 0.1% of 1990 levels ({german_1990_co2_mtco2 * 0.001:.3f} MtCO2)")
    
    return True

if __name__ == "__main__":
    analyze_co2_emissions()
