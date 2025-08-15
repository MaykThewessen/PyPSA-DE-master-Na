#!/usr/bin/env python3
"""
Dashboard Viewer - Quick launcher for PyPSA Interactive Dashboard
================================================================

Simple script to open the interactive dashboard in your default web browser.

Usage: python view_dashboard.py
"""

import os
import webbrowser
import sys

def main():
    """Open the interactive dashboard in the default web browser."""
    
    dashboard_path = "outputs/plots/pypsa_interactive_dashboard.html"
    
    if os.path.exists(dashboard_path):
        # Convert to absolute path for browser
        abs_path = os.path.abspath(dashboard_path)
        file_url = f"file:///{abs_path.replace(os.sep, '/')}"
        
        print("🚀 Opening PyPSA Interactive Dashboard...")
        print(f"📄 File: {abs_path}")
        print(f"🌐 URL: {file_url}")
        
        try:
            webbrowser.open(file_url)
            print("✅ Dashboard opened in your default web browser!")
            print("\n📊 Dashboard Features:")
            print("  • Installed Technology Capacity by Scenario")
            print("  • Energy Storage Capacity by Technology")
            print("  • System Costs vs CO₂ Price (€/tCO₂)")
            print("  • Interactive hover details and zoom")
            print("  • Downloadable plots (PNG/HTML)")
            
        except Exception as e:
            print(f"❌ Failed to open dashboard: {e}")
            print(f"💡 Manual access: Open {abs_path} in your web browser")
            
    else:
        print("❌ Dashboard file not found!")
        print(f"Expected location: {dashboard_path}")
        print("\n💡 To create the dashboard:")
        print("python scripts/create_interactive_dashboard.py")

if __name__ == "__main__":
    main()
