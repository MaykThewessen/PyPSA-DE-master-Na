#!/usr/bin/env python
"""
Benchmark script for testing and comparing PyPSA-Eur model runs.

This script runs both a one-week slice and full-year model to benchmark:
- Model build time
- Presolve reductions  
- HiGHS warnings
- Memory usage
- Optimal objective value
- Infeasibilities and cost deltas

Usage:
    python benchmark_test.py
"""

import subprocess
import sys
import time
import os
import shutil
import logging
import json
import pandas as pd
import re
from pathlib import Path
from datetime import datetime
import psutil
import yaml

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('benchmark_results.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ModelBenchmark:
    """Class to handle model benchmarking operations."""
    
    def __init__(self):
        self.results = {}
        self.baseline_results = {}
        
    def run_snakemake(self, config_file, run_name, target_rule="solve_network"):
        """Run Snakemake with specified configuration."""
        logger.info(f"Starting {run_name} run with config: {config_file}")
        
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        # Backup original config if exists
        original_config = "config/config.yaml"
        backup_config = None
        if os.path.exists(original_config):
            backup_config = f"config/config.yaml.backup_{int(time.time())}"
            shutil.copy2(original_config, backup_config)
        
        try:
            # Copy test config as active config
            shutil.copy2(config_file, original_config)
            
            # Run Snakemake - targeting the solve_network rule specifically
            cmd = [
                "snakemake", 
                "--cores", "1",  # Use single core for consistent comparison
                "--forceall",    # Force rerun to ensure clean comparison
                "--quiet",       # Reduce output verbosity
                f"results/{run_name}/networks/base_s_37_elec_.nc"  # Target specific output file
            ]
            
            logger.info(f"Executing: {' '.join(cmd)}")
            
            # Capture both stdout and stderr
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=7200  # 2 hour timeout
            )
            
            end_time = time.time()
            end_memory = self.get_memory_usage()
            
            # Parse results
            build_time = end_time - start_time
            max_memory = max(start_memory, end_memory)  # Simple approximation
            
            # Extract solver information from logs
            solver_info = self.parse_solver_logs(run_name)
            
            # Collect metrics
            metrics = {
                'run_name': run_name,
                'config_file': config_file,
                'build_time_seconds': build_time,
                'build_time_minutes': build_time / 60,
                'memory_mb': max_memory,
                'return_code': result.returncode,
                'stdout_lines': len(result.stdout.splitlines()) if result.stdout else 0,
                'stderr_lines': len(result.stderr.splitlines()) if result.stderr else 0,
                'timestamp': datetime.now().isoformat(),
                **solver_info
            }
            
            # Save detailed logs
            self.save_run_output(run_name, result.stdout, result.stderr)
            
            if result.returncode != 0:
                logger.error(f"Run {run_name} failed with return code {result.returncode}")
                logger.error(f"STDERR: {result.stderr}")
            else:
                logger.info(f"Run {run_name} completed successfully in {build_time:.1f} seconds")
                # Try to extract objective value
                metrics['objective_value'] = self.extract_objective_value(run_name)
            
            return metrics
            
        except subprocess.TimeoutExpired:
            logger.error(f"Run {run_name} timed out after 2 hours")
            return {
                'run_name': run_name,
                'config_file': config_file,
                'error': 'timeout',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error running {run_name}: {str(e)}")
            return {
                'run_name': run_name,
                'config_file': config_file,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
        finally:
            # Restore original config
            if backup_config and os.path.exists(backup_config):
                shutil.copy2(backup_config, original_config)
                os.remove(backup_config)
            elif os.path.exists(original_config):
                os.remove(original_config)
    
    def get_memory_usage(self):
        """Get current memory usage in MB."""
        return psutil.virtual_memory().used / 1024 / 1024
    
    def save_run_output(self, run_name, stdout, stderr):
        """Save run output to files."""
        os.makedirs("benchmark_outputs", exist_ok=True)
        
        with open(f"benchmark_outputs/{run_name}_stdout.log", 'w') as f:
            f.write(stdout or "")
            
        with open(f"benchmark_outputs/{run_name}_stderr.log", 'w') as f:
            f.write(stderr or "")
    
    def parse_solver_logs(self, run_name):
        """Parse solver logs to extract presolve info and warnings."""
        solver_info = {
            'highs_warnings': 0,
            'presolve_reductions': {},
            'solver_status': 'unknown'
        }
        
        # Look for solver log files
        log_patterns = [
            f"results/{run_name}/logs/solve_network/*solver.log",
            f"results/logs/solve_network/*solver.log"
        ]
        
        import glob
        for pattern in log_patterns:
            log_files = glob.glob(pattern)
            for log_file in log_files:
                try:
                    with open(log_file, 'r') as f:
                        content = f.read()
                        
                    # Count HiGHS warnings
                    solver_info['highs_warnings'] = content.lower().count('warning')
                    
                    # Extract presolve information
                    presolve_match = re.search(r'Presolve : Reductions: rows (-?\d+)\(\d+\.\d+%\); columns (-?\d+)\(\d+\.\d+%\)', content)
                    if presolve_match:
                        solver_info['presolve_reductions'] = {
                            'rows_reduced': int(presolve_match.group(1)),
                            'columns_reduced': int(presolve_match.group(2))
                        }
                    
                    # Extract solver status
                    if 'Optimal' in content:
                        solver_info['solver_status'] = 'Optimal'
                    elif 'Infeasible' in content:
                        solver_info['solver_status'] = 'Infeasible'
                    elif 'Unbounded' in content:
                        solver_info['solver_status'] = 'Unbounded'
                        
                except Exception as e:
                    logger.warning(f"Could not parse solver log {log_file}: {e}")
        
        return solver_info
    
    def extract_objective_value(self, run_name):
        """Extract optimal objective value from network file."""
        try:
            import pypsa
            network_file = f"results/{run_name}/networks/base_s_37_elec_.nc"
            if os.path.exists(network_file):
                n = pypsa.Network(network_file)
                return float(n.objective)
        except Exception as e:
            logger.warning(f"Could not extract objective value for {run_name}: {e}")
        return None
    
    def compare_results(self, week_results, year_results):
        """Compare week slice vs full year results."""
        comparison = {
            'timestamp': datetime.now().isoformat(),
            'week_slice': week_results,
            'full_year': year_results,
            'comparison_metrics': {}
        }
        
        if week_results and year_results:
            # Time comparison
            week_time = week_results.get('build_time_seconds', 0)
            year_time = year_results.get('build_time_seconds', 0)
            if year_time > 0:
                comparison['comparison_metrics']['time_ratio'] = week_time / year_time
            
            # Memory comparison
            week_memory = week_results.get('memory_mb', 0)
            year_memory = year_results.get('memory_mb', 0)
            if year_memory > 0:
                comparison['comparison_metrics']['memory_ratio'] = week_memory / year_memory
            
            # Objective value comparison (if both available)
            week_obj = week_results.get('objective_value')
            year_obj = year_results.get('objective_value')
            if week_obj and year_obj:
                cost_delta_pct = abs(week_obj - year_obj) / year_obj * 100
                comparison['comparison_metrics']['cost_delta_percent'] = cost_delta_pct
                comparison['comparison_metrics']['cost_delta_significant'] = cost_delta_pct > 1.0
            
            # Solver status comparison
            comparison['comparison_metrics']['both_optimal'] = (
                week_results.get('solver_status') == 'Optimal' and 
                year_results.get('solver_status') == 'Optimal'
            )
            
            # Warning comparison
            comparison['comparison_metrics']['warnings_increased'] = (
                week_results.get('highs_warnings', 0) > year_results.get('highs_warnings', 0)
            )
        
        return comparison
    
    def save_results(self, comparison_data):
        """Save benchmark results to file."""
        results_file = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(results_file, 'w') as f:
            json.dump(comparison_data, f, indent=2)
        
        logger.info(f"Results saved to {results_file}")
        
        # Also create a summary
        self.create_summary_report(comparison_data, results_file.replace('.json', '_summary.txt'))
    
    def create_summary_report(self, data, filename):
        """Create a human-readable summary report."""
        with open(filename, 'w') as f:
            f.write("PyPSA-Eur Benchmark Test Results\n")
            f.write("=" * 40 + "\n\n")
            
            # Week slice results
            week = data.get('week_slice', {})
            if week:
                f.write("ONE WEEK SLICE RESULTS:\n")
                f.write(f"  Build time: {week.get('build_time_minutes', 'N/A'):.1f} minutes\n")
                f.write(f"  Memory usage: {week.get('memory_mb', 'N/A'):.1f} MB\n")
                f.write(f"  Solver status: {week.get('solver_status', 'Unknown')}\n")
                f.write(f"  HiGHS warnings: {week.get('highs_warnings', 'N/A')}\n")
                f.write(f"  Objective value: {week.get('objective_value', 'N/A')}\n")
                presolve = week.get('presolve_reductions', {})
                if presolve:
                    f.write(f"  Presolve reductions: {presolve.get('rows_reduced', 'N/A')} rows, {presolve.get('columns_reduced', 'N/A')} columns\n")
                f.write("\n")
            
            # Full year results  
            year = data.get('full_year', {})
            if year:
                f.write("FULL YEAR RESULTS:\n")
                f.write(f"  Build time: {year.get('build_time_minutes', 'N/A'):.1f} minutes\n")
                f.write(f"  Memory usage: {year.get('memory_mb', 'N/A'):.1f} MB\n")
                f.write(f"  Solver status: {year.get('solver_status', 'Unknown')}\n")
                f.write(f"  HiGHS warnings: {year.get('highs_warnings', 'N/A')}\n")
                f.write(f"  Objective value: {year.get('objective_value', 'N/A')}\n")
                presolve = year.get('presolve_reductions', {})
                if presolve:
                    f.write(f"  Presolve reductions: {presolve.get('rows_reduced', 'N/A')} rows, {presolve.get('columns_reduced', 'N/A')} columns\n")
                f.write("\n")
            
            # Comparison metrics
            comp = data.get('comparison_metrics', {})
            if comp:
                f.write("COMPARISON METRICS:\n")
                if 'time_ratio' in comp:
                    f.write(f"  Week/Year time ratio: {comp['time_ratio']:.3f}\n")
                if 'memory_ratio' in comp:
                    f.write(f"  Week/Year memory ratio: {comp['memory_ratio']:.3f}\n")
                if 'cost_delta_percent' in comp:
                    f.write(f"  Cost delta: {comp['cost_delta_percent']:.2f}%\n")
                    f.write(f"  Cost delta > 1%: {'YES' if comp.get('cost_delta_significant') else 'NO'}\n")
                f.write(f"  Both runs optimal: {'YES' if comp.get('both_optimal') else 'NO'}\n")
                f.write(f"  Warnings increased: {'YES' if comp.get('warnings_increased') else 'NO'}\n")
        
        logger.info(f"Summary report saved to {filename}")

def main():
    """Main function to run the benchmark tests."""
    logger.info("Starting PyPSA-Eur benchmark test")
    
    benchmark = ModelBenchmark()
    
    # Test configurations
    configs = {
        'week_slice': 'config/config.test-week.yaml',
        'baseline_full_year': 'config/config.default.yaml'
    }
    
    # Check that config files exist
    for name, config_file in configs.items():
        if not os.path.exists(config_file):
            logger.error(f"Configuration file not found: {config_file}")
            sys.exit(1)
    
    results = {}
    
    # Run week slice first (faster)
    logger.info("Running one-week slice test...")
    results['week_slice'] = benchmark.run_snakemake(
        configs['week_slice'], 
        'de-all-tech-2035-test-week'
    )
    
    # Run full year baseline
    logger.info("Running full-year baseline test...")
    results['full_year'] = benchmark.run_snakemake(
        configs['baseline_full_year'],
        'de-all-tech-2035-mayk'
    )
    
    # Compare results
    logger.info("Comparing results...")
    comparison_data = benchmark.compare_results(
        results['week_slice'], 
        results['full_year']
    )
    
    # Save results
    benchmark.save_results(comparison_data)
    
    # Print summary to console
    logger.info("\n" + "="*50)
    logger.info("BENCHMARK TEST SUMMARY")
    logger.info("="*50)
    
    week = results.get('week_slice', {})
    year = results.get('full_year', {})
    
    if week:
        logger.info(f"Week slice: {week.get('build_time_minutes', 'N/A'):.1f} min, "
                   f"{week.get('memory_mb', 'N/A'):.0f} MB, "
                   f"Status: {week.get('solver_status', 'Unknown')}")
    
    if year:
        logger.info(f"Full year: {year.get('build_time_minutes', 'N/A'):.1f} min, "
                   f"{year.get('memory_mb', 'N/A'):.0f} MB, "
                   f"Status: {year.get('solver_status', 'Unknown')}")
    
    comp = comparison_data.get('comparison_metrics', {})
    if comp:
        if 'cost_delta_percent' in comp:
            logger.info(f"Cost delta: {comp['cost_delta_percent']:.2f}% "
                       f"{'(>1% - SIGNIFICANT)' if comp.get('cost_delta_significant') else '(<1% - OK)'}")
        
        logger.info(f"Both optimal: {'YES' if comp.get('both_optimal') else 'NO'}")
        
        if comp.get('warnings_increased'):
            logger.warning("HiGHS warnings increased in week slice!")
    
    logger.info("Benchmark test completed!")

if __name__ == "__main__":
    main()
