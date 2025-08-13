#!/usr/bin/env python3
"""
Test script to demonstrate HiGHS real-time monitoring integration.
This creates a simple PyPSA network and solves it with HiGHS monitoring.
"""

import logging
import subprocess
import sys
import tempfile
from pathlib import Path
import time

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def start_highs_monitor(log_file: str, config: dict) -> subprocess.Popen | None:
    """
    Start HiGHS real-time monitoring in background process.
    
    Parameters
    ----------
    log_file : str
        Path to HiGHS solver log file
    config : dict
        Configuration dictionary containing monitoring settings
    
    Returns
    -------
    subprocess.Popen | None
        Monitor process handle or None if monitoring disabled
    """
    monitoring_config = config.get("solving", {}).get("monitoring", {})
    
    if not monitoring_config.get("enable", False):
        return None
    
    if not monitoring_config.get("auto_start", True):
        logger.info("HiGHS monitoring configured but auto_start is disabled. "
                   f"Run manually: python monitor_highs.py {log_file}")
        return None
    
    try:
        # Get the directory of the current script
        script_dir = Path(__file__).parent
        monitor_script = script_dir / "monitor_highs.py"
        
        if not monitor_script.exists():
            logger.warning(f"HiGHS monitor script not found at {monitor_script}. "
                          "Monitoring disabled.")
            return None
        
        # Prepare command
        update_interval = monitoring_config.get("update_interval", 2.0)
        cmd = [
            sys.executable, str(monitor_script),
            log_file,
            "-i", str(update_interval)
        ]
        
        logger.info(f"🚀 Starting HiGHS real-time monitoring: {' '.join(cmd)}")
        
        # Start monitoring process with output redirected to avoid interference
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Give the process a moment to start
        time.sleep(1)
        
        if process.poll() is not None:
            # Process already terminated
            stderr = process.stderr.read() if process.stderr else "No error output"
            logger.error(f"HiGHS monitor failed to start: {stderr}")
            return None
            
        logger.info("✅ HiGHS monitoring started successfully")
        return process
        
    except Exception as e:
        logger.warning(f"Failed to start HiGHS monitoring: {e}. Continuing without monitoring.")
        return None


def stop_highs_monitor(process: subprocess.Popen | None) -> None:
    """
    Stop HiGHS monitoring process gracefully.
    
    Parameters
    ----------
    process : subprocess.Popen | None
        Monitor process handle
    """
    if process is None:
        return
        
    try:
        if process.poll() is None:  # Process is still running
            logger.info("🛑 Stopping HiGHS monitoring")
            process.terminate()
            
            # Wait up to 5 seconds for graceful termination
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("HiGHS monitor didn't terminate gracefully, killing process")
                process.kill()
                process.wait()
                
            logger.info("✅ HiGHS monitoring stopped")
        else:
            logger.debug("HiGHS monitor process already terminated")
            
    except Exception as e:
        logger.warning(f"Error stopping HiGHS monitor: {e}")


def simple_pypsa_test():
    """Test the monitoring integration with a simple PyPSA network."""
    try:
        import pypsa
        import numpy as np
        import pandas as pd
    except ImportError as e:
        logger.error(f"Missing required dependencies: {e}")
        logger.info("Please install with: pip install pypsa pandas")
        return False
    
    logger.info("Creating simple test network...")
    
    # Create a simple 2-bus network
    n = pypsa.Network()
    
    # Add buses
    n.add("Bus", "bus_0", v_nom=380)
    n.add("Bus", "bus_1", v_nom=380)
    
    # Add line between buses
    n.add("Line", "line_0", bus0="bus_0", bus1="bus_1", 
          x=0.1, r=0.05, s_nom_extendable=True, capital_cost=1000)
    
    # Add generators
    n.add("Generator", "gen_0", bus="bus_0", p_nom_extendable=True,
          marginal_cost=20, capital_cost=1000)
    n.add("Generator", "gen_1", bus="bus_1", p_nom_extendable=True,
          marginal_cost=30, capital_cost=1200)
    
    # Add loads
    n.add("Load", "load_0", bus="bus_0", p_set=100)
    n.add("Load", "load_1", bus="bus_1", p_set=150)
    
    logger.info("Network created successfully")
    
    # Configuration with monitoring enabled
    config = {
        "solving": {
            "monitoring": {
                "enable": True,
                "update_interval": 1.0,
                "auto_start": True
            }
        }
    }
    
    # Create temporary log file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        log_file = f.name
    
    logger.info(f"Using log file: {log_file}")
    
    # Start monitoring
    monitor_process = start_highs_monitor(log_file, config)
    
    try:
        logger.info("🔧 Solving network with HiGHS...")
        
        # Solve the network
        n.optimize(
            solver_name="highs",
            log_fn=log_file,
            solver_options={
                "log_to_console": True,
                "log_file": log_file,
                "time_limit": 60,
                "threads": 4
            }
        )
        
        logger.info("✅ Network solved successfully!")
        logger.info(f"Objective value: {n.objective:.2f}")
        
        # Show some results
        logger.info(f"Generator capacities: {n.generators.p_nom_opt.to_dict()}")
        logger.info(f"Line capacity: {n.lines.s_nom_opt.iloc[0]:.2f} MW")
        
        return True
        
    except Exception as e:
        logger.error(f"Error solving network: {e}")
        return False
        
    finally:
        # Always stop monitoring
        stop_highs_monitor(monitor_process)
        
        # Cleanup log file
        try:
            Path(log_file).unlink()
        except:
            pass


if __name__ == "__main__":
    logger.info("🧪 Testing HiGHS monitoring integration...")
    success = simple_pypsa_test()
    
    if success:
        logger.info("🎉 Test completed successfully!")
        logger.info("The HiGHS real-time monitoring integration is working!")
    else:
        logger.error("❌ Test failed")
        sys.exit(1)
