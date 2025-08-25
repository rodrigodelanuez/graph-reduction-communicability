"""
Command-line interface for running standardized graph reduction experiments.
"""

import typer
import time
import traceback
from pathlib import Path
from typing import List, Optional, Annotated, Dict
from enum import Enum
from .analysis.spectral import analyze_single_graph_properties
from .io import load_graph, save_reduced_graph, save_metrics_excel, save_metrics_csv, save_metrics_json, iter_graph_files
from .core.coarseners import CoarseNetCoarsener, CoCoNUTCoarsener, BaseCoarsener

app = typer.Typer(add_completion=False, context_settings={"help_option_names": ["-h", "--help"]})

class Method(str, Enum):
    coarsenet = "coarsenet"
    coconut = "coconut"

class Metric(str, Enum):
    spectral_ratio_L = "spectral_ratio_L"
    spectral_gap_A = "spectral_gap_A"
    algebraic_connectivity_L = "algebraic_connectivity_L"
    spectral_radius_A = "spectral_radius_A"

METRIC_NAME_MAP = {
    'spectral_ratio_L': 'Spectral Ratio of L',
    'spectral_gap_A': 'Spectral Gap of A',
    'algebraic_connectivity_L': 'Algebraic Connectivity of L',
    'spectral_radius_A': 'Spectral Radius of A',
    # AÑADIDO: Nombres para las nuevas métricas fijas
    'Number of Nodes': 'Number of Nodes',
    'Number of Edges': 'Number of Edges'
}

@app.command()
def run_experiment(
    data_dir: Annotated[Path, typer.Argument(help="Directory containing graph files.")],
    method: Annotated[Method, typer.Option(help="Coarsening algorithm to use.")],
    metrics_to_compute: Annotated[Optional[List[Metric]], typer.Option("--metric", "-m", help="Spectral metric to compute. Can be used multiple times.")] = None,
    output_dir: Annotated[Optional[Path], typer.Option("--output", "-o", help="Output directory for results.")] = None,
    ratios: Annotated[List[float], typer.Option("--ratios", "-r", help="List of reduction ratios.")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output.")] = False,
    save_graphs: Annotated[bool, typer.Option(help="Save the reduced graph files.")] = True,
    output_format: Annotated[str, typer.Option("--format", "-f", help="Output format for metrics (excel, csv, json).")] = "excel"
):
    """
    Run a graph reduction experiment with a specified method, dataset, and metrics.
    """
    coarseners: Dict[str, BaseCoarsener] = {
        "coarsenet": CoarseNetCoarsener(), 
        "coconut": CoCoNUTCoarsener()
    }
    coarsener = coarseners[method.value]

    ratio_list = ratios if ratios else [0.1, 0.3, 0.5, 0.7, 0.9]
    if not all(0 < r < 1 for r in ratio_list):
        typer.echo("Error: All reduction ratios must be between 0 and 1.")
        raise typer.Exit(code=1)

    if output_dir is None:
        timestamp = int(time.time())
        output_dir = Path("results") / f"{method.value}_{data_dir.name}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    graphs = iter_graph_files(data_dir)
    if not graphs:
        typer.echo(f"Error: No graph files found in {data_dir}")
        raise typer.Exit(code=1)

    typer.echo(f"Starting experiment: Method='{method.value}', Dataset='{data_dir.name}'")
    typer.echo(f"Found {len(graphs)} graphs to process.")
    typer.echo(f"Testing reduction ratios: {sorted(ratio_list)}")
    typer.echo(f"Output will be saved to: {output_dir}")

    all_results = []
    
    if not metrics_to_compute:
        metrics_to_compute = [m.value for m in Metric]
        typer.echo(f"No specific metrics selected. Computing all: {metrics_to_compute}")

    for graph_name, graph_file in graphs.items():
        print(f"\n{'='*60}\nProcessing: {graph_name}\n{'='*60}")
        graph_start_time = time.monotonic()
        try:
            try:
                G = load_graph(graph_file)
                print(f"Loaded graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
            except Exception as e:
                print(f"✗ FAILED to load {graph_name}. Error: {e}. Skipping this graph.")
                continue
            
            original_metrics = analyze_single_graph_properties(G)
            
            reduced_graphs = coarsener.coarsen_with_intermediate_checkpoints(G, ratio_list, verbose=verbose)

            for ratio in sorted(ratio_list):
                if ratio not in reduced_graphs:
                    print(f"Warning: No reduced graph found for ratio {ratio}. Skipping.")
                    continue
                G_reduced = reduced_graphs[ratio]
                
                ratio_start_time = time.monotonic()
                reduced_metrics = analyze_single_graph_properties(G_reduced)
                ratio_end_time = time.monotonic()
                duration = ratio_end_time - ratio_start_time

                print(f"  -> Analyzing ratio {ratio:.2f} (Reduced Graph: {G_reduced.number_of_nodes()} nodes) - Time: {duration:.2f}s")
                
                base_info = {'Network': graph_name, 'Method': method.value, 'Alpha': ratio}

                # Procesa las métricas espectrales seleccionadas por el usuario
                for key in metrics_to_compute:
                    original_value = original_metrics.get(key)
                    reduced_value = reduced_metrics.get(key)
                    reduction_perc = ((original_value - reduced_value) / original_value * 100) if original_value else 0.0
                    
                    all_results.append({
                        **base_info,
                        'Metric': METRIC_NAME_MAP[key],
                        'Original': original_value,
                        'Reduced': reduced_value,
                        'Reduction (%)': reduction_perc
                    })
                
                # AÑADIDO: Añade siempre el número de nodos y aristas a los resultados
                nodes_orig = G.number_of_nodes()
                nodes_red = G_reduced.number_of_nodes()
                edges_orig = G.number_of_edges()
                edges_red = G_reduced.number_of_edges()

                all_results.append({
                    **base_info,
                    'Metric': METRIC_NAME_MAP['Number of Nodes'],
                    'Original': nodes_orig,
                    'Reduced': nodes_red,
                    'Reduction (%)': (1 - nodes_red / nodes_orig) * 100 if nodes_orig > 0 else 0
                })
                all_results.append({
                    **base_info,
                    'Metric': METRIC_NAME_MAP['Number of Edges'],
                    'Original': edges_orig,
                    'Reduced': edges_red,
                    'Reduction (%)': (1 - edges_red / edges_orig) * 100 if edges_orig > 0 else 0
                })

                if save_graphs:
                    output_file = output_dir / graph_name / f"{graph_name}_reduced_{method.value}_{ratio:.2f}.gml"
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    save_reduced_graph(G_reduced, output_file)
            
            graph_end_time = time.monotonic()
            print(f"\n✓ Completed {graph_name} in {graph_end_time - graph_start_time:.2f}s")

        except Exception:
            print(f"✗ An unexpected error occurred while processing {graph_name}:")
            traceback.print_exc()
            continue

    if not all_results:
        typer.echo("Experiment finished, but no results were generated.")
        raise typer.Exit(code=1)

    format_extensions = {'excel': 'xlsx', 'csv': 'csv', 'json': 'json'}
    file_ext = format_extensions.get(output_format.lower(), output_format.lower())
    results_path = output_dir / f"{method.value}_{data_dir.name}_results.{file_ext}"
    
    save_func = {'excel': save_metrics_excel, 'csv': save_metrics_csv, 'json': save_metrics_json}.get(output_format.lower())
    if save_func:
        save_func(all_results, results_path)

    typer.echo(f"\n{'='*60}\nExperiment complete!\n{'='*60}")
    typer.echo(f"Results for {len(graphs)} graphs saved to: {results_path}")