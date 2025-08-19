#!/usr/bin/env python3
"""
Solver Benchmark Script for PyPSA-DE

This script helps compare solver performance across different configurations.
Run this to optimize your solver settings for your specific use case.
"""

import time
import psutil
import pypsa
import pandas as pd
from pathlib import Path

def benchmark_solver_config(network_path: str, solver_configs: dict) -> pd.DataFrame:
    """
    Benchmark different solver configurations on the same network.
    
    Parameters
    ----------
    network_path : str
        Path to the network file to solve
    solver_configs : dict
        Dictionary of solver configurations to test
        
    Returns
    -------
    pd.DataFrame
        Results table with timing and memory usage
    """
    results = []
    
    for config_name, config in solver_configs.items():
        print(f"Testing configuration: {config_name}")
        
        # Load fresh network for each test
        n = pypsa.Network(network_path)
        
        # Monitor memory and time
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024**3  # GB
        start_time = time.time()
        
        try:
            # Solve with current configuration
            status, condition = n.optimize(
                solver_name=config['solver_name'],
                solver_options=config.get('solver_options', {}),
                linearized_unit_commitment=config.get('linearized_unit_commitment', True),
            )
            
            end_time = time.time()
            end_memory = process.memory_info().rss / 1024**3  # GB
            
            results.append({
                'config_name': config_name,
                'solver_name': config['solver_name'],
                'status': status,
                'condition': condition,
                'solve_time_seconds': end_time - start_time,
                'memory_peak_gb': end_memory,
                'memory_increase_gb': end_memory - start_memory,
                'objective_value': n.objective if hasattr(n, 'objective') else None,
                'success': status == 'ok'
            })
            
        except Exception as e:
            results.append({
                'config_name': config_name,
                'solver_name': config['solver_name'],
                'status': 'error',
                'condition': str(e),
                'solve_time_seconds': None,
                'memory_peak_gb': None,
                'memory_increase_gb': None,
                'objective_value': None,
                'success': False
            })
        
        print(f"  Status: {results[-1]['status']}")
        if results[-1]['success']:
            print(f"  Time: {results[-1]['solve_time_seconds']:.1f}s")
            print(f"  Memory: {results[-1]['memory_peak_gb']:.2f} GB")
    
    return pd.DataFrame(results)

def get_test_configurations():
    """Define solver configurations to benchmark."""
    
    # HiGHS configurations with different thread counts
    highs_base = {
        'threads': 8,
        'presolve': 'on',
        'parallel': 'on',
        'time_limit': 3600,  # 1 hour
        'primal_feasibility_tolerance': 1e-6,
        'dual_feasibility_tolerance': 1e-6,
    }
    
    configs = {
        'HiGHS_8_threads': {
            'solver_name': 'highs',
            'solver_options': {**highs_base, 'threads': 8},
            'linearized_unit_commitment': True
        },
        'HiGHS_16_threads': {
            'solver_name': 'highs', 
            'solver_options': {**highs_base, 'threads': 16},
            'linearized_unit_commitment': True
        },
        'HiGHS_aggressive': {
            'solver_name': 'highs',
            'solver_options': {
                **highs_base, 
                'threads': 16,
                'primal_feasibility_tolerance': 1e-4,  # Looser tolerance
                'dual_feasibility_tolerance': 1e-4,
            },
            'linearized_unit_commitment': True
        }
    }
    
    # Add SCIP if available for comparison
    configs['SCIP_comparison'] = {
        'solver_name': 'scip',
        'solver_options': {
            'limits/time': 3600,
            'numerics/feastol': 1e-6,
        },
        'linearized_unit_commitment': True
    }
    
    # Add GLPK as baseline (should be slower)
    configs['GLPK_baseline'] = {
        'solver_name': 'glpk',
        'solver_options': {},
        'linearized_unit_commitment': True
    }
    
    return configs

if __name__ == "__main__":
    # Example usage - replace with your actual network path
    network_path = "results/test-elec/networks/base_s_6_elec_.nc"
    
    if not Path(network_path).exists():
        print(f"Network file not found: {network_path}")
        print("Please run a test optimization first or adjust the path.")
        exit(1)
    
    configs = get_test_configurations()
    results_df = benchmark_solver_config(network_path, configs)
    
    # Display results
    print("\n" + "="*80)
    print("SOLVER BENCHMARK RESULTS")
    print("="*80)
    
    # Sort by successful runs first, then by solve time
    results_df['sort_key'] = results_df['success'].astype(int) * 1000 - results_df['solve_time_seconds'].fillna(9999)
    results_df = results_df.sort_values('sort_key', ascending=False).drop('sort_key', axis=1)
    
    for _, row in results_df.iterrows():
        print(f"\n{row['config_name']} ({row['solver_name']}):")
        print(f"  Success: {row['success']}")
        if row['success']:
            print(f"  Solve Time: {row['solve_time_seconds']:.1f} seconds")
            print(f"  Peak Memory: {row['memory_peak_gb']:.2f} GB")
            print(f"  Objective: {row['objective_value']:,.0f}")
        else:
            print(f"  Error: {row['condition']}")
    
    # Save detailed results
    results_df.to_csv('solver_benchmark_results.csv', index=False)
    print(f"\nDetailed results saved to: solver_benchmark_results.csv")
