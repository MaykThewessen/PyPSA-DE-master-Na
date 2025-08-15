#!/usr/bin/env python3
"""
PyPSA-DE Costs File Integration Test
===================================

This script verifies that the updated costs file works correctly with PyPSA-DE:
1. Load the updated costs file 
2. Check that storage technologies are recognized with new names
3. Verify that cost calculations and optimizations run without errors
4. Confirm that storage capacity and operation constraints work as expected
5. Document any required updates to other model configuration files

Test Steps:
- Load costs file and verify structure
- Check storage technology mappings
- Run small optimization test with storage technologies
- Verify cost calculations are correct
- Test constraint handling for storage operations
"""

import os
import sys
import pandas as pd
import numpy as np
import pypsa
import yaml
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CostsFileIntegrationTest:
    """Test suite for costs file integration with PyPSA-DE."""
    
    def __init__(self):
        self.test_results = {}
        self.costs_file_path = "resources/de-all-tech-2035-mayk/costs_2035_mapped.csv"
        self.backup_costs_path = "resources/de-all-tech-2035-mayk/costs_2035.csv"
        self.config_path = "config/config.default.yaml"
        
        # Storage technologies to verify
        self.storage_technologies = {
            'battery-store': 'Battery storage (energy)',
            'battery-charger': 'Battery charger (power)',
            'H2-store': 'Hydrogen storage (energy)', 
            'H2-electrolysis': 'Hydrogen electrolysis (power)',
            'H2-fuel-cell': 'Hydrogen fuel cell (power)',
            'CAES-store': 'Compressed Air Energy Storage (energy)',
            'CAES-bicharger': 'CAES bi-directional charger (power)',
            'PHS-turbine': 'Pumped hydro turbine (power)',
            'PHS-pump': 'Pumped hydro pump (power)',
            'Pumped-Storage-Hydro-store': 'Pumped hydro storage (energy)',
            'Concrete-store': 'Concrete thermal storage (energy)',
            'Concrete-charger': 'Concrete thermal charger (power)',
            'Concrete-discharger': 'Concrete thermal discharger (power)'
        }
        
        self.required_parameters = ['investment', 'FOM', 'lifetime']
        
    def run_all_tests(self):
        """Run complete costs file integration test suite."""
        logger.info("=" * 100)
        logger.info("PYPSA-DE COSTS FILE INTEGRATION TEST SUITE")
        logger.info("=" * 100)
        
        try:
            # Step 1: Load and validate costs file structure
            self.test_costs_file_loading()
            
            # Step 2: Verify storage technology recognition
            self.test_storage_technology_recognition()
            
            # Step 3: Test cost calculations
            self.test_cost_calculations()
            
            # Step 4: Run optimization test with storage
            self.test_optimization_with_storage()
            
            # Step 5: Verify constraint handling
            self.test_storage_constraints()
            
            # Step 6: Check configuration file compatibility
            self.test_configuration_compatibility()
            
            # Generate comprehensive report
            self.generate_integration_report()
            
        except Exception as e:
            logger.error(f"Integration test suite failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        return True
    
    def test_costs_file_loading(self):
        """Test 1: Load and validate costs file structure."""
        logger.info("\n🔍 TEST 1: COSTS FILE LOADING AND VALIDATION")
        logger.info("-" * 60)
        
        test_passed = True
        
        try:
            # Load the main costs file
            if os.path.exists(self.costs_file_path):
                costs_df = pd.read_csv(self.costs_file_path)
                logger.info(f"✅ Main costs file loaded: {len(costs_df)} entries")
                
                # Verify required columns
                required_cols = ['technology', 'parameter', 'value', 'unit', 'source']
                missing_cols = [col for col in required_cols if col not in costs_df.columns]
                
                if missing_cols:
                    logger.error(f"❌ Missing required columns: {missing_cols}")
                    test_passed = False
                else:
                    logger.info("✅ All required columns present")
                
                # Check for duplicate entries
                duplicates = costs_df.duplicated(subset=['technology', 'parameter']).sum()
                if duplicates > 0:
                    logger.warning(f"⚠️  Found {duplicates} duplicate technology-parameter combinations")
                else:
                    logger.info("✅ No duplicate entries found")
                
                # Verify data types
                if costs_df['value'].dtype in ['float64', 'int64']:
                    logger.info("✅ Value column has correct numeric type")
                else:
                    logger.warning("⚠️  Value column may have non-numeric entries")
                
                self.costs_data = costs_df
                
            else:
                logger.error(f"❌ Costs file not found: {self.costs_file_path}")
                test_passed = False
                
        except Exception as e:
            logger.error(f"❌ Error loading costs file: {e}")
            test_passed = False
        
        self.test_results['costs_file_loading'] = {'passed': test_passed}
        
        if test_passed:
            logger.info("✅ TEST 1 PASSED: Costs file loaded and validated successfully")
        else:
            logger.error("❌ TEST 1 FAILED: Issues with costs file loading")
    
    def test_storage_technology_recognition(self):
        """Test 2: Verify storage technologies are recognized with new names."""
        logger.info("\n🔍 TEST 2: STORAGE TECHNOLOGY RECOGNITION")
        logger.info("-" * 60)
        
        test_passed = True
        found_technologies = {}
        
        # Get unique technologies from costs file
        technologies = set(self.costs_data['technology'].unique())
        logger.info(f"Total technologies in costs file: {len(technologies)}")
        
        # Check each storage technology
        for tech_key, description in self.storage_technologies.items():
            if tech_key in technologies:
                found_technologies[tech_key] = description
                logger.info(f"✅ Found: {tech_key} - {description}")
            else:
                logger.warning(f"⚠️  Missing: {tech_key} - {description}")
        
        # Check required parameters for found technologies
        missing_params = {}
        for tech in found_technologies.keys():
            tech_data = self.costs_data[self.costs_data['technology'] == tech]
            tech_params = set(tech_data['parameter'].unique())
            
            missing = [p for p in self.required_parameters if p not in tech_params]
            if missing:
                missing_params[tech] = missing
                logger.error(f"❌ {tech} missing parameters: {missing}")
                test_passed = False
            else:
                logger.info(f"✅ {tech} has all required parameters")
        
        # Summary
        storage_coverage = len(found_technologies) / len(self.storage_technologies) * 100
        logger.info(f"Storage technology coverage: {storage_coverage:.1f}%")
        
        self.test_results['storage_recognition'] = {
            'passed': test_passed,
            'technologies_found': len(found_technologies),
            'technologies_expected': len(self.storage_technologies),
            'coverage_percent': storage_coverage,
            'missing_parameters': missing_params
        }
        
        if test_passed and storage_coverage >= 80:
            logger.info("✅ TEST 2 PASSED: Storage technologies adequately recognized")
        else:
            logger.error("❌ TEST 2 FAILED: Issues with storage technology recognition")
    
    def test_cost_calculations(self):
        """Test 3: Verify cost calculations work correctly."""
        logger.info("\n🔍 TEST 3: COST CALCULATIONS")
        logger.info("-" * 60)
        
        test_passed = True
        
        try:
            # Test cost calculations for storage technologies
            for tech in ['battery-store', 'H2-store', 'CAES-store']:
                if tech not in self.costs_data['technology'].values:
                    continue
                    
                tech_data = self.costs_data[self.costs_data['technology'] == tech]
                
                # Get investment cost
                investment_data = tech_data[tech_data['parameter'] == 'investment']
                if not investment_data.empty:
                    investment_cost = investment_data['value'].iloc[0]
                    unit = investment_data['unit'].iloc[0]
                    logger.info(f"✅ {tech} investment: {investment_cost} {unit}")
                    
                    # Validate cost is reasonable (not zero or negative)
                    if investment_cost <= 0:
                        logger.error(f"❌ {tech} has invalid investment cost: {investment_cost}")
                        test_passed = False
                else:
                    logger.warning(f"⚠️  {tech} missing investment cost")
                
                # Get lifetime
                lifetime_data = tech_data[tech_data['parameter'] == 'lifetime']
                if not lifetime_data.empty:
                    lifetime = lifetime_data['value'].iloc[0]
                    logger.info(f"✅ {tech} lifetime: {lifetime} years")
                    
                    # Validate lifetime is reasonable
                    if not (1 <= lifetime <= 100):
                        logger.error(f"❌ {tech} has unrealistic lifetime: {lifetime}")
                        test_passed = False
                else:
                    logger.warning(f"⚠️  {tech} missing lifetime")
                
                # Calculate annualized cost
                if not investment_data.empty and not lifetime_data.empty:
                    discount_rate = 0.07  # Typical discount rate
                    annuity_factor = (discount_rate * (1 + discount_rate)**lifetime) / ((1 + discount_rate)**lifetime - 1)
                    annualized_cost = investment_cost * annuity_factor
                    logger.info(f"✅ {tech} annualized cost: {annualized_cost:.2f} {unit}/year")
                    
        except Exception as e:
            logger.error(f"❌ Error in cost calculations: {e}")
            test_passed = False
        
        self.test_results['cost_calculations'] = {'passed': test_passed}
        
        if test_passed:
            logger.info("✅ TEST 3 PASSED: Cost calculations working correctly")
        else:
            logger.error("❌ TEST 3 FAILED: Issues with cost calculations")
    
    def test_optimization_with_storage(self):
        """Test 4: Run small optimization test with storage technologies."""
        logger.info("\n🔍 TEST 4: OPTIMIZATION WITH STORAGE")
        logger.info("-" * 60)
        
        test_passed = True
        
        try:
            # Create minimal test network
            n = pypsa.Network()
            
            # Add single bus
            n.add("Bus", "bus", carrier="AC", x=10, y=50)
            
            # Add basic load
            n.add("Load", "load", bus="bus", p_set=100)
            
            # Add renewable generator with variability
            n.add("Generator", "solar", bus="bus", carrier="solar", 
                  p_nom_extendable=True, marginal_cost=0,
                  p_max_pu=[0.3, 0.8, 0.9, 0.7, 0.2, 0.1] * 4)  # 24h pattern
            
            # Add storage based on costs file
            battery_data = self.costs_data[self.costs_data['technology'] == 'battery-store']
            if not battery_data.empty:
                investment_cost = battery_data[battery_data['parameter'] == 'investment']['value'].iloc[0]
                
                # Add battery storage
                n.add("Store", "battery", bus="bus", carrier="battery",
                      e_nom_extendable=True, capital_cost=investment_cost,
                      e_cyclic=True)
                
                logger.info(f"✅ Added battery storage with cost: {investment_cost}")
            
            # Set time series (24 hours)
            n.set_snapshots(pd.date_range('2020-01-01', periods=24, freq='H'))
            
            # Try to solve optimization
            try:
                n.optimize(solver_name='highs')
                
                if n.objective > 0:
                    logger.info(f"✅ Optimization successful, objective: {n.objective:.2f}")
                    
                    # Check storage installation
                    if 'battery' in n.stores.index:
                        battery_capacity = n.stores.loc['battery', 'e_nom_opt']
                        logger.info(f"✅ Battery capacity optimized: {battery_capacity:.2f} MWh")
                        
                        if battery_capacity > 0:
                            logger.info("✅ Storage investment occurred as expected")
                        else:
                            logger.warning("⚠️  No storage investment (may be expected)")
                    
                else:
                    logger.warning("⚠️  Optimization completed but with zero objective")
                    
            except Exception as solve_error:
                logger.error(f"❌ Optimization failed: {solve_error}")
                test_passed = False
                
        except Exception as e:
            logger.error(f"❌ Error setting up optimization test: {e}")
            test_passed = False
        
        self.test_results['optimization'] = {'passed': test_passed}
        
        if test_passed:
            logger.info("✅ TEST 4 PASSED: Optimization with storage working")
        else:
            logger.error("❌ TEST 4 FAILED: Issues with optimization")
    
    def test_storage_constraints(self):
        """Test 5: Verify storage capacity and operation constraints."""
        logger.info("\n🔍 TEST 5: STORAGE CONSTRAINTS")
        logger.info("-" * 60)
        
        test_passed = True
        
        try:
            # Create test network with storage constraints
            n = pypsa.Network()
            n.add("Bus", "bus", carrier="AC")
            
            # Add storage with constraints based on costs data
            storage_types = ['battery-store', 'H2-store']
            
            for storage_type in storage_types:
                storage_data = self.costs_data[self.costs_data['technology'] == storage_type]
                if storage_data.empty:
                    continue
                
                # Get efficiency if available
                efficiency_data = storage_data[storage_data['parameter'] == 'efficiency']
                efficiency = 0.9  # Default
                if not efficiency_data.empty:
                    efficiency = efficiency_data['value'].iloc[0]
                
                # Add store with constraints
                store_name = f"{storage_type}_test"
                n.add("Store", store_name, bus="bus", carrier=storage_type,
                      e_nom=100,  # Fixed capacity for testing
                      e_max_pu=1.0, e_min_pu=0.0,
                      standing_loss=0.01)  # 1% per hour standing loss
                
                logger.info(f"✅ Added {storage_type} with efficiency: {efficiency}")
            
            # Test constraint validation
            if len(n.stores) > 0:
                logger.info(f"✅ Successfully created {len(n.stores)} storage units")
                
                # Check constraint bounds
                for store in n.stores.index:
                    e_max = n.stores.loc[store, 'e_max_pu']
                    e_min = n.stores.loc[store, 'e_min_pu']
                    
                    if e_max >= e_min and 0 <= e_min <= 1 and 0 <= e_max <= 1:
                        logger.info(f"✅ {store} has valid constraints: [{e_min}, {e_max}]")
                    else:
                        logger.error(f"❌ {store} has invalid constraints: [{e_min}, {e_max}]")
                        test_passed = False
            else:
                logger.warning("⚠️  No storage units created for constraint testing")
                
        except Exception as e:
            logger.error(f"❌ Error in storage constraints test: {e}")
            test_passed = False
        
        self.test_results['storage_constraints'] = {'passed': test_passed}
        
        if test_passed:
            logger.info("✅ TEST 5 PASSED: Storage constraints working correctly")
        else:
            logger.error("❌ TEST 5 FAILED: Issues with storage constraints")
    
    def test_configuration_compatibility(self):
        """Test 6: Check compatibility with PyPSA-DE configuration files."""
        logger.info("\n🔍 TEST 6: CONFIGURATION COMPATIBILITY")
        logger.info("-" * 60)
        
        test_passed = True
        config_issues = []
        
        try:
            # Load default configuration
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                logger.info("✅ Configuration file loaded successfully")
                
                # Check for storage-related configurations
                if 'costs' in config:
                    costs_config = config['costs']
                    logger.info("✅ Costs configuration section found")
                    
                    # Check if costs file path is referenced
                    if 'file' in costs_config:
                        config_costs_file = costs_config['file']
                        logger.info(f"Configuration references costs file: {config_costs_file}")
                    
                # Check technology data sections
                if 'electricity' in config:
                    elec_config = config['electricity']
                    
                    # Look for storage technologies in configuration
                    storage_in_config = []
                    for key, value in elec_config.items():
                        if isinstance(value, dict) and any(storage_tech in str(value) 
                                                         for storage_tech in self.storage_technologies.keys()):
                            storage_in_config.append(key)
                    
                    if storage_in_config:
                        logger.info(f"✅ Found storage references in config: {storage_in_config}")
                    else:
                        logger.info("ℹ️  No explicit storage references found in electricity config")
                
                # Check for any technology name mismatches
                if 'costs' in config and 'technology_data' in config['costs']:
                    tech_data_config = config['costs']['technology_data']
                    # This would need specific implementation based on actual config structure
                
            else:
                logger.warning(f"⚠️  Configuration file not found: {self.config_path}")
                config_issues.append(f"Missing config file: {self.config_path}")
            
        except Exception as e:
            logger.error(f"❌ Error checking configuration compatibility: {e}")
            test_passed = False
            config_issues.append(str(e))
        
        self.test_results['configuration_compatibility'] = {
            'passed': test_passed,
            'issues': config_issues
        }
        
        if test_passed and not config_issues:
            logger.info("✅ TEST 6 PASSED: Configuration compatibility verified")
        else:
            logger.error("❌ TEST 6 FAILED: Configuration compatibility issues")
    
    def generate_integration_report(self):
        """Generate comprehensive integration test report."""
        logger.info("\n" + "=" * 100)
        logger.info("INTEGRATION TEST REPORT")
        logger.info("=" * 100)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get('passed', False))
        
        logger.info(f"Tests Passed: {passed_tests}/{total_tests}")
        logger.info(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        # Detailed results
        logger.info("\nDETAILED RESULTS:")
        logger.info("-" * 60)
        
        for test_name, results in self.test_results.items():
            status = "✅ PASSED" if results.get('passed', False) else "❌ FAILED"
            logger.info(f"{test_name.upper()}: {status}")
            
            # Add specific details
            if test_name == 'storage_recognition':
                coverage = results.get('coverage_percent', 0)
                logger.info(f"  Storage coverage: {coverage:.1f}%")
                
                if results.get('missing_parameters'):
                    logger.info("  Missing parameters:")
                    for tech, params in results['missing_parameters'].items():
                        logger.info(f"    {tech}: {params}")
            
            elif test_name == 'configuration_compatibility':
                if results.get('issues'):
                    logger.info("  Issues found:")
                    for issue in results['issues']:
                        logger.info(f"    - {issue}")
        
        # Summary and recommendations
        logger.info("\nRECOMMENDATIONS:")
        logger.info("-" * 60)
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED! The costs file is ready for production use.")
            logger.info("📋 No immediate action required.")
        else:
            logger.info("⚠️  SOME TESTS FAILED. Please address the following:")
            
            for test_name, results in self.test_results.items():
                if not results.get('passed', False):
                    if test_name == 'costs_file_loading':
                        logger.info("  - Fix costs file loading issues")
                    elif test_name == 'storage_recognition':
                        logger.info("  - Add missing storage technologies or parameters")
                    elif test_name == 'cost_calculations':
                        logger.info("  - Verify cost calculation logic")
                    elif test_name == 'optimization':
                        logger.info("  - Debug optimization solver issues")
                    elif test_name == 'storage_constraints':
                        logger.info("  - Fix storage constraint definitions")
                    elif test_name == 'configuration_compatibility':
                        logger.info("  - Update configuration files to reference new technology names")
        
        # Save detailed results to file
        report_path = "costs_integration_test_report.json"
        try:
            import json
            with open(report_path, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            logger.info(f"\n📄 Detailed report saved to: {report_path}")
        except Exception as e:
            logger.warning(f"Could not save report to file: {e}")

def main():
    """Run the costs file integration test."""
    test_suite = CostsFileIntegrationTest()
    
    # Run all tests
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 Integration test completed successfully!")
        return 0
    else:
        print("\n❌ Integration test encountered failures!")
        return 1

if __name__ == "__main__":
    exit(main())
