"""
Spectral analysis functions for graph reduction evaluation.
"""

import numpy as np
import networkx as nx
from typing import Dict, Any, Union

def analyze_single_graph_properties(graph: Union[np.ndarray, nx.Graph],
                                    tol: float = 1e-12) -> Dict[str, Any]:
    """
    Calculate spectral properties of a single graph on its unweighted structure.

    Parameters
    ----------
    graph : numpy.ndarray or nx.Graph
        Graph to analyze (adjacency matrix or NetworkX graph).
    tol : float
        Tolerance to clean numerical noise (default: 1e-12).

    Returns
    -------
    metrics : dict
        Dictionary containing computed spectral metrics for the graph.
    """
    if isinstance(graph, np.ndarray):
        G = nx.from_numpy_array(graph)
    else:
        G = graph.copy()
        
    if G.number_of_nodes() > 0:
        sample_node = next(iter(G.nodes()))
        if isinstance(sample_node, tuple):
            node_mapping = {node: i for i, node in enumerate(G.nodes())}
            G = nx.relabel_nodes(G, node_mapping)

    if G.number_of_nodes() == 0:
        return {
            'spectral_ratio_L': 0.0,
            'spectral_gap_A': 0.0,
            'algebraic_connectivity_L': 0.0,
            'spectral_radius_A': 0.0
        }

    # IMPORTANT: Use weight=None to ensure unweighted calculation.
    A = nx.to_numpy_array(G, weight=None)
    L = nx.laplacian_matrix(G, weight=None).toarray()

    eigenvalues_A = np.linalg.eigvalsh(A)
    eigenvalues_L = np.linalg.eigvalsh(L)
    eigenvalues_L[np.abs(eigenvalues_L) < tol] = 0.0

    largest_eigenvalue_L = eigenvalues_L[-1]
    second_smallest_eigenvalue_L = eigenvalues_L[1] if len(eigenvalues_L) > 1 else 0.0
    spectral_ratio_L = largest_eigenvalue_L / second_smallest_eigenvalue_L if second_smallest_eigenvalue_L > 0 else 0.0

    algebraic_connectivity_L = second_smallest_eigenvalue_L
    spectral_gap_A = eigenvalues_A[-1] - eigenvalues_A[-2] if len(eigenvalues_A) > 1 else 0.0
    spectral_radius_A = np.max(np.abs(eigenvalues_A)) if len(eigenvalues_A) > 0 else 0.0

    metrics = {
        'spectral_ratio_L': spectral_ratio_L,
        'spectral_gap_A': spectral_gap_A,
        'algebraic_connectivity_L': algebraic_connectivity_L,
        'spectral_radius_A': spectral_radius_A,
    }
    return metrics