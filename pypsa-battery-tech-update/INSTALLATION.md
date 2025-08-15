# Installation and Setup Guide

## 🛠️ Prerequisites

### System Requirements
- Python 3.7 or higher
- Windows 10/11, macOS, or Linux
- At least 2 GB free disk space
- 8 GB RAM recommended

### Required Python Packages
```bash
pip install pypsa>=0.35.1
pip install pandas>=1.3.0
pip install numpy>=1.21.0
pip install matplotlib>=3.5.0
pip install seaborn>=0.11.0
```

## 📦 Installation Steps

### 1. Extract the Package
```bash
# If you received a zip file, extract it to your desired location
unzip pypsa-battery-tech-update.zip
cd pypsa-battery-tech-update
```

### 2. Set Up Python Environment (Recommended)
```bash
# Create a virtual environment
python -m venv pypsa-battery-env

# Activate the environment
# On Windows:
pypsa-battery-env\Scripts\activate
# On macOS/Linux:
source pypsa-battery-env/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Verify Installation
Run the comprehensive test suite to ensure everything is working:
```bash
python tests/comprehensive_data_processing_test.py
```

Expected output:
```
✅ Network Loading: PASSED
✅ Capacity Data Extraction: PASSED  
✅ Emissions Calculations: PASSED
✅ Cost Calculations: PASSED
✅ Plot Generation: PASSED
✅ Curtailment Calculations: PASSED
✅ Storage Analysis: PASSED
✅ Battery Technology Naming: PASSED

Overall Result: 8/8 tests passed
🎉 ALL TESTS PASSED!
```

## 🔗 Integration with Existing PyPSA Project

### Method 1: Copy Files to Your Existing Project
```bash
# Copy configuration files
cp config/plotting.default.yaml /path/to/your/pypsa/project/config/

# Copy scripts to your scripts directory
cp scripts/* /path/to/your/pypsa/project/scripts/

# Copy network files
cp data/networks/* /path/to/your/pypsa/project/data/networks/
```

### Method 2: Use as Standalone Package
Update the file paths in your Jupyter notebook to point to this package:
```python
# Add the package to your Python path
import sys
sys.path.append('/path/to/pypsa-battery-tech-update')

# Import functions
from scripts.scenario_comparison_analysis import load_and_compare_scenarios
from scripts.capacity_data_handler import get_capacity_data
```

## 📊 Verify Your Network Files

Ensure your network files are in the correct format:
```python
import pypsa
import os

# Check if network files exist and are valid
network_files = [
    'data/networks/250Mt_CO2_Limit_solved_network.nc',
    'data/networks/300Mt_CO2_Limit_solved_network.nc', 
    'data/networks/500Mt_CO2_Limit_solved_network.nc'
]

for file_path in network_files:
    if os.path.exists(file_path):
        try:
            network = pypsa.Network(file_path)
            print(f"✅ {file_path}: Valid network file")
            print(f"   Buses: {len(network.buses)}, Generators: {len(network.generators)}")
        except Exception as e:
            print(f"❌ {file_path}: Error loading - {e}")
    else:
        print(f"⚠️  {file_path}: File not found")
```

## 🎨 Configuration Customization

### Update Battery Colors
Edit `config/plotting.default.yaml`:
```yaml
tech_colors:
  iron-air battery: '#FF6B35'         # Orange-red
  Lithium-Ion-LFP-bicharger: '#004E89'  # Dark blue
  Lithium-Ion-LFP-store: '#1A759F'      # Medium blue
  battery storage: '#168AAD'              # Light blue
  battery inverter: '#34A0A4'             # Teal
```

### Customize Analysis Parameters
Edit analysis scripts to adjust:
- CO₂ emission factors
- Renewable technology groupings  
- Output file naming conventions
- Plot styling and formats

## 🧪 Test Different Scenarios

### Basic Scenario Analysis
```python
# Run scenario comparison
from scripts.scenario_comparison_analysis import load_and_compare_scenarios
networks = load_and_compare_scenarios()
```

### Individual Network Analysis
```python
# Analyze single scenario
import pypsa
from scripts.capacity_data_handler import get_capacity_data

network = pypsa.Network('data/networks/250Mt_CO2_Limit_solved_network.nc')
capacity_data = get_capacity_data(network)
print(capacity_data)
```

### Custom Analysis
```python
# Extract specific metrics
from scripts.scenario_comparison_analysis import analyze_network_metrics

network = pypsa.Network('data/networks/300Mt_CO2_Limit_solved_network.nc') 
metrics = analyze_network_metrics(network)
print(f"System Cost: {metrics['system_cost_billion_eur']:.1f} B€")
print(f"Renewable Share: {metrics['renewable_share_pct']:.1f}%")
```

## 🔧 Troubleshooting

### Common Installation Issues

**Issue**: `ModuleNotFoundError: No module named 'pypsa'`
```bash
# Solution: Install PyPSA
pip install pypsa>=0.35.1
```

**Issue**: `FileNotFoundError` when running tests
```bash
# Solution: Ensure you're in the correct directory
cd pypsa-battery-tech-update
python tests/comprehensive_data_processing_test.py
```

**Issue**: Network files not loading
```bash
# Check file paths and permissions
ls -la data/networks/
# Ensure files have read permissions
chmod 644 data/networks/*.nc
```

**Issue**: PyPSA version warnings
```bash
# Check your PyPSA version
python -c "import pypsa; print(pypsa.__version__)"
# Update if necessary
pip install --upgrade pypsa
```

### Performance Optimization

For large networks:
```python
# Increase memory limit if needed
import numpy as np
np.seterr(all='ignore')  # Suppress warnings for large calculations

# Use chunked processing for very large time series
chunk_size = 1000  # Adjust based on available memory
```

## 🔄 Updates and Maintenance

### Keeping the Package Updated
1. Check for new network files periodically
2. Update battery technology definitions as needed
3. Verify test suite passes after any changes
4. Update documentation for any customizations

### Adding New Scenarios
1. Place new network files in `data/networks/`
2. Update scenario lists in analysis scripts
3. Run test suite to verify compatibility
4. Update documentation with new scenario details

## 📞 Support

If you encounter issues:
1. Check the test suite output for specific error messages
2. Review the `DATA_PROCESSING_VERIFICATION_REPORT.md` for detailed validation results
3. Ensure all file paths are correct for your system
4. Verify PyPSA version compatibility

### Log Analysis
Enable detailed logging for troubleshooting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will provide detailed information about the analysis process and help identify any issues.
