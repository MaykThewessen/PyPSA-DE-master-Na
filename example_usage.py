#!/usr/bin/env python3
"""
Example usage of the HiGHS monitoring script
Demonstrates key features and functionality
"""

from monitor_highs import HiGHSMonitor, SolverMetrics
from datetime import datetime
import time

def demo_monitor_features():
    """Demonstrate the key features of the monitor"""
    
    print("🔍 HiGHS Monitor Feature Demonstration")
    print("=" * 50)
    
    # Create monitor instance
    monitor = HiGHSMonitor(history_length=20, stall_threshold=5)
    
    # Simulate some solver metrics
    sample_lines = [
        "      1  1.000000e+03  1.000000e+01  5.000000e+01",
        "      2  9.950000e+02  8.500000e+00  4.200000e+01", 
        "      3  9.900000e+02  7.200000e+00  3.500000e+01",
        "      4  9.850000e+02  6.100000e+00  2.900000e+01",
        "      5  9.800000e+02  5.200000e+00  2.400000e+01",
        "     10  9.500000e+02  2.100000e+00  1.100000e+01",
        "     15  9.200000e+02  8.500000e-01  4.200000e+00",
        "     20  9.000000e+02  3.400000e-01  1.700000e+00",
        "     25  8.950000e+02  1.400000e-01  6.800000e-01",
        "     30  8.920000e+02  5.700000e-02  2.700000e-01",
        "     35  8.900000e+02  2.300000e-02  1.100000e-01",
        "     40  8.890000e+02  9.400000e-03  4.400000e-02",
        "     45  8.885000e+02  3.800000e-03  1.800000e-02",
        "     50  8.882000e+02  1.500000e-03  7.200000e-03",
        "     55  8.880000e+02  6.200000e-04  2.900000e-03",
        "     60  8.879000e+02  2.500000e-04  1.200000e-03",
        "     65  8.878500e+02  1.000000e-04  4.800000e-04",
        "     70  8.878200e+02  4.100000e-05  1.900000e-04",
        "     75  8.878100e+02  1.700000e-05  7.800000e-05",
        "     80  8.878050e+02  6.900000e-06  3.100000e-05",
    ]
    
    print("\n📊 Parsing Sample Solver Output:")
    print("-" * 40)
    
    metrics_list = []
    for i, line in enumerate(sample_lines):
        metrics = monitor.parse_line(line)
        if metrics:
            monitor.metrics_history.append(metrics)
            metrics_list.append(metrics)
            
            # Show parsing result
            print(f"Line: {line}")
            print(f"  -> {metrics}")
            
            # Demonstrate convergence analysis every 5 iterations
            if i % 5 == 4 and len(monitor.metrics_history) >= 3:
                print(f"\n🔍 Analysis at iteration {metrics.iteration}:")
                
                # Analyze convergence
                convergence_stats = monitor.analyze_convergence(metrics)
                
                if convergence_stats.primal_rate:
                    print(f"  Primal convergence rate: {convergence_stats.primal_rate:.4f} log10/iter")
                if convergence_stats.dual_rate:
                    print(f"  Dual convergence rate: {convergence_stats.dual_rate:.4f} log10/iter")
                
                # Check for issues
                warnings = monitor.detect_issues(metrics, convergence_stats)
                if warnings:
                    print("  Warnings:")
                    for warning in warnings:
                        print(f"    {warning}")
                else:
                    print("  ✅ No issues detected")
                    
                # Estimate completion
                if convergence_stats.estimated_completion:
                    eta = convergence_stats.estimated_completion
                    remaining = eta - metrics.timestamp
                    print(f"  🎯 ETA: {eta.strftime('%H:%M:%S')} ({remaining} remaining)")
                
                print("-" * 40)
        
        # Small delay to simulate real-time processing
        time.sleep(0.1)
    
    print(f"\n📈 Final Analysis:")
    print(f"Total metrics parsed: {len(metrics_list)}")
    if metrics_list:
        final_metrics = metrics_list[-1]
        print(f"Final iteration: {final_metrics.iteration}")
        print(f"Final primal infeasibility: {final_metrics.primal_infeasibility:.6e}")
        print(f"Final dual infeasibility: {final_metrics.dual_infeasibility:.6e}")
        
        # Show convergence achieved
        if (final_metrics.primal_infeasibility < 1e-6 and 
            final_metrics.dual_infeasibility < 1e-6):
            print("🎉 Convergence achieved!")
        else:
            print("🔄 Still converging...")

def demo_status_detection():
    """Demonstrate status detection capabilities"""
    
    print("\n\n🏁 Status Detection Demo")
    print("=" * 30)
    
    monitor = HiGHSMonitor()
    
    status_lines = [
        "Model status: Optimal",
        "INFEASIBLE PROBLEM DETECTED",
        "Time limit reached",
        "Numerical instability detected",
        "Model status: Unbounded"
    ]
    
    for line in status_lines:
        print(f"Testing: '{line}'")
        if monitor.check_final_status(line):
            print("  -> ✅ Status detected!")
        else:
            print("  -> ❌ No status detected")

if __name__ == "__main__":
    demo_monitor_features()
    demo_status_detection()
    
    print(f"\n🎯 Demo Complete!")
    print("Run 'python test_monitor.py' for a full real-time test")
    print("Use 'python monitor_highs.py --help' for usage information")
