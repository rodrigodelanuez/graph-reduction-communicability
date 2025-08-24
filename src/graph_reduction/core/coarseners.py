"""
Core coarsening strategies including the adapted CoarseNet algorithm.
"""

import networkx as nx
import numpy as np
from scipy.sparse.linalg import eigs
import warnings
from typing import Tuple, Optional, Dict, List

class CoarseNetCoarsener:
    """
    Implementation of the Fast Influence-based Coarsening algorithm (CoarseNet).
    
    This algorithm uses spectral properties to determine optimal node pairs 
    for contraction, preserving important structural and spectral characteristics
    of the original graph. It uses optimized data structures to avoid recursion
    and performance issues.
    """
    
    def __init__(self, tolerance: float = 1e-15):
        self.tolerance = tolerance
    
    def _sanitize_graph(self, G: nx.Graph) -> nx.Graph:
        """
        Forces the graph to be unweighted and have no self-loops.
        Sets all edge weights to 1.
        Creates a new graph object to avoid modifying the original.
        """
        # Crear un nuevo grafo
        H = nx.Graph()
        H.add_nodes_from(G.nodes())
        # Añadir todas las aristas con peso = 1
        H.add_edges_from((u, v, {"weight": 1}) for u, v in G.edges())
        # Eliminar auto-loops por seguridad
        H.remove_edges_from(nx.selfloop_edges(H))
        return H


    def _calculate_eigensystem(self, G: nx.Graph, nodelist: List) -> Tuple[Optional[float], np.ndarray, np.ndarray]:
        """
        Calculate the dominant eigenvalue and corresponding eigenvectors.
        """
        num_nodes = G.number_of_nodes()

        if 0 < num_nodes <= 2:
            try:
                A_dense = nx.to_numpy_array(G, nodelist=nodelist, weight=None)
                eigenvalues = np.linalg.eigvals(A_dense)
                lambda_val = np.max(np.real(eigenvalues))
                return lambda_val, np.array([]), np.array([])
            except Exception as e:
                warnings.warn(f"NumPy eigenvalue calculation failed: {e}")
                return None, None, None

        A = nx.to_scipy_sparse_array(G, nodelist=nodelist, weight=None, dtype=np.float64)
        try:
            # 'LR' corresponds to Largest Real part
            lambda_val, u = eigs(A, k=1, which='LR')
            _, v = eigs(A.T, k=1, which='LR')
        except Exception as e:
            warnings.warn(f"Eigenvalue calculation failed: {e}")
            return None, None, None

        lambda_val = np.real(lambda_val[0])
        u = np.real(u[:, 0])
        v = np.real(v[:, 0])
        return lambda_val, u, v

    def _contract_pair(self, G: nx.Graph, a, b) -> nx.Graph:
        """
        Contract nodes (a, b) into a super-node (a,b) IN-PLACE.
        """
        new_node = (a, b)
        
        # Get neighbors before modifying the graph.
        # Convert to a list to prevent errors while iterating over a changing object.
        neigh_a = list(G.neighbors(a))
        neigh_b = list(G.neighbors(b))

        G.add_node(new_node)
        
        all_neighbors = set(neigh_a) | set(neigh_b)
        all_neighbors.discard(a)
        all_neighbors.discard(b)
        
        for neighbor in all_neighbors:
            G.add_edge(new_node, neighbor)
            
        G.remove_node(a)
        G.remove_node(b)
        
        return G

    def coarsen(self, G: nx.Graph, alpha: float, verbose: bool = False) -> nx.Graph:
        """Alias for the main coarsening implementation."""
        return self.coarsen_old(G, alpha, verbose)

    def coarsen_old(self, G: nx.Graph, alpha: float, verbose: bool = False) -> nx.Graph:
        """
        Main coarsening function. The input graph will be sanitized.
        """
        G_coarse = self._sanitize_graph(G)

        if not (0 < alpha < 1):
            raise ValueError("Reduction factor alpha must be between 0 and 1.")
        if G_coarse.number_of_nodes() < 2:
            return G_coarse.copy()

        n_original = G_coarse.number_of_nodes()
        nodelist = list(G_coarse.nodes())
        node_to_idx = {node: i for i, node in enumerate(nodelist)}
        
        if verbose:
            print("Graph has been sanitized: Unweighted, Undirected, No Self-loops.")
        
        lambda_val, u, v = self._calculate_eigensystem(G_coarse, nodelist)
        if verbose:
            print(f"Initial eigenvalue (Lambda): {lambda_val:.4f}")

        if lambda_val is None:
            return G_coarse

        v_dot_u = v.T @ u
        if abs(v_dot_u) < self.tolerance:
            warnings.warn("The product v^T*u is close to zero.")

        scores = []
        for a_node, b_node in G_coarse.edges():
            pair = tuple(sorted((a_node, b_node)))
            idx_a, idx_b = node_to_idx[pair[0]], node_to_idx[pair[1]]
            u_a, u_b = u[idx_a], u[idx_b]
            v_a, v_b = v[idx_a], v[idx_b]
            
            uT_co = (lambda_val * u_a - u_b) + (lambda_val * u_b - u_a)
            numerator = -lambda_val * (u_a * v_a + u_b * v_b) + v_a * uT_co + u_a * v_b + u_b * v_a
            denominator = v_dot_u - (u_a * v_a + u_b * v_b)

            if abs(denominator) > self.tolerance:
                score = numerator / denominator
                scores.append((score, pair))

        sorted_tasks = sorted(scores, key=lambda x: x[0], reverse=True)

        supernode_to_originals = {node: {node} for node in G_coarse.nodes()}
        node_map = {node: node for node in G_coarse.nodes()}

        target_nodes = int(round((1 - alpha) * n_original))
        num_contractions_to_perform = n_original - target_nodes
        contractions_done = 0

        if verbose:
            print(f"Starting coarsening: {n_original} nodes -> target: {target_nodes} nodes")
            print(f"Will perform {num_contractions_to_perform} contractions")
            print("-" * 50)

        unique_pairs = set()
        for _, original_pair in sorted_tasks:
            if contractions_done >= num_contractions_to_perform: break
            if original_pair in unique_pairs: continue
            unique_pairs.add(original_pair)

            a_orig, b_orig = original_pair
            super_a, super_b = node_map[a_orig], node_map[b_orig]

            if super_a == super_b: continue
            
            G_coarse = self._contract_pair(G_coarse, super_a, super_b)
            new_supernode = (super_a, super_b)
            
            originals_a = supernode_to_originals.pop(super_a)
            originals_b = supernode_to_originals.pop(super_b)
            combined_originals = originals_a | originals_b
            supernode_to_originals[new_supernode] = combined_originals
            
            node_map.update((node, new_supernode) for node in combined_originals)
            contractions_done += 1
            
        if verbose:
            print("-" * 50)
            print(f"Coarsening complete! Final graph has {G_coarse.number_of_nodes()} nodes")

        return G_coarse

    def coarsen_with_intermediate_checkpoints(self, G: nx.Graph, ratios: List[float], verbose: bool = False) -> Dict[float, nx.Graph]:
        """Alias for the checkpointing implementation."""
        return self.coarsen_with_intermediate_checkpoints_old(G, ratios, verbose)

    def coarsen_with_intermediate_checkpoints_old(self, G: nx.Graph, ratios: List[float], verbose: bool = False) -> Dict[float, nx.Graph]:
        """
        Coarsen graph with intermediate checkpoints. This is the logically correct
        and performance-aware version.
        """
        G_sanitized = self._sanitize_graph(G)
        if not ratios: return {}
        
        ratios = sorted(list(set(ratios)))
        highest_ratio = ratios[-1]
        
        results = {}
        G_coarse = G_sanitized.copy()
        n_original = G_sanitized.number_of_nodes()
        nodelist = list(G_coarse.nodes())
        node_to_idx = {node: i for i, node in enumerate(nodelist)}
        
        if verbose:
            print("Graph has been sanitized: Unweighted, Undirected, No Self-loops.")
        
        lambda_val, u, v = self._calculate_eigensystem(G_coarse, nodelist)
        if verbose:
            print(f"Initial eigenvalue (Lambda): {lambda_val:.4f}")

        if lambda_val is None: return results

        v_dot_u = v.T @ u
        if abs(v_dot_u) < self.tolerance:
            warnings.warn("The product v^T*u is close to zero.")

        scores = []
        for a_node, b_node in G_coarse.edges():
            pair = tuple(sorted((a_node, b_node)))
            idx_a, idx_b = node_to_idx[pair[0]], node_to_idx[pair[1]]
            u_a, u_b = u[idx_a], u[idx_b]
            v_a, v_b = v[idx_a], v[idx_b]

            uT_co = (lambda_val * u_a - u_b) + (lambda_val * u_b - u_a)
            numerator = -lambda_val * (u_a * v_a + u_b * v_b) + v_a * uT_co + u_a * v_b + u_b * v_a
            denominator = v_dot_u - (u_a * v_a + u_b * v_b)

            if abs(denominator) > self.tolerance:
                score = numerator / denominator
                scores.append((score, pair))

        sorted_tasks = sorted(scores, key=lambda x: x[0], reverse=True)
        
        supernode_to_originals = {node: {node} for node in G_sanitized.nodes()}
        node_map = {node: node for node in G_sanitized.nodes()}

        final_target_nodes = int(round((1 - highest_ratio) * n_original))
        total_contractions_needed = n_original - final_target_nodes
        contractions_done = 0
        
        contractions_to_checkpoint = {
            n_original - int(round((1 - r) * n_original)): r for r in ratios
        }

        if verbose:
            print(f"Starting coarsening: {n_original} nodes -> target: {final_target_nodes} nodes")
            print(f"Will perform {total_contractions_needed} contractions")
            print(f"Checkpoints at contraction counts: {list(contractions_to_checkpoint.keys())}")
            print("-" * 50)

        unique_pairs = set()
        for _, original_pair in sorted_tasks:
            if contractions_done >= total_contractions_needed: break
            if original_pair in unique_pairs: continue
            unique_pairs.add(original_pair)

            a_orig, b_orig = original_pair
            super_a, super_b = node_map[a_orig], node_map[b_orig]

            if super_a == super_b: continue

            # Combine the original nodes from both super-nodes to be contracted
            originals_a = supernode_to_originals.pop(super_a)
            originals_b = supernode_to_originals.pop(super_b)
            combined_originals = originals_a.union(originals_b)

            # Create a new, FLAT tuple node name from the sorted original nodes
            new_supernode = tuple(sorted(list(combined_originals)))
            
            # Manually perform the contraction in-place
            neighbors = set(G_coarse.neighbors(super_a)) | set(G_coarse.neighbors(super_b))
            neighbors.discard(super_a)
            neighbors.discard(super_b)
            
            G_coarse.add_node(new_supernode)
            for neighbor in neighbors:
                G_coarse.add_edge(new_supernode, neighbor)
                
            G_coarse.remove_node(super_a)
            G_coarse.remove_node(super_b)

            # Store the mapping to the new flat super-node
            supernode_to_originals[new_supernode] = combined_originals
            
            # Update the map for all original nodes to point to the new super-node
            node_map.update((node, new_supernode) for node in combined_originals)

            contractions_done += 1
            
            if contractions_done in contractions_to_checkpoint:
                ratio = contractions_to_checkpoint[contractions_done]
                if ratio not in results:
                    results[ratio] = G_coarse.copy()
                    if verbose:
                        print(f"✓ Checkpoint snapshot saved for ratio {ratio}: {G_coarse.number_of_nodes()} nodes")
                
        if verbose:
            print("-" * 50)
            print(f"Coarsening complete! Final graph has {G_coarse.number_of_nodes()} nodes")
        
        if highest_ratio not in results:
            results[highest_ratio] = G_coarse.copy()

        return results

def coarsenet(G: nx.Graph, alpha: float, verbose: bool = False) -> nx.Graph:
    """
    Convenience function to use CoarseNet algorithm.
    """
    coarsener = CoarseNetCoarsener()
    return coarsener.coarsen(G, alpha, verbose)