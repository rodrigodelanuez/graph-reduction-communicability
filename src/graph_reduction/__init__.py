"""
Graph Reduction and Communicability Analysis Package

This package provides tools for graph coarsening using the CoarseNet algorithm
and evaluation of spectral properties preservation.
"""

from .core.coarseners import CoarseNetCoarsener
from .io import load_graph, save_reduced_graph, iter_graph_files
from .analysis.spectral import analyze_spectral_properties, analyze_single_graph_properties

__version__ = "0.1.0"

__all__ = [
    "CoarseNetCoarsener",
    "load_graph", 
    "save_reduced_graph",
    "analyze_spectral_properties",
    "analyze_single_graph_properties",
    "iter_graph_files"
]
