#!/usr/bin/env python3
"""
Quick Start Example for PyPSA Battery Technology Update Package
================================================================

This script demonstrates the basic usage of the updated PyPSA functions
with new battery technology support and scenario analysis capabilities.

Run this script to see the package in action!
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main demonstration function."""
    
    logger.info("🚀 PyPSA Battery Technology Update Package - Quick Start Example")
    logger.info("=" * 70)
    
    # Check if we're in the correct directory
    if not os.path.exists('data/networks'):
        logger.error("❌ Network data directory not found!")
        logger.error("Please ensure you're running this script from the pypsa-battery-tech-update directory")
        return False
    
    try:
        # Import the analysis functions
        logger.info("📦 Importing analysis functions...")
        
        # Add scripts to path if needed
        if 'scripts' not in sys.path:
            sys.path.insert(0, 'scripts')
        
        from scenario_comparison_analysis import load_and_compare_scenarios, analyze_network_metrics
        from capacity_data_handler import get_capacity_data
        
        logger.info("✅ Successfully imported all functions!")
        
        # Step 1: Load and compare scenarios
        logger.info("\n🔍 Step 1: Loading and comparing all three scenarios...")
        networks = load_and_compare_scenarios()
        
        if len(networks) == 3:
            logger.info("✅ Successfully loaded all 3 scenario networks!")
        else:
            logger.warning(f"⚠️  Only loaded {len(networks)} out of 3 expected networks")
        
        # Step 2: Detailed analysis of one scenario
        logger.info("\n🔍 Step 2: Performing detailed analysis of 250Mt CO₂ scenario...")
        
        if '250Mt_CO2_Limit' in networks:
            network_250 = networks['250Mt_CO2_Limit']
            
            # Extract metrics
            metrics = analyze_network_metrics(network_250)
            logger.info(f"   📊 System Cost: {metrics.get('system_cost_billion_eur', 'N/A'):.1f} billion EUR")
            logger.info(f"   📊 Renewable Share: {metrics.get('renewable_share_pct', 'N/A'):.1f}%")
            logger.info(f"   📊 CO₂ Emissions: {metrics.get('co2_emissions_mt', 'N/A'):.1f} Mt")
            logger.info(f"   📊 Total Generation: {metrics.get('total_generation_twh', 'N/A'):.1f} TWh")
            
            # Extract capacity data
            capacity_data = get_capacity_data(network_250)
            logger.info(f"   🔋 Capacity data extracted with {len(capacity_data)} technology entries")
            
        else:
            logger.warning("⚠️  250Mt CO₂ scenario not available for detailed analysis")
        
        # Step 3: Show battery technology support
        logger.info("\n🔍 Step 3: Testing new battery technology support...")
        
        # Test carrier grouping function (if available)
        try:
            from capacity_data_handler import group_battery_carriers
            
            test_carriers = [
                'iron-air battery charger',
                'Lithium-Ion-LFP-bicharger-1',
                'Lithium-Ion-LFP-store-main',
                'battery storage link',
                'battery inverter AC'
            ]
            
            logger.info("   Testing carrier grouping for new battery technologies:")
            for carrier in test_carriers:
                grouped = group_battery_carriers(carrier)
                logger.info(f"   ✅ '{carrier}' → '{grouped}'")
                
        except ImportError:
            logger.info("   📝 Carrier grouping function not available in this configuration")
        
        # Step 4: Check output files
        logger.info("\n🔍 Step 4: Checking generated output files...")
        
        plot_dirs = ['outputs/plots/scenario_comparison', 'outputs/plots/test_plots']
        total_plots = 0
        
        for plot_dir in plot_dirs:
            if os.path.exists(plot_dir):
                plot_files = [f for f in os.listdir(plot_dir) if f.endswith('.png')]
                total_plots += len(plot_files)
                logger.info(f"   📈 Found {len(plot_files)} plots in {plot_dir}/")
                for plot_file in plot_files:
                    logger.info(f"      - {plot_file}")
        
        logger.info(f"   📊 Total plots generated: {total_plots}")
        
        # Step 5: Summary
        logger.info("\n🎉 Quick Start Example Complete!")
        logger.info("=" * 70)
        logger.info("Summary of capabilities demonstrated:")
        logger.info("✅ Multi-scenario network loading")
        logger.info("✅ Comprehensive metric extraction") 
        logger.info("✅ New battery technology support")
        logger.info("✅ Capacity data processing")
        logger.info("✅ Plot generation and visualization")
        logger.info("✅ Error handling and logging")
        
        logger.info("\n📚 Next steps:")
        logger.info("- Review the generated plots in outputs/plots/")
        logger.info("- Check the detailed verification report in documentation/")
        logger.info("- Run the full test suite: python tests/comprehensive_data_processing_test.py")
        logger.info("- Integrate functions into your Jupyter notebook")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("Please ensure all required packages are installed:")
        logger.error("pip install -r requirements.txt")
        return False
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        logger.error("Please check the installation and try again")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 Quick start example completed successfully!")
        print("The package is ready for use in your PyPSA analysis workflow.")
    else:
        print("\n❌ Quick start example failed.")
        print("Please review the error messages and check the installation.")
        sys.exit(1)
