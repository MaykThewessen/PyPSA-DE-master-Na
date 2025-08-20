"""
Snakemake rules for automatic dashboard generation after optimization.
"""

import os
from datetime import datetime

rule generate_dashboard:
    """
    Generate interactive dashboard from optimization results.
    This rule runs after solve_elec_networks to automatically create visualizations.
    """
    input:
        networks=expand(
            "results/{scenario}/networks/base_s_1_elec_Co2L{co2_limit}.nc",
            scenario=config.get("scenarios", ["de-co2-scenario-A-2035", "de-co2-scenario-B-2035", 
                                             "de-co2-scenario-C-2035", "de-co2-scenario-D-2035"]),
            co2_limit=config.get("co2_limits", ["0.15", "0.05", "0.01", "0.00"])
        )
    output:
        csv="results/dashboard/co2_scenarios_results_{timestamp}.csv",
        html="results/dashboard/co2_scenarios_dashboard_{timestamp}.html"
    params:
        timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    log:
        "logs/dashboard/generate_dashboard_{timestamp}.log"
    script:
        "../scripts/generate_dashboard.py"

rule auto_dashboard_post_solve:
    """
    Automatically generate dashboard after solving electricity networks.
    This is a convenience rule that can be added to the main workflow.
    """
    input:
        networks=rules.solve_elec_networks.output
    output:
        flag=touch("results/dashboard/.dashboard_generated")
    log:
        "logs/dashboard/auto_dashboard.log"
    shell:
        """
        echo "Starting automatic dashboard generation..." > {log}
        python auto_dashboard_generator.py >> {log} 2>&1
        echo "Dashboard generation completed." >> {log}
        """

rule open_dashboard:
    """
    Open the latest dashboard in browser.
    Usage: snakemake open_dashboard
    """
    input:
        flag="results/dashboard/.dashboard_generated"
    shell:
        """
        latest_html=$(ls -t co2_scenarios_dashboard_*.html 2>/dev/null | head -1)
        if [ -n "$latest_html" ]; then
            echo "Opening dashboard: $latest_html"
            open "$latest_html" 2>/dev/null || echo "Please open $latest_html manually"
        else
            echo "No dashboard files found. Run 'snakemake generate_dashboard' first."
        fi
        """
