"""
Command-line interface for running graph reduction experiments.
"""

import typer
import networkx as nx
from pathlib import Path
from typing import List, Optional, Annotated
import time
from .analysis.spectral import analyze_single_graph_properties
from .io import load_graph, save_reduced_graph, save_metrics_excel, save_metrics_csv, save_metrics_json, save_adjacency_matrix, iter_graph_files
from .core.coarseners import CoarseNetCoarsener

app = typer.Typer(add_completion=False, context_settings={"help_option_names": ["-h", "--help"]})

import traceback

@app.command()
def run_coarsenet(
    data_dir: Annotated[Path, typer.Argument(help="Directory containing BigNets graph files")],
    output_dir: Annotated[Optional[Path], typer.Option("--output", "-o", help="Output directory for results")] = None,
    ratios: Annotated[List[float], typer.Option("--ratios", "-r", help="Reduction ratios (e.g., -r 0.3 0.5)")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
    save_graphs: Annotated[bool, typer.Option("--save-graphs", help="Save reduced graphs")] = True,
    save_matrices: Annotated[bool, typer.Option("--save-matrices", help="Save adjacency matrices")] = False,
    output_format: Annotated[str, typer.Option("--format", "-f", help="Output format (excel, csv, json)")] = "excel"
):
    """
    Run CoarseNet experiments on BigNets dataset with multiple reduction ratios.
    """
    # Use default ratios if none are provided
    ratio_list = ratios if ratios is not None else [0.1]

    # Validate ratios list
    if not ratio_list:
        typer.echo("Please provide at least one reduction ratio (e.g., -r 0.3 0.5 0.7)")
        raise typer.Exit(code=1)
    for ratio in ratio_list:
        if not (0 < ratio < 1):
            typer.echo(f"Reduction ratio must be between 0 and 1, got: {ratio}")
            raise typer.Exit(code=1)

    # Create output directory
    if output_dir is None:
        timestamp = int(time.time())
        output_dir = Path("results") / f"coarsenet_experiment_{timestamp}"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Get graph files
    graphs = iter_graph_files(data_dir)
    if not graphs:
        typer.echo(f"No graph files found in {data_dir}")
        raise typer.Exit(code=1)

    typer.echo(f"Found {len(graphs)} graphs in {data_dir}")
    typer.echo(f"Testing reduction ratios: {ratio_list}")
    typer.echo(f"Output directory: {output_dir}")

    # Initialize coarsener
    coarsener = CoarseNetCoarsener()

    # Results storage
    all_results = []

    # Process each graph with all ratios
    for graph_name, graph_file in graphs.items():
        print(f"\n{'='*60}")
        print(f"Processing: {graph_name}")
        print(f"{'='*60}")

        try:
            # Load graph
            G = load_graph(graph_file)
            print(f"Loaded graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

            # Analyze original graph properties once
            original_metrics = analyze_single_graph_properties(G)
            original_metrics['Number of Nodes'] = G.number_of_nodes()
            original_metrics['Number of Edges'] = G.number_of_edges()

            # Coarsen graph with all ratios
            reduced_graphs = coarsener.coarsen_with_intermediate_checkpoints(G, ratio_list, verbose=verbose)

            # Calculate metrics for each reduction ratio
            for ratio in ratio_list:
                if ratio in reduced_graphs:
                    G_reduced = reduced_graphs[ratio]

                    # Analyze reduced graph properties
                    reduced_metrics = analyze_single_graph_properties(G_reduced)
                    reduced_metrics['Number of Nodes'] = G_reduced.number_of_nodes()
                    reduced_metrics['Number of Edges'] = G_reduced.number_of_edges()

                    # Mapping from internal keys to desired output names
                    metric_mapping = {
                        'spectral_ratio_L': 'Spectral Ratio of L',
                        'eigenratio': 'Eigenratio',
                        'spectral_gap_A': 'Spectral Gap of A',
                        'algebraic_connectivity_L': 'Algebraic Connectivity of L',
                        'spectral_radius_A': 'Spectral Radius of A',
                        'Number of Nodes': 'Number of Nodes',
                        'Number of Edges': 'Number of Edges'
                    }

                    # Transform results into the specified long format
                    for key, metric_name in metric_mapping.items():
                        if key in original_metrics and key in reduced_metrics:
                            original_value = original_metrics[key]
                            reduced_value = reduced_metrics[key]

                            # Calculate reduction percentage, handling division by zero
                            if original_value is not None and original_value != 0:
                                reduction_perc = (original_value - reduced_value) / original_value * 100
                            else:
                                reduction_perc = 0.0

                            result_row = {
                                'Network': graph_name,
                                'Method': 'CoarseNet',
                                'Alpha': ratio,
                                'Metric': metric_name,
                                'Original': original_value,
                                'Reduced': reduced_value,
                                'Reduction (%)': reduction_perc
                            }
                            all_results.append(result_row)

                    # Save reduced graph if requested
                    if save_graphs:
                        output_file = output_dir / graph_name / f"{graph_name}_reduced_{ratio:.2f}.gml"
                        output_file.parent.mkdir(parents=True, exist_ok=True)
                        save_reduced_graph(G_reduced, output_file)

            # Save metrics after processing all ratios for a graph
            if all_results:
                if output_format.lower() == "excel":
                    results_path = output_dir / "coarsenet_results.xlsx"
                    save_metrics_excel(all_results, results_path)
                elif output_format.lower() == "csv":
                    results_path = output_dir / "coarsenet_results.csv"
                    save_metrics_csv(all_results, results_path)
                elif output_format.lower() == "json":
                    results_path = output_dir / "coarsenet_results.json"
                    save_metrics_json(all_results, results_path)
                print(f"✓ Completed {graph_name} - Metrics updated in {results_path}")

        except Exception as e:
            print(f"✗ An error occurred while processing {graph_name}. The original error was:")
            # This prints the full traceback of the INITIAL error without triggering repr
            traceback.print_exc() 
            continue

    # Print final summary
    if all_results:
        typer.echo(f"\n{'='*60}")
        typer.echo("Experiment completed!")

        # Print summary
        typer.echo(f"\nExperiment Summary:")
        typer.echo(f"  Total graphs processed: {len(graphs)}")
        typer.echo(f"  Total result rows: {len(all_results)}")
        typer.echo(f"  Reduction ratios tested: {ratio_list}")
        typer.echo(f"  Output directory: {output_dir}")
        file_ext = 'xlsx' if output_format.lower() not in ['csv', 'json'] else output_format.lower()
        typer.echo(f"  Results file: {output_dir}/coarsenet_results.{file_ext}")

    else:
        typer.echo("No results to save.")
        raise typer.Exit(code=1)


@app.command()
def info(
    data_dir: Path = typer.Argument(..., help="Directory containing graph files")
):
    """
    Display information about available graphs in the dataset.
    """
    graphs = iter_graph_files(data_dir)

    if not graphs:
        typer.echo(f"No graph files found in {data_dir}")
        return

    typer.echo(f"Found {len(graphs)} graphs in {data_dir}:")
    typer.echo("-" * 50)

    for graph_name, graph_path in graphs.items():
        try:
            G = load_graph(graph_path)
            nodes = G.number_of_nodes()
            edges = G.number_of_edges()
            is_directed = G.is_directed()
            is_weighted = nx.is_weighted(G)

            typer.echo(f"{graph_name}:")
            typer.echo(f"  Nodes: {nodes}")
            typer.echo(f"  Edges: {edges}")
            typer.echo(f"  Directed: {is_directed}")
            typer.echo(f"  Weighted: {is_weighted}")
            typer.echo(f"  File: {graph_path.name}")
            typer.echo()

        except Exception as e:
            typer.echo(f"{graph_name}: Error loading - {e}")


if __name__ == "__main__":
    app()