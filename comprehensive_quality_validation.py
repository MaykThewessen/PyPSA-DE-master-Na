#!/usr/bin/env python3
"""
Comprehensive Quality Validation for Storage Technology Data Processing
Step 5: Validate data integrity and format

This script performs comprehensive quality checks:
1. Verify CSV format is maintained (proper delimiters, no corrupted rows)
2. Check that all numeric values remain unchanged
3. Ensure no data loss - same number of rows for storage technologies
4. Validate that units and sources are preserved correctly
5. Confirm no accidental changes to non-storage technologies
"""

import pandas as pd
import numpy as np
import csv
import os
from pathlib import Path
import sys
from typing import Dict, List, Tuple, Set
import hashlib
import json
from datetime import datetime

class QualityValidator:
    def __init__(self):
        self.base_dir = Path(".")
        self.original_file = self.base_dir / "resources" / "de-all-tech-2035-mayk" / "costs_2035.csv"
        self.mapped_file = self.base_dir / "resources" / "de-all-tech-2035-mayk" / "costs_2035_mapped.csv"
        self.storage_mapping_file = self.base_dir / "storage_mapping_summary.csv"
        
        self.results = {
            "validation_timestamp": datetime.now().isoformat(),
            "csv_format_check": {},
            "numeric_integrity_check": {},
            "data_loss_check": {},
            "units_sources_check": {},
            "non_storage_integrity_check": {},
            "overall_status": "PENDING"
        }
        
        # Storage technologies to monitor (from mapping summary)
        self.storage_technologies = {
            'vanadium', 'IronAir', 'H2', 'CAES', 
            'battery1', 'battery2', 'battery4', 'battery8', 
            'battery12', 'battery24', 'battery48', 'battery'
        }
        
        # Storage-related terms for partial matching
        self.storage_terms = {
            'battery', 'Battery', 'vanadium', 'Vanadium', 'IronAir', 'iron-air', 'Iron-Air',
            'H2', 'hydrogen', 'Hydrogen', 'CAES', 'caes', 'Compressed-Air', 'compressed-air',
            'electrolyzer', 'electrolysis', 'fuel cell', 'fuel-cell'
        }
        
    def validate_csv_format(self) -> Dict:
        """Check CSV format integrity - proper delimiters, no corrupted rows."""
        print("🔍 Step 1: Validating CSV format integrity...")
        
        format_results = {
            "original_file_status": "OK",
            "mapped_file_status": "OK",
            "delimiter_consistency": "OK",
            "row_structure_integrity": "OK",
            "encoding_check": "OK",
            "issues": []
        }
        
        try:
            # Test original file
            with open(self.original_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                original_rows = list(reader)
                if not original_rows:
                    format_results["original_file_status"] = "ERROR"
                    format_results["issues"].append("Original file is empty")
            
            # Test mapped file
            with open(self.mapped_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                mapped_rows = list(reader)
                if not mapped_rows:
                    format_results["mapped_file_status"] = "ERROR"
                    format_results["issues"].append("Mapped file is empty")
            
            # Check header consistency
            if len(original_rows) > 0 and len(mapped_rows) > 0:
                original_header = original_rows[0]
                mapped_header = mapped_rows[0]
                
                if original_header != mapped_header:
                    format_results["row_structure_integrity"] = "WARNING"
                    format_results["issues"].append("Headers differ between files")
            
            # Check for consistent column count
            original_col_count = len(original_rows[0]) if original_rows else 0
            mapped_col_count = len(mapped_rows[0]) if mapped_rows else 0
            
            if original_col_count != mapped_col_count:
                format_results["row_structure_integrity"] = "ERROR"
                format_results["issues"].append(f"Column count mismatch: original={original_col_count}, mapped={mapped_col_count}")
            
            # Test pandas reading (catches delimiter issues)
            try:
                pd.read_csv(self.original_file)
                pd.read_csv(self.mapped_file)
            except Exception as e:
                format_results["delimiter_consistency"] = "ERROR"
                format_results["issues"].append(f"Pandas CSV reading error: {str(e)}")
                
        except Exception as e:
            format_results["original_file_status"] = "ERROR"
            format_results["issues"].append(f"File access error: {str(e)}")
        
        return format_results
    
    def validate_numeric_integrity(self) -> Dict:
        """Check that all numeric values remain unchanged."""
        print("🔢 Step 2: Validating numeric value integrity...")
        
        numeric_results = {
            "total_numeric_values": 0,
            "unchanged_values": 0,
            "changed_values": 0,
            "storage_tech_changes": 0,
            "non_storage_changes": 0,
            "value_changes": [],
            "status": "OK"
        }
        
        try:
            # Read both files
            original_df = pd.read_csv(self.original_file)
            mapped_df = pd.read_csv(self.mapped_file)
            
            # Focus on numeric columns (value column)
            if 'value' in original_df.columns and 'value' in mapped_df.columns:
                # Create comparison dataframes with technology names for tracking
                orig_values = original_df[['technology', 'parameter', 'value', 'unit']].copy()
                mapped_values = mapped_df[['technology', 'parameter', 'value', 'unit']].copy()
                
                # Convert to numeric where possible
                orig_values['value_num'] = pd.to_numeric(orig_values['value'], errors='coerce')
                mapped_values['value_num'] = pd.to_numeric(mapped_values['value'], errors='coerce')
                
                # Count total numeric values
                numeric_mask = ~orig_values['value_num'].isna()
                numeric_results["total_numeric_values"] = numeric_mask.sum()
                
                # Compare values by creating lookup keys
                orig_lookup = {}
                mapped_lookup = {}
                
                for _, row in orig_values.iterrows():
                    if not pd.isna(row['value_num']):
                        key = f"{row['technology']}||{row['parameter']}"
                        orig_lookup[key] = row['value_num']
                
                for _, row in mapped_values.iterrows():
                    if not pd.isna(row['value_num']):
                        key = f"{row['technology']}||{row['parameter']}"
                        mapped_lookup[key] = row['value_num']
                
                # Find changes
                unchanged = 0
                changed = 0
                
                for key, orig_val in orig_lookup.items():
                    if key in mapped_lookup:
                        mapped_val = mapped_lookup[key]
                        if abs(orig_val - mapped_val) < 1e-10:  # Allow for floating point precision
                            unchanged += 1
                        else:
                            changed += 1
                            tech_name = key.split('||')[0]
                            param_name = key.split('||')[1]
                            
                            # Determine if this is storage-related
                            is_storage = any(term in tech_name for term in self.storage_terms)
                            
                            change_info = {
                                "technology": tech_name,
                                "parameter": param_name,
                                "original_value": orig_val,
                                "mapped_value": mapped_val,
                                "is_storage_related": is_storage
                            }
                            
                            numeric_results["value_changes"].append(change_info)
                            
                            if is_storage:
                                numeric_results["storage_tech_changes"] += 1
                            else:
                                numeric_results["non_storage_changes"] += 1
                    else:
                        # Value disappeared - this is concerning
                        changed += 1
                        numeric_results["value_changes"].append({
                            "technology": key.split('||')[0],
                            "parameter": key.split('||')[1],
                            "original_value": orig_val,
                            "mapped_value": "MISSING",
                            "is_storage_related": True
                        })
                
                numeric_results["unchanged_values"] = unchanged
                numeric_results["changed_values"] = changed
                
                # Set status
                if changed > 0:
                    if numeric_results["non_storage_changes"] > 0:
                        numeric_results["status"] = "ERROR - Non-storage values changed"
                    else:
                        numeric_results["status"] = "WARNING - Only storage values changed"
                else:
                    numeric_results["status"] = "OK"
            
        except Exception as e:
            numeric_results["status"] = f"ERROR: {str(e)}"
            
        return numeric_results
    
    def validate_data_loss(self) -> Dict:
        """Ensure no data loss - same number of rows for storage technologies."""
        print("📊 Step 3: Validating data completeness...")
        
        data_loss_results = {
            "original_total_rows": 0,
            "mapped_total_rows": 0,
            "storage_tech_counts": {},
            "missing_technologies": [],
            "extra_technologies": [],
            "row_count_changes": {},
            "status": "OK"
        }
        
        try:
            # Read both files
            original_df = pd.read_csv(self.original_file)
            mapped_df = pd.read_csv(self.mapped_file)
            
            data_loss_results["original_total_rows"] = len(original_df)
            data_loss_results["mapped_total_rows"] = len(mapped_df)
            
            # Count storage technology occurrences
            original_storage_counts = {}
            mapped_storage_counts = {}
            
            # Count all technologies that contain storage terms
            for _, row in original_df.iterrows():
                tech = str(row['technology'])
                if any(term in tech for term in self.storage_terms):
                    original_storage_counts[tech] = original_storage_counts.get(tech, 0) + 1
            
            for _, row in mapped_df.iterrows():
                tech = str(row['technology'])
                if any(term in tech for term in self.storage_terms):
                    mapped_storage_counts[tech] = mapped_storage_counts.get(tech, 0) + 1
            
            # Find missing and extra technologies
            orig_techs = set(original_storage_counts.keys())
            mapped_techs = set(mapped_storage_counts.keys())
            
            data_loss_results["missing_technologies"] = list(orig_techs - mapped_techs)
            data_loss_results["extra_technologies"] = list(mapped_techs - orig_techs)
            
            # Check row count changes for each technology
            all_storage_techs = orig_techs | mapped_techs
            for tech in all_storage_techs:
                orig_count = original_storage_counts.get(tech, 0)
                mapped_count = mapped_storage_counts.get(tech, 0)
                
                data_loss_results["storage_tech_counts"][tech] = {
                    "original": orig_count,
                    "mapped": mapped_count,
                    "difference": mapped_count - orig_count
                }
                
                if orig_count != mapped_count:
                    data_loss_results["row_count_changes"][tech] = {
                        "original": orig_count,
                        "mapped": mapped_count,
                        "change": mapped_count - orig_count
                    }
            
            # Determine status
            if data_loss_results["missing_technologies"] or any(
                change["change"] < 0 for change in data_loss_results["row_count_changes"].values()
            ):
                data_loss_results["status"] = "ERROR - Data loss detected"
            elif data_loss_results["row_count_changes"]:
                data_loss_results["status"] = "WARNING - Row count changes detected"
            else:
                data_loss_results["status"] = "OK"
                
        except Exception as e:
            data_loss_results["status"] = f"ERROR: {str(e)}"
            
        return data_loss_results
    
    def validate_units_and_sources(self) -> Dict:
        """Validate that units and sources are preserved correctly."""
        print("📏 Step 4: Validating units and sources preservation...")
        
        units_sources_results = {
            "unit_preservation": {},
            "source_preservation": {},
            "changed_units": [],
            "changed_sources": [],
            "status": "OK"
        }
        
        try:
            # Read both files
            original_df = pd.read_csv(self.original_file)
            mapped_df = pd.read_csv(self.mapped_file)
            
            # Check unit preservation for storage technologies
            units_changed = 0
            sources_changed = 0
            
            # Create lookup dictionaries
            orig_lookup = {}
            mapped_lookup = {}
            
            for _, row in original_df.iterrows():
                tech = str(row['technology'])
                if any(term in tech for term in self.storage_terms):
                    key = f"{tech}||{row['parameter']}"
                    orig_lookup[key] = {
                        'unit': str(row.get('unit', '')),
                        'source': str(row.get('source', ''))
                    }
            
            for _, row in mapped_df.iterrows():
                tech = str(row['technology'])
                if any(term in tech for term in self.storage_terms):
                    key = f"{tech}||{row['parameter']}"
                    mapped_lookup[key] = {
                        'unit': str(row.get('unit', '')),
                        'source': str(row.get('source', ''))
                    }
            
            # Compare units and sources
            for key, orig_data in orig_lookup.items():
                if key in mapped_lookup:
                    mapped_data = mapped_lookup[key]
                    
                    if orig_data['unit'] != mapped_data['unit']:
                        units_changed += 1
                        units_sources_results["changed_units"].append({
                            "key": key,
                            "original_unit": orig_data['unit'],
                            "mapped_unit": mapped_data['unit']
                        })
                    
                    if orig_data['source'] != mapped_data['source']:
                        sources_changed += 1
                        units_sources_results["changed_sources"].append({
                            "key": key,
                            "original_source": orig_data['source'][:100] + "..." if len(orig_data['source']) > 100 else orig_data['source'],
                            "mapped_source": mapped_data['source'][:100] + "..." if len(mapped_data['source']) > 100 else mapped_data['source']
                        })
            
            units_sources_results["unit_preservation"]["total_checked"] = len(orig_lookup)
            units_sources_results["unit_preservation"]["changed_count"] = units_changed
            units_sources_results["unit_preservation"]["preservation_rate"] = 1.0 - (units_changed / len(orig_lookup)) if orig_lookup else 1.0
            
            units_sources_results["source_preservation"]["total_checked"] = len(orig_lookup)
            units_sources_results["source_preservation"]["changed_count"] = sources_changed
            units_sources_results["source_preservation"]["preservation_rate"] = 1.0 - (sources_changed / len(orig_lookup)) if orig_lookup else 1.0
            
            # Set status
            if units_changed > 0 or sources_changed > 0:
                units_sources_results["status"] = "WARNING - Units or sources changed"
            else:
                units_sources_results["status"] = "OK"
                
        except Exception as e:
            units_sources_results["status"] = f"ERROR: {str(e)}"
            
        return units_sources_results
    
    def validate_non_storage_integrity(self) -> Dict:
        """Confirm no accidental changes to non-storage technologies."""
        print("🛡️ Step 5: Validating non-storage technology integrity...")
        
        non_storage_results = {
            "total_non_storage_rows": 0,
            "unchanged_rows": 0,
            "changed_rows": 0,
            "technology_changes": [],
            "parameter_changes": [],
            "value_changes": [],
            "status": "OK"
        }
        
        try:
            # Read both files
            original_df = pd.read_csv(self.original_file)
            mapped_df = pd.read_csv(self.mapped_file)
            
            # Filter to non-storage technologies
            orig_non_storage = original_df[~original_df['technology'].apply(
                lambda x: any(term in str(x) for term in self.storage_terms)
            )].copy()
            
            mapped_non_storage = mapped_df[~mapped_df['technology'].apply(
                lambda x: any(term in str(x) for term in self.storage_terms)
            )].copy()
            
            non_storage_results["total_non_storage_rows"] = len(orig_non_storage)
            
            # Create comparison keys
            orig_keys = set()
            mapped_keys = set()
            
            for _, row in orig_non_storage.iterrows():
                key = f"{row['technology']}||{row['parameter']}"
                orig_keys.add(key)
            
            for _, row in mapped_non_storage.iterrows():
                key = f"{row['technology']}||{row['parameter']}"
                mapped_keys.add(key)
            
            # Find changes
            unchanged_keys = orig_keys & mapped_keys
            missing_keys = orig_keys - mapped_keys
            extra_keys = mapped_keys - orig_keys
            
            non_storage_results["unchanged_rows"] = len(unchanged_keys)
            non_storage_results["changed_rows"] = len(missing_keys) + len(extra_keys)
            
            # Detailed analysis of changes
            for key in missing_keys:
                tech, param = key.split('||')
                non_storage_results["technology_changes"].append({
                    "technology": tech,
                    "parameter": param,
                    "change_type": "REMOVED"
                })
            
            for key in extra_keys:
                tech, param = key.split('||')
                non_storage_results["technology_changes"].append({
                    "technology": tech,
                    "parameter": param,
                    "change_type": "ADDED"
                })
            
            # Set status
            if non_storage_results["changed_rows"] > 0:
                non_storage_results["status"] = "ERROR - Non-storage technologies modified"
            else:
                non_storage_results["status"] = "OK"
                
        except Exception as e:
            non_storage_results["status"] = f"ERROR: {str(e)}"
            
        return non_storage_results
    
    def generate_summary_report(self) -> str:
        """Generate a comprehensive summary report."""
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE QUALITY VALIDATION REPORT")
        report.append("Step 5: Data Integrity and Format Validation")
        report.append("=" * 80)
        report.append(f"Validation Date: {self.results['validation_timestamp']}")
        report.append("")
        
        # Overall Status
        all_statuses = [
            self.results["csv_format_check"].get("row_structure_integrity", "UNKNOWN"),
            self.results["numeric_integrity_check"].get("status", "UNKNOWN"),
            self.results["data_loss_check"].get("status", "UNKNOWN"),
            self.results["units_sources_check"].get("status", "UNKNOWN"),
            self.results["non_storage_integrity_check"].get("status", "UNKNOWN")
        ]
        
        if all(s == "OK" for s in all_statuses):
            overall_status = "✅ ALL CHECKS PASSED"
        elif any("ERROR" in s for s in all_statuses):
            overall_status = "❌ CRITICAL ERRORS DETECTED"
        else:
            overall_status = "⚠️ WARNINGS DETECTED"
        
        self.results["overall_status"] = overall_status
        
        report.append(f"OVERALL STATUS: {overall_status}")
        report.append("")
        
        # CSV Format Check Results
        report.append("1. CSV FORMAT INTEGRITY CHECK")
        report.append("-" * 40)
        csv_check = self.results["csv_format_check"]
        report.append(f"   Original File Status: {csv_check.get('original_file_status', 'UNKNOWN')}")
        report.append(f"   Mapped File Status: {csv_check.get('mapped_file_status', 'UNKNOWN')}")
        report.append(f"   Delimiter Consistency: {csv_check.get('delimiter_consistency', 'UNKNOWN')}")
        report.append(f"   Row Structure Integrity: {csv_check.get('row_structure_integrity', 'UNKNOWN')}")
        
        if csv_check.get("issues"):
            report.append("   Issues found:")
            for issue in csv_check["issues"]:
                report.append(f"     - {issue}")
        report.append("")
        
        # Numeric Integrity Check Results
        report.append("2. NUMERIC VALUE INTEGRITY CHECK")
        report.append("-" * 40)
        numeric_check = self.results["numeric_integrity_check"]
        report.append(f"   Total Numeric Values: {numeric_check.get('total_numeric_values', 0)}")
        report.append(f"   Unchanged Values: {numeric_check.get('unchanged_values', 0)}")
        report.append(f"   Changed Values: {numeric_check.get('changed_values', 0)}")
        report.append(f"   Storage Tech Changes: {numeric_check.get('storage_tech_changes', 0)}")
        report.append(f"   Non-Storage Changes: {numeric_check.get('non_storage_changes', 0)}")
        report.append(f"   Status: {numeric_check.get('status', 'UNKNOWN')}")
        
        if numeric_check.get("value_changes"):
            report.append(f"   First 5 value changes:")
            for change in numeric_check["value_changes"][:5]:
                report.append(f"     - {change['technology']} [{change['parameter']}]: {change['original_value']} → {change['mapped_value']}")
        report.append("")
        
        # Data Loss Check Results
        report.append("3. DATA COMPLETENESS CHECK")
        report.append("-" * 40)
        data_loss_check = self.results["data_loss_check"]
        report.append(f"   Original Total Rows: {data_loss_check.get('original_total_rows', 0)}")
        report.append(f"   Mapped Total Rows: {data_loss_check.get('mapped_total_rows', 0)}")
        report.append(f"   Missing Technologies: {len(data_loss_check.get('missing_technologies', []))}")
        report.append(f"   Extra Technologies: {len(data_loss_check.get('extra_technologies', []))}")
        report.append(f"   Row Count Changes: {len(data_loss_check.get('row_count_changes', {}))}")
        report.append(f"   Status: {data_loss_check.get('status', 'UNKNOWN')}")
        
        if data_loss_check.get("missing_technologies"):
            report.append("   Missing Technologies:")
            for tech in data_loss_check["missing_technologies"][:10]:
                report.append(f"     - {tech}")
        
        if data_loss_check.get("row_count_changes"):
            report.append("   Row Count Changes:")
            for tech, change in list(data_loss_check["row_count_changes"].items())[:10]:
                report.append(f"     - {tech}: {change['original']} → {change['mapped']} ({change['change']:+d})")
        report.append("")
        
        # Units and Sources Check Results
        report.append("4. UNITS AND SOURCES PRESERVATION CHECK")
        report.append("-" * 40)
        units_check = self.results["units_sources_check"]
        
        unit_pres = units_check.get("unit_preservation", {})
        source_pres = units_check.get("source_preservation", {})
        
        report.append(f"   Unit Preservation Rate: {unit_pres.get('preservation_rate', 0):.1%}")
        report.append(f"   Source Preservation Rate: {source_pres.get('preservation_rate', 0):.1%}")
        report.append(f"   Changed Units: {len(units_check.get('changed_units', []))}")
        report.append(f"   Changed Sources: {len(units_check.get('changed_sources', []))}")
        report.append(f"   Status: {units_check.get('status', 'UNKNOWN')}")
        report.append("")
        
        # Non-Storage Integrity Check Results
        report.append("5. NON-STORAGE TECHNOLOGY INTEGRITY CHECK")
        report.append("-" * 40)
        non_storage_check = self.results["non_storage_integrity_check"]
        report.append(f"   Total Non-Storage Rows: {non_storage_check.get('total_non_storage_rows', 0)}")
        report.append(f"   Unchanged Rows: {non_storage_check.get('unchanged_rows', 0)}")
        report.append(f"   Changed Rows: {non_storage_check.get('changed_rows', 0)}")
        report.append(f"   Status: {non_storage_check.get('status', 'UNKNOWN')}")
        
        if non_storage_check.get("technology_changes"):
            report.append("   First 5 technology changes:")
            for change in non_storage_check["technology_changes"][:5]:
                report.append(f"     - {change['technology']} [{change['parameter']}]: {change['change_type']}")
        report.append("")
        
        # Summary and Recommendations
        report.append("SUMMARY AND RECOMMENDATIONS")
        report.append("-" * 40)
        
        if overall_status == "✅ ALL CHECKS PASSED":
            report.append("✅ All quality validation checks have passed successfully.")
            report.append("✅ Data integrity has been maintained throughout the processing.")
            report.append("✅ CSV format is consistent and valid.")
            report.append("✅ No data loss detected for storage technologies.")
            report.append("✅ Units and sources have been preserved correctly.")
            report.append("✅ Non-storage technologies remain unchanged.")
            report.append("")
            report.append("RECOMMENDATION: The data processing is complete and ready for use.")
            
        elif "CRITICAL ERRORS" in overall_status:
            report.append("❌ Critical errors have been detected in the data processing.")
            report.append("❌ Data integrity issues require immediate attention.")
            report.append("")
            report.append("RECOMMENDATION: Review and fix critical errors before proceeding.")
            
        else:
            report.append("⚠️ Some warnings have been detected but no critical errors.")
            report.append("⚠️ Review the warnings to ensure they are expected changes.")
            report.append("")
            report.append("RECOMMENDATION: Verify warnings are intentional, then proceed with caution.")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run_validation(self) -> Dict:
        """Run all validation checks and generate report."""
        print("🚀 Starting Comprehensive Quality Validation...")
        print(f"📁 Original file: {self.original_file}")
        print(f"📁 Mapped file: {self.mapped_file}")
        print("")
        
        # Run all validation checks
        self.results["csv_format_check"] = self.validate_csv_format()
        self.results["numeric_integrity_check"] = self.validate_numeric_integrity()
        self.results["data_loss_check"] = self.validate_data_loss()
        self.results["units_sources_check"] = self.validate_units_and_sources()
        self.results["non_storage_integrity_check"] = self.validate_non_storage_integrity()
        
        # Generate and display report
        report = self.generate_summary_report()
        print(report)
        
        # Save results to file
        results_file = "quality_validation_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Save report to file
        report_file = "QUALITY_VALIDATION_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Quality Validation Report\n\n")
            f.write("```\n")
            f.write(report)
            f.write("\n```\n")
        
        print(f"\n📊 Results saved to: {results_file}")
        print(f"📋 Report saved to: {report_file}")
        
        return self.results


def main():
    """Main function to run quality validation."""
    validator = QualityValidator()
    
    # Check if required files exist
    if not validator.original_file.exists():
        print(f"❌ ERROR: Original file not found: {validator.original_file}")
        return 1
    
    if not validator.mapped_file.exists():
        print(f"❌ ERROR: Mapped file not found: {validator.mapped_file}")
        return 1
    
    # Run validation
    results = validator.run_validation()
    
    # Return appropriate exit code
    overall_status = results.get("overall_status", "")
    if "ALL CHECKS PASSED" in overall_status:
        return 0
    elif "CRITICAL ERRORS" in overall_status:
        return 2
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
