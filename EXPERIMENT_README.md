# CoCoNUT Big Networks Experiment

This directory contains scripts for running comprehensive experiments with the CoCoNUT (Communicability-based Coarsening of Networks Using Topology) algorithm on large networks.

## Quick Start

1. **Run a quick test with sample networks:**
   ```bash
   python run_coconut_experiment.py
   # Select option 1 for quick test
   ```

2. **Run the full experiment:**
   ```bash
   python run_coconut_experiment.py
   # Select option 2 for full experiment
   ```

## Files Description

### Main Scripts

- **`coconut_bignets_experiment.py`**: Main experimental framework
- **`run_coconut_experiment.py`**: Interactive runner script with menu options
- **`experiment_config.py`**: Configuration settings for experiments
- **`test_refactored_coconut.py`**: Test suite for the CoCoNUT implementation

### Key Features

- **Multiple Network Types**: Supports various graph types (social networks, random graphs, structured graphs)
- **Comprehensive Metrics**: Calculates spectral properties, connectivity measures, and reduction ratios
- **Method Comparison**: Compares CoCoNUT with CoarseNet and other coarsening methods
- **Flexible Configuration**: Easy to customize through configuration files
- **Results Export**: Saves results in Excel, CSV, and text formats

## Directory Structure

```
graph-reduction-communicability/
├── src/
│   └── graph_reduction/
│       └── core/
│           └── coarseners.py          # CoCoNUT and CoarseNet implementations
├── data/
│   ├── networks/                      # Your .gml network files go here
│   └── sample_networks/               # Auto-generated sample networks
├── results/
│   ├── quick_test/                    # Quick test results
│   ├── full_experiment/               # Full experiment results
│   └── coconut_experiments/           # Default experiment results
├── coconut_bignets_experiment.py      # Main experiment script
├── run_coconut_experiment.py          # Interactive runner
├── experiment_config.py               # Configuration settings
└── EXPERIMENT_README.md               # This file
```

## Usage Instructions

### Option 1: Interactive Runner (Recommended)

```bash
python run_coconut_experiment.py
```

This will show a menu with options:
1. **Quick test**: Runs on sample networks with reduced parameter range
2. **Full experiment**: Runs on all networks with full parameter range  
3. **Create sample networks**: Generates test networks for experimentation
4. **Exit**: Quit the program

### Option 2: Direct Script Usage

```python
from coconut_bignets_experiment import NetworkExperiment

# Initialize experiment
experiment = NetworkExperiment("data/networks", "results/my_experiment")

# Run experiments
results = experiment.run_experiments(
    methods=['CoCoNUT', 'CoarseNet'],
    max_networks=10  # Limit to first 10 networks
)

# Generate report
experiment.generate_summary_report(results)
```

### Option 3: Custom Configuration

```python
from experiment_config import ExperimentConfig, EXPERIMENT_PRESETS

# Use a preset configuration
config = EXPERIMENT_PRESETS["comparison_study"]

# Or create custom configuration
config = ExperimentConfig.get_custom_config(
    alpha_range=[0.2, 0.4, 0.6, 0.8],
    methods=['CoCoNUT'],
    max_networks=5
)
```

## Input Requirements

### Network Files
- Place your network files in `.gml` format in the `data/networks/` directory
- Networks should be:
  - Undirected (or will be converted to undirected)
  - Simple (no self-loops, no multi-edges)
  - Connected (isolated nodes will be removed)

### Supported Network Formats
- **GML files** (`.gml`): Primary format
- The script can be extended to support other formats (GraphML, edge lists, etc.)

## Output Files

### Results Directory Structure
```
results/experiment_name/
├── coconut_experiment_results.xlsx    # Main results file
├── experiment_summary.txt             # Summary report
└── network_name/                      # Per-network results
    ├── original_network_name.gml
    ├── reduced_CoCoNUT_network_name_0.5.gml
    ├── reduced_CoarseNet_network_name_0.5.gml
    └── *_adj_matrix.txt               # Adjacency matrices
```

### Metrics Calculated

1. **Basic Properties**:
   - Number of nodes/edges (original vs reduced)
   - Reduction ratios

2. **Spectral Properties**:
   - Algebraic connectivity
   - Spectral gap
   - Eigenvalue preservation

3. **Connectivity**:
   - Connected components
   - Connectivity preservation

4. **Performance**:
   - Execution time per experiment
   - Memory usage (if available)

## Algorithm Parameters

### Alpha (Reduction Factor)
- **Range**: 0.1 to 0.95 (default)
- **Meaning**: Fraction of nodes to merge
- **Example**: α=0.5 means merge ~50% of nodes

### Methods Available
- **CoCoNUT**: Communicability-based coarsening
- **CoarseNet**: Spectral coarsening baseline

## Sample Networks

The script can generate various types of sample networks for testing:

- **Real-world**: Karate Club graph
- **Random**: Erdős-Rényi graphs
- **Scale-free**: Barabási-Albert graphs  
- **Small-world**: Watts-Strogatz graphs
- **Regular**: Random regular graphs
- **Structured**: Complete, cycle, star, grid, path graphs

## Configuration Options

Edit `experiment_config.py` to customize:

```python
# Experiment parameters
ALPHA_RANGE_FULL = [0.1, 0.2, 0.3, ..., 0.95]
ALPHA_RANGE_QUICK = [0.2, 0.4, 0.6, 0.8]

# Methods to test
DEFAULT_METHODS = ['CoCoNUT', 'CoarseNet']

# Performance limits
TIMEOUT_PER_EXPERIMENT = 300  # 5 minutes max per experiment
MAX_NETWORKS_QUICK_TEST = 5
```

## Troubleshooting

### Common Issues

1. **No networks found**:
   ```
   No .gml files found in 'data/networks'
   ```
   **Solution**: Add `.gml` network files to the `data/networks/` directory or run option 3 to create sample networks.

2. **Memory errors with large networks**:
   **Solution**: Reduce the number of networks or alpha values, or run experiments on smaller subsets.

3. **Import errors**:
   ```
   ModuleNotFoundError: No module named 'src.graph_reduction'
   ```
   **Solution**: Run scripts from the root directory of the project.

### Performance Tips

1. **For large experiments**: Use the `max_networks` parameter to limit the number of networks
2. **For quick testing**: Use the quick test option with sample networks
3. **For memory efficiency**: Process networks one at a time instead of loading all at once

## Extension and Customization

### Adding New Coarsening Methods

1. Implement your method in `src/graph_reduction/core/coarseners.py`
2. Add it to the `available_methods` dictionary in `NetworkExperiment`
3. Update the configuration files

### Adding New Metrics

1. Extend the `calculate_spectral_metrics` method in `NetworkExperiment`
2. Add new metric calculations as needed

### Custom Network Formats

1. Extend the `load_networks` method to support additional formats
2. Add format detection and loading logic

## Citation

If you use this experimental framework in your research, please cite:

```
CoCoNUT: Communicability-based Coarsening of Networks Using Topology
[Add your publication details here]
```

## Contact

For questions, issues, or contributions, please [add contact information or repository details].
