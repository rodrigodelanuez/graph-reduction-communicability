"""
Input/Output utilities for loading graphs and saving results.
"""

import networkx as nx
from pathlib import Path
from typing import Dict, List, Tuple, Union
import pandas as pd
import json
import numpy as np


def load_graph(file_path: Union[str, Path]) -> nx.Graph:
    """
    Load a graph from various file formats.
    
    Args:
        file_path: Path to the graph file
        
    Returns:
        Loaded NetworkX graph
        
    Raises:
        ValueError: If file format is not supported
    """
    file_path = Path(file_path)
    
    if file_path.suffix.lower() == '.gml':
        return nx.read_gml(file_path)
    elif file_path.suffix.lower() == '.edgelist':
        return nx.read_edgelist(file_path)
    elif file_path.suffix.lower() == '.txt':
        # Try to read as adjacency matrix
        try:
            matrix = np.loadtxt(file_path)
            return nx.from_numpy_array(matrix)
        except:
            # Try as edge list
            return nx.read_edgelist(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")


def iter_graph_files(data_dir: Union[str, Path]) -> Dict[str, Path]:
    """
    Iterate over graph files in a directory.
    
    Args:
        data_dir: Directory containing graph files
        
    Returns:
        Dictionary mapping graph names to file paths
    """
    data_dir = Path(data_dir)
    supported_extensions = {'.gml', '.edgelist', '.txt'}
    
    graphs = {}
    for file_path in data_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            graph_name = file_path.stem
            graphs[graph_name] = file_path
    
    return graphs


def save_reduced_graph(graph: nx.Graph, output_path: Union[str, Path], 
                      format: str = 'gml') -> None:
    """
    Save a reduced graph to file.
    
    Args:
        graph: Graph to save
        output_path: Output file path
        format: Output format ('gml', 'edgelist', 'txt')
    """
    output_path = Path(output_path)
    
    if format == 'gml':
        nx.write_gml(graph, output_path)
    elif format == 'edgelist':
        nx.write_edgelist(graph, output_path)
    elif format == 'txt':
        # Save as adjacency matrix
        matrix = nx.to_numpy_array(graph)
        np.savetxt(output_path, matrix)
    else:
        raise ValueError(f"Unsupported output format: {format}")


def save_metrics_excel(results: List[Dict], output_path: Union[str, Path]) -> None:
    """
    Save metrics results to Excel file.
    
    Args:
        results: List of metric dictionaries
        output_path: Output Excel file path
    """
    df = pd.DataFrame(results)
    df.to_excel(output_path, index=False)


def save_metrics_csv(results: List[Dict], output_path: Union[str, Path]) -> None:
    """
    Save metrics results to CSV file.
    
    Args:
        results: List of metric dictionaries
        output_path: Output CSV file path
    """
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)


def save_metrics_json(results: List[Dict], output_path: Union[str, Path]) -> None:
    """
    Save metrics results to JSON file.
    
    Args:
        results: List of metric dictionaries
        output_path: Output JSON file path
    """
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)


def save_adjacency_matrix(matrix: np.ndarray, output_path: Union[str, Path]) -> None:
    """
    Save adjacency matrix to text file.
    
    Args:
        matrix: Adjacency matrix
        output_path: Output file path
    """
    np.savetxt(output_path, matrix)
