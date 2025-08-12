#!/usr/bin/env python3
"""
Test script to load PyPSA networks with explicit netcdf4 engine
"""

import xarray as xr
import pypsa
import os

def test_network_loading():
    """Test loading networks with explicit netcdf4 engine"""
    
    # Define paths
    results_folder = "results/networks"
    networks = {'de-all-tech-2035-mayk': 'base_s_1___2035.nc'}
    
    print("Testing network loading with explicit netcdf4 engine...")
    
    network_objects = {}
    for name, file in networks.items():
        file_path = os.path.join(results_folder, file)
        print(f"Loading {file_path}...")
        
        try:
            # Method 1: Try loading directly with PyPSA (should work now with netcdf4 installed)
            print("  Method 1: Loading directly with PyPSA...")
            network_objects[name] = pypsa.Network(file_path)
            print(f"  ✓ Success! Network has {len(network_objects[name].buses)} buses")
            
        except Exception as e1:
            print(f"  ✗ Method 1 failed: {e1}")
            
            try:
                # Method 2: Load with xarray first, then PyPSA
                print("  Method 2: Loading with xarray first...")
                ds = xr.open_dataset(file_path, engine='netcdf4')
                print(f"  ✓ xarray dataset loaded with {len(ds.dims)} dimensions")
                
                # Convert dataset to PyPSA network
                network_objects[name] = pypsa.Network(ds)
                print(f"  ✓ Success! Network has {len(network_objects[name].buses)} buses")
                
            except Exception as e2:
                print(f"  ✗ Method 2 failed: {e2}")
                print("  Both methods failed. Check your NetCDF file and dependencies.")
                return False
    
    print("\nAll networks loaded successfully!")
    return True

if __name__ == "__main__":
    success = test_network_loading()
    if success:
        print("\n✅ Network loading test passed!")
    else:
        print("\n❌ Network loading test failed!")
