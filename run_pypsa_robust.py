#!/usr/bin/env python3
"""
Enhanced PyPSA Run Script with Performance & Robustness Tweaks
==============================================================

This script runs PyPSA with performance and robustness improvements:
- Auto-detects available CPUs and uses all cores for maximum performance
- Adds --rerun-incomplete flag for interrupted runs
- Uses --resources mem_mb=30000 for memory management
- Cleans tmp folder older than 7 days at script start
- Validates config files before launching Snakemake
- Provides robust error handling and logging

Usage:
    python run_pypsa_robust.py [scenario_config] [additional_snakemake_args]
    
Examples:
    python run_pypsa_robust.py config/de-all-tech-2035.yaml
    python run_pypsa_robust.py config/de-no-ironair-2035.yaml --dry-run
    python run_pypsa_robust.py config/de-no-mds-2035.yaml --unlock
"""

import os
import sys
import time
import shutil
import subprocess
import logging
import psutil
from datetime import datetime, timedelta
from pathlib import Path
import yaml
import glob

# Configuration
DEFAULT_CONFIG = "config/config.default.yaml"
MEMORY_MB = 30000
TMP_CLEANUP_DAYS = 7

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"pypsa_run_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def get_cpu_cores():
    """Get all available logical CPU cores for maximum performance"""
    total_cores = psutil.cpu_count(logical=True)
    if total_cores is None:
        logger.warning("Could not detect CPU count, defaulting to 2 cores")
        return 2
    
    # Use all available cores for maximum performance
    cores_to_use = total_cores
    logger.info(f"Detected {total_cores} logical CPUs, using all {cores_to_use} cores for Snakemake")
    return cores_to_use


def clean_tmp_folder():
    """Clean tmp folder of files older than 7 days"""
    logger.info("Cleaning tmp folder of files older than 7 days...")
    
    tmp_dir = Path("tmp")
    if not tmp_dir.exists():
        logger.info("No tmp directory found, skipping cleanup")
        return
    
    cutoff_time = datetime.now() - timedelta(days=TMP_CLEANUP_DAYS)
    cleaned_count = 0
    
    try:
        for item in tmp_dir.rglob("*"):
            if item.is_file():
                # Get file modification time
                mod_time = datetime.fromtimestamp(item.stat().st_mtime)
                if mod_time < cutoff_time:
                    try:
                        item.unlink()
                        cleaned_count += 1
                        logger.debug(f"Removed old file: {item}")
                    except Exception as e:
                        logger.warning(f"Could not remove {item}: {e}")
        
        # Remove empty directories
        for item in tmp_dir.rglob("*"):
            if item.is_dir() and not any(item.iterdir()):
                try:
                    item.rmdir()
                    logger.debug(f"Removed empty directory: {item}")
                except Exception as e:
                    logger.debug(f"Could not remove empty directory {item}: {e}")
        
        logger.info(f"Cleaned {cleaned_count} old files from tmp directory")
        
    except Exception as e:
        logger.error(f"Error cleaning tmp directory: {e}")


def validate_config_file(config_path):
    """Validate that config file exists and is readable"""
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.error(f"Config file does not exist: {config_path}")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
            
        if not config_data:
            logger.error(f"Config file appears to be empty: {config_path}")
            return False
            
        logger.info(f"Config file validation successful: {config_path}")
        return True
        
    except yaml.YAMLError as e:
        logger.error(f"Config file has invalid YAML syntax: {config_path}\nError: {e}")
        return False
    except Exception as e:
        logger.error(f"Error reading config file {config_path}: {e}")
        return False


def validate_required_configs():
    """Validate that required config files exist"""
    required_configs = [
        "config/config.default.yaml",
        "config/plotting.default.yaml"
    ]
    
    optional_configs = [
        "config/config.yaml"
    ]
    
    logger.info("Validating configuration files...")
    
    # Check required configs
    for config in required_configs:
        if not validate_config_file(config):
            logger.error(f"Required config file missing or invalid: {config}")
            return False
    
    # Check optional configs (only if they exist)
    for config in optional_configs:
        if Path(config).exists():
            if not validate_config_file(config):
                logger.error(f"Optional config file exists but is invalid: {config}")
                return False
    
    logger.info("All configuration files validated successfully")
    return True


def build_snakemake_command(scenario_config=None, additional_args=None):
    """Build the Snakemake command with performance optimizations"""
    cores = get_cpu_cores()
    
    cmd = [
        "snakemake",
        "--cores", str(cores),
        "--rerun-incomplete",
        "--resources", f"mem_mb={MEMORY_MB}",
    ]
    
    # Add scenario config if provided
    if scenario_config:
        if not validate_config_file(scenario_config):
            logger.error(f"Scenario config file validation failed: {scenario_config}")
            return None
        cmd.extend(["--configfile", scenario_config])
    
    # Add additional arguments if provided
    if additional_args:
        cmd.extend(additional_args)
    
    logger.info(f"Snakemake command: {' '.join(cmd)}")
    return cmd


def run_snakemake(cmd):
    """Execute Snakemake with error handling and logging"""
    logger.info("Starting Snakemake execution...")
    start_time = time.time()
    
    try:
        # Run Snakemake
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Stream output in real-time
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if line:
                print(line)
                logger.info(f"Snakemake: {line}")
        
        process.wait()
        end_time = time.time()
        duration = end_time - start_time
        
        if process.returncode == 0:
            logger.info(f"Snakemake completed successfully in {duration:.1f} seconds")
            return True
        else:
            logger.error(f"Snakemake failed with return code {process.returncode}")
            return False
            
    except KeyboardInterrupt:
        logger.warning("Received keyboard interrupt, terminating Snakemake...")
        if 'process' in locals():
            process.terminate()
        return False
    except Exception as e:
        logger.error(f"Error running Snakemake: {e}")
        return False


def show_usage():
    """Display usage information"""
    print(__doc__)
    
    # Show available scenario configs
    config_dir = Path("config")
    if config_dir.exists():
        scenario_configs = list(config_dir.glob("de-*.yaml"))
        if scenario_configs:
            print("\nAvailable scenario configs:")
            for config in sorted(scenario_configs):
                print(f"  - {config}")
    
    print(f"\nSystem info:")
    print(f"  - Available CPU cores: {psutil.cpu_count(logical=True)}")
    print(f"  - Cores to use: {get_cpu_cores()}")
    print(f"  - Memory limit: {MEMORY_MB} MB")
    print(f"  - Tmp cleanup: {TMP_CLEANUP_DAYS} days")


def main():
    """Main execution function"""
    print("Enhanced PyPSA Run Script")
    print("=" * 50)
    
    # Parse command line arguments
    args = sys.argv[1:]
    
    # Show help if requested
    if "--help" in args or "-h" in args:
        show_usage()
        return
    
    # Extract scenario config if provided
    scenario_config = None
    additional_args = []
    
    if args:
        first_arg = args[0]
        if first_arg.endswith('.yaml') or first_arg.endswith('.yml'):
            scenario_config = first_arg
            additional_args = args[1:]
        else:
            additional_args = args
    
    logger.info("Starting PyPSA robust run script")
    logger.info(f"Scenario config: {scenario_config or 'default'}")
    logger.info(f"Additional args: {' '.join(additional_args) if additional_args else 'none'}")
    
    # Step 1: Clean tmp folder
    clean_tmp_folder()
    
    # Step 2: Validate configuration files
    if not validate_required_configs():
        logger.error("Configuration validation failed, aborting")
        sys.exit(1)
    
    # Step 3: Build Snakemake command
    cmd = build_snakemake_command(scenario_config, additional_args)
    if cmd is None:
        logger.error("Failed to build Snakemake command, aborting")
        sys.exit(1)
    
    # Step 4: Run Snakemake
    success = run_snakemake(cmd)
    
    if success:
        logger.info("PyPSA run completed successfully!")
        print(f"\nLog file saved to: {log_file}")
    else:
        logger.error("PyPSA run failed!")
        print(f"\nCheck log file for details: {log_file}")
        sys.exit(1)


if __name__ == "__main__":
    main()
