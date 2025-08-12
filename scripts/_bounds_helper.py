# SPDX-FileCopyrightText: Contributors to PyPSA-Eur <https://github.com/pypsa/pypsa-eur>
#
# SPDX-License-Identifier: MIT

"""
Bounds and limits helper functions to centralize capacity constraints.

This module provides utility functions to retrieve technical limits for various
power system components, replacing magic numbers and np.inf with configurable
bounds based on technical and engineering constraints.
"""

import logging
import numpy as np
import pandas as pd
from typing import Union, Dict, Any, Optional
import yaml
import os

logger = logging.getLogger(__name__)

# Default technical limits if config file is not available
DEFAULT_LIMITS = {
    "generators": {
        "p_nom_max": {
            "default": 5000,  # MW - reasonable default for large generators
            "nuclear": 1650,
            "coal": 1100,
            "lignite": 1100,
            "CCGT": 850,
            "OCGT": 400,
            "onwind": 500,
            "offwind-ac": 1200,
            "offwind-dc": 1400,
            "offwind-float": 500,
            "solar": 800,
            "solar-hsat": 800,
            "solar rooftop": 100,
            "ror": 400,
            "hydro": 1800,
            "biomass": 300,
            "geothermal": 100,
        }
    },
    "storage": {
        "p_nom_max": {
            "default": 2000,
            "battery": 2000,
            "H2": 500,
            "PHS": 1800,
            "Compressed-Air-Adiabatic": 500,
            "Iron-Air": 200,
            "Li-Ion": 2000,
            "Vanadium-Redox-Flow": 100,
        },
        "e_nom_max": {
            "default": 50000,  # MWh
            "battery": 10000,
            "H2": 2000000,  # 2 TWh for seasonal storage
            "PHS": 25000,
            "Compressed-Air-Adiabatic": 12000,
            "Iron-Air": 2000,
            "Vanadium-Redox-Flow": 1000,
        }
    },
    "lines": {
        "s_nom_max": 4000,  # MVA
        "max_extension": 4000,
    },
    "links": {
        "p_nom_max": 6000,  # MW
        "max_extension": 6000,
    },
    "system": {
        "total_renewable_capacity": 200000,  # MW
        "total_storage_power": 100000,
        "total_storage_energy": 2000000,  # MWh
        "default_lifetime": 40,  # years - reasonable default lifetime
        "max_operational_hours": 1e6,  # hours - for operational constraints
    }
}

def load_technical_limits(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load technical limits from configuration file or return defaults.
    
    Parameters
    ----------
    config_path : str, optional
        Path to technical limits configuration file
        
    Returns
    -------
    dict
        Dictionary containing technical limits for all components
    """
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                limits = yaml.safe_load(f)
            logger.info(f"Loaded technical limits from {config_path}")
            return limits
        except Exception as e:
            logger.warning(f"Failed to load technical limits from {config_path}: {e}")
            logger.info("Using default technical limits")
            return DEFAULT_LIMITS
    else:
        if config_path:
            logger.warning(f"Technical limits file not found: {config_path}")
        logger.info("Using default technical limits")
        return DEFAULT_LIMITS


def get_max_cap(carrier: str, 
                component_type: str = "generators",
                limits: Optional[Dict[str, Any]] = None,
                default_multiplier: float = 1.0) -> float:
    """
    Get maximum capacity limit for a given carrier and component type.
    
    This function centralizes capacity limits and avoids magic numbers by
    providing a single point of access to technically justified bounds.
    
    Parameters
    ----------
    carrier : str
        The carrier/technology name (e.g., 'solar', 'onwind', 'H2', 'battery')
    component_type : str, default 'generators' 
        The component type ('generators', 'storage', 'lines', 'links')
    limits : dict, optional
        Dictionary of technical limits. If None, will load from default config
    default_multiplier : float, default 1.0
        Multiplier to apply to the limit value
        
    Returns
    -------
    float
        Maximum capacity limit in MW or MVA, avoiding infinite values
        
    Examples
    --------
    >>> get_max_cap('solar')  # Returns solar generator p_nom_max
    800.0
    >>> get_max_cap('battery', 'storage')  # Returns battery storage p_nom_max  
    2000.0
    >>> get_max_cap('H2', 'storage')  # Returns H2 storage p_nom_max
    500.0
    """
    if limits is None:
        limits = load_technical_limits()
        
    try:
        if component_type in limits:
            component_limits = limits[component_type]
            
            if component_type in ["generators", "storage"]:
                p_nom_limits = component_limits.get("p_nom_max", {})
                
                # Try exact match first
                if carrier in p_nom_limits:
                    return float(p_nom_limits[carrier]) * default_multiplier
                    
                # Try partial matches for compound carriers
                for key, value in p_nom_limits.items():
                    if carrier.startswith(key) or key in carrier:
                        return float(value) * default_multiplier
                        
                # Use default for component type
                if "default" in p_nom_limits:
                    return float(p_nom_limits["default"]) * default_multiplier
                    
            elif component_type in ["lines", "links"]:
                limit_key = "s_nom_max" if component_type == "lines" else "p_nom_max"
                if limit_key in component_limits:
                    return float(component_limits[limit_key]) * default_multiplier
                    
        # Fallback to system defaults
        if "system" in limits:
            if component_type == "generators":
                return float(limits["system"].get("total_renewable_capacity", 200000)) * default_multiplier / 100  # Divided by typical number of buses
            elif component_type == "storage":
                return float(limits["system"].get("total_storage_power", 100000)) * default_multiplier / 100
                
        # Final fallback
        logger.warning(f"No technical limit found for carrier '{carrier}' in component '{component_type}', using fallback")
        return 5000.0 * default_multiplier  # 5 GW reasonable fallback
        
    except Exception as e:
        logger.error(f"Error getting max capacity for {carrier} ({component_type}): {e}")
        return 5000.0 * default_multiplier


def get_max_energy_cap(carrier: str, limits: Optional[Dict[str, Any]] = None) -> float:
    """
    Get maximum energy capacity limit for storage technologies.
    
    Parameters
    ----------
    carrier : str
        The storage carrier name (e.g., 'battery', 'H2', 'PHS')
    limits : dict, optional
        Dictionary of technical limits
        
    Returns
    -------
    float
        Maximum energy capacity limit in MWh
    """
    if limits is None:
        limits = load_technical_limits()
        
    try:
        if "storage" in limits:
            e_nom_limits = limits["storage"].get("e_nom_max", {})
            
            # Try exact match first
            if carrier in e_nom_limits:
                return float(e_nom_limits[carrier])
                
            # Try partial matches
            for key, value in e_nom_limits.items():
                if carrier.startswith(key) or key in carrier:
                    return float(value)
                    
            # Use default
            if "default" in e_nom_limits:
                return float(e_nom_limits["default"])
                
        # Fallback
        return 50000.0  # 50 GWh reasonable fallback
        
    except Exception as e:
        logger.error(f"Error getting max energy capacity for {carrier}: {e}")
        return 50000.0


def get_system_limit(limit_type: str, limits: Optional[Dict[str, Any]] = None) -> float:
    """
    Get system-level limits.
    
    Parameters
    ----------
    limit_type : str
        Type of system limit ('total_renewable_capacity', 'total_storage_power', 
        'total_storage_energy', 'default_lifetime', 'max_operational_hours')
    limits : dict, optional
        Dictionary of technical limits
        
    Returns
    -------
    float
        System limit value
    """
    if limits is None:
        limits = load_technical_limits()
        
    try:
        if "system" in limits and limit_type in limits["system"]:
            return float(limits["system"][limit_type])
    except Exception as e:
        logger.error(f"Error getting system limit {limit_type}: {e}")
    
    # Fallbacks
    fallbacks = {
        "total_renewable_capacity": 200000.0,
        "total_storage_power": 100000.0,
        "total_storage_energy": 2000000.0,
        "default_lifetime": 40.0,
        "max_operational_hours": 1e6,
    }
    return fallbacks.get(limit_type, 10000.0)


def replace_infinite_bounds(value: Union[float, pd.Series, np.ndarray], 
                            replacement_factor: float = 1000.0,
                            limits: Optional[Dict[str, Any]] = None) -> Union[float, pd.Series, np.ndarray]:
    """
    Replace infinite values with technically justified finite bounds.
    
    Parameters
    ----------
    value : float, pd.Series, or np.ndarray
        Values that may contain infinite bounds
    replacement_factor : float, default 1000.0
        Factor to use when determining replacement values
    limits : dict, optional
        Dictionary of technical limits
        
    Returns
    -------
    float, pd.Series, or np.ndarray
        Values with infinite bounds replaced by finite limits
    """
    if isinstance(value, (float, int)):
        if np.isinf(value):
            return get_system_limit("max_operational_hours", limits)
        return float(value)
        
    elif isinstance(value, pd.Series):
        finite_values = value.copy()
        inf_mask = np.isinf(finite_values)
        if inf_mask.any():
            replacement_val = get_system_limit("max_operational_hours", limits)
            finite_values[inf_mask] = replacement_val
            logger.info(f"Replaced {inf_mask.sum()} infinite values with {replacement_val}")
        return finite_values
        
    elif isinstance(value, np.ndarray):
        finite_values = value.copy()
        inf_mask = np.isinf(finite_values)
        if inf_mask.any():
            replacement_val = get_system_limit("max_operational_hours", limits)
            finite_values[inf_mask] = replacement_val
            logger.info(f"Replaced {inf_mask.sum()} infinite values with {replacement_val}")
        return finite_values
        
    return value


def validate_bounds(component_type: str, carrier: str, value: float, 
                    limits: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate that a capacity value is within technically reasonable bounds.
    
    Parameters
    ----------
    component_type : str
        Component type ('generators', 'storage', 'lines', 'links')
    carrier : str
        Carrier/technology name
    value : float
        Value to validate
    limits : dict, optional
        Dictionary of technical limits
        
    Returns
    -------
    bool
        True if value is within reasonable bounds
    """
    try:
        max_limit = get_max_cap(carrier, component_type, limits)
        if value > max_limit:
            logger.warning(f"{component_type} {carrier}: value {value} exceeds technical limit {max_limit}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error validating bounds for {component_type} {carrier}: {e}")
        return False
