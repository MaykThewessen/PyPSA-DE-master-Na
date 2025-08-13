#!/usr/bin/env python3
"""
Example PyPSA scenario with integrated logging and monitoring.

This script demonstrates how to use the logging utilities for:
- Python logging with rotating file handler
- Runtime tracking
- Toast notifications
- Integration with PowerShell transcript logging
"""

import sys
import time
import traceback
from pathlib import Path

# Import our logging utilities
from logger_utils import create_scenario_logger


def example_pypsa_scenario():
    """
    Example PyPSA scenario that demonstrates the logging capabilities.
    """
    # Create scenario logger
    logger = create_scenario_logger("example_scenario")
    
    try:
        # Start the scenario
        logger.start_scenario("Example PyPSA Scenario")
        
        logger.info("Initializing scenario parameters...")
        time.sleep(1)  # Simulate initialization
        
        logger.info("Loading network data...")
        # Simulate some work
        for i in range(5):
            logger.info(f"Processing network component {i+1}/5...")
            time.sleep(0.5)
        
        logger.info("Running optimization...")
        time.sleep(2)  # Simulate optimization
        
        logger.info("Analyzing results...")
        time.sleep(1)
        
        # Simulate some warnings
        logger.warning("Some non-critical issues found in optimization results")
        
        logger.info("Generating reports...")
        time.sleep(0.5)
        
        logger.info("Scenario completed successfully!")
        
        # End scenario successfully
        logger.end_scenario(success=True)
        
    except Exception as e:
        # Handle failure
        error_msg = f"Scenario failed with error: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # End scenario with failure
        logger.end_scenario(success=False, error_msg=error_msg)
        
        return False
        
    return True


def example_failing_scenario():
    """
    Example scenario that demonstrates failure handling.
    """
    logger = create_scenario_logger("failing_scenario")
    
    try:
        logger.start_scenario("Example Failing Scenario")
        
        logger.info("Starting scenario that will fail...")
        time.sleep(1)
        
        logger.warning("Something doesn't look right...")
        time.sleep(0.5)
        
        # Simulate failure
        raise ValueError("Simulated critical error in optimization")
        
    except Exception as e:
        error_msg = f"Critical error occurred: {str(e)}"
        logger.error(error_msg)
        logger.end_scenario(success=False, error_msg=error_msg)
        return False
        
    return True


if __name__ == "__main__":
    print("PyPSA Scenario Logging Example")
    print("=" * 50)
    
    # Run successful scenario
    print("\n1. Running successful scenario...")
    success = example_pypsa_scenario()
    print(f"Scenario result: {'SUCCESS' if success else 'FAILURE'}")
    
    # Wait a bit
    time.sleep(2)
    
    # Run failing scenario
    print("\n2. Running failing scenario...")
    success = example_failing_scenario()
    print(f"Scenario result: {'SUCCESS' if success else 'FAILURE'}")
    
    print("\nCheck the following locations:")
    print("- Logs: logs/ directory")
    print("- Runtime reports: reports/ directory")
    print("- Toast notifications should have appeared")
