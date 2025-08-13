"""
Logging and monitoring utilities for PyPSA-DE benchmarking scenarios.

This module provides:
- Python logging with rotating file handler (max 5 MB, 3 backups)
- Windows toast notifications for scenario completion/failure
- Runtime tracking functionality
"""

import logging
import logging.handlers
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ScenarioLogger:
    """Enhanced logger for PyPSA-DE scenarios with rotating files and notifications."""
    
    def __init__(self, name: str = "pypsa_scenario", log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create the main log file path
        self.log_file = self.log_dir / f"{name}.log"
        
        # Set up the logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Create rotating file handler (max 5 MB, 3 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(self.log_file),
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding='utf-8'
        )
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Set formatters
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Runtime tracking
        self.start_time = None
        self.scenario_name = None
        
    def start_scenario(self, scenario_name: str):
        """Start tracking a scenario run."""
        self.scenario_name = scenario_name
        self.start_time = datetime.now()
        self.logger.info(f"Starting scenario: {scenario_name}")
        
    def end_scenario(self, success: bool = True, error_msg: str = None):
        """End scenario tracking and emit notifications."""
        if self.start_time is None:
            self.logger.warning("end_scenario called without start_scenario")
            return
            
        end_time = datetime.now()
        runtime = end_time - self.start_time
        
        # Log completion
        if success:
            self.logger.info(f"Scenario '{self.scenario_name}' completed successfully in {runtime}")
        else:
            self.logger.error(f"Scenario '{self.scenario_name}' failed after {runtime}")
            if error_msg:
                self.logger.error(f"Error: {error_msg}")
        
        # Store runtime
        self._store_runtime(runtime, success, error_msg)
        
        # Emit toast notification
        self._emit_toast_notification(success, runtime, error_msg)
        
        # Reset tracking
        self.start_time = None
        self.scenario_name = None
        
    def _store_runtime(self, runtime, success: bool, error_msg: str = None):
        """Store runtime information to reports directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        runtime_file = Path("reports") / f"runtime_{timestamp}.txt"
        
        try:
            with open(runtime_file, 'w', encoding='utf-8') as f:
                f.write(f"Scenario: {self.scenario_name}\n")
                f.write(f"Start Time: {self.start_time.isoformat()}\n")
                f.write(f"End Time: {datetime.now().isoformat()}\n")
                f.write(f"Runtime: {runtime}\n")
                f.write(f"Runtime (seconds): {runtime.total_seconds():.2f}\n")
                f.write(f"Status: {'SUCCESS' if success else 'FAILURE'}\n")
                if error_msg:
                    f.write(f"Error: {error_msg}\n")
                    
            self.logger.info(f"Runtime stored in {runtime_file}")
        except Exception as e:
            self.logger.error(f"Failed to store runtime: {e}")
            
    def _emit_toast_notification(self, success: bool, runtime, error_msg: str = None):
        """Emit Windows toast notification using PowerShell."""
        try:
            status = "Completed" if success else "Failed"
            runtime_str = f"{runtime.total_seconds():.1f}s"
            
            title = f"PyPSA Scenario {status}"
            if success:
                message = f"'{self.scenario_name}' completed successfully in {runtime_str}"
            else:
                message = f"'{self.scenario_name}' failed after {runtime_str}"
                if error_msg:
                    # Truncate error message for notification
                    short_error = error_msg[:100] + "..." if len(error_msg) > 100 else error_msg
                    message += f"\nError: {short_error}"
            
            # PowerShell command to show toast notification
            ps_command = f"""
            if (Get-Module -ListAvailable -Name BurntToast) {{
                Import-Module BurntToast
                New-BurntToastNotification -Text "{title}", "{message}"
            }} else {{
                Write-Host "BurntToast module not available. Install with: Install-Module -Name BurntToast"
                # Fallback to simple message box
                Add-Type -AssemblyName System.Windows.Forms
                [System.Windows.Forms.MessageBox]::Show("{message}", "{title}")
            }}
            """
            
            # Execute PowerShell command
            subprocess.run([
                "powershell", "-Command", ps_command
            ], capture_output=True, text=True, timeout=10)
            
        except Exception as e:
            self.logger.warning(f"Failed to emit toast notification: {e}")
            
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
        
    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
        
    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)
        
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)
        
    def get_log_file_path(self) -> str:
        """Get the path to the main log file."""
        return str(self.log_file)


def create_scenario_logger(scenario_name: str = None) -> ScenarioLogger:
    """Create a scenario logger instance."""
    if scenario_name:
        return ScenarioLogger(f"pypsa_{scenario_name}")
    else:
        return ScenarioLogger()


# Example usage and testing
if __name__ == "__main__":
    # Test the logger
    logger = create_scenario_logger("test")
    
    logger.start_scenario("Test Scenario")
    logger.info("This is a test info message")
    logger.warning("This is a test warning")
    
    # Simulate some work
    import time
    time.sleep(2)
    
    # Test successful completion
    logger.end_scenario(success=True)
    
    # Test failure scenario
    logger.start_scenario("Failed Test Scenario")
    logger.error("This is a test error")
    time.sleep(1)
    logger.end_scenario(success=False, error_msg="Simulated failure for testing")
