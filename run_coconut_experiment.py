#!/usr/bin/env python3
"""
Simple runner script for CoCoNUT experiments.
"""

import os
import sys
from pathlib import Path
import networkx as nx

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from coconut_bignets_experiment import NetworkExperiment

def create_sample_networks(output_dir: str):
    """Create sample networks for testing."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Sample networks of different types and sizes
    networks = {
        "karate_club": nx.karate_club_graph(),
        "erdos_renyi_30": nx.erdos_renyi_graph(30, 0.15, seed=42),
        "barabasi_albert_25": nx.barabasi_albert_graph(25, 3, seed=42),
        "watts_strogatz_30": nx.watts_strogatz_graph(30, 4, 0.3, seed=42),
        "random_regular_20": nx.random_regular_graph(3, 20, seed=42),
        "complete_graph_10": nx.complete_graph(10),
        "cycle_graph_20": nx.cycle_graph(20),
        "star_graph_15": nx.star_graph(14),  # 14+1=15 nodes
        "grid_2d_5x5": nx.grid_2d_graph(5, 5),
        "path_graph_25": nx.path_graph(25)
    }
    
    print(f"Creating {len(networks)} sample networks in {output_dir}...")
    
    for name, G in networks.items():
        # Ensure graph is simple and connected
        if G.is_directed():
            G = G.to_undirected()
        G.remove_edges_from(nx.selfloop_edges(G))
        
        # For grid graph, convert node labels to integers
        if "grid" in name:
            G = nx.convert_node_labels_to_integers(G)
        
        # Save as GML
        gml_path = Path(output_dir) / f"{name}.gml"
        nx.write_gml(G, gml_path)
        print(f"  Created {name}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    print("Sample networks created successfully!")

def run_quick_test():
    """Run a quick test with sample networks."""
    print("CoCoNUT Quick Experiment Test")
    print("="*40)
    
    # Paths
    sample_networks_dir = "data/sample_networks"
    results_dir = "results/quick_test"
    
    # Create sample networks
    create_sample_networks(sample_networks_dir)
    
    # Run experiment
    experiment = NetworkExperiment(sample_networks_dir, results_dir)
    
    # Quick test with limited alpha range
    original_alpha_range = experiment.alpha_range
    experiment.alpha_range = [0.2, 0.4, 0.6, 0.8]  # Reduced range for quick test
    
    print(f"\nRunning quick test with alpha values: {experiment.alpha_range}")
    
    results = experiment.run_experiments(
        methods=['CoCoNUT', 'CoarseNet'], 
        max_networks=5  # Test first 5 networks only
    )
    
    experiment.generate_summary_report(results)
    
    print(f"\nQuick test completed!")
    print(f"Results saved to: {results_dir}")

def run_full_experiment():
    """Run the full experiment with all networks."""
    print("CoCoNUT Full Experiment")
    print("="*40)
    
    # Check for networks directory
    networks_dir = input("Enter path to networks directory (or press Enter for 'data/networks'): ").strip()
    if not networks_dir:
        networks_dir = "data/networks"
    
    if not os.path.exists(networks_dir):
        print(f"Directory {networks_dir} does not exist.")
        print("Would you like to create sample networks for testing? (y/n): ", end="")
        if input().lower().startswith('y'):
            create_sample_networks(networks_dir)
        else:
            return
    
    results_dir = "results/full_experiment"
    
    # Run full experiment
    experiment = NetworkExperiment(networks_dir, results_dir)
    
    print(f"Running full experiment with {len(experiment.alpha_range)} alpha values")
    
    results = experiment.run_experiments(
        methods=['CoCoNUT', 'CoarseNet']
    )
    
    experiment.generate_summary_report(results)
    
    print(f"\nFull experiment completed!")
    print(f"Results saved to: {results_dir}")

def main():
    """Main menu for running experiments."""
    print("CoCoNUT Experiment Runner")
    print("="*30)
    print("1. Quick test (sample networks, reduced alpha range)")
    print("2. Full experiment (all networks, full alpha range)")
    print("3. Create sample networks only")
    print("4. Exit")
    
    while True:
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            run_quick_test()
            break
        elif choice == "2":
            run_full_experiment()
            break
        elif choice == "3":
            output_dir = input("Enter output directory (default: 'data/sample_networks'): ").strip()
            if not output_dir:
                output_dir = "data/sample_networks"
            create_sample_networks(output_dir)
            break
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please select 1-4.")

if __name__ == "__main__":
    main()
