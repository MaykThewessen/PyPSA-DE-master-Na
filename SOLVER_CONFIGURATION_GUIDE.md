# 🚀 PyPSA-DE Solver Configuration Guide

## 📋 **Overview**
This guide explains the optimized solver configurations implemented in `config/config.default.yaml` for maximum numerical stability and convergence reliability.

## ⚙️ **Available Solver Configurations**

### 🥇 **Primary: `stable_highs` (Recommended)**
- **Purpose**: Balanced stability and performance with HiGHS
- **Key Features**:
  - Balanced tolerances (1e-7 primal/dual, 1e-8 IPM)
  - Devex pivoting for improved numerical behavior
  - Aggressive scaling (simplex_scale_strategy: 2)
  - Crossover disabled for stability
  - 2-hour time limit

**When to use**: Default choice for all standard PyPSA-DE runs

### 🥈 **Backup: `robust_highs`**
- **Purpose**: Fallback when stable_highs has convergence issues
- **Key Features**:
  - Slightly relaxed tolerances (1e-7)
  - Crossover enabled
  - 12-hour time limit
  - Standard scaling

**When to use**: If stable_highs fails to converge

### 🏆 **Alternative: `stable_cplex`**
- **Purpose**: For users with CPLEX license
- **Key Features**:
  - Numerical emphasis enabled
  - Barrier method with no crossover
  - Ultra-tight tolerances (1e-9)
  - Enterprise-grade stability

**When to use**: If you have CPLEX license and need maximum reliability

### 🐌 **Fallback: `conservative`**
- **Purpose**: Last resort for difficult problems
- **Key Features**:
  - Presolving disabled
  - Reduced parallelism
  - 20-hour time limit
  - Minimal optimization tricks

**When to use**: Only when all other configurations fail

## 🔄 **How to Switch Configurations**

### Method 1: Edit config file directly
```yaml
solving:
  solver:
    name: highs
    options: robust_highs  # Change this line
```

### Method 2: Command line override
```bash
# For CPLEX (if available)
snakemake --config solving.solver.name=cplex solving.solver.options=stable_cplex

# For conservative HiGHS
snakemake --config solving.solver.options=conservative
```

## 📊 **Key Improvements Implemented**

### ✅ **Numerical Stability**
- **Tolerances**: Tightened from 1e-6 to 1e-8
- **Scaling**: Aggressive scaling enabled
- **Pivoting**: Devex method for better conditioning
- **Crossover**: Disabled by default for stability

### ✅ **Memory Management**
- **Allocation**: Increased to 120GB for large networks
- **Cleanup**: Automatic temporary file cleanup
- **Logging**: Memory usage tracking every 30 seconds

### ✅ **Problem Conditioning**
- **Preprocessing**: Remove values < 1e-3 with `clip_p_max_pu`
- **Load Shedding**: Enabled at 10,000 EUR/MWh
- **Noisy Costs**: Disabled for numerical stability
- **Seed**: Fixed at 12345 for reproducibility

### ✅ **Iteration Control**
- **Transmission Expansion**: 2-8 iterations (was 1)
- **Tracking**: Full iteration monitoring enabled
- **Losses**: Start without losses (can be enabled later)

## 🎯 **Recommended Usage Strategy**

### 1. **Start with `stable_highs`**
```yaml
solving:
  solver:
    options: stable_highs
```

### 2. **If convergence issues, try `robust_highs`**
```yaml
solving:
  solver:
    options: robust_highs
```

### 3. **For critical production runs with CPLEX license**
```yaml
solving:
  solver:
    name: cplex
    options: stable_cplex
```

### 4. **Last resort: `conservative`**
```yaml
solving:
  solver:
    options: conservative
```

## 🚨 **Troubleshooting Guide**

### **Solver fails with "Infeasible"**
1. Enable load shedding: `load_shedding: 10000`
2. Check constraints: Disable CCL, EQ, BAU temporarily
3. Try `robust_highs` configuration
4. Increase `clip_p_max_pu` to 1e-2

### **Solver runs too long**
1. Reduce time horizon: `horizon: 168` (weekly)
2. Use temporal clustering: `resolution_elec: 12`
3. Disable iterations: `skip_iterations: true`
4. Reduce tolerance slightly: Edit solver_options

### **Memory issues**
1. Increase `mem_mb: 200000` (200GB)
2. Enable temporal clustering
3. Reduce network size with higher clustering
4. Use `assign_all_duals: false`

### **Numerical precision warnings**
1. Switch to `stable_cplex` if available
2. Increase `highs_debug_level: 2`
3. Use `conservative` configuration
4. Check input data for extreme values

## 📈 **Performance Expectations**

| Configuration | Speed | Reliability | Memory | Best For |
|---------------|-------|-------------|--------|----------|
| `stable_highs` | Fast | High | Moderate | General use |
| `robust_highs` | Fast | Moderate | Moderate | Fallback |
| `stable_cplex` | Medium | Very High | High | Production |
| `conservative` | Slow | High | Low | Difficult problems |

## ⚡ **Quick Commands**

```bash
# Test current configuration
snakemake solve_elec_networks --dry-run

# Run with stable configuration
snakemake solve_elec_networks --config solving.solver.options=stable_highs

# Enable more logging
snakemake solve_elec_networks --config solving.solver_options.stable_highs.highs_debug_level=2

# Use CPLEX if available
snakemake solve_elec_networks --config solving.solver.name=cplex solving.solver.options=stable_cplex
```

## 📝 **Notes**
- All configurations include enhanced monitoring and logging
- Memory allocation set to 120GB - adjust based on your system
- Time limits are generous - reduce if needed
- Fixed seed ensures reproducible results
- Direct API (`io_api: 'direct'`) used when available for better performance
