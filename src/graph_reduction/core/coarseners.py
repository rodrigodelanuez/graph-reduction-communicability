"""
Core coarsening strategies using an abstract base class for shared logic.
This module provides implementations for the CoarseNet and CoCoNUT algorithms.
"""

import networkx as nx
import numpy as np
from scipy.sparse.linalg import eigs
from scipy.linalg import expm
import warnings
from typing import Tuple, Optional, Dict, List, Any
from abc import ABC, abstractmethod


class BaseCoarsener(ABC):
    """
    Abstract Base Class for graph coarsening algorithms.
    """
    def __init__(self, tolerance: float = 1e-15, sort_descending: bool = False):
        """
        Initializes the coarsener.

        Args:
            tolerance (float): Numerical tolerance for floating-point comparisons.
            sort_descending (bool): If True, scores are sorted in descending order (for similarity scores).
                                    If False, scores are sorted in ascending order (for cost scores).
        """
        self.tolerance = tolerance
        self.sort_descending = sort_descending

    def _sanitize_graph(self, G: nx.Graph) -> nx.Graph:
        """Creates a simple, unweighted, undirected graph with no self-loops."""
        H = nx.Graph()
        H.add_nodes_from(G.nodes())
        H.add_edges_from(G.edges(), weight=1)
        H.remove_edges_from(nx.selfloop_edges(H))
        return H

    @abstractmethod
    def _calculate_scores(
        self, G: nx.Graph, nodelist: List[Any]
    ) -> List[Tuple[float, Tuple[Any, Any]]]:
        """Abstract method to be implemented by subclasses for calculating merge scores."""
        pass

    def coarsen(
        self, G: nx.Graph, alpha: float, verbose: bool = False
    ) -> nx.Graph:
        """Coarsens a graph to a single target ratio."""
        results = self.coarsen_with_intermediate_checkpoints(G, [alpha], verbose)
        return results.get(alpha, G)

    def coarsen_with_intermediate_checkpoints(
        self, G: nx.Graph, ratios: List[float], verbose: bool = False
    ) -> Dict[float, nx.Graph]:
        """
        Efficiently coarsens a graph, saving intermediate results at specified ratios.
        """
        G_coarse = self._sanitize_graph(G)
        if not ratios:
            return {}
        
        ratios = sorted(list(set(r for r in ratios if 0 < r < 1)))
        if not ratios:
            raise ValueError("All provided ratios must be between 0 and 1.")

        n_original = G_coarse.number_of_nodes()
        if n_original < 2:
            return {r: G_coarse.copy() for r in ratios}
            
        nodelist = sorted(list(G_coarse.nodes()))
        scores = self._calculate_scores(G_coarse, nodelist)
        if not scores:
            return {r: G_coarse.copy() for r in ratios}

        # The sorting order is now determined by the subclass via the 'sort_descending' attribute.
        sorted_tasks = sorted(scores, key=lambda x: (x[0], x[1]), reverse=self.sort_descending)
        
        node_map = {node: node for node in G_coarse.nodes()}
        supernode_to_originals = {node: {node} for node in G_coarse.nodes()}
        
        # Determine the number of contractions needed for each target ratio.
        contractions_to_checkpoint = {
            n_original - int(round((1 - r) * n_original)): r for r in ratios
        }
        max_contractions = max(contractions_to_checkpoint.keys()) if contractions_to_checkpoint else 0
        
        results = {}
        contractions_done = 0
        
        for _, original_pair in sorted_tasks:
            if contractions_done >= max_contractions:
                break

            super_a = node_map[original_pair[0]]
            super_b = node_map[original_pair[1]]

            if super_a == super_b:
                continue

            # Merge nodes and update tracking dictionaries
            originals_a = supernode_to_originals.pop(super_a)
            originals_b = supernode_to_originals.pop(super_b)
            combined_originals = originals_a.union(originals_b)
            new_supernode = tuple(sorted(list(combined_originals)))
            
            # Rewire edges to the new supernode
            neighbors = set(G_coarse.neighbors(super_a)) | set(G_coarse.neighbors(super_b))
            neighbors.discard(super_a)
            neighbors.discard(super_b)
            
            G_coarse.add_node(new_supernode)
            for neighbor in neighbors:
                G_coarse.add_edge(new_supernode, neighbor)
            
            G_coarse.remove_node(super_a)
            G_coarse.remove_node(super_b)
            
            supernode_to_originals[new_supernode] = combined_originals
            for node in combined_originals:
                node_map[node] = new_supernode
            
            contractions_done += 1

            # Save a snapshot if a target ratio is reached
            if contractions_done in contractions_to_checkpoint:
                ratio = contractions_to_checkpoint[contractions_done]
                if ratio not in results:
                    results[ratio] = G_coarse.copy()
                    if verbose:
                        print(f"✓ Checkpoint snapshot saved for ratio {ratio}: {G_coarse.number_of_nodes()} nodes")
        
        # Ensure all requested ratios have a corresponding graph in the results
        final_graph = G_coarse.copy()
        for ratio in ratios:
            if ratio not in results:
                results[ratio] = final_graph
                
        return results


class CoarseNetCoarsener(BaseCoarsener):
    """
    Implementation of the CoarseNet algorithm using spectral properties.
    The score represents a cost, so lower values are prioritized for merging.
    """
    def __init__(self, tolerance: float = 1e-15):
        # Initializes the base class to sort scores in ascending order (lower is better).
        super().__init__(tolerance=tolerance, sort_descending=False)

    def _calculate_eigensystem(
        self, G: nx.Graph, nodelist: List[Any]
    ) -> Tuple[Optional[float], Optional[np.ndarray], Optional[np.ndarray]]:
        """Calculates the dominant eigenvalue and left/right eigenvectors."""
        num_nodes = G.number_of_nodes()
        if num_nodes <= 2:
            try:
                A_dense = nx.to_numpy_array(G, nodelist=nodelist, weight=None)
                eigenvalues = np.linalg.eigvals(A_dense)
                return np.max(np.real(eigenvalues)), np.array([]), np.array([])
            except Exception as e:
                warnings.warn(f"NumPy eigenvalue calculation failed: {e}")
                return None, None, None

        A = nx.to_scipy_sparse_array(G, nodelist=nodelist, weight=None, dtype=np.float64)
        try:
            lambda_val, u = eigs(A, k=1, which='LR')
            _, v = eigs(A.T, k=1, which='LR')
        except Exception as e:
            warnings.warn(f"Eigenvalue calculation failed: {e}")
            return None, None, None

        return np.real(lambda_val[0]), np.real(u[:, 0]), np.real(v[:, 0])

    def _calculate_scores(
        self, G: nx.Graph, nodelist: List[Any]
    ) -> List[Tuple[float, Tuple[Any, Any]]]:
        """Calculates the cost score for merging adjacent nodes."""
        lambda_val, u, v = self._calculate_eigensystem(G, nodelist)
        if lambda_val is None or u is None or v is None or G.number_of_nodes() <= 2:
            return [(1.0, tuple(sorted(edge))) for edge in G.edges()]

        v_dot_u = v.T @ u
        if abs(v_dot_u) < self.tolerance:
            warnings.warn("The product v^T*u is close to zero.")

        scores = []
        # --- BUCLE ORIGINAL (SOLO SOBRE ARISTAS) ---
        #
        # node_to_idx = {node: i for i, node in enumerate(nodelist)}
        # for a_node, b_node in G.edges():
        #     pair = tuple(sorted((a_node, b_node)))
        #     idx_a, idx_b = node_to_idx[pair[0]], node_to_idx[pair[1]]
        #     u_a, u_b = u[idx_a], u[idx_b]
        #     v_a, v_b = v[idx_a], v[idx_b]
        #
        #     uT_co = (lambda_val * u_a - u_b) + (lambda_val * u_b - u_a)
        #     numerator = -lambda_val * (u_a * v_a + u_b * v_b) + v_a * uT_co + u_a * v_b + u_b * v_a
        #     denominator = v_dot_u - (u_a * v_a + u_b * v_b)
        #
        #     if abs(denominator) > self.tolerance:
        #         score = abs(numerator / denominator)
        #         scores.append((score, pair))

        # --- NUEVO BUCLE (SOBRE TODOS LOS PARES DE NODOS) ---
        n = len(nodelist)
        for i in range(n):
            for j in range(i + 1, n):
                # i y j son los índices de los nodos en la nodelist
                u_a, u_b = u[i], u[j]
                v_a, v_b = v[i], v[j]
                
                # El cálculo del score es el mismo
                uT_co = (lambda_val * u_a - u_b) + (lambda_val * u_b - u_a)
                numerator = -lambda_val * (u_a * v_a + u_b * v_b) + v_a * uT_co + u_a * v_b + u_b * v_a
                denominator = v_dot_u - (u_a * v_a + u_b * v_b)
                
                if abs(denominator) > self.tolerance:
                    score = abs(numerator / denominator)
                    
                    # Obtenemos los nombres de los nodos para devolver el par
                    node_a = nodelist[i]
                    node_b = nodelist[j]
                    pair = tuple(sorted((node_a, node_b)))
                    scores.append((score, pair))
        
        return scores


class CoCoNUTCoarsener(BaseCoarsener):
    """
    Implementation of the CoCoNUT algorithm using communicability.
    The score represents a similarity, so higher values are prioritized for merging.
    """
    def __init__(self, tolerance: float = 1e-15):
        # Initializes the base class to sort scores in descending order (higher is better).
        super().__init__(tolerance=tolerance, sort_descending=True)

    def _calculate_scores(
        self, G: nx.Graph, nodelist: List[Any]
    ) -> List[Tuple[float, Tuple[Any, Any]]]:
        """
        Calculates similarity scores for all unique pairs of nodes in the graph.
        """
        n = G.number_of_nodes()
        if n < 2:
            return []
        
        # 1. Calculate Communicability Cosine Distance (CCD) matrix D
        A = nx.to_numpy_array(G, nodelist=nodelist, weight=None)
        expA = expm(A)

        G_diag = np.diag(expA)
        with np.errstate(divide='ignore', invalid='ignore'):
            G_vv_G_ww = np.sqrt(np.outer(G_diag, G_diag))
            cos_theta = expA / G_vv_G_ww
        cos_theta[np.isnan(cos_theta)] = 0
        D = 2 - 2 * cos_theta
        np.fill_diagonal(D, 0)

        # 2. Calculate Communicability Closeness Centrality (CCC)
        sum_dist = D.sum(axis=1)
        centrality = np.zeros_like(sum_dist, dtype=float)
        mask = sum_dist > 0
        centrality[mask] = 1.0 / sum_dist[mask]

        # 3. Calculate the final score matrix S
        centrality_diff = np.abs(centrality[:, np.newaxis] - centrality)
        centrality_sim = np.exp(-1.0 * centrality_diff)
        comm_sim = np.exp(-0.5 * D)
        S = 0.5 * (comm_sim + centrality_sim)
        
        # 4. Collect scores for all unique pairs
        scores = []
        for i in range(n):
            for j in range(i + 1, n):
                node_a = nodelist[i]
                node_b = nodelist[j]
                pair = tuple(sorted((node_a, node_b)))
                score_value = S[i, j]
                scores.append((score_value, pair))
                
        return scores