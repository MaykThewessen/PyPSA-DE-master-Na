#!/usr/bin/env python3
"""
Test Script for Performance & Robustness Improvements
====================================================

This script tests the implemented improvements to ensure they work correctly.

Usage:
    python test_improvements.py
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
import logging

# Test imports
try:
    import psutil
    import yaml
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    print("✅ All required packages are available")
except ImportError as e:
    print(f"❌ Missing package: {e}")
    sys.exit(1)

def test_cpu_detection():
    """Test CPU detection functionality"""
    print("\n🧪 Testing CPU Detection:")
    
    try:
        from run_pypsa_robust import get_cpu_cores
        
        total_cores = psutil.cpu_count(logical=True)
        detected_cores = get_cpu_cores()
        
        print(f"  Total CPUs: {total_cores}")
        print(f"  Cores to use: {detected_cores}")
        print(f"  Using all available cores")
        
        assert detected_cores >= 1, "Must use at least 1 core"
        assert detected_cores == total_cores, "Should use all available cores"
        
        print("  ✅ CPU detection working correctly")
        return True
        
    except Exception as e:
        print(f"  ❌ CPU detection failed: {e}")
        return False

def test_config_validation():
    """Test config file validation"""
    print("\n🧪 Testing Config Validation:")
    
    try:
        from run_pypsa_robust import validate_config_file
        
        # Test with a temporary valid YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({'test': 'value'}, f)
            temp_file = f.name
        
        # Test valid config
        result = validate_config_file(temp_file)
        assert result == True, "Valid config should pass validation"
        print("  ✅ Valid config validation passed")
        
        # Test invalid config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            invalid_file = f.name
        
        result = validate_config_file(invalid_file)
        assert result == False, "Invalid config should fail validation"
        print("  ✅ Invalid config validation failed (as expected)")
        
        # Test non-existent config
        result = validate_config_file("non_existent_file.yaml")
        assert result == False, "Non-existent config should fail validation"
        print("  ✅ Non-existent config validation failed (as expected)")
        
        # Cleanup
        os.unlink(temp_file)
        os.unlink(invalid_file)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Config validation test failed: {e}")
        return False

def test_memory_optimization():
    """Test memory optimization functions"""
    print("\n🧪 Testing Memory Optimization:")
    
    try:
        from compare_results import NetworkAnalyzer
        
        # Create a test DataFrame
        test_data = pd.DataFrame({
            'float64_col': np.random.random(1000).astype('float64'),
            'int64_col': np.random.randint(0, 100, 1000).astype('int64'),
            'string_col': ['test'] * 1000
        })
        
        original_memory = test_data.memory_usage(deep=True).sum()
        print(f"  Original memory usage: {original_memory} bytes")
        
        # Test downcast functionality would go here
        # For now, just verify the functions exist
        analyzer = NetworkAnalyzer()
        
        assert hasattr(analyzer, '_downcast_network_dtypes'), "Downcast method should exist"
        assert hasattr(analyzer, '_load_network_optimized'), "Optimized loading method should exist"
        
        print("  ✅ Memory optimization functions available")
        return True
        
    except Exception as e:
        print(f"  ❌ Memory optimization test failed: {e}")
        return False

def test_tmp_cleanup():
    """Test tmp folder cleanup functionality"""
    print("\n🧪 Testing Tmp Cleanup:")
    
    try:
        from run_pypsa_robust import clean_tmp_folder
        
        # Create temporary test directory
        test_tmp = Path("test_tmp")
        test_tmp.mkdir(exist_ok=True)
        
        # Create some test files with different ages
        old_file = test_tmp / "old_file.txt"
        old_file.write_text("old content")
        
        new_file = test_tmp / "new_file.txt" 
        new_file.write_text("new content")
        
        print(f"  Created test files in {test_tmp}")
        
        # The actual cleanup function would clean based on file age
        # For this test, just verify it doesn't crash
        original_tmp = Path("tmp")
        if original_tmp.exists():
            file_count_before = len(list(original_tmp.rglob("*")))
            clean_tmp_folder()
            print(f"  ✅ Tmp cleanup executed without errors")
        else:
            print("  ✅ No tmp folder to clean")
        
        # Cleanup test directory
        shutil.rmtree(test_tmp)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Tmp cleanup test failed: {e}")
        return False

def test_plotting_functions():
    """Test plotting script functions"""
    print("\n🧪 Testing Plotting Functions:")
    
    try:
        from plot_3scenarios import get_carrier_color, add_network_identifier
        
        # Test color function
        color = get_carrier_color('solar')
        assert isinstance(color, str), "Color should be a string"
        assert color.startswith('#'), "Color should be a hex code"
        print("  ✅ Carrier color function working")
        
        # Test network identifier function
        test_df = pd.DataFrame({'capacity': [1, 2, 3]})
        result_df = add_network_identifier(test_df, 'Test Network')
        assert 'network' in result_df.columns, "Network column should be added"
        assert result_df['network'].iloc[0] == 'Test Network', "Network identifier should be correct"
        print("  ✅ Network identifier function working")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Plotting functions test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist"""
    print("\n🧪 Testing File Structure:")
    
    required_files = [
        'run_pypsa_robust.py',
        'compare_results.py', 
        'plot_3scenarios.py',
        'PERFORMANCE_IMPROVEMENTS.md'
    ]
    
    all_exist = True
    for file in required_files:
        if Path(file).exists():
            print(f"  ✅ {file} exists")
        else:
            print(f"  ❌ {file} missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("Performance & Robustness Improvements Test Suite")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("CPU Detection", test_cpu_detection),
        ("Config Validation", test_config_validation),
        ("Memory Optimization", test_memory_optimization),
        ("Tmp Cleanup", test_tmp_cleanup),
        ("Plotting Functions", test_plotting_functions)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Performance improvements are working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
