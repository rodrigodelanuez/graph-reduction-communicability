#!/usr/bin/env python3
"""
Configuration file for CoCoNUT experiments.
Modify these settings to customize your experiments.
"""

import numpy as np
from pathlib import Path

class ExperimentConfig:
    """Configuration settings for CoCoNUT experiments."""
    
    # Paths
    DEFAULT_INPUT_PATH = "data/networks"
    DEFAULT_OUTPUT_PATH = "results/coconut_experiments"
    SAMPLE_NETWORKS_PATH = "data/sample_networks"
    
    # Experiment parameters
    ALPHA_RANGE_FULL = [round(a, 2) for a in np.arange(0.1, 0.96, 0.05)]  # 0.1 to 0.95, step 0.05
    ALPHA_RANGE_QUICK = [0.2, 0.4, 0.6, 0.8]  # Quick test range
    
    # Methods to test
    AVAILABLE_METHODS = ['CoCoNUT', 'CoarseNet']
    DEFAULT_METHODS = ['CoCoNUT', 'CoarseNet']
    
    # Experiment limits
    MAX_NETWORKS_QUICK_TEST = 5
    MAX_NETWORKS_FULL = None  # None means all networks
    
    # Graph preprocessing
    REMOVE_SELF_LOOPS = True
    REMOVE_ISOLATED_NODES = True
    FORCE_UNDIRECTED = True
    MIN_NODES = 3  # Minimum nodes required for a network to be included
    MIN_EDGES = 1  # Minimum edges required for a network to be included
    
    # Output settings
    SAVE_GRAPHS = True  # Whether to save coarsened graphs
    SAVE_ADJACENCY_MATRICES = True  # Whether to save adjacency matrices
    VERBOSE_OUTPUT = True  # Whether to print detailed progress
    
    # Performance settings
    TIMEOUT_PER_EXPERIMENT = 300  # Maximum seconds per single experiment (5 minutes)
    
    # Sample networks configuration (for testing)
    SAMPLE_NETWORKS = {
        "karate_club": {"type": "karate_club", "params": {}},
        "erdos_renyi_30": {"type": "erdos_renyi", "params": {"n": 30, "p": 0.15, "seed": 42}},
        "erdos_renyi_50": {"type": "erdos_renyi", "params": {"n": 50, "p": 0.1, "seed": 43}},
        "barabasi_albert_25": {"type": "barabasi_albert", "params": {"n": 25, "m": 3, "seed": 42}},
        "barabasi_albert_40": {"type": "barabasi_albert", "params": {"n": 40, "m": 2, "seed": 43}},
        "watts_strogatz_30": {"type": "watts_strogatz", "params": {"n": 30, "k": 4, "p": 0.3, "seed": 42}},
        "random_regular_20": {"type": "random_regular", "params": {"d": 3, "n": 20, "seed": 42}},
        "complete_graph_10": {"type": "complete", "params": {"n": 10}},
        "complete_graph_15": {"type": "complete", "params": {"n": 15}},
        "cycle_graph_20": {"type": "cycle", "params": {"n": 20}},
        "cycle_graph_30": {"type": "cycle", "params": {"n": 30}},
        "star_graph_15": {"type": "star", "params": {"n": 14}},  # n+1 total nodes
        "star_graph_25": {"type": "star", "params": {"n": 24}},
        "grid_2d_5x5": {"type": "grid_2d", "params": {"m": 5, "n": 5}},
        "grid_2d_6x4": {"type": "grid_2d", "params": {"m": 6, "n": 4}},
        "path_graph_25": {"type": "path", "params": {"n": 25}},
        "path_graph_35": {"type": "path", "params": {"n": 35}},
    }
    
    # Metrics to calculate
    CALCULATE_SPECTRAL_METRICS = True
    CALCULATE_CONNECTIVITY_METRICS = True
    CALCULATE_CLUSTERING_METRICS = False  # Can be slow for large graphs
    CALCULATE_CENTRALITY_METRICS = False  # Can be slow for large graphs
    
    # Results formatting
    EXCEL_OUTPUT = True
    CSV_OUTPUT = True
    JSON_OUTPUT = False
    
    @classmethod
    def get_quick_test_config(cls):
        """Get configuration for quick testing."""
        return {
            'alpha_range': cls.ALPHA_RANGE_QUICK,
            'methods': cls.DEFAULT_METHODS,
            'max_networks': cls.MAX_NETWORKS_QUICK_TEST,
            'input_path': cls.SAMPLE_NETWORKS_PATH,
            'output_path': "results/quick_test",
            'verbose': True
        }
    
    @classmethod
    def get_full_experiment_config(cls):
        """Get configuration for full experiment."""
        return {
            'alpha_range': cls.ALPHA_RANGE_FULL,
            'methods': cls.DEFAULT_METHODS,
            'max_networks': cls.MAX_NETWORKS_FULL,
            'input_path': cls.DEFAULT_INPUT_PATH,
            'output_path': cls.DEFAULT_OUTPUT_PATH,
            'verbose': cls.VERBOSE_OUTPUT
        }
    
    @classmethod
    def get_custom_config(cls, **kwargs):
        """Get custom configuration with specified overrides."""
        config = cls.get_full_experiment_config()
        config.update(kwargs)
        return config


# Additional experiment presets
EXPERIMENT_PRESETS = {
    "quick_test": {
        "description": "Quick test with sample networks",
        "alpha_range": [0.3, 0.5, 0.7],
        "max_networks": 3,
        "methods": ["CoCoNUT"]
    },
    
    "comparison_study": {
        "description": "Compare CoCoNUT vs CoarseNet",
        "alpha_range": [0.2, 0.4, 0.6, 0.8],
        "max_networks": None,
        "methods": ["CoCoNUT", "CoarseNet"]
    },
    
    "alpha_sensitivity": {
        "description": "Study sensitivity to alpha parameter",
        "alpha_range": [round(a, 2) for a in np.arange(0.1, 0.91, 0.02)],  # Fine-grained
        "max_networks": 10,
        "methods": ["CoCoNUT"]
    },
    
    "coconut_only": {
        "description": "CoCoNUT algorithm evaluation",
        "alpha_range": [round(a, 2) for a in np.arange(0.1, 0.96, 0.05)],
        "max_networks": None,
        "methods": ["CoCoNUT"]
    }
}
