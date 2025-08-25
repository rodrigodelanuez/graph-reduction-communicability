#!/usr/bin/env python3
"""
Test the refactored CoCoNUT coarsener that follows CoarseNet structure.
"""

import networkx as nx
import numpy as np
from src.graph_reduction.core.coarseners import CoCoNUTCoarsener, coconut, CoarseNetCoarsener, coarsenet

def test_refactored_coconut():
    """Test the refactored CoCoNUT implementation."""
    print("Testing refactored CoCoNUT coarsener...")
    
    # Create test graphs
    graphs = [
        ("Path graph (5 nodes)", nx.path_graph(5)),
        ("Cycle graph (6 nodes)", nx.cycle_graph(6)),
        ("Star graph (7 nodes)", nx.star_graph(6)),
        ("Complete graph (5 nodes)", nx.complete_graph(5)),
    ]
    
    coconut_coarsener = CoCoNUTCoarsener()
    coarsenet_coarsener = CoarseNetCoarsener()
    
    for graph_name, G in graphs:
        print(f"\n--- Testing {graph_name} ---")
        print(f"Original: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        
        for alpha in [0.3, 0.5, 0.7]:
            print(f"\n  α = {alpha}:")
            
            # Test CoCoNUT
            try:
                H_coconut = coconut_coarsener.coarsen(G, alpha=alpha, verbose=False)
                coconut_ratio = H_coconut.number_of_nodes() / G.number_of_nodes()
                print(f"    CoCoNUT: {G.number_of_nodes()} → {H_coconut.number_of_nodes()} nodes (ratio: {coconut_ratio:.2f})")
                
                # Check connectivity preservation for connected graphs
                if nx.is_connected(G) and H_coconut.number_of_nodes() > 1:
                    is_connected = nx.is_connected(H_coconut)
                    print(f"      Connected: {is_connected}")
                
            except Exception as e:
                print(f"    CoCoNUT failed: {e}")
            
            # Test CoarseNet for comparison
            try:
                H_coarsenet = coarsenet_coarsener.coarsen(G, alpha=alpha, verbose=False)
                coarsenet_ratio = H_coarsenet.number_of_nodes() / G.number_of_nodes()
                print(f"    CoarseNet: {G.number_of_nodes()} → {H_coarsenet.number_of_nodes()} nodes (ratio: {coarsenet_ratio:.2f})")
                
            except Exception as e:
                print(f"    CoarseNet failed: {e}")

def test_coconut_convenience_function():
    """Test the convenience function."""
    print("\n\nTesting CoCoNUT convenience function...")
    
    G = nx.karate_club_graph()
    print(f"Karate club graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    for alpha in [0.3, 0.5, 0.7]:
        H = coconut(G, alpha=alpha, verbose=True)
        ratio = H.number_of_nodes() / G.number_of_nodes()
        print(f"α={alpha}: {G.number_of_nodes()} → {H.number_of_nodes()} nodes (ratio: {ratio:.2f})")

def test_supernode_structure():
    """Test that supernodes are created correctly."""
    print("\n\nTesting supernode structure...")
    
    G = nx.path_graph(6)  # 0-1-2-3-4-5
    print(f"Original graph: nodes {list(G.nodes())}, edges {list(G.edges())}")
    
    coconut_coarsener = CoCoNUTCoarsener()
    H = coconut_coarsener.coarsen(G, alpha=0.6, verbose=True)
    
    print(f"Coarsened graph: nodes {list(H.nodes())}, edges {list(H.edges())}")
    
    # Check supernode structure
    for node in H.nodes():
        if isinstance(node, tuple):
            print(f"Supernode {node} represents merger of nodes {node[0]} and {node[1]}")

def compare_algorithms():
    """Compare CoCoNUT and CoarseNet side by side."""
    print("\n\nComparing CoCoNUT vs CoarseNet...")
    
    G = nx.erdos_renyi_graph(20, 0.3, seed=42)
    print(f"Random graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    coconut_coarsener = CoCoNUTCoarsener()
    coarsenet_coarsener = CoarseNetCoarsener()
    
    print("\nReduction comparison:")
    print("Alpha\tCoCoNUT\tCoarseNet")
    print("-" * 30)
    
    for alpha in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        try:
            H_coconut = coconut_coarsener.coarsen(G, alpha=alpha)
            nodes_coconut = H_coconut.number_of_nodes()
        except:
            nodes_coconut = "Error"
        
        try:
            H_coarsenet = coarsenet_coarsener.coarsen(G, alpha=alpha)
            nodes_coarsenet = H_coarsenet.number_of_nodes()
        except:
            nodes_coarsenet = "Error"
        
        print(f"{alpha:.1f}\t{nodes_coconut}\t{nodes_coarsenet}")

if __name__ == "__main__":
    try:
        test_refactored_coconut()
        test_coconut_convenience_function()
        test_supernode_structure()
        compare_algorithms()
        print("\n🎉 All refactored CoCoNUT tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
