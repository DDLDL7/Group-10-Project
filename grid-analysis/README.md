# National Electricity Grid Network Analysis

Data science component of the CS 112 final project. Reproducible pipeline
for cleaning, analysing, and visualising a synthetic Ghana-grounded
electricity grid dataset. The generator is seeded (`random.seed(42)`), so
every run — and every team member — produces byte-for-byte identical CSVs.

## Folder structure

```
.
├── requirements.txt
├── generate_data.py            # seeded dataset generator -> data/*.csv
├── src/                        # tested, reusable analysis modules
│   ├── cleaning.py             #   load/clean/validate/merge
│   ├── network.py              #   NetworkX graph, centrality, N-1 contingency
│   ├── geo.py                  #   Folium/Plotly maps, distance/cluster analysis
│   └── business_intelligence.py#   utility footprint, capacity, reliability-risk proxy
├── tests/                      # pytest unit tests for src/
├── notebooks/                  # 01-04: cleaning/EDA, network, geographic, merging
├── dashboard.py                # Streamlit dashboard (Overview/Network/Geography/Reliability/Search)
├── task_2_3_business_intelligence.py  # standalone BI/reliability report script
├── task_2_3_findings.md        # its generated findings summary
├── REPORT.md                   # 2-3 page written findings report
├── data/                       # generated CSVs (utilities/substations/lines)
├── outputs/                    # charts, maps, merged dataset
└── legacy_scripts/             # early individual exploratory work (contribution evidence)
```

## One-time setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running it

```bash
python generate_data.py          # (re)generate data/utilities.csv, substations.csv, lines.csv
pytest tests/                    # unit tests for cleaning/geo/network
streamlit run dashboard.py       # interactive dashboard
python task_2_3_business_intelligence.py   # standalone BI/reliability report + charts
```

Or work through `notebooks/01_data_cleaning_and_eda.ipynb` →
`04_merging_and_visualization.ipynb` in order for the full walkthrough.

## Why this runs the same on every laptop

- The generator is seeded, so `data/*.csv` is identical for everyone.
- `src/` modules take DataFrames/paths as arguments rather than relying on
  the current working directory, so they work the same whether you run
  `pytest`, the dashboard, or a notebook.
- `requirements.txt` pins the packages needed (not exact versions) — run
  `pip freeze > requirements-lock.txt` after installing if your team wants
  fully locked versions.

## Notes

- `data/` and `outputs/` are committed so teammates and graders can see
  results without running anything first.
- All figures are computed from **synthetic, seeded data** grounded in
  real Ghanaian/WAPP geography and utility names, but with illustrative
  coordinates, capacities, and connections — see `REPORT.md` section 5 for
  the full limitations note before treating anything here as a verified
  fact about Ghana's actual grid.
