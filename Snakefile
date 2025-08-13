# SPDX-FileCopyrightText: Contributors to PyPSA-Eur <https://github.com/pypsa/pypsa-eur>
#
# SPDX-License-Identifier: MIT

# =============================================================================
# PYPSA-DE SNAKEFILE - Main Workflow Definition
# =============================================================================
# This Snakefile orchestrates the complete energy system modeling workflow for
# Germany, including electricity, heat, transport, and industry sectors.
# It uses Snakemake to manage dependencies and automate the modeling pipeline.

from pathlib import Path
import yaml
from os.path import normpath, exists, join
from shutil import copyfile, move, rmtree
from snakemake.utils import min_version

# Ensure minimum Snakemake version for compatibility
min_version("8.11")

# Import helper functions for path management and scenario handling
from scripts._helpers import (
    path_provider,      # Manages shared vs. scenario-specific resource paths
    get_scenarios,      # Extracts scenario configurations from run config
    get_rdir,          # Gets run directory name
    get_shadow,        # Gets shadow configuration for parallel runs
)

# =============================================================================
# CONFIGURATION FILES
# =============================================================================
# Load default configuration files - these provide baseline settings
configfile: "config/config.default.yaml"        # Main model configuration
configfile: "config/plotting.default.yaml"      # Plotting and visualization settings

# Load user-specific configuration if it exists (overrides defaults)
if Path("config/config.yaml").exists():
    configfile: "config/config.yaml"

# =============================================================================
# CONFIGURATION EXTRACTION AND SETUP
# =============================================================================
# Extract key configuration parameters
run = config["run"]                              # Run-specific settings
scenarios = get_scenarios(run)                   # Available scenarios
RDIR = get_rdir(run)                            # Run directory name
shadow_config = get_shadow(run)                  # Shadow configuration for parallel runs

# Set up shared resource management across scenarios
shared_resources = run["shared_resources"]["policy"]      # Which resources to share
exclude_from_shared = run["shared_resources"]["exclude"] # Which resources to exclude

# Define path providers for different resource types
logs = path_provider("logs/", RDIR, shared_resources, exclude_from_shared)           # Log files
benchmarks = path_provider("benchmarks/", RDIR, shared_resources, exclude_from_shared) # Performance benchmarks
resources = path_provider("resources/", RDIR, shared_resources, exclude_from_shared)   # Intermediate data

# Set up cutout directory for renewable energy data (weather/climate data)
cutout_dir = config["atlite"]["cutout_directory"]
CDIR = Path(cutout_dir).joinpath("" if run["shared_cutouts"] else RDIR)

# Define results directory for final outputs
RESULTS = "results/" + RDIR

# =============================================================================
# LOCAL RULES AND CONSTRAINTS
# =============================================================================
# Define rules that should not be executed on remote clusters
localrules:
    purge,  # Purge rule must run locally for safety

# Define constraints for wildcards to prevent invalid combinations
wildcard_constraints:
    clusters="[0-9]+(m|c)?|all|adm",           # Cluster sizes: numbers, 'all', or 'adm'
    opts=r"[-+a-zA-Z0-9\.]*",                  # Option strings for technology choices
    sector_opts=r"[-+a-zA-Z0-9\.\s]*",         # Sector-specific options
    planning_horizons=r"[0-9]{4}",             # Year format (e.g., 2035)

# =============================================================================
# RULE MODULE INCLUSIONS
# =============================================================================
# Include modular rule files that contain specific workflow components
include: "rules/common.smk"           # Common utilities and helper rules
include: "rules/collect.smk"          # Data collection and aggregation
include: "rules/retrieve.smk"         # Data retrieval from external sources
include: "rules/build_electricity.smk" # Electricity system construction
include: "rules/build_sector.smk"     # Multi-sector energy system building
include: "rules/solve_electricity.smk" # Electricity system optimization
include: "rules/postprocess.smk"      # Results analysis and visualization
include: "rules/development.smk"      # Development and testing utilities

# Conditionally include foresight-specific solving rules based on configuration
if config["foresight"] == "overnight":
    include: "rules/solve_overnight.smk"  # Overnight optimization (no learning)

if config["foresight"] == "myopic":
    include: "rules/solve_myopic.smk"     # Myopic optimization (limited foresight)

if config["foresight"] == "perfect":
    include: "rules/solve_perfect.smk"    # Perfect foresight optimization

# =============================================================================
# MAIN WORKFLOW RULE
# =============================================================================
# This rule defines all the outputs that should be generated
# It serves as the entry point for the entire workflow
rule all:
    input:
        # Cost analysis visualizations
        expand(RESULTS + "graphs/costs.svg", run=config["run"]["name"]),
        
        # Power network maps
        expand(resources("maps/power-network.pdf"), run=config["run"]["name"]),
        expand(
            resources("maps/power-network-s-{clusters}.pdf"),
            run=config["run"]["name"],
            **config["scenario"],
        ),
        
        # Base scenario cost maps for different cluster sizes and options
        expand(
            RESULTS
            + "maps/base_s_{clusters}_{opts}_{sector_opts}-costs-all_{planning_horizons}.pdf",
            run=config["run"]["name"],
            **config["scenario"],
        ),
        
        # Hydrogen network maps (conditional on H2_network being enabled)
        lambda w: expand(
            (
                RESULTS
                + "maps/base_s_{clusters}_{opts}_{sector_opts}-h2_network_{planning_horizons}.pdf"
                if config_provider("sector", "H2_network")(w)
                else []
            ),
            run=config["run"]["name"],
            **config["scenario"],
        ),
        
        # Gas network maps (conditional on gas_network being enabled)
        lambda w: expand(
            (
                RESULTS
                + "maps/base_s_{clusters}_{opts}_{sector_opts}-ch4_network_{planning_horizons}.pdf"
                if config_provider("sector", "gas_network")(w)
                else []
            ),
            run=config["run"]["name"],
            **config["scenario"],
        ),
        
        # Cumulative costs CSV (only for myopic foresight)
        lambda w: expand(
            (
                RESULTS + "csvs/cumulative_costs.csv"
                if config_provider("foresight")(w) == "myopic"
                else []
            ),
            run=config["run"]["name"],
        ),
        
        # Balance maps for different energy carriers
        lambda w: expand(
            (
                RESULTS
                + "maps/base_s_{clusters}_{opts}_{sector_opts}_{planning_horizons}-balance_map_{carrier}.pdf"
            ),
            **config["scenario"],
            run=config["run"]["name"],
            carrier=config_provider("plotting", "balance_map", "bus_carriers")(w),
        ),
        
        # Balance timeseries visualizations
        expand(
            RESULTS
            + "graphics/balance_timeseries/s_{clusters}_{opts}_{sector_opts}_{planning_horizons}",
            run=config["run"]["name"],
            **config["scenario"],
        ),
        
        # Heatmap timeseries visualizations
        expand(
            RESULTS
            + "graphics/heatmap_timeseries/s_{clusters}_{opts}_{sector_opts}_{planning_horizons}",
            run=config["run"]["name"],
            **config["scenario"],
        ),
    default_target: True

# =============================================================================
# SCENARIO CREATION RULE
# =============================================================================
# Creates scenario configuration files based on the main configuration
rule create_scenarios:
    output:
        config["run"]["scenarios"]["file"],  # Output scenario file path
    conda:
        "envs/environment.yaml"              # Conda environment specification
    script:
        "config/create_scenarios.py"         # Python script to generate scenarios

# =============================================================================
# PURGE RULE (SAFETY CLEANUP)
# =============================================================================
# Safely removes all generated files with user confirmation
# This is a local rule for safety reasons
rule purge:
    run:
        import builtins
        
        # Prompt user for confirmation before deletion
        do_purge = builtins.input(
            "Do you really want to delete all generated resources, \nresults and docs (downloads are kept)? [y/N] "
        )
        if do_purge == "y":
            # Remove generated directories while keeping downloads
            rmtree("resources/", ignore_errors=True)      # Intermediate data
            rmtree("results/", ignore_errors=True)        # Final results
            rmtree("doc/_build", ignore_errors=True)      # Built documentation
            print("Purging generated resources, results and docs. Downloads are kept.")
        else:
            raise Exception(f"Input {do_purge}. Aborting purge.")

# =============================================================================
# CONFIGURATION DUMP RULE
# =============================================================================
# Dumps the current Snakemake configuration to a YAML file
# This is used by the graph generation rules to ensure consistency
rule dump_graph_config:
    """Dump the current Snakemake configuration to a YAML file for graph generation."""
    output:
        config_file=temp(resources("dag_final_config.yaml")),  # Temporary config file
    run:
        import yaml
        
        # Write current configuration to file
        with open(output.config_file, "w") as f:
            yaml.dump(config, f)

# =============================================================================
# RULE DEPENDENCY GRAPH GENERATION
# =============================================================================
# Generates visualizations of the rule dependency graph (DAG)
# Shows how different rules depend on each other
rule rulegraph:
    """Generates Rule DAG in DOT, PDF, PNG, and SVG formats using the final configuration."""
    message:
        "Creating RULEGRAPH dag in multiple formats using the final configuration."
    input:
        config_file=rules.dump_graph_config.output.config_file,  # Final config file
    output:
        dot=resources("dag_rulegraph.dot"),   # Graphviz DOT format
        pdf=resources("dag_rulegraph.pdf"),   # PDF visualization
        png=resources("dag_rulegraph.png"),   # PNG image
        svg=resources("dag_rulegraph.svg"),   # Scalable vector graphics
    conda:
        "envs/environment.yaml"               # Required environment
    shell:
        r"""
        # Generate DOT file using nested snakemake with the dumped final config
        echo "[Rule rulegraph] Using final config file: {input.config_file}"
        snakemake --rulegraph --configfile {input.config_file} --quiet | sed -n "/digraph/,\$p" > {output.dot}

        # Generate visualizations from the DOT file
        if [ -s {output.dot} ]; then
            echo "[Rule rulegraph] Generating PDF from DOT"
            dot -Tpdf -o {output.pdf} {output.dot} || {{ echo "Error: Failed to generate PDF. Is graphviz installed?" >&2; exit 1; }}
            
            echo "[Rule rulegraph] Generating PNG from DOT"
            dot -Tpng -o {output.png} {output.dot} || {{ echo "Error: Failed to generate PNG. Is graphviz installed?" >&2; exit 1; }}
            
            echo "[Rule rulegraph] Generating SVG from DOT"
            dot -Tsvg -o {output.svg} {output.dot} || {{ echo "Error: Failed to generate SVG. Is graphviz installed?" >&2; exit 1; }}
            
            echo "[Rule rulegraph] Successfully generated all formats."
        else
            echo "[Rule rulegraph] Error: Failed to generate valid DOT content." >&2
            exit 1
        fi
        """

# =============================================================================
# FILE DEPENDENCY GRAPH GENERATION
# =============================================================================
# Generates visualizations of the file dependency graph
# Shows how different output files depend on input files
rule filegraph:
    """Generates File DAG in DOT, PDF, PNG, and SVG formats using the final configuration."""
    message:
        "Creating FILEGRAPH dag in multiple formats using the final configuration."
    input:
        config_file=rules.dump_graph_config.output.config_file,  # Final config file
    output:
        dot=resources("dag_filegraph.dot"),   # Graphviz DOT format
        pdf=resources("dag_filegraph.pdf"),   # PDF visualization
        png=resources("dag_filegraph.png"),   # PNG image
        svg=resources("dag_filegraph.svg"),   # Scalable vector graphics
    conda:
        "envs/environment.yaml"               # Required environment
    shell:
        r"""
        # Generate DOT file using nested snakemake with the dumped final config
        echo "[Rule filegraph] Using final config file: {input.config_file}"
        snakemake --filegraph all --configfile {input.config_file} --quiet | sed -n "/digraph/,\$p" > {output.dot}

        # Generate visualizations from the DOT file
        if [ -s {output.dot} ]; then
            echo "[Rule filegraph] Generating PDF from DOT"
            dot -Tpdf -o {output.pdf} {output.dot} || {{ echo "Error: Failed to generate PDF. Is graphviz installed?" >&2; exit 1; }}
            
            echo "[Rule filegraph] Generating PNG from DOT"
            dot -Tpng -o {output.png} {output.dot} || {{ echo "Error: Failed to generate PNG. Is graphviz installed?" >&2; exit 1; }}
            
            echo "[Rule filegraph] Generating SVG from DOT"
            dot -Tsvg -o {output.svg} {output.dot} || {{ echo "Error: Failed to generate SVG. Is graphviz installed?" >&2; exit 1; }}
            
            echo "[Rule filegraph] Successfully generated all formats."
        else
            echo "[Rule filegraph] Error: Failed to generate valid DOT content." >&2
            exit 1
        fi
        """

# =============================================================================
# DOCUMENTATION BUILDING RULE
# =============================================================================
# Builds the project documentation using Sphinx
rule doc:
    message:
        "Build documentation."
    output:
        directory("doc/_build"),  # Documentation build directory
    shell:
        "make -C doc html"        # Run make command in doc directory

# =============================================================================
# REMOTE SYNCHRONIZATION RULES
# =============================================================================
# Synchronizes local files with remote computing clusters
# Useful for running heavy computations on remote servers

# Full synchronization
rule sync:
    params:
        cluster=f"{config['remote']['ssh']}:{config['remote']['path']}",  # Remote cluster details
    shell:
        """
        # Sync local files to remote cluster
        rsync -uvarh --ignore-missing-args --files-from=.sync-send . {params.cluster}
        
        # Sync resources back from remote (if they exist)
        rsync -uvarh --no-g {params.cluster}/resources . || echo "No resources directory, skipping rsync"
        
        # Sync results back from remote (if they exist)
        rsync -uvarh --no-g {params.cluster}/results . || echo "No results directory, skipping rsync"
        
        # Sync logs back from remote (if they exist)
        rsync -uvarh --no-g {params.cluster}/logs . || echo "No logs directory, skipping rsync"
        """

# Dry-run synchronization (shows what would be synced without actually doing it)
rule sync_dry:
    params:
        cluster=f"{config['remote']['ssh']}:{config['remote']['path']}",  # Remote cluster details
    shell:
        """
        # Dry-run sync to remote cluster (shows what would be sent)
        rsync -uvarh --ignore-missing-args --files-from=.sync-send . {params.cluster} -n
        
        # Dry-run sync of resources from remote (shows what would be received)
        rsync -uvarh --no-g {params.cluster}/resources . -n || echo "No resources directory, skipping rsync"
        
        # Dry-run sync of results from remote (shows what would be received)
        rsync -uvarh --no-g {params.cluster}/results . -n || echo "No results directory, skipping rsync"
        
        # Dry-run sync of logs from remote (shows what would be received)
        rsync -uvarh --no-g {params.cluster}/logs . -n || echo "No logs directory, skipping rsync"
        """
