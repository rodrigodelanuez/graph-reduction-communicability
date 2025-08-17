# graph-reduction-communicability

Initial proposed structure for the project:

```markdown
graph-reduction-communicability/
│
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── pyproject.toml
│
├── data/
│   ├── raw/                  # Raw graph files (e.g., .gml, .txt)
│   │   └── karate.gml
│   └── processed/            # Graphs after any cleaning or preprocessing
│
├── notebooks/
│   ├── 1-exploratory-analysis.ipynb
│   └── 2-visualize-reduction-results.ipynb
│
├── results/
│   ├── figures/              # Saved plots (e.g., original vs. reduced graphs)
│   │   └── karate_club_reduction.png
│   ├── tables/               # Saved metric comparisons (e.g., as .csv files)
│   │   └── karate_club_spectral_metrics.csv
│   └── reduced_graphs/       # Saved instances of reduced graphs
│       └── karate_club_reduced.gml
│
├── scripts/
│   ├── download_datasets.py  # Script to fetch all networks used in the paper
│   └── reproduce_paper_results.py # Master script to run all analyses
│
└── src/
    └── graph_reduction/
        ├── __init__.py
        ├── analysis/
        │   ├── __init__.py
        │   ├── spectral.py   # Functions for all spectral metrics
        │   └── structural.py # Functions for structural metrics and graph kernels
        │
        ├── algorithms/...  # Folder with the logic from Loukas repo
        │
        ├── core/
        │   ├── __init__.py
        │   ├── coarseners.py # Coarsening strategies (e.g., AdaptedCoarseNet)
        │   └── scorers.py    # Scoring strategies (e.g., CommunicabilityScore)
        │
        ├── utils.py          # Functions to process our data
        ├── io.py             # Functions to load/save graphs and results
        └── cli.py            # Command-line interface to run a reduction
```