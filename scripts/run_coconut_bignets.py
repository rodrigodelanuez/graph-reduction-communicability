"""
Script to run CoCoNUT experiments on BigNets dataset.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from graph_reduction.core.coarseners import CoCoNUTCoarsener
from graph_reduction.analysis.spectral import analyze_spectral_properties


def run_coconut(data_dir, output_dir, ratios, verbose=True, save_graphs=True):
    """
    Run CoCoNUT coarsening experiments.
    
    Args:
        data_dir: Directory containing .gml network files
        output_dir: Directory to save results
        ratios: List of reduction ratios (alpha values)
        verbose: Print progress information
        save_graphs: Save coarsened graphs
    """
    import networkx as nx
    import csv
    import os
    
    coarsener = CoCoNUTCoarsener()
    results = []
    
    # Get all .gml files
    gml_files = list(Path(data_dir).glob("*.gml"))
    total_experiments = len(gml_files) * len(ratios)
    
    if verbose:
        print(f"Found {len(gml_files)} networks")
        print(f"Running {total_experiments} experiments with {len(ratios)} ratios")
    
    experiment_count = 0
    
    for gml_file in gml_files:
        network_name = gml_file.stem
        
        try:
            # Load network
            G = nx.read_gml(gml_file)
            
            # Sanitize: make undirected, remove self-loops
            if G.is_directed():
                G = G.to_undirected()
            G.remove_edges_from(nx.selfloop_edges(G))
            
            if verbose:
                print(f"\nProcessing {network_name}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
            
            # Create network output directory
            network_dir = output_dir / network_name
            network_dir.mkdir(parents=True, exist_ok=True)
            
            for ratio in ratios:
                experiment_count += 1
                
                try:
                    # Run CoCoNUT
                    start_time = time.time()
                    G_reduced = coarsener.coarsen(G, alpha=ratio, verbose=False)
                    execution_time = time.time() - start_time
                    
                    # Save coarsened graph
                    if save_graphs:
                        output_file = network_dir / f"reduced_CoCoNUT_{network_name}_{ratio:.2f}.gml"
                        nx.write_gml(G_reduced, output_file)
                    
                    # Calculate spectral metrics (same as CoarseNet)
                    spectral_metrics = analyze_spectral_properties(G, G_reduced)
                    
                    # Record results with all spectral metrics
                    result = {
                        'network': network_name,
                        'method': 'CoCoNUT',
                        'ratio': ratio,
                        'execution_time': execution_time,
                        **spectral_metrics  # Include all spectral metrics
                    }
                    results.append(result)
                    
                    if verbose:
                        print(f"  Ratio {ratio:.2f}: {G.number_of_nodes()}→{G_reduced.number_of_nodes()} nodes ({execution_time:.3f}s)")
                
                except Exception as e:
                    if verbose:
                        print(f"  Ratio {ratio:.2f}: Error - {e}")
                    # Create error result with basic structure
                    error_result = {
                        'network': network_name,
                        'method': 'CoCoNUT',
                        'ratio': ratio,
                        'execution_time': 0,
                        'error': str(e),
                        # Add default values for metrics to maintain CSV consistency
                        'Spectral Ratio (Original)': 0,
                        'Spectral Ratio (Reduced)': 0,
                        'Spectral Ratio Reduction (%)': 0,
                        'Eigenratio (Original)': 0,
                        'Eigenratio (Reduced)': 0,
                        'Eigenratio Reduction (%)': 0,
                        'Spectral Gap (Original)': 0,
                        'Spectral Gap (Reduced)': 0,
                        'Spectral Gap Reduction (%)': 0,
                        'Algebraic Connectivity (Original)': 0,
                        'Algebraic Connectivity (Reduced)': 0,
                        'Algebraic Connectivity Reduction (%)': 0,
                        'Spectral Radius (Original)': 0,
                        'Spectral Radius (Reduced)': 0,
                        'Spectral Radius Reduction (%)': 0,
                        'Number of Nodes (Original)': 0,
                        'Number of Nodes (Reduced)': 0,
                        'Number of Edges (Original)': 0,
                        'Number of Edges (Reduced)': 0
                    }
                    results.append(error_result)
        
        except Exception as e:
            if verbose:
                print(f"Error loading {network_name}: {e}")
    
    # Save results to CSV
    if results:
        results_file = output_dir / "coconut_results.csv"
        with open(results_file, 'w', newline='') as csvfile:
            fieldnames = results[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        if verbose:
            print(f"\nResults saved to: {results_file}")


def main():
    """Main function to run the experiment."""
    big_nets_dir = Path("data/big_nets")
    if not big_nets_dir.exists():
        print(f"Error: BigNets directory not found at {big_nets_dir}")
        print("Please ensure the data/big_nets directory exists and contains graph files.")
        return 1

    # Create custom output directory name
    timestamp = int(time.time())
    output_dir = Path("results") / f"coconut_bignets_{timestamp}"

    print("Starting CoCoNUT experiment on BigNets dataset...")
    print(f"Dataset directory: {big_nets_dir.absolute()}")
    print(f"Output directory: {output_dir}")
    
    ratios = [i / 100 for i in range(10, 100, 5)]
    
    try:
        run_coconut(
            data_dir=big_nets_dir,
            output_dir=output_dir,
            ratios=ratios,
            verbose=True,
            save_graphs=True
        )
        print("\nExperiment completed successfully")
        
    except Exception as e:
        print(f"\nExperiment failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
