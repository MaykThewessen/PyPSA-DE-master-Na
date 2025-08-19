# CO2 SCENARIOS ANALYSIS SETUP

## 🎯 **OBJECTIVE**

Run PyPSA-EUR for 4 different CO2 emission targets to analyze the impact of decarbonization on Germany's 2035 energy system design.

## 📋 **SCENARIOS CONFIGURED**

| Scenario    | CO2 Target  | Description                | Config File                            |
| ----------- | ----------- | -------------------------- | -------------------------------------- |
| **A** | 15% of 1990 | Moderate decarbonization   | `config/de-co2-scenario-A-2035.yaml` |
| **B** | 5% of 1990  | Aggressive decarbonization | `config/de-co2-scenario-B-2035.yaml` |
| **C** | 1% of 1990  | Near net-zero              | `config/de-co2-scenario-C-2035.yaml` |
| **D** | 0% of 1990  | Net-zero emissions         | `config/de-co2-scenario-D-2035.yaml` |

## ⚙️ **MODEL CONFIGURATION**

### **Key Settings Applied:**

- **Country:** Germany only (DE)
- **Spatial Resolution:** 1 node (entire country)
- **Temporal Resolution:** 4380 timesteps (2-hour resolution)
- **Heating Sector:** DISABLED ✅
- **Sector Coupling:** DISABLED ✅
- **Transmission Losses:** 2% linear ✅
- **LP Optimization:** Linear programming only ✅

### **Solver Configuration:**

- **Solver:** HiGHS
- **Time Limit:** 5 hours (18,000 seconds) ✅
- **Tolerance:** 1e-6 ✅
- **Threads:** 8
- **Memory:** 60 GB
- **Iterations:** Single iteration (no iterative solving)

### **Technologies Included:**

**Generation:**

- Solar PV
- Onshore Wind
- Offshore Wind (AC)
- CCGT (gas)
- OCGT (gas)
- Nuclear (limited)
- Biomass

**Storage:**

- Li-ion Batteries (8h max)
- IronAir storage (variable duration)
- Hydrogen Storage (variable duration)
- Pumped Hydro Storage (PHS)

## 📂 **FILES CREATED**

### **Configuration Files:**

- `config/de-co2-scenarios-2035.yaml` - Base configuration
- `config/de-co2-scenario-A-2035.yaml` - Scenario A (15% CO2)
- `config/de-co2-scenario-B-2035.yaml` - Scenario B (5% CO2)
- `config/de-co2-scenario-C-2035.yaml` - Scenario C (1% CO2)
- `config/de-co2-scenario-D-2035.yaml` - Scenario D (0% CO2)

### **Execution Scripts:**

- `run_co2_scenarios.py` - Main script to run all scenarios sequentially
- `co2_scenarios_dashboard.py` - Dashboard generation script

### **Output Files:**

- `co2_scenarios_comparison.csv` - Results comparison table
- `co2_scenarios_dashboard.html` - Interactive Plotly dashboard

## 🚀 **HOW TO RUN**

### **Option 1: Run All Scenarios Sequentially**

```bash
python run_co2_scenarios.py
```

*Note: This will take 10+ hours (2-5 hours per scenario)*

### **Option 2: Run Individual Scenarios**

```bash
# Scenario A (15% CO2)
snakemake --configfile=config/de-co2-scenario-A-2035.yaml -j1 solve_elec_networks

# Scenario B (5% CO2)  
snakemake --configfile=config/de-co2-scenario-B-2035.yaml -j1 solve_elec_networks

# And so on...
```

### **Option 3: Generate Dashboard with Sample Data**

```bash
python co2_scenarios_dashboard.py
```

## 📊 **EXPECTED RESULTS**

### **Key Insights Expected:**

1. **Renewable Capacity:** Increases from 15% to 0% CO2 targets
2. **Storage Deployment:** More storage needed for higher renewable shares
3. **System Costs:** Trade-off between renewables investment and emissions
4. **Technology Mix:** Shift from gas to renewables + storage

### **Dashboard Features:**

- Generation capacity evolution across scenarios
- Storage technology deployment trends
- System cost vs CO2 emissions trade-offs
- Renewable energy transition pathway
- Storage energy capacity evolution
- Summary table with key metrics

## 🔧 **TROUBLESHOOTING**

### **Common Issues:**

1. **Missing Data Files:** Ensure all required data bundles are downloaded
2. **Memory Issues:** Reduce complexity or increase RAM allocation
3. **Solver Timeout:** Increase time limit in solver options
4. **Infeasible Solutions:** Check CO2 constraints for very low targets

### **Check Model Status:**

```bash
# Dry run to check dependencies
snakemake --configfile=config/de-co2-scenario-A-2035.yaml -j1 solve_elec_networks --dry-run

# Check available rules
snakemake --list
```

## 📈 **NEXT STEPS**

1. **Run Single Scenario First:** Test with Scenario A to verify setup
2. **Monitor Progress:** Check solver logs for convergence
3. **Extract Results:** Use results for comparison analysis
4. **Generate Dashboard:** Create interactive visualizations
5. **Analyze Trade-offs:** Examine cost-emissions relationships

## 🎯 **SUCCESS CRITERIA**

- ✅ All 4 scenarios complete successfully
- ✅ Results saved in `.nc` format
- ✅ Comparison CSV generated
- ✅ Interactive dashboard created
- ✅ Technology trade-offs clearly visible
- ✅ Renewable transition pathway demonstrated

---

**Status:** Configuration complete, ready for execution
**Estimated Runtime:** 10-20 hours for all scenarios
**Output:** Comprehensive analysis of CO2 impact on energy system design
