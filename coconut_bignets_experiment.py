#!/usr/bin/env python3
"""
Big Networks Experiment Script for CoCoNUT Algorithm

This script runs comprehensive experiments comparing CoCoNUT with other coarsening methods
on large real-world networks, similar to the experiments in Graph-Reduction-Project.
"""

import os
import sys
import time
import networkx as nx
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import warnings

# Optional imports
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("Warning: pandas not available. Results will be saved as CSV only.")

try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not available. Plotting features disabled.")

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    # Simple replacement for tqdm when not available
    def tqdm(iterable, desc="", leave=True):
        return iterable

# Add the src directory to the path to import our coarseners
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.graph_reduction.core.coarseners import CoCoNUTCoarsener, CoarseNetCoarsener

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

class NetworkExperiment:
    """
    Handles the experimental setup and execution for network coarsening experiments.
    """
    
    def __init__(self, input_path: str, output_path: str):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Experiment parameters
        self.alpha_range = np.arange(0.1, 0.96, 0.05)  # Reduction factors from 0.1 to 0.95
        self.alpha_range = [round(a, 2) for a in self.alpha_range]
        
        # Available methods
        self.available_methods = {
            'CoCoNUT': CoCoNUTCoarsener(),
            'CoarseNet': CoarseNetCoarsener()
        }
    
    def load_networks(self, max_networks: Optional[int] = None) -> List[Tuple[str, nx.Graph]]:
        """
        Load networks from .gml files in the input directory.
        """
        networks = []
        gml_files = list(self.input_path.glob("*.gml"))
        
        if max_networks:
            gml_files = gml_files[:max_networks]
        
        print(f"Loading networks from {self.input_path}")
        
        for gml_file in tqdm(gml_files, desc="Loading networks"):
            try:
                G = nx.read_gml(gml_file)
                # Ensure the graph is undirected and simple
                if G.is_directed():
                    G = G.to_undirected()
                # Remove self-loops
                G.remove_edges_from(nx.selfloop_edges(G))
                # Remove isolated nodes
                G.remove_nodes_from(list(nx.isolates(G)))
                
                if G.number_of_nodes() > 0 and G.number_of_edges() > 0:
                    networks.append((gml_file.stem, G))
                    print(f"  Loaded {gml_file.stem}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
                else:
                    print(f"  Skipped {gml_file.stem}: empty graph")
                    
            except Exception as e:
                print(f"  Error loading {gml_file.name}: {e}")
        
        print(f"Successfully loaded {len(networks)} networks")
        return networks
    
    def calculate_spectral_metrics(self, G_original: nx.Graph, G_reduced: nx.Graph) -> Dict[str, float]:
        """
        Calculate comprehensive spectral metrics for graph comparison.
        """
        metrics = {}
        
        try:
            # Basic graph properties
            metrics['Number of Nodes (Original)'] = G_original.number_of_nodes()
            metrics['Number of Nodes (Reduced)'] = G_reduced.number_of_nodes()
            metrics['Number of Edges (Original)'] = G_original.number_of_edges()
            metrics['Number of Edges (Reduced)'] = G_reduced.number_of_edges()
            
            # Reduction ratios
            node_reduction = (G_original.number_of_nodes() - G_reduced.number_of_nodes()) / G_original.number_of_nodes()
            edge_reduction = (G_original.number_of_edges() - G_reduced.number_of_edges()) / G_original.number_of_edges()
            
            metrics['Node Reduction Ratio'] = node_reduction
            metrics['Edge Reduction Ratio'] = edge_reduction
            
            # Connectivity preservation
            metrics['Original Connected'] = nx.is_connected(G_original)
            metrics['Reduced Connected'] = nx.is_connected(G_reduced)
            
            # Calculate Laplacian eigenvalues for spectral properties
            if G_original.number_of_nodes() > 1 and G_reduced.number_of_nodes() > 1:
                try:
                    # Original graph eigenvalues
                    L_orig = nx.laplacian_matrix(G_original, weight=None).toarray()
                    eigenvals_orig = np.linalg.eigvals(L_orig)
                    eigenvals_orig = np.real(eigenvals_orig[eigenvals_orig > 1e-10])
                    
                    # Reduced graph eigenvalues
                    L_red = nx.laplacian_matrix(G_reduced, weight=None).toarray()
                    eigenvals_red = np.linalg.eigvals(L_red)
                    eigenvals_red = np.real(eigenvals_red[eigenvals_red > 1e-10])
                    
                    if len(eigenvals_orig) > 0 and len(eigenvals_red) > 0:
                        # Algebraic connectivity (second smallest eigenvalue)
                        if len(eigenvals_orig) > 1:
                            alg_conn_orig = np.sort(eigenvals_orig)[1]
                        else:
                            alg_conn_orig = 0
                        
                        if len(eigenvals_red) > 1:
                            alg_conn_red = np.sort(eigenvals_red)[1]
                        else:
                            alg_conn_red = 0
                        
                        metrics['Algebraic Connectivity (Original)'] = alg_conn_orig
                        metrics['Algebraic Connectivity (Reduced)'] = alg_conn_red
                        
                        if alg_conn_orig > 0:
                            metrics['Algebraic Connectivity Preservation'] = alg_conn_red / alg_conn_orig
                        else:
                            metrics['Algebraic Connectivity Preservation'] = 0
                        
                        # Spectral gap (difference between largest and smallest non-zero eigenvalues)
                        spectral_gap_orig = np.max(eigenvals_orig) - np.min(eigenvals_orig)
                        spectral_gap_red = np.max(eigenvals_red) - np.min(eigenvals_red)
                        
                        metrics['Spectral Gap (Original)'] = spectral_gap_orig
                        metrics['Spectral Gap (Reduced)'] = spectral_gap_red
                        
                        if spectral_gap_orig > 0:
                            metrics['Spectral Gap Preservation'] = spectral_gap_red / spectral_gap_orig
                        else:
                            metrics['Spectral Gap Preservation'] = 0
                
                except Exception as e:
                    print(f"    Warning: Could not calculate spectral metrics: {e}")
                    
        except Exception as e:
            print(f"    Error calculating metrics: {e}")
        
        return metrics
    
    def save_graph_data(self, G: nx.Graph, network_name: str, method: str, alpha: float, graph_type: str = "reduced"):
        """
        Save graph in multiple formats for analysis.
        """
        network_folder = self.output_path / network_name
        network_folder.mkdir(exist_ok=True)
        
        if graph_type == "original":
            filename_base = f"{graph_type}_{network_name}"
        else:
            filename_base = f"{graph_type}_{method}_{network_name}_{alpha}"
        
        # Save as GML
        gml_path = network_folder / f"{filename_base}.gml"
        nx.write_gml(G, gml_path)
        
        # Save adjacency matrix as text
        adj_matrix = nx.to_numpy_array(G, weight=None)
        txt_path = network_folder / f"{filename_base}_adj_matrix.txt"
        np.savetxt(txt_path, adj_matrix, fmt='%d')
    
    def run_single_experiment(self, network_name: str, G_original: nx.Graph, 
                            method_name: str, alpha: float) -> Dict[str, any]:
        """
        Run a single coarsening experiment.
        """
        try:
            start_time = time.time()
            
            coarsener = self.available_methods[method_name]
            G_reduced = coarsener.coarsen(G_original, alpha=alpha, verbose=False)
            
            execution_time = time.time() - start_time
            
            # Calculate metrics
            metrics = self.calculate_spectral_metrics(G_original, G_reduced)
            
            # Add experiment metadata
            result = {
                'Network': network_name,
                'Method': method_name,
                'Alpha': alpha,
                'Execution_Time': execution_time,
                **metrics
            }
            
            # Save reduced graph
            self.save_graph_data(G_reduced, network_name, method_name, alpha, "reduced")
            
            return result
            
        except Exception as e:
            print(f"    Error in experiment {method_name} α={alpha}: {e}")
            return {
                'Network': network_name,
                'Method': method_name,
                'Alpha': alpha,
                'Error': str(e)
            }
    
    def run_experiments(self, methods: List[str] = None, max_networks: Optional[int] = None):
        """
        Run the complete experimental suite.
        """
        if methods is None:
            methods = list(self.available_methods.keys())
        
        # Load networks
        networks = self.load_networks(max_networks)
        
        if not networks:
            raise ValueError("No networks loaded successfully")
        
        all_results = []
        
        print(f"\nStarting experiments with methods: {methods}")
        print(f"Alpha range: {self.alpha_range}")
        print(f"Total experiments: {len(networks) * len(methods) * len(self.alpha_range)}")
        
        for network_name, G_original in networks:
            print(f"\n--- Processing network: {network_name} ---")
            print(f"Original graph: {G_original.number_of_nodes()} nodes, {G_original.number_of_edges()} edges")
            
            # Save original graph
            self.save_graph_data(G_original, network_name, "", 0, "original")
            
            for method_name in methods:
                print(f"  Method: {method_name}")
                
                method_results = []
                for alpha in tqdm(self.alpha_range, desc=f"  {method_name} progress", leave=False):
                    result = self.run_single_experiment(network_name, G_original, method_name, alpha)
                    method_results.append(result)
                    all_results.append(result)
                
                # Print summary for this method
                successful_runs = [r for r in method_results if 'Error' not in r]
                if successful_runs:
                    avg_time = np.mean([r['Execution_Time'] for r in successful_runs])
                    print(f"    Completed {len(successful_runs)}/{len(self.alpha_range)} runs, avg time: {avg_time:.3f}s")
        
        # Save results
        if HAS_PANDAS:
            # Convert to DataFrame and save as Excel
            results_df = pd.DataFrame(all_results)
            results_path = self.output_path / "coconut_experiment_results.xlsx"
            results_df.to_excel(results_path, index=False)
            print(f"\nResults saved to: {results_path}")
            return results_df
        else:
            # Save as CSV without pandas
            import csv
            results_path = self.output_path / "coconut_experiment_results.csv"
            if all_results:
                with open(results_path, 'w', newline='') as csvfile:
                    fieldnames = all_results[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(all_results)
                print(f"\nResults saved to: {results_path}")
            return all_results
    
    def generate_summary_report(self, results_df: pd.DataFrame):
        """
        Generate a summary report of the experimental results.
        """
        print("\n" + "="*80)
        print("EXPERIMENT SUMMARY REPORT")
        print("="*80)
        
        # Filter successful runs
        successful_df = results_df[~results_df['Network'].isna() & ~results_df.get('Error', pd.Series()).notna()]
        
        if successful_df.empty:
            print("No successful experiments to summarize.")
            return
        
        print(f"Total successful experiments: {len(successful_df)}")
        print(f"Networks tested: {successful_df['Network'].nunique()}")
        print(f"Methods tested: {successful_df['Method'].nunique()}")
        
        # Performance summary by method
        print(f"\nPerformance Summary by Method:")
        print("-" * 50)
        for method in successful_df['Method'].unique():
            method_data = successful_df[successful_df['Method'] == method]
            avg_node_reduction = method_data['Node Reduction Ratio'].mean()
            avg_edge_reduction = method_data['Edge Reduction Ratio'].mean()
            avg_execution_time = method_data['Execution_Time'].mean()
            
            print(f"{method}:")
            print(f"  Average node reduction: {avg_node_reduction:.3f}")
            print(f"  Average edge reduction: {avg_edge_reduction:.3f}")
            print(f"  Average execution time: {avg_execution_time:.3f}s")
            print()
        
        # Save summary to file
        summary_path = self.output_path / "experiment_summary.txt"
        with open(summary_path, 'w') as f:
            f.write("CoCoNUT Big Networks Experiment Summary\n")
            f.write("="*50 + "\n\n")
            f.write(f"Total experiments: {len(successful_df)}\n")
            f.write(f"Networks: {successful_df['Network'].nunique()}\n")
            f.write(f"Methods: {list(successful_df['Method'].unique())}\n")
            f.write(f"Alpha range: {list(self.alpha_range)}\n\n")
            
            for method in successful_df['Method'].unique():
                method_data = successful_df[successful_df['Method'] == method]
                f.write(f"{method} Results:\n")
                f.write(f"  Experiments: {len(method_data)}\n")
                f.write(f"  Avg node reduction: {method_data['Node Reduction Ratio'].mean():.3f}\n")
                f.write(f"  Avg edge reduction: {method_data['Edge Reduction Ratio'].mean():.3f}\n")
                f.write(f"  Avg execution time: {method_data['Execution_Time'].mean():.3f}s\n\n")
        
        print(f"Summary saved to: {summary_path}")


def main():
    """
    Main function to run the big networks experiment.
    """
    # Configuration
    DEFAULT_INPUT_PATH = "data/networks"  # Change this to your networks directory
    DEFAULT_OUTPUT_PATH = "results/coconut_experiments"
    
    # Create default directories if they don't exist
    os.makedirs(DEFAULT_INPUT_PATH, exist_ok=True)
    os.makedirs(DEFAULT_OUTPUT_PATH, exist_ok=True)
    
    # You can modify these paths as needed
    input_path = DEFAULT_INPUT_PATH
    output_path = DEFAULT_OUTPUT_PATH
    
    print("CoCoNUT Big Networks Experiment")
    print("="*50)
    print(f"Input path: {input_path}")
    print(f"Output path: {output_path}")
    
    # Check if input directory exists and has networks
    if not os.path.exists(input_path):
        print(f"\nError: Input directory '{input_path}' does not exist.")
        print("Please create the directory and add .gml network files.")
        return
    
    gml_files = list(Path(input_path).glob("*.gml"))
    if not gml_files:
        print(f"\nNo .gml files found in '{input_path}'.")
        print("Please add network files in .gml format to the input directory.")
        
        # Create a sample network for testing
        print("\nCreating a sample network for testing...")
        sample_dir = Path(input_path)
        sample_dir.mkdir(exist_ok=True)
        
        # Create sample networks
        sample_networks = [
            ("karate_club", nx.karate_club_graph()),
            ("erdos_renyi_50", nx.erdos_renyi_graph(50, 0.1, seed=42)),
            ("barabasi_albert_40", nx.barabasi_albert_graph(40, 3, seed=42))
        ]
        
        for name, G in sample_networks:
            sample_path = sample_dir / f"{name}.gml"
            nx.write_gml(G, sample_path)
            print(f"  Created: {sample_path}")
        
        print(f"\nSample networks created. Re-run the experiment.")
        return
    
    try:
        # Initialize experiment
        experiment = NetworkExperiment(input_path, output_path)
        
        # Run experiments (limit to first 3 networks for testing, remove max_networks for all)
        results = experiment.run_experiments(
            methods=['CoCoNUT', 'CoarseNet'], 
            max_networks=3  # Remove this parameter to process all networks
        )
        
        # Generate summary report
        experiment.generate_summary_report(results)
        
        print(f"\nExperiment completed successfully!")
        print(f"Results saved to: {output_path}")
        
    except Exception as e:
        print(f"Experiment failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
