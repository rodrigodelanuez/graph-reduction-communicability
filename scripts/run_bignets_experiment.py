"""
Script to run CoarseNet experiments on BigNets dataset.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from graph_reduction.cli import run_coarsenet


def main():
    """Main function to run the experiment."""
    big_nets_dir = Path("data/big_nets")
    if not big_nets_dir.exists():
        print(f"Error: BigNets directory not found at {big_nets_dir}")
        print("Please ensure the data/big_nets directory exists and contains graph files.")
        return 1

    # Create custom output directory name
    timestamp = int(time.time())
    output_dir = Path("results") / f"bignets_{timestamp}"

    print("Starting CoarseNet experiment on BigNets dataset...")
    print(f"Dataset directory: {big_nets_dir.absolute()}")
    print(f"Output directory: {output_dir}")
    
    ratios = [i / 100 for i in range(10, 100, 5)]
    
    try:
        run_coarsenet(
            data_dir=big_nets_dir,
            output_dir=output_dir,  # Pass the custom output directory
            ratios=ratios,
            verbose=True,
            save_graphs=True,
            save_matrices=False,
            output_format="excel"
        )
        print("\nExperiment completed successfully")
        
    except Exception as e:
        print(f"\nExperiment failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())