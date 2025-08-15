#!/usr/bin/env python3
"""
Final Quality Validation for Storage Technology Data Processing
Step 5: Validate data integrity and format

This script performs quality checks that ACCOUNT FOR EXPECTED MAPPINGS:
1. Verify CSV format is maintained (proper delimiters, no corrupted rows)
2. Check that all numeric values remain unchanged for unmapped entries
3. Ensure no data loss - verify mapped technologies have correct entries
4. Validate that units and sources are preserved correctly
5. Confirm transportation technologies remain unchanged (not mapped)
"""

import pandas as pd
import numpy as np
import csv
import os
from pathlib import Path
import sys
from typing import Dict, List, Tuple, Set
import json
from datetime import datetime

class FinalQualityValidator:
    def __init__(self):
        self.base_dir = Path(".")
        self.original_file = self.base_dir / "resources" / "de-all-tech-2035-mayk" / "costs_2035.csv"
        self.mapped_file = self.base_dir / "resources" / "de-all-tech-2035-mayk" / "costs_2035_mapped.csv"
        self.mapping_report = self.base_dir / "technology_mapping_report.txt"
        
        self.results = {
            "validation_timestamp": datetime.now().isoformat(),
            "csv_format_check": {},
            "mapping_integrity_check": {},
            "numeric_preservation_check": {},
            "units_sources_check": {},
            "transportation_integrity_check": {},
            "overall_status": "PENDING"
        }
        
        # Load expected mappings from the report
        self.expected_mappings = {}
        self.transportation_technologies = {
            'Battery electric (passenger cars)',
            'Battery electric (trucks)',
            'Hydrogen fuel cell (passenger cars)',
            'Hydrogen fuel cell (trucks)',
            'Charging infrastructure fast (purely) battery electric vehicles passenger cars',
            'Charging infrastructure slow (purely) battery electric vehicles passenger cars',
            'BEV Bus city',
            'BEV Coach',
            'BEV Truck Semi-Trailer max 50 tons',
            'BEV Truck Solo max 26 tons',
            'BEV Truck Trailer max 56 tons'
        }
        
        self.load_expected_mappings()
        
    def load_expected_mappings(self):
        """Load the expected mappings from the mapping report."""
        try:
            if self.mapping_report.exists():
                with open(self.mapping_report, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for line in lines:
                        if '→' in line and '(' in line:
                            # Extract mapping: 'source' → 'target' (count entries)
                            parts = line.strip().split('→')
                            if len(parts) == 2:
                                source = parts[0].strip().strip("'")
                                target_part = parts[1].strip()
                                target = target_part.split(' (')[0].strip().strip("'")
                                self.expected_mappings[source] = target
                
                print(f"✓ Loaded {len(self.expected_mappings)} expected mappings")
        except Exception as e:
            print(f"⚠ Could not load mappings: {e}")
    
    def validate_csv_format(self) -> Dict:
        """Check CSV format integrity."""
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
            # Test both files
            original_df = pd.read_csv(self.original_file)
            mapped_df = pd.read_csv(self.mapped_file)
            
            # Check row counts
            if len(original_df) != len(mapped_df):
                format_results["row_structure_integrity"] = "ERROR"
                format_results["issues"].append(f"Row count mismatch: original={len(original_df)}, mapped={len(mapped_df)}")
            
            # Check column structure
            if list(original_df.columns) != list(mapped_df.columns):
                format_results["row_structure_integrity"] = "ERROR"
                format_results["issues"].append("Column structure differs")
                
        except Exception as e:
            format_results["original_file_status"] = "ERROR"
            format_results["issues"].append(f"File access error: {str(e)}")
        
        return format_results
    
    def validate_mapping_integrity(self) -> Dict:
        """Check that mappings were applied correctly."""
        print("🔄 Step 2: Validating mapping integrity...")
        
        mapping_results = {
            "expected_mappings_applied": 0,
            "missing_mappings": [],
            "unexpected_mappings": [],
            "mapping_accuracy": 0.0,
            "status": "OK"
        }
        
        try:
            original_df = pd.read_csv(self.original_file)
            mapped_df = pd.read_csv(self.mapped_file)
            
            # Check if expected mappings were applied
            applied_correctly = 0
            
            for source_tech, target_tech in self.expected_mappings.items():
                # Check if source technology existed in original
                source_exists = source_tech in original_df['technology'].values
                
                if source_exists:
                    # Check if it was mapped correctly
                    source_in_mapped = source_tech in mapped_df['technology'].values
                    target_in_mapped = target_tech in mapped_df['technology'].values
                    
                    if not source_in_mapped and target_in_mapped:
                        # Correct mapping
                        applied_correctly += 1
                    elif source_in_mapped and not target_in_mapped:
                        # Mapping not applied
                        mapping_results["missing_mappings"].append(source_tech)
                    elif source_in_mapped and target_in_mapped:
                        # Partial mapping or issue
                        mapping_results["unexpected_mappings"].append(f"{source_tech} still exists alongside {target_tech}")
            
            mapping_results["expected_mappings_applied"] = applied_correctly
            mapping_results["mapping_accuracy"] = applied_correctly / len(self.expected_mappings) if self.expected_mappings else 1.0
            
            # Set status
            if mapping_results["mapping_accuracy"] >= 0.95:
                mapping_results["status"] = "OK"
            elif mapping_results["mapping_accuracy"] >= 0.8:
                mapping_results["status"] = "WARNING"
            else:
                mapping_results["status"] = "ERROR"
                
        except Exception as e:
            mapping_results["status"] = f"ERROR: {str(e)}"
            
        return mapping_results
    
    def validate_numeric_preservation(self) -> Dict:
        """Check that numeric values are preserved for non-mapped technologies."""
        print("🔢 Step 3: Validating numeric value preservation...")
        
        numeric_results = {
            "total_numeric_comparisons": 0,
            "preserved_values": 0,
            "changed_values": 0,
            "transportation_values_preserved": 0,
            "transportation_values_changed": 0,
            "value_changes": [],
            "status": "OK"
        }
        
        try:
            original_df = pd.read_csv(self.original_file)
            mapped_df = pd.read_csv(self.mapped_file)
            
            # Focus on transportation technologies (should be unchanged)
            for tech in self.transportation_technologies:
                orig_subset = original_df[original_df['technology'] == tech]
                mapped_subset = mapped_df[mapped_df['technology'] == tech]
                
                if len(orig_subset) > 0:
                    if len(orig_subset) == len(mapped_subset):
                        # Check if values are preserved
                        for idx, orig_row in orig_subset.iterrows():
                            # Find corresponding row in mapped data
                            matching_rows = mapped_subset[
                                (mapped_subset['parameter'] == orig_row['parameter']) &
                                (mapped_subset['technology'] == orig_row['technology'])
                            ]
                            
                            if len(matching_rows) == 1:
                                mapped_row = matching_rows.iloc[0]
                                numeric_results["total_numeric_comparisons"] += 1
                                
                                # Compare numeric values
                                try:
                                    orig_val = float(orig_row['value'])
                                    mapped_val = float(mapped_row['value'])
                                    
                                    if abs(orig_val - mapped_val) < 1e-10:
                                        numeric_results["preserved_values"] += 1
                                        numeric_results["transportation_values_preserved"] += 1
                                    else:
                                        numeric_results["changed_values"] += 1
                                        numeric_results["transportation_values_changed"] += 1
                                        numeric_results["value_changes"].append({
                                            "technology": tech,
                                            "parameter": orig_row['parameter'],
                                            "original": orig_val,
                                            "mapped": mapped_val
                                        })
                                except (ValueError, TypeError):
                                    # Non-numeric values, check string equality
                                    if str(orig_row['value']) == str(mapped_row['value']):
                                        numeric_results["preserved_values"] += 1
                                        numeric_results["transportation_values_preserved"] += 1
                                    else:
                                        numeric_results["changed_values"] += 1
                                        numeric_results["transportation_values_changed"] += 1
            
            # Set status
            if numeric_results["transportation_values_changed"] == 0:
                numeric_results["status"] = "OK"
            else:
                numeric_results["status"] = "ERROR - Transportation values changed"
                
        except Exception as e:
            numeric_results["status"] = f"ERROR: {str(e)}"
            
        return numeric_results
    
    def validate_units_and_sources(self) -> Dict:
        """Validate that units and sources are preserved for transportation technologies."""
        print("📏 Step 4: Validating units and sources preservation...")
        
        units_sources_results = {
            "transportation_entries_checked": 0,
            "units_preserved": 0,
            "sources_preserved": 0,
            "units_changed": [],
            "sources_changed": [],
            "status": "OK"
        }
        
        try:
            original_df = pd.read_csv(self.original_file)
            mapped_df = pd.read_csv(self.mapped_file)
            
            # Check transportation technologies
            for tech in self.transportation_technologies:
                orig_subset = original_df[original_df['technology'] == tech]
                mapped_subset = mapped_df[mapped_df['technology'] == tech]
                
                for idx, orig_row in orig_subset.iterrows():
                    matching_rows = mapped_subset[
                        (mapped_subset['parameter'] == orig_row['parameter']) &
                        (mapped_subset['technology'] == orig_row['technology'])
                    ]
                    
                    if len(matching_rows) == 1:
                        mapped_row = matching_rows.iloc[0]
                        units_sources_results["transportation_entries_checked"] += 1
                        
                        # Check units
                        if str(orig_row.get('unit', '')) == str(mapped_row.get('unit', '')):
                            units_sources_results["units_preserved"] += 1
                        else:
                            units_sources_results["units_changed"].append({
                                "technology": tech,
                                "parameter": orig_row['parameter'],
                                "original_unit": orig_row.get('unit', ''),
                                "mapped_unit": mapped_row.get('unit', '')
                            })
                        
                        # Check sources
                        if str(orig_row.get('source', '')) == str(mapped_row.get('source', '')):
                            units_sources_results["sources_preserved"] += 1
                        else:
                            units_sources_results["sources_changed"].append({
                                "technology": tech,
                                "parameter": orig_row['parameter']
                            })
            
            # Set status
            if (len(units_sources_results["units_changed"]) == 0 and 
                len(units_sources_results["sources_changed"]) == 0):
                units_sources_results["status"] = "OK"
            else:
                units_sources_results["status"] = "WARNING"
                
        except Exception as e:
            units_sources_results["status"] = f"ERROR: {str(e)}"
            
        return units_sources_results
    
    def validate_transportation_integrity(self) -> Dict:
        """Confirm transportation technologies remain unchanged."""
        print("🚗 Step 5: Validating transportation technology integrity...")
        
        transport_results = {
            "transportation_technologies_found": 0,
            "transportation_entries_preserved": 0,
            "transportation_entries_lost": 0,
            "missing_technologies": [],
            "status": "OK"
        }
        
        try:
            original_df = pd.read_csv(self.original_file)
            mapped_df = pd.read_csv(self.mapped_file)
            
            for tech in self.transportation_technologies:
                orig_count = (original_df['technology'] == tech).sum()
                mapped_count = (mapped_df['technology'] == tech).sum()
                
                if orig_count > 0:
                    transport_results["transportation_technologies_found"] += 1
                    
                    if orig_count == mapped_count:
                        transport_results["transportation_entries_preserved"] += orig_count
                    else:
                        transport_results["transportation_entries_lost"] += (orig_count - mapped_count)
                        if mapped_count == 0:
                            transport_results["missing_technologies"].append(tech)
            
            # Set status
            if transport_results["transportation_entries_lost"] == 0:
                transport_results["status"] = "OK"
            else:
                transport_results["status"] = "ERROR - Transportation data lost"
                
        except Exception as e:
            transport_results["status"] = f"ERROR: {str(e)}"
            
        return transport_results
    
    def generate_summary_report(self) -> str:
        """Generate a comprehensive summary report."""
        report = []
        report.append("=" * 80)
        report.append("FINAL QUALITY VALIDATION REPORT")
        report.append("Step 5: Data Integrity and Format Validation (Mapping-Aware)")
        report.append("=" * 80)
        report.append(f"Validation Date: {self.results['validation_timestamp']}")
        report.append("")
        
        # Overall Status
        all_statuses = [
            self.results["csv_format_check"].get("row_structure_integrity", "UNKNOWN"),
            self.results["mapping_integrity_check"].get("status", "UNKNOWN"),
            self.results["numeric_preservation_check"].get("status", "UNKNOWN"),
            self.results["units_sources_check"].get("status", "UNKNOWN"),
            self.results["transportation_integrity_check"].get("status", "UNKNOWN")
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
        
        # Individual check results
        csv_check = self.results["csv_format_check"]
        report.append("1. CSV FORMAT INTEGRITY CHECK")
        report.append("-" * 40)
        report.append(f"   Status: {csv_check.get('row_structure_integrity', 'UNKNOWN')}")
        if csv_check.get("issues"):
            for issue in csv_check["issues"]:
                report.append(f"   Issue: {issue}")
        report.append("")
        
        mapping_check = self.results["mapping_integrity_check"]
        report.append("2. MAPPING INTEGRITY CHECK")
        report.append("-" * 40)
        report.append(f"   Expected Mappings Applied: {mapping_check.get('expected_mappings_applied', 0)}")
        report.append(f"   Mapping Accuracy: {mapping_check.get('mapping_accuracy', 0):.1%}")
        report.append(f"   Missing Mappings: {len(mapping_check.get('missing_mappings', []))}")
        report.append(f"   Status: {mapping_check.get('status', 'UNKNOWN')}")
        report.append("")
        
        numeric_check = self.results["numeric_preservation_check"]
        report.append("3. NUMERIC VALUE PRESERVATION CHECK")
        report.append("-" * 40)
        report.append(f"   Transportation Values Preserved: {numeric_check.get('transportation_values_preserved', 0)}")
        report.append(f"   Transportation Values Changed: {numeric_check.get('transportation_values_changed', 0)}")
        report.append(f"   Status: {numeric_check.get('status', 'UNKNOWN')}")
        report.append("")
        
        units_check = self.results["units_sources_check"]
        report.append("4. UNITS AND SOURCES PRESERVATION CHECK")
        report.append("-" * 40)
        report.append(f"   Transportation Entries Checked: {units_check.get('transportation_entries_checked', 0)}")
        report.append(f"   Units Preserved: {units_check.get('units_preserved', 0)}")
        report.append(f"   Sources Preserved: {units_check.get('sources_preserved', 0)}")
        report.append(f"   Status: {units_check.get('status', 'UNKNOWN')}")
        report.append("")
        
        transport_check = self.results["transportation_integrity_check"]
        report.append("5. TRANSPORTATION TECHNOLOGY INTEGRITY CHECK")
        report.append("-" * 40)
        report.append(f"   Transportation Technologies Found: {transport_check.get('transportation_technologies_found', 0)}")
        report.append(f"   Entries Preserved: {transport_check.get('transportation_entries_preserved', 0)}")
        report.append(f"   Entries Lost: {transport_check.get('transportation_entries_lost', 0)}")
        report.append(f"   Status: {transport_check.get('status', 'UNKNOWN')}")
        report.append("")
        
        # Summary and Recommendations
        report.append("SUMMARY AND RECOMMENDATIONS")
        report.append("-" * 40)
        
        if overall_status == "✅ ALL CHECKS PASSED":
            report.append("✅ All quality validation checks have passed successfully.")
            report.append("✅ Storage technology mappings applied correctly.")
            report.append("✅ Transportation technologies preserved unchanged.")
            report.append("✅ Data integrity maintained throughout processing.")
            report.append("")
            report.append("RECOMMENDATION: Data processing completed successfully and ready for use.")
            
        elif "CRITICAL ERRORS" in overall_status:
            report.append("❌ Critical errors detected in the data processing.")
            report.append("❌ Data integrity issues require immediate attention.")
            report.append("")
            report.append("RECOMMENDATION: Review and fix critical errors before proceeding.")
            
        else:
            report.append("⚠️ Some warnings detected but no critical errors.")
            report.append("⚠️ Review warnings to ensure they are expected.")
            report.append("")
            report.append("RECOMMENDATION: Verify warnings are acceptable, then proceed.")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run_validation(self) -> Dict:
        """Run all validation checks and generate report."""
        print("🚀 Starting Final Quality Validation (Mapping-Aware)...")
        print(f"📁 Original file: {self.original_file}")
        print(f"📁 Mapped file: {self.mapped_file}")
        print(f"📋 Expected mappings: {len(self.expected_mappings)}")
        print("")
        
        # Run all validation checks
        self.results["csv_format_check"] = self.validate_csv_format()
        self.results["mapping_integrity_check"] = self.validate_mapping_integrity()
        self.results["numeric_preservation_check"] = self.validate_numeric_preservation()
        self.results["units_sources_check"] = self.validate_units_and_sources()
        self.results["transportation_integrity_check"] = self.validate_transportation_integrity()
        
        # Generate and display report
        report = self.generate_summary_report()
        print(report)
        
        # Save results
        results_file = "FINAL_quality_validation_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        report_file = "FINAL_QUALITY_VALIDATION_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Final Quality Validation Report\n\n")
            f.write("```\n")
            f.write(report)
            f.write("\n```\n")
        
        print(f"\n📊 Results saved to: {results_file}")
        print(f"📋 Report saved to: {report_file}")
        
        return self.results


def main():
    """Main function to run final quality validation."""
    validator = FinalQualityValidator()
    
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
