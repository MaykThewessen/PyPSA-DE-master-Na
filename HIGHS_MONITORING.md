# HiGHS Real-Time Monitoring Integration

This repository now includes **real-time monitoring** for HiGHS solver optimization runs. The monitoring provides live updates on solver progress, health indicators, and estimated completion times.

## 🚀 Features

- **Live Progress Tracking**: Monitor iterations, objective values, and convergence in real-time
- **Health Indicators**: Detect stalling, infeasibilities, and slow progress
- **ETA Estimation**: Smart completion time predictions based on convergence trends
- **Automatic Integration**: Seamlessly starts and stops with PyPSA-EUR solve runs

## 🔧 Quick Start

### Automatic Mode (Default)
The monitoring is automatically enabled in PyPSA-EUR when using HiGHS solver. Configure in `config/config.default.yaml`:

```yaml
solving:
  solver:
    name: highs          # Use HiGHS solver
    
  monitoring:            # Real-time monitoring configuration
    enable: true         # Enable monitoring (default: true)
    update_interval: 2.0 # Update frequency in seconds
    auto_start: true     # Auto-start with solver (default: true)
```

### Manual Mode
You can also run the monitoring manually for any HiGHS log file:

```bash
# Monitor a specific log file
python monitor_highs.py solver.log

# Monitor with custom update interval
python monitor_highs.py solver.log --interval 1.0

# Auto-detect the latest log file
python monitor_highs.py
```

## 📊 Monitoring Display

The real-time monitor shows:

```
🚀 HiGHS Optimization Monitor Started
===============================================================================================
    Time     Iter       Objective       Primal         Dual        ETA Status
-----------------------------------------------------------------------------------------------
🔧 Presolve: 300 rows, 400 cols removed
    0.5s        1        1.23e+08     0.123400     0.023450         2s 🟡 HIGH DUAL INFEASIBILITY
         ⚠️  Primal infeas: 1.23e-01
         ⚠️  Dual infeas: 2.34e-02
    1.0s       15        1.15e+08     0.001234     0.000987         3s 🟢 HEALTHY
    1.5s       28        1.12e+08     0.000012     0.000009         2s 🟢 HEALTHY
🎉 OPTIMAL SOLUTION FOUND!
```

### Status Indicators

- 🟢 **HEALTHY**: Normal progress
- 🟡 **WARNING**: Issues detected (stalling, high infeasibilities, slow progress)
- ⚠️  **Specific warnings** with detailed metrics

## 🏗️ Integration Details

### PyPSA-EUR Integration
The monitoring is integrated directly into `scripts/solve_network.py`:

1. **Automatic Detection**: Only activates when solver is "highs"
2. **Configuration-Driven**: Respects monitoring settings in config files
3. **Background Process**: Runs as separate subprocess to avoid interference
4. **Graceful Cleanup**: Always terminates monitoring when solver completes

### Key Integration Points

```python
# In solve_network() function:
monitor_process = None
if kwargs["solver_name"].lower() == "highs":
    log_file = kwargs.get("log_fn", "solver.log")
    if log_file:
        monitor_process = start_highs_monitor(log_file, config)

try:
    # PyPSA optimization runs here
    status, condition = n.optimize(**kwargs)
finally:
    # Always stop monitoring
    stop_highs_monitor(monitor_process)
```

## ⚙️ Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `enable` | `true` | Master switch for monitoring |
| `update_interval` | `2.0` | Update frequency in seconds |
| `auto_start` | `true` | Automatically start with solver |

## 🧪 Testing

Test the monitoring integration:

```bash
python test_monitoring_integration.py
```

This creates a simple PyPSA network and solves it with monitoring enabled to verify everything works.

## 📋 Requirements

- Python 3.8+
- PyPSA with HiGHS solver
- Unicode-capable terminal (for emoji indicators)

## 🐛 Troubleshooting

### Common Issues

1. **"Monitor script not found"**
   - Ensure `monitor_highs.py` is in the same directory as `solve_network.py`

2. **Unicode encoding errors on Windows**
   - Fixed in v2.0+ with automatic UTF-8 encoding configuration

3. **Monitoring doesn't start**
   - Check that `solver_name` is set to "highs" (case-insensitive)
   - Verify `monitoring.enable` is `true` in config

### Debug Mode

To see detailed monitoring startup information:

```yaml
logging:
  level: DEBUG
```

## 🔄 Version History

- **v2.0**: Windows compatibility, Unicode fix, automatic integration
- **v1.0**: Initial monitoring script with health indicators
- **v0.5**: Basic iteration tracking

## 🤝 Contributing

To enhance the monitoring:

1. **Add new health indicators** in `_assess_health()` method
2. **Improve ETA estimation** in `_estimate_completion_time()` method  
3. **Add support for other solvers** by extending pattern recognition

The monitoring system is designed to be easily extensible for additional solver types and metrics.
