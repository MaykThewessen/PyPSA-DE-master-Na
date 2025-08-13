# HiGHS Solver Monitor

A comprehensive Python script for real-time monitoring of HiGHS solver output with health indicators, convergence analysis, and issue detection.

## Features

### Core Monitoring Capabilities
- **Real-time parsing** of HiGHS solver output from files or stdin
- **Key metrics extraction**: iteration count, primal/dual infeasibility, objective value
- **Convergence rate calculation** using linear regression on log scale
- **Time-to-completion estimation** based on convergence trends
- **Solver health indicators** with color-coded status updates

### Health Monitoring & Warnings
- **Stalling detection**: Identifies when progress has stopped
- **Convergence rate analysis**: Detects slow convergence patterns  
- **Numerical stability warnings**: Alerts for very large infeasibilities
- **Progress monitoring**: Tracks iteration rates and timing

### Advanced Analytics
- **Historical trend analysis** with configurable history length
- **Multi-metric convergence tracking** (primal, dual, objective)
- **Automated completion time estimation**
- **Final optimization statistics summary**

## Usage

### Command Line Interface

```bash
# Monitor from log file
python monitor_highs.py solver.log

# Monitor from stdin (pipe solver output)
highs_solver problem.mps | python monitor_highs.py

# Monitor with custom settings
python monitor_highs.py --history 100 --stall-threshold 50 solver.log

# Show help
python monitor_highs.py --help
```

### Parameters

- `logfile`: HiGHS log file to monitor (optional, defaults to stdin)
- `--history`: Number of iterations to keep in history (default: 50)
- `--stall-threshold`: Number of iterations to detect stalling (default: 20)

## Output Format

The monitor provides comprehensive status updates including:

```
🔍 HiGHS Solver Monitor - 14:23:15
================================================================================
📊 Current Metrics:
   Iter:     45 | Primal Inf: 1.234567e-03 | Dual Inf: 5.678901e-04 | Objective: 1.234567e+02

⏱️  Runtime: 0:00:12.345678
   Iterations/sec: 3.64

📈 Convergence Analysis:
   Primal convergence rate: -0.2341 log10/iter
   Dual convergence rate: -0.1876 log10/iter
   Objective convergence rate: -0.0532 log10/iter

🎯 Estimated Completion:
   ETA: 14:24:32
   Time remaining: 0:01:17.234567
   Iterations remaining: ~87

💚 Solver Health:
   🔄 Converging to feasible solution

✅ No issues detected
================================================================================
```

## Supported HiGHS Output Formats

The monitor automatically detects and parses various HiGHS output formats:

### Standard Simplex Output
```
   Iter     Objective    Primal Inf   Dual Inf
      1  1.234567e+02  1.234567e-01  5.678901e-02
```

### Interior Point Method Output
```
   Iter     Objective    Primal Inf   Dual Inf    Compl Gap
      1  1.234567e+02  1.234567e-01  5.678901e-02  1.000000e-03
```

### Alternative Formats
```
Iteration 1 Primal infeasibility 1.234567e-01 Dual infeasibility 5.678901e-02
```

## Health Indicators

### Status Messages
- ✅ **Both primal and dual feasible**: Solution found
- 🔄 **Converging to feasible solution**: Normal progress
- ✅ **Primal feasible, 🔄 Dual converging**: Primal constraints satisfied
- ✅ **Dual feasible, 🔄 Primal converging**: Dual constraints satisfied

### Warning Types
- ⚠️  **Primal/Dual infeasibility stalling**: No progress in reducing infeasibilities
- 🐌 **Slow convergence rate detected**: Convergence rate is below expected threshold
- ⚠️  **Very large infeasibilities detected**: Possible numerical issues
- ⏱️  **No progress updates received**: Solver may have stopped

## Convergence Analysis

### Rate Calculation
The monitor calculates convergence rates using linear regression on a logarithmic scale:
- **Primal/Dual rates**: log10(infeasibility) vs iteration number
- **Objective rate**: log10(relative_change) vs iteration number

### Completion Estimation
Time-to-completion estimates are based on:
1. Current convergence rates for primal and dual infeasibilities
2. Target tolerance (typically 1e-6)
3. Historical iteration timing
4. Conservative estimation with safety margins

## Testing

Run the included test script to see the monitor in action:

```bash
python test_monitor.py
```

This will:
- Generate simulated HiGHS solver output
- Demonstrate real-time monitoring capabilities
- Show convergence analysis and health indicators
- Include simulated stalling periods and warnings

## Requirements

- Python 3.6+
- Standard library modules only (no external dependencies)

## Integration Examples

### With HiGHS Command Line
```bash
# Direct piping
highs --solver=ipm problem.mps | python monitor_highs.py

# Log to file and monitor simultaneously
highs problem.mps 2>&1 | tee solver.log | python monitor_highs.py
```

### With Python HiGHS Interface
```python
import subprocess
import threading

# Start solver with logging
solver_process = subprocess.Popen(
    ['highs', 'problem.mps'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True
)

# Start monitor in separate thread
monitor_process = subprocess.Popen(
    ['python', 'monitor_highs.py'],
    stdin=solver_process.stdout
)
```

## Advanced Usage

### Custom Monitoring Scripts
The `HiGHSMonitor` class can be imported and customized:

```python
from monitor_highs import HiGHSMonitor

# Create custom monitor
monitor = HiGHSMonitor(history_length=100, stall_threshold=30)

# Custom callback for metrics
def my_callback(metrics, stats, warnings):
    # Your custom logic here
    pass

# Monitor with callback
monitor.monitor_stream(sys.stdin)
```

### Configuration Options
- Adjust `history_length` for longer/shorter trend analysis
- Modify `stall_threshold` for earlier/later stalling detection
- Customize warning thresholds in the `detect_issues` method
- Add custom status patterns for specific solver versions

## Troubleshooting

### Common Issues

1. **No output detected**
   - Ensure HiGHS is configured for verbose output
   - Check that log file exists and is being written to
   - Verify file permissions

2. **Parsing failures**
   - HiGHS output format may vary between versions
   - Check regex patterns in `iteration_patterns`
   - Enable debug output to see raw lines

3. **Incorrect convergence estimates**
   - Estimates are based on recent history
   - Early iterations may have poor estimates
   - Non-linear convergence patterns affect accuracy

### Debug Mode
Enable additional output by modifying the script:
```python
# Uncomment in monitor_stream method
if line and not line.startswith('#'):
    print(f"Log: {line}")
```

## License

This script is provided as-is for monitoring HiGHS solver optimization progress. Feel free to modify and adapt for your specific needs.
