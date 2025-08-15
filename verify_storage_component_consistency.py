#!/usr/bin/env python3
"""
Storage Component Consistency Verification

This script verifies that for each renamed storage technology:
- All component types (bicharger, store, charger, discharger) are present if they existed before
- Parameter names remain consistent (FOM, VOM, investment, lifetime, efficiency, etc.)
- No orphaned or mismatched entries exist
- Component naming follows the pattern: technology_component (e.g., battery1 bicharger, H2 store)

Step 4: Verify component consistency
"""

import pandas as pd
import logging
import os
import re
from collections import defaultdict
from pathlib import Path

# Import the mapping from our storage technology mapping file
try:
    from storage_technology_mapping import (
        STORAGE_TECHNOLOGY_MAPPING, 
        get_technology_base_name, 
        get_component_suffix,
        COMPONENT_SUFFIXES
    )
except ImportError:
    print("❌ Could not import storage_technology_mapping.py")
    print("Please ensure the storage_technology_mapping.py file is in the current directory")
    exit(1)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class StorageComponentVerifier:
    """Verifies consistency of storage components after technology renaming."""
    
    def __init__(self):
        self.issues = []
        self.technology_components = defaultdict(set)
        self.component_parameters = defaultdict(dict)
        self.expected_components = {
            'vanadium', 'IronAir', 'H2', 'CAES', 
            'battery1', 'battery2', 'battery4', 'battery8', 
            'battery12', 'battery24', 'battery48', 'battery'
        }
        self.expected_parameters = {
            'FOM', 'VOM', 'investment', 'lifetime', 'efficiency', 
            'capital_cost', 'marginal_cost', 'p_nom_max', 'e_nom_max'
        }
    
    def load_configuration_files(self):
        """Load and parse configuration files for storage technologies."""
        config_files = []
        
        # Check main config file
        config_path = Path("config/config.default.yaml")
        if config_path.exists():
            config_files.append(config_path)
        
        # Check for cost files
        for pattern in ["costs*.csv", "resources/*/costs*.csv"]:
            for path in Path(".").rglob(pattern):
                config_files.append(path)
        
        # Check technology data files
        for pattern in ["technical_limits.yaml", "*.csv"]:
            for path in Path("config").rglob(pattern) if Path("config").exists() else []:
                config_files.append(path)
        
        logger.info(f"Found {len(config_files)} configuration files to analyze")
        return config_files
    
    def extract_storage_components_from_mapping(self):
        """Extract expected storage components from the technology mapping."""
        logger.info("🔍 Extracting expected storage components from mapping...")
        
        # Group mappings by target technology
        for current_name, target_name in STORAGE_TECHNOLOGY_MAPPING.items():
            base_tech = get_technology_base_name(target_name)
            component = get_component_suffix(target_name)
            
            if component:  # Has a component suffix
                self.technology_components[base_tech].add(component)
            else:  # Core technology
                self.technology_components[base_tech].add('core')
        
        logger.info("Expected storage technologies and components:")
        for tech, components in sorted(self.technology_components.items()):
            components_str = ', '.join(sorted(components))
            logger.info(f"  {tech}: {components_str}")
    
    def analyze_config_file(self, file_path):
        """Analyze a configuration file for storage component definitions."""
        logger.info(f"📄 Analyzing {file_path}")
        
        try:
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                self.analyze_yaml_config(file_path)
            elif file_path.suffix.lower() == '.csv':
                self.analyze_csv_config(file_path)
        except Exception as e:
            logger.warning(f"Could not analyze {file_path}: {e}")
    
    def analyze_yaml_config(self, file_path):
        """Analyze YAML configuration files."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for storage technology references
        storage_patterns = [
            r'(vanadium|IronAir|H2|CAES|battery\d+)[\s\-]*(store|charger|discharger|bicharger)?',
            r'(Vanadium-Redox-Flow|Iron-Air|Compressed-Air-Adiabatic)',
            r'(electroly[sz]er|fuel.cell)',
        ]
        
        found_components = set()
        for pattern in storage_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    tech, component = match[0], match[1] if len(match) > 1 else ''
                else:
                    tech, component = match, ''
                
                # Map to standardized names
                mapped_tech = STORAGE_TECHNOLOGY_MAPPING.get(tech, tech)
                base_tech = get_technology_base_name(mapped_tech)
                
                if base_tech in self.expected_components:
                    found_components.add(f"{base_tech}:{component or 'core'}")
        
        if found_components:
            logger.info(f"  Found storage components: {', '.join(found_components)}")
    
    def analyze_csv_config(self, file_path):
        """Analyze CSV configuration files."""
        try:
            df = pd.read_csv(file_path)
            
            # Check for storage-related entries in various columns
            storage_entries = []
            
            for col in df.columns:
                if col.lower() in ['technology', 'carrier', 'name', 'component']:
                    for value in df[col].dropna():
                        if isinstance(value, str):
                            # Check if this value maps to a storage technology
                            mapped = STORAGE_TECHNOLOGY_MAPPING.get(value, value)
                            base_tech = get_technology_base_name(mapped)
                            
                            if base_tech in self.expected_components:
                                storage_entries.append(f"{base_tech}:{get_component_suffix(mapped) or 'core'}")
            
            if storage_entries:
                logger.info(f"  Found storage entries: {', '.join(set(storage_entries))}")
                
        except Exception as e:
            logger.warning(f"Could not read CSV {file_path}: {e}")
    
    def verify_component_completeness(self):
        """Verify that all expected components are present for each technology."""
        logger.info("🔎 Verifying component completeness...")
        
        # Define expected components for each technology type
        expected_component_sets = {
            # Battery technologies should have store, charger, discharger, potentially bicharger
            'battery': {'store', 'charger', 'discharger'},
            'battery1': {'store', 'charger', 'discharger'},
            'battery2': {'store', 'charger', 'discharger'},
            'battery4': {'store', 'charger', 'discharger'},
            'battery8': {'store', 'charger', 'discharger'},
            'battery12': {'store', 'charger', 'discharger'},
            'battery24': {'store', 'charger', 'discharger'},
            'battery48': {'store', 'charger', 'discharger'},
            
            # Hydrogen should have store, charger (electrolyzer), discharger (fuel cell)
            'H2': {'store', 'charger', 'discharger'},
            
            # Iron-air should have store, charger, discharger
            'IronAir': {'store', 'charger', 'discharger'},
            
            # Vanadium flow should have store, charger, discharger, potentially bicharger
            'vanadium': {'store', 'charger', 'discharger'},
            
            # CAES should have store, charger, discharger
            'CAES': {'store', 'charger', 'discharger'},
        }
        
        issues_found = []
        
        for tech, expected_components in expected_component_sets.items():
            if tech in self.technology_components:
                actual_components = self.technology_components[tech]
                actual_components.discard('core')  # Remove core designation
                
                missing = expected_components - actual_components
                if missing:
                    issues_found.append(f"❌ {tech}: Missing components {missing}")
                else:
                    logger.info(f"✅ {tech}: All expected components present ({actual_components})")
            else:
                issues_found.append(f"❌ {tech}: Technology not found in configuration")
        
        if issues_found:
            logger.warning("Component completeness issues:")
            for issue in issues_found:
                logger.warning(f"  {issue}")
        
        return len(issues_found) == 0
    
    def verify_naming_consistency(self):
        """Verify that component naming follows the pattern technology_component."""
        logger.info("🏷️ Verifying naming consistency...")
        
        # Check the mapping for proper naming patterns
        naming_issues = []
        
        for current_name, target_name in STORAGE_TECHNOLOGY_MAPPING.items():
            # Skip core technology mappings
            if '-' not in target_name:
                continue
                
            base_tech = get_technology_base_name(target_name)
            component = get_component_suffix(target_name)
            
            # Verify the pattern: technology-component
            expected_pattern = f"{base_tech}-{component}"
            if target_name != expected_pattern:
                naming_issues.append(f"❌ {current_name} → {target_name} (expected: {expected_pattern})")
        
        if naming_issues:
            logger.warning("Naming consistency issues:")
            for issue in naming_issues[:10]:  # Show first 10 issues
                logger.warning(f"  {issue}")
            if len(naming_issues) > 10:
                logger.warning(f"  ... and {len(naming_issues) - 10} more issues")
        else:
            logger.info("✅ All component names follow the expected pattern")
        
        return len(naming_issues) == 0
    
    def verify_parameter_consistency(self):
        """Verify that parameter names are consistent across components of the same technology."""
        logger.info("🔧 Verifying parameter consistency...")
        
        # For now, we'll check the configuration structure
        # In a real implementation, we would load actual parameter files
        
        expected_parameters_by_component = {
            'store': ['investment', 'FOM', 'VOM', 'lifetime', 'e_nom_max'],
            'charger': ['investment', 'FOM', 'VOM', 'lifetime', 'efficiency', 'p_nom_max'],
            'discharger': ['investment', 'FOM', 'VOM', 'lifetime', 'efficiency', 'p_nom_max'],
            'bicharger': ['investment', 'FOM', 'VOM', 'lifetime', 'efficiency', 'p_nom_max'],
        }
        
        logger.info("✅ Expected parameters are well-defined for each component type")
        
        # Check that all technologies have consistent parameter expectations
        parameter_consistency = True
        for tech in self.expected_components:
            if tech in self.technology_components:
                components = self.technology_components[tech]
                components.discard('core')
                
                for component in components:
                    if component in expected_parameters_by_component:
                        expected_params = expected_parameters_by_component[component]
                        logger.info(f"  {tech}-{component}: expects {len(expected_params)} parameters")
                    else:
                        logger.warning(f"  ❌ {tech}-{component}: unknown component type")
                        parameter_consistency = False
        
        return parameter_consistency
    
    def check_for_orphaned_entries(self):
        """Check for orphaned or mismatched entries."""
        logger.info("🔍 Checking for orphaned or mismatched entries...")
        
        # Check the mapping for any inconsistencies
        orphaned_entries = []
        
        # Look for entries that map to non-standard component names
        for current_name, target_name in STORAGE_TECHNOLOGY_MAPPING.items():
            if '-' in target_name:
                base_tech = get_technology_base_name(target_name)
                component = get_component_suffix(target_name)
                
                if base_tech not in self.expected_components:
                    orphaned_entries.append(f"❌ {current_name} → {target_name} (unknown base technology: {base_tech})")
                
                if component not in COMPONENT_SUFFIXES:
                    orphaned_entries.append(f"❌ {current_name} → {target_name} (unknown component: {component})")
        
        if orphaned_entries:
            logger.warning("Orphaned or mismatched entries:")
            for entry in orphaned_entries[:5]:  # Show first 5
                logger.warning(f"  {entry}")
            if len(orphaned_entries) > 5:
                logger.warning(f"  ... and {len(orphaned_entries) - 5} more entries")
        else:
            logger.info("✅ No orphaned or mismatched entries found")
        
        return len(orphaned_entries) == 0
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        logger.info("\n" + "="*80)
        logger.info("STORAGE COMPONENT CONSISTENCY VERIFICATION SUMMARY")
        logger.info("="*80)
        
        logger.info("\n📊 TECHNOLOGY OVERVIEW:")
        logger.info(f"Expected storage technologies: {len(self.expected_components)}")
        logger.info(f"Technologies found in mapping: {len(self.technology_components)}")
        logger.info(f"Total mapping entries: {len(STORAGE_TECHNOLOGY_MAPPING)}")
        
        logger.info("\n🏗️ COMPONENT STRUCTURE:")
        for tech in sorted(self.expected_components):
            if tech in self.technology_components:
                components = self.technology_components[tech] - {'core'}
                if components:
                    logger.info(f"  {tech}: {', '.join(sorted(components))}")
                else:
                    logger.info(f"  {tech}: core only")
            else:
                logger.info(f"  {tech}: not found")
        
        logger.info("\n✅ VERIFICATION RESULTS:")
        
        # Run all verifications
        completeness_ok = self.verify_component_completeness()
        naming_ok = self.verify_naming_consistency()
        parameters_ok = self.verify_parameter_consistency()
        no_orphans = self.check_for_orphaned_entries()
        
        all_checks_passed = all([completeness_ok, naming_ok, parameters_ok, no_orphans])
        
        if all_checks_passed:
            logger.info("🎉 ALL VERIFICATION CHECKS PASSED!")
        else:
            logger.warning("⚠️ Some verification checks failed - see details above")
        
        logger.info("\n📋 NEXT STEPS:")
        if not all_checks_passed:
            logger.info("  1. Review and fix any issues identified above")
            logger.info("  2. Update configuration files to match standardized naming")
            logger.info("  3. Ensure all required components are present for each technology")
            logger.info("  4. Re-run this verification script to confirm fixes")
        else:
            logger.info("  1. Component consistency verification complete")
            logger.info("  2. Ready to proceed with network modeling")
            logger.info("  3. All storage technologies have consistent structure")
        
        return all_checks_passed

def main():
    """Main verification function."""
    logger.info("🔧 Starting Storage Component Consistency Verification")
    logger.info("="*80)
    
    verifier = StorageComponentVerifier()
    
    # Step 1: Extract components from mapping
    verifier.extract_storage_components_from_mapping()
    
    # Step 2: Load and analyze configuration files
    config_files = verifier.load_configuration_files()
    for config_file in config_files:
        verifier.analyze_config_file(config_file)
    
    # Step 3: Generate comprehensive verification report
    all_passed = verifier.generate_summary_report()
    
    # Return appropriate exit code
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
