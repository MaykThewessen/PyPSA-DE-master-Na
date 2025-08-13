#!/usr/bin/env python3
"""
HiGHS Solver Monitoring Script

This script monitors HiGHS solver output in real-time, extracts key metrics,
calculates convergence rates, estimates completion time, and displays solver
health indicators with warnings for potential issues.

Usage:
    python monitor_highs.py [log_file]
    
    If no log_file is provided, reads from stdin (useful for piping solver output)
    
Example:
    # Monitor from file
    python monitor_highs.py solver.log
    
    # Monitor from stdin (pipe solver output)
    highs_solver problem.mps | python monitor_highs.py
    
    # Monitor with custom settings
    python monitor_highs.py --history 100 --stall-threshold 50 solver.log
"""

import sys
import re
import time
import math
import argparse
import os
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timedelta


@dataclass
class SolverMetrics:
    """Container for solver metrics at a specific iteration"""
    iteration: int
    primal_infeasibility: float
    dual_infeasibility: float
    objective_value: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __str__(self):
        obj_str = f"{self.objective_value:.6e}" if self.objective_value is not None else "N/A"
        return (f"Iter: {self.iteration:6d} | "
                f"Primal Inf: {self.primal_infeasibility:.6e} | "
                f"Dual Inf: {self.dual_infeasibility:.6e} | "
                f"Objective: {obj_str}")


@dataclass 
class ConvergenceStats:
    """Statistics for convergence analysis"""
    primal_rate: Optional[float] = None
    dual_rate: Optional[float] = None
    objective_rate: Optional[float] = None
    estimated_completion: Optional[datetime] = None
    iterations_remaining: Optional[int] = None


class HiGHSMonitor:
    """Real-time monitor for HiGHS solver output"""
    
    def __init__(self, history_length: int = 50, stall_threshold: int = 20):
        self.history_length = history_length
        self.stall_threshold = stall_threshold
        self.metrics_history = deque(maxlen=history_length)
        self.start_time = datetime.now()
        self.last_update = datetime.now()
        
        # Regex patterns for parsing HiGHS output
        self.iteration_patterns = [
            # Pattern for simplex iterations with objective
            re.compile(r'\s*(\d+)\s+([+-]?\d+\.?\d*[eE]?[+-]?\d*)\s+([+-]?\d+\.?\d*[eE]?[+-]?\d*)\s+([+-]?\d+\.?\d*[eE]?[+-]?\d*)'),
            # Pattern for IPM iterations with more columns
            re.compile(r'\s*(\d+)\s+([+-]?\d+\.?\d*[eE]?[+-]?\d*)\s+([+-]?\d+\.?\d*[eE]?[+-]?\d*)\s+([+-]?\d+\.?\d*[eE]?[+-]?\d*)\s+([+-]?\d+\.?\d*[eE]?[+-]?\d*)'),
            # Alternative pattern for different output formats
            re.compile(r'Iteration\s+(\d+).*Primal\s+infeasibility\s+([+-]?\d+\.?\d*[eE]?[+-]?\d*).*Dual\s+infeasibility\s+([+-]?\d+\.?\d*[eE]?[+-]?\d*)'),
            # Compact format pattern
            re.compile(r'(\d+)\s+([+-]?\d+\.?\d*[eE]?[+-]?\d*)\s+([+-]?\d+\.?\d*[eE]?[+-]?\d*)'),
        ]
        
        # Status patterns
        self.status_patterns = {
            'optimal': re.compile(r'Optimal|OPTIMAL|Model\s+status\s*:\s*Optimal', re.IGNORECASE),
            'infeasible': re.compile(r'Infeasible|INFEASIBLE|Model\s+status\s*:\s*Infeasible', re.IGNORECASE),
            'unbounded': re.compile(r'Unbounded|UNBOUNDED|Model\s+status\s*:\s*Unbounded', re.IGNORECASE),
            'numerical_issues': re.compile(r'numerical|instability|conditioning|ill.conditioned', re.IGNORECASE),
            'time_limit': re.compile(r'time.?limit|TIME.?LIMIT|Model\s+status\s*:\s*Time\s+limit', re.IGNORECASE),
            'iteration_limit': re.compile(r'iteration.?limit|ITERATION.?LIMIT', re.IGNORECASE),
        }

    def parse_line(self, line: str) -> Optional[SolverMetrics]:
        """Parse a single line of HiGHS output"""
        line = line.strip()
        if not line:
            return None
            
        # Try each pattern to extract metrics
        for pattern in self.iteration_patterns:
            match = pattern.search(line)
            if match:
                groups = match.groups()
                try:
                    iteration = int(groups[0])
                    
                    if len(groups) >= 4:
                        # Standard format: iteration, objective, primal_inf, dual_inf
                        objective = self._safe_float(groups[1])
                        primal_inf = self._safe_float(groups[2])
                        dual_inf = self._safe_float(groups[3])
                    elif len(groups) == 3:
                        # Alternative format: iteration, primal_inf, dual_inf
                        primal_inf = self._safe_float(groups[1])
                        dual_inf = self._safe_float(groups[2])
                        objective = None
                    else:
                        continue
                        
                    if primal_inf is None or dual_inf is None:
                        continue
                        
                    return SolverMetrics(
                        iteration=iteration,
                        primal_infeasibility=primal_inf,
                        dual_infeasibility=dual_inf,
                        objective_value=objective
                    )
                except (ValueError, IndexError):
                    continue
        
        return None

    def _safe_float(self, value: str) -> Optional[float]:
        """Safely convert string to float"""
        if not value or value == '-' or value == 'N/A':
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def calculate_convergence_rate(self, values: List[float], iterations: List[int]) -> Optional[float]:
        """Calculate convergence rate using linear regression on log scale"""
        if len(values) < 3:
            return None
            
        # Filter out zero/negative values and convert to log scale
        log_values = []
        iter_values = []
        for i, val in enumerate(values):
            if val > 1e-16:  # Avoid log of very small numbers
                log_values.append(math.log10(val))
                iter_values.append(iterations[i])
        
        if len(log_values) < 3:
            return None
            
        # Simple linear regression: log(value) = a * iteration + b
        n = len(log_values)
        sum_x = sum(iter_values)
        sum_y = sum(log_values)
        sum_xy = sum(x * y for x, y in zip(iter_values, log_values))
        sum_x2 = sum(x * x for x in iter_values)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if abs(denominator) < 1e-12:
            return None
            
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope

    def estimate_completion(self, current_metrics: SolverMetrics, 
                          convergence_stats: ConvergenceStats) -> Optional[datetime]:
        """Estimate time to completion based on convergence rates"""
        if not convergence_stats.primal_rate or not convergence_stats.dual_rate:
            return None
            
        tolerance = 1e-6  # Typical solver tolerance
        
        # Estimate iterations needed for both primal and dual to reach tolerance
        primal_iterations = None
        dual_iterations = None
        
        if current_metrics.primal_infeasibility > tolerance and convergence_stats.primal_rate < 0:
            try:
                log_current_primal = math.log10(current_metrics.primal_infeasibility)
                log_tolerance = math.log10(tolerance)
                primal_iterations = (log_tolerance - log_current_primal) / convergence_stats.primal_rate
            except (ValueError, ZeroDivisionError):
                pass
            
        if current_metrics.dual_infeasibility > tolerance and convergence_stats.dual_rate < 0:
            try:
                log_current_dual = math.log10(current_metrics.dual_infeasibility)
                log_tolerance = math.log10(tolerance)
                dual_iterations = (log_tolerance - log_current_dual) / convergence_stats.dual_rate
            except (ValueError, ZeroDivisionError):
                pass
        
        # Take the maximum iterations needed
        iterations_needed = None
        if primal_iterations is not None and dual_iterations is not None:
            iterations_needed = max(primal_iterations, dual_iterations)
        elif primal_iterations is not None:
            iterations_needed = primal_iterations
        elif dual_iterations is not None:
            iterations_needed = dual_iterations
            
        if iterations_needed is None or iterations_needed <= 0:
            return None
            
        # Estimate time per iteration
        if len(self.metrics_history) < 2:
            return None
            
        total_iterations = current_metrics.iteration - self.metrics_history[0].iteration
        total_time = (current_metrics.timestamp - self.metrics_history[0].timestamp).total_seconds()
        
        if total_iterations <= 0 or total_time <= 0:
            return None
            
        time_per_iteration = total_time / total_iterations
        estimated_seconds = iterations_needed * time_per_iteration
        
        convergence_stats.iterations_remaining = int(iterations_needed)
        return current_metrics.timestamp + timedelta(seconds=estimated_seconds)

    def analyze_convergence(self, current_metrics: SolverMetrics) -> ConvergenceStats:
        """Analyze convergence rates and estimate completion time"""
        stats = ConvergenceStats()
        
        if len(self.metrics_history) < 3:
            return stats
            
        # Extract recent values for analysis
        recent_metrics = list(self.metrics_history)[-min(20, len(self.metrics_history)):]
        
        primal_values = [m.primal_infeasibility for m in recent_metrics if m.primal_infeasibility > 0]
        dual_values = [m.dual_infeasibility for m in recent_metrics if m.dual_infeasibility > 0]
        iterations = [m.iteration for m in recent_metrics]
        
        # Calculate convergence rates
        if primal_values:
            stats.primal_rate = self.calculate_convergence_rate(primal_values, iterations[-len(primal_values):])
        if dual_values:
            stats.dual_rate = self.calculate_convergence_rate(dual_values, iterations[-len(dual_values):])
            
        # Calculate objective convergence rate if available
        objective_values = [m.objective_value for m in recent_metrics if m.objective_value is not None]
        if len(objective_values) > 3:
            # For objectives, we look at relative changes
            relative_changes = []
            for i in range(1, len(objective_values)):
                if abs(objective_values[i-1]) > 1e-12:
                    rel_change = abs((objective_values[i] - objective_values[i-1]) / objective_values[i-1])
                    if rel_change > 1e-16:
                        relative_changes.append(rel_change)
            if relative_changes:
                stats.objective_rate = self.calculate_convergence_rate(
                    relative_changes, iterations[-len(relative_changes):]
                )
        
        # Estimate completion time
        stats.estimated_completion = self.estimate_completion(current_metrics, stats)
        
        return stats

    def detect_issues(self, current_metrics: SolverMetrics, 
                     convergence_stats: ConvergenceStats) -> List[str]:
        """Detect potential solver issues"""
        warnings = []
        
        # Check for stalling
        if len(self.metrics_history) >= self.stall_threshold:
            recent_metrics = list(self.metrics_history)[-self.stall_threshold:]
            
            # Check primal infeasibility stalling
            primal_values = [m.primal_infeasibility for m in recent_metrics]
            if len(set(f"{v:.6e}" for v in primal_values)) <= 3:
                warnings.append("⚠️  Primal infeasibility appears to be stalling")
            
            # Check dual infeasibility stalling
            dual_values = [m.dual_infeasibility for m in recent_metrics]
            if len(set(f"{v:.6e}" for v in dual_values)) <= 3:
                warnings.append("⚠️  Dual infeasibility appears to be stalling")
        
        # Check for slow convergence
        if convergence_stats.primal_rate is not None and convergence_stats.primal_rate > -0.1:
            warnings.append("🐌 Slow primal convergence rate detected")
        if convergence_stats.dual_rate is not None and convergence_stats.dual_rate > -0.1:
            warnings.append("🐌 Slow dual convergence rate detected")
        
        # Check for numerical issues
        if current_metrics.primal_infeasibility > 1e10 or current_metrics.dual_infeasibility > 1e10:
            warnings.append("⚠️  Very large infeasibilities detected - possible numerical issues")
        
        # Check for very slow progress
        if len(self.metrics_history) > 10:
            recent_time = (current_metrics.timestamp - self.last_update).total_seconds()
            if recent_time > 30:  # No update for 30 seconds
                warnings.append("⏱️  No progress updates received recently")
        
        return warnings

    def display_status(self, current_metrics: SolverMetrics, 
                      convergence_stats: ConvergenceStats, warnings: List[str]):
        """Display current solver status"""
        print("\n" + "="*80)
        print(f"🔍 HiGHS Solver Monitor - {current_metrics.timestamp.strftime('%H:%M:%S')}")
        print("="*80)
        
        # Current metrics
        print(f"📊 Current Metrics:")
        print(f"   {current_metrics}")
        
        # Runtime information
        runtime = current_metrics.timestamp - self.start_time
        print(f"\n⏱️  Runtime: {runtime}")
        
        if len(self.metrics_history) > 1:
            iter_per_sec = current_metrics.iteration / runtime.total_seconds()
            print(f"   Iterations/sec: {iter_per_sec:.2f}")
        
        # Convergence analysis
        print(f"\n📈 Convergence Analysis:")
        if convergence_stats.primal_rate is not None:
            print(f"   Primal convergence rate: {convergence_stats.primal_rate:.4f} log10/iter")
        if convergence_stats.dual_rate is not None:
            print(f"   Dual convergence rate: {convergence_stats.dual_rate:.4f} log10/iter")
        if convergence_stats.objective_rate is not None:
            print(f"   Objective convergence rate: {convergence_stats.objective_rate:.4f} log10/iter")
        
        # Time estimation
        if convergence_stats.estimated_completion:
            eta = convergence_stats.estimated_completion
            time_remaining = eta - current_metrics.timestamp
            print(f"\n🎯 Estimated Completion:")
            print(f"   ETA: {eta.strftime('%H:%M:%S')}")
            print(f"   Time remaining: {time_remaining}")
            if convergence_stats.iterations_remaining:
                print(f"   Iterations remaining: ~{convergence_stats.iterations_remaining}")
        
        # Health indicators
        print(f"\n💚 Solver Health:")
        if current_metrics.primal_infeasibility < 1e-6 and current_metrics.dual_infeasibility < 1e-6:
            print("   ✅ Both primal and dual feasible")
        elif current_metrics.primal_infeasibility < 1e-6:
            print("   ✅ Primal feasible, 🔄 Dual converging")
        elif current_metrics.dual_infeasibility < 1e-6:
            print("   ✅ Dual feasible, 🔄 Primal converging") 
        else:
            print("   🔄 Converging to feasible solution")
        
        # Warnings
        if warnings:
            print(f"\n🚨 Warnings:")
            for warning in warnings:
                print(f"   {warning}")
        else:
            print(f"\n✅ No issues detected")
        
        print("="*80)

    def check_final_status(self, line: str) -> bool:
        """Check if line indicates solver completion"""
        for status_name, pattern in self.status_patterns.items():
            if pattern.search(line):
                print(f"\n🏁 Solver completed with status: {status_name.upper()}")
                return True
        return False

    def monitor_stream(self, input_stream):
        """Monitor solver output from stream"""
        print("🚀 Starting HiGHS solver monitoring...")
        print("📡 Waiting for solver output...\n")
        
        try:
            line_count = 0
            for line in input_stream:
                line = line.strip()
                line_count += 1
                
                # Check for final status
                if self.check_final_status(line):
                    break
                
                # Parse metrics
                metrics = self.parse_line(line)
                if metrics:
                    self.metrics_history.append(metrics)
                    self.last_update = datetime.now()
                    
                    # Analyze convergence
                    convergence_stats = self.analyze_convergence(metrics)
                    
                    # Detect issues
                    warnings = self.detect_issues(metrics, convergence_stats)
                    
                    # Display status every 10 iterations or if warnings
                    if metrics.iteration % 10 == 0 or warnings:
                        self.display_status(metrics, convergence_stats, warnings)
                
                # Print original line for reference (optional, can be disabled for cleaner output)
                # if line and not line.startswith('#'):
                #     print(f"Log: {line}")
                    
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Error during monitoring: {e}")
        finally:
            # Final summary
            if self.metrics_history:
                final_metrics = self.metrics_history[-1]
                total_runtime = final_metrics.timestamp - self.start_time
                print(f"\n📋 Final Summary:")
                print(f"   Total iterations: {final_metrics.iteration}")
                print(f"   Total runtime: {total_runtime}")
                print(f"   Final primal infeasibility: {final_metrics.primal_infeasibility:.6e}")
                print(f"   Final dual infeasibility: {final_metrics.dual_infeasibility:.6e}")
                if final_metrics.objective_value is not None:
                    print(f"   Final objective value: {final_metrics.objective_value:.6e}")

    def monitor_file(self, filename: str):
        """Monitor solver output from file"""
        try:
            # Check if file exists
            if not os.path.exists(filename):
                print(f"⏳ Waiting for file '{filename}' to be created...")
                while not os.path.exists(filename):
                    time.sleep(1)
                print(f"✅ File '{filename}' found!")
            
            # Monitor file for changes
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                # Read existing content first
                for line in f:
                    metrics = self.parse_line(line)
                    if metrics:
                        self.metrics_history.append(metrics)
                
                # Monitor for new content
                while True:
                    line = f.readline()
                    if line:
                        line = line.strip()
                        if self.check_final_status(line):
                            break
                        
                        metrics = self.parse_line(line)
                        if metrics:
                            self.metrics_history.append(metrics)
                            self.last_update = datetime.now()
                            
                            convergence_stats = self.analyze_convergence(metrics)
                            warnings = self.detect_issues(metrics, convergence_stats)
                            
                            if metrics.iteration % 10 == 0 or warnings:
                                self.display_status(metrics, convergence_stats, warnings)
                    else:
                        time.sleep(1)  # Wait for more content
                        
        except FileNotFoundError:
            print(f"❌ Error: File '{filename}' not found")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            sys.exit(1)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Monitor HiGHS solver output in real-time',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Monitor from file
    python monitor_highs.py solver.log
    
    # Monitor from stdin (pipe solver output)
    highs_solver problem.mps | python monitor_highs.py
    
    # Monitor with custom settings
    python monitor_highs.py --history 100 --stall-threshold 50 solver.log
        """
    )
    
    parser.add_argument('logfile', nargs='?', 
                       help='HiGHS log file to monitor (default: read from stdin)')
    parser.add_argument('--history', type=int, default=50,
                       help='Number of iterations to keep in history (default: 50)')
    parser.add_argument('--stall-threshold', type=int, default=20,
                       help='Number of iterations to detect stalling (default: 20)')
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = HiGHSMonitor(
        history_length=args.history,
        stall_threshold=args.stall_threshold
    )
    
    # Start monitoring
    if args.logfile:
        monitor.monitor_file(args.logfile)
    else:
        monitor.monitor_stream(sys.stdin)


if __name__ == "__main__":
    main()
