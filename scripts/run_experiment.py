"""
Main script to configure and run graph reduction experiments.
Edit the 'EXPERIMENT CONFIGURATION' section to define a run.
"""

import sys
from pathlib import Path

# Add the source directory to the Python path for module access
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from graph_reduction.cli import run_experiment, Method, Metric

# ======================================================================
# --- EXPERIMENT CONFIGURATION ---
# ======================================================================

# 1. Choose the method: 
#    - Method.coarsenet
#    - Method.coconut
METHOD_TO_RUN = Method.coarsenet

# 2. Choose the dataset directory name:
#    - "big_nets"
#    - "small_nets"
DATASET_TO_RUN = "big_nets"

# 3. Define a list of reduction ratios (floats between 0 and 1)
RATIOS_TO_RUN = [i / 100 for i in range(10, 100, 5)]

# 4. Select which metrics to compute from the available options:
#    - Metric.spectral_ratio_L
#    - Metric.spectral_gap_A
#    - Metric.algebraic_connectivity_L
#    - Metric.spectral_radius_A
#    Leave the list empty [] to compute all available metrics.
METRICS_TO_COMPUTE = []

# 5. Other settings
VERBOSE_OUTPUT = False
SAVE_REDUCED_GRAPHS = True
OUTPUT_FILE_FORMAT = "excel"  # "excel", "csv", or "json"

# ======================================================================
# --- END OF CONFIGURATION ---
# ======================================================================

def main():
    """Constructs the data path and calls the CLI function with the configuration."""
    data_dir = Path("data") / DATASET_TO_RUN
    
    if not data_dir.exists():
        print(f"Error: Dataset directory not found at '{data_dir.resolve()}'")
        print("Please ensure the specified dataset directory exists.")
        return 1

    try:
        # Call the underlying CLI function with the configured parameters
        run_experiment(
            data_dir=data_dir,
            method=METHOD_TO_RUN,
            metrics_to_compute=METRICS_TO_COMPUTE,
            ratios=RATIOS_TO_RUN,
            verbose=VERBOSE_OUTPUT,
            save_graphs=SAVE_REDUCED_GRAPHS,
            output_format=OUTPUT_FILE_FORMAT
        )
        print("\nScript finished successfully.")
        return 0
    except Exception as e:
        print(f"\nAn error occurred during the experiment: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())