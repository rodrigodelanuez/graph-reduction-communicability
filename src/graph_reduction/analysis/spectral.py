"""
Spectral analysis functions for graph reduction evaluation.
"""

import numpy as np
import networkx as nx
from scipy.linalg import eigh
from typing import Dict, Any, Union


def analyze_single_graph_properties(graph: Union[np.ndarray, nx.Graph],
                                    tol: float = 1e-12) -> Dict[str, Any]:
    """
    Calculate spectral properties of a single graph.

    Parameters
    ----------
    graph : numpy.ndarray or nx.Graph
        Graph to analyze (adjacency matrix or NetworkX graph)
    tol : float
        Tolerance to clean numerical noise (default: 1e-12)

    Returns
    -------
    metrics : dict
        Dictionary containing computed spectral metrics for the graph
    """
    # Ensure we have a NetworkX graph object for consistent calculations
    if isinstance(graph, np.ndarray):
        G = nx.from_numpy_array(graph)
    else:
        G = graph.copy()
        
    # Fix recursion issue: rename complex tuple nodes to simple integers
    if G.number_of_nodes() > 0:
        # Check if any node is a complex tuple (indicates deeply nested structure)
        sample_node = next(iter(G.nodes()))
        if isinstance(sample_node, tuple):
            # Relabel all nodes to simple integers to avoid recursion in NetworkX
            node_mapping = {node: i for i, node in enumerate(G.nodes())}
            G = nx.relabel_nodes(G, node_mapping)

    # Return empty metrics for empty graphs to avoid errors
    if G.number_of_nodes() == 0:
        return {
            'spectral_ratio_L': 0.0,
            'eigenratio': 0.0,
            'spectral_gap_A': 0.0,
            'algebraic_connectivity_L': 0.0,
            'spectral_radius_A': 0.0
        }

    # Adjacency and Laplacian matrices
    A = nx.to_numpy_array(G)
    L = nx.laplacian_matrix(G).toarray()

    # Eigenvalues of Adjacency matrix (sorted)
    eigenvalues_A = np.linalg.eigvalsh(A)

    # Eigenvalues of Laplacian matrix (sorted)
    eigenvalues_L = np.linalg.eigvalsh(L)
    eigenvalues_L[np.abs(eigenvalues_L) < tol] = 0.0 # Clean numerical noise

    # --- Metric Calculations ---

    # Spectral Ratio of L
    largest_eigenvalue_L = eigenvalues_L[-1]
    second_smallest_eigenvalue_L = eigenvalues_L[1] if len(eigenvalues_L) > 1 else 0.0
    spectral_ratio_L = largest_eigenvalue_L / second_smallest_eigenvalue_L if second_smallest_eigenvalue_L > 0 else 0.0

    # Eigenratio of L
    non_zero_eigenvalues_L = eigenvalues_L[eigenvalues_L > tol]
    smallest_non_zero_L = non_zero_eigenvalues_L[0] if len(non_zero_eigenvalues_L) > 0 else 0.0
    eigenratio_L = smallest_non_zero_L / largest_eigenvalue_L if largest_eigenvalue_L > 0 else 0.0

    # Algebraic Connectivity of L (is the second-smallest eigenvalue)
    algebraic_connectivity_L = second_smallest_eigenvalue_L

    # Spectral Gap of A
    spectral_gap_A = eigenvalues_A[-1] - eigenvalues_A[-2] if len(eigenvalues_A) > 1 else 0.0

    # Spectral Radius of A (maximum absolute eigenvalue)
    spectral_radius_A = np.max(np.abs(eigenvalues_A)) if len(eigenvalues_A) > 0 else 0.0

    # Compile results with machine-readable keys
    metrics = {
        'spectral_ratio_L': spectral_ratio_L,
        'eigenratio': eigenratio_L,
        'spectral_gap_A': spectral_gap_A,
        'algebraic_connectivity_L': algebraic_connectivity_L,
        'spectral_radius_A': spectral_radius_A,
    }

    return metrics


def analyze_spectral_properties(graph: Union[np.ndarray, nx.Graph],
                                reduced_graph: Union[np.ndarray, nx.Graph],
                                tol: float = 1e-12) -> Dict[str, Any]:
    """
    Calculate and compare spectral properties between original and reduced graphs.
    
    (This function is kept for potential future use but is not called by the current CLI)
    """
    original_metrics = analyze_single_graph_properties(graph, tol)
    reduced_metrics = analyze_single_graph_properties(reduced_graph, tol)

    if isinstance(graph, nx.Graph):
        num_nodes_orig = graph.number_of_nodes()
        num_edges_orig = graph.number_of_edges()
    else:
        num_nodes_orig = graph.shape[0]
        num_edges_orig = np.count_nonzero(graph) // 2
        
    if isinstance(reduced_graph, nx.Graph):
        num_nodes_red = reduced_graph.number_of_nodes()
        num_edges_red = reduced_graph.number_of_edges()
    else:
        num_nodes_red = reduced_graph.shape[0]
        num_edges_red = np.count_nonzero(reduced_graph) // 2

    def pct_reduction(original, reduced):
        return 100 * (original - reduced) / original if original != 0 else 0

    metrics = {
        'Spectral Ratio (Original)': original_metrics.get('spectral_ratio_L', 0.0),
        'Spectral Ratio (Reduced)': reduced_metrics.get('spectral_ratio_L', 0.0),
        'Spectral Ratio Reduction (%)': pct_reduction(original_metrics.get('spectral_ratio_L', 0.0), reduced_metrics.get('spectral_ratio_L', 0.0)),
        
        'Eigenratio (Original)': original_metrics.get('eigenratio', 0.0),
        'Eigenratio (Reduced)': reduced_metrics.get('eigenratio', 0.0),
        'Eigenratio Reduction (%)': pct_reduction(original_metrics.get('eigenratio', 0.0), reduced_metrics.get('eigenratio', 0.0)),

        'Spectral Gap (Original)': original_metrics.get('spectral_gap_A', 0.0),
        'Spectral Gap (Reduced)': reduced_metrics.get('spectral_gap_A', 0.0),
        'Spectral Gap Reduction (%)': pct_reduction(original_metrics.get('spectral_gap_A', 0.0), reduced_metrics.get('spectral_gap_A', 0.0)),

        'Algebraic Connectivity (Original)': original_metrics.get('algebraic_connectivity_L', 0.0),
        'Algebraic Connectivity (Reduced)': reduced_metrics.get('algebraic_connectivity_L', 0.0),
        'Algebraic Connectivity Reduction (%)': pct_reduction(original_metrics.get('algebraic_connectivity_L', 0.0), reduced_metrics.get('algebraic_connectivity_L', 0.0)),
        
        'Spectral Radius (Original)': original_metrics.get('spectral_radius_A', 0.0),
        'Spectral Radius (Reduced)': reduced_metrics.get('spectral_radius_A', 0.0),
        'Spectral Radius Reduction (%)': pct_reduction(original_metrics.get('spectral_radius_A', 0.0), reduced_metrics.get('spectral_radius_A', 0.0)),
        
        'Number of Nodes (Original)': num_nodes_orig,
        'Number of Nodes (Reduced)': num_nodes_red,
        'Number of Edges (Original)': num_edges_orig,
        'Number of Edges (Reduced)': num_edges_red
    }
    return metrics