# HiGHS Live Monitoring Guide

## Quick Health Check Indicators

### 🟢 HEALTHY Signs
- **Iterations progressing steadily** (new iterations every few seconds)
- **Objective value improving** (decreasing for minimization, increasing for maximization)
- **Infeasibilities decreasing** (both primal and dual heading toward zero)
- **Reasonable iteration timing** (< 30 seconds per iteration for large problems)

### 🟡 WARNING Signs
- **STALLING**: Same iteration number for >10 seconds
- **HIGH INFEASIBILITIES**: Primal or dual infeasibility > 1e-3
- **SLOW PROGRESS**: >30 seconds per iteration consistently
- **MINIMAL IMPROVEMENT**: Objective change < 1e-8 for >100 iterations

### 🔴 CRITICAL Signs
- **Model status: Infeasible** - Problem has no feasible solution
- **Model status: Unbounded** - Objective can go to infinity
- **Very large infeasibilities** (> 1e-1) persisting
- **No progress for >5 minutes** on reasonably-sized problems

## Key HiGHS Output Columns

```
Iteration | Objective | Primal Infeas | Dual Infeas | Time
----------|-----------|---------------|-------------|------
    0     | 1.234e+06 |   1.23e-01   |  5.67e-02  |  0.1s
   100    | 1.233e+06 |   2.34e-03   |  1.23e-03  |  5.2s
   500    | 1.232e+06 |   4.56e-06   |  7.89e-07  | 25.1s
```

### What Each Column Means:

1. **Iteration**: Current iteration number (should increase steadily)
2. **Objective**: Current objective value (should improve toward optimum)
3. **Primal Infeasibility**: How much constraints are violated
   - Target: < 1e-6 (feasibility tolerance)
   - Warning: > 1e-3
   - Critical: > 1e-1
4. **Dual Infeasibility**: How much optimality conditions are violated
   - Target: < 1e-6 (optimality tolerance)
   - Warning: > 1e-3
   - Critical: > 1e-1

## Decision Tree for Live Monitoring

### First 10 minutes:
- ✅ **Iterations advancing?** → Continue monitoring
- ❌ **Stuck at presolve?** → Check problem formulation
- ❌ **Very high infeasibilities?** → Potential infeasible problem

### After 10+ minutes:
- ✅ **Objective improving + infeasibilities decreasing?** → Healthy progress
- ⚠️ **Objective stalled but infeasibilities decreasing?** → May need more time
- ⚠️ **Both stalled?** → Potential numerical issues
- ❌ **Infeasibilities increasing?** → Likely infeasible

### For Large Problems (>1M variables):
- **Expected**: 10-100+ seconds per iteration
- **Concerning**: No progress for 30+ minutes
- **Critical**: Memory issues or numerical instability

## Common PyPSA-EUR Scenarios

### Normal Operation:
```
   Time     Iter      Objective       Primal         Dual    Status
   2.3s      150    4.521e+11     2.34e-05     1.23e-06    🟢 HEALTHY
   4.7s      298    4.520e+11     8.76e-07     4.56e-08    🟢 HEALTHY
```

### Convergence Issues:
```
   Time     Iter      Objective       Primal         Dual    Status
  45.2s     1250    4.521e+11     1.23e-02     5.67e-03    🟡 HIGH PRIMAL INFEASIBILITY
  47.8s     1251    4.521e+11     1.23e-02     5.67e-03    🟡 STALLING
```

### When to Intervene:

1. **After 1 hour with no progress**: Consider solver settings adjustment
2. **High infeasibilities persisting**: Check constraint formulation
3. **Memory warnings**: Reduce problem size or use different solver
4. **Unbounded status**: Check objective bounds and constraint completeness

## Monitoring Commands

### Start monitoring:
```bash
# Monitor most recent log file automatically
python monitor_highs.py

# Monitor specific log file
python monitor_highs.py path/to/solver.log

# Monitor with faster updates (1 second intervals)
python monitor_highs.py -i 1.0
```

### Alternative manual monitoring:
```bash
# Watch log file in real-time
Get-Content solver.log -Wait -Tail 20

# Check recent iterations
Select-String -Pattern "^\s*\d+\s+" solver.log | Select-Object -Last 10
```

## Solver Settings to Consider

If monitoring reveals issues, consider these PyPSA solver options:

```python
# In config.yaml or solve_network.py
solver:
  name: highs
  options:
    presolve: "on"           # Usually helpful
    time_limit: 7200         # 2 hour limit
    mip_rel_gap: 0.01        # 1% optimality gap for MIP
    primal_feasibility_tolerance: 1e-6
    dual_feasibility_tolerance: 1e-6
```
