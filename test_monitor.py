#!/usr/bin/env python3
"""
Test script for HiGHS monitoring functionality
Simulates HiGHS solver output to demonstrate monitoring capabilities
"""

import time
import random
import math
import subprocess
import os

def generate_test_log():
    """Generate simulated HiGHS solver output"""
    
    # Create a test log file
    with open('test_solver.log', 'w') as f:
        # Write header
        f.write("HiGHS Solver Test Log\n")
        f.write("=====================\n\n")
        
        # Simulate preprocessing
        f.write("Presolve : Reductions: rows 1000(-50); columns 500(-25)\n")
        f.write("Starting simplex iterations...\n\n")
        
        # Column headers
        f.write("   Iter     Objective    Primal Inf   Dual Inf\n")
        f.write("-------  ------------  -----------  ----------\n")
        
        f.flush()
        
        # Simulate iterations with decreasing infeasibilities
        objective = 1000.0
        primal_inf = 1e2
        dual_inf = 5e2
        
        for i in range(1, 101):
            # Simulate convergence with some noise
            primal_inf *= 0.92 + 0.1 * random.random()
            dual_inf *= 0.94 + 0.08 * random.random()
            objective += random.uniform(-5, 5)
            
            # Add some stalling periods for demonstration
            if 30 <= i <= 35:
                primal_inf *= 1.01  # Slight stall
            if 60 <= i <= 65:
                dual_inf *= 1.005   # Slight stall
                
            # Write iteration line
            f.write(f"   {i:4d}  {objective:12.6e}  {primal_inf:.6e}  {dual_inf:.6e}\n")
            f.flush()
            
            # Sleep to simulate real-time progress
            time.sleep(0.2)
            
            # Break early if converged
            if primal_inf < 1e-6 and dual_inf < 1e-6:
                break
        
        # Write final status
        f.write("\nOptimization completed successfully\n")
        f.write("Model status: Optimal\n")
        f.write(f"Objective value: {objective:.8e}\n")

def run_monitor_test():
    """Run the monitor on the test log"""
    print("🧪 Starting HiGHS Monitor Test")
    print("===============================")
    print("This test will:")
    print("- Generate simulated HiGHS solver output")
    print("- Run the monitor script to analyze the output")
    print("- Demonstrate real-time monitoring capabilities\n")
    
    input("Press Enter to start the test...")
    
    try:
        # Start the monitor process
        monitor_process = subprocess.Popen(
            ['python', 'monitor_highs.py', 'test_solver.log'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Generate the test log in parallel
        generate_test_log()
        
        # Wait for monitor to finish and capture output
        output, _ = monitor_process.communicate(timeout=30)
        print(output)
        
    except subprocess.TimeoutExpired:
        monitor_process.kill()
        print("\n⏰ Test completed (timeout)")
    except KeyboardInterrupt:
        monitor_process.kill()
        print("\n🛑 Test stopped by user")
    except Exception as e:
        print(f"❌ Test error: {e}")
    finally:
        # Clean up test file
        if os.path.exists('test_solver.log'):
            os.remove('test_solver.log')
        print("\n🧹 Test cleanup completed")

if __name__ == "__main__":
    run_monitor_test()
