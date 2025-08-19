# 🔒 Local Costs Configuration - Quick Reference

## ✅ Current Status

The PyPSA-DE repository is now configured to **always use local `costs_2035.csv` files** and **never download from the cloud**.

## 🔧 What Changed

1. **Configuration**: `retrieve_cost_data: false` in `config/config.default.yaml`
2. **New Rule**: `ensure_local_costs` rule automatically finds and uses local costs files
3. **Protection**: Your local costs files will never be overwritten by cloud downloads

## 📁 Local Costs Files Found

✅ `resources/costs_2035.csv` (main file - **will be used first**)  
✅ `resources/de-co2-scenario-A-2035/costs_2035.csv`  
✅ `resources/de-co2-scenario-B-2035/costs_2035.csv`  
✅ `resources/de-co2-scenario-C-2035/costs_2035.csv`  
✅ `resources/de-all-tech-2035-mayk/costs_2035.csv`  

## 🚀 Usage

**Normal workflow - unlock first, then run:**
```bash
# 1. Standard unlock before starting
snakemake --unlock

# 2. Run the workflow
snakemake -c all
```

The system automatically:
- Uses your local costs files
- Never downloads from cloud
- Logs which file it's using

## ✏️ To Edit Costs

**Edit the main costs file:**
```bash
# Open for editing
vim resources/costs_2035.csv

# Or use any editor
nano resources/costs_2035.csv
```

Changes take effect immediately on the next run.

## 🔍 Verify Setup

**Check configuration:**
```bash
grep "retrieve_cost_data" config/config.default.yaml
# Should show: retrieve_cost_data: false
```

**Check which costs file is being used:**
```bash
cat logs/ensure_local_costs_2035.log
```

## 📚 Full Documentation

- **Detailed setup**: `docs/local_costs_setup.md`
- **Download optimization**: `docs/data_download_optimization.md`

## ✋ Important Notes

- ✅ **Your costs files are protected** - will never be overwritten
- ✅ **No internet needed** for costs data
- ✅ **Changes are preserved** across workflow runs
- ✅ **Works offline** - no external dependencies for costs

Your local `costs_2035.csv` files are now the single source of truth! 🎯
