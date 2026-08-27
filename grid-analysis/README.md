# grid-analysis

Data-science analysis of a synthetic National Electricity Grid dataset
(pandas, NetworkX, Folium, Plotly, Streamlit), grounded in Ghana's real grid
operators (ECG, NEDCo, GRIDCo, VRA).

## Running it

```bash
cd grid-analysis
pip install -r requirements.txt
python generate_data.py          # writes data/utilities.csv, substations.csv, lines.csv (seeded, reproducible)
streamlit run dashboard.py       # interactive dashboard
```

Or step through the notebooks in order (`notebooks/01_...` through
`06_...`) to see the full narrated analysis.

## Structure

```
grid-analysis/
  generate_data.py     # seeded synthetic dataset generator
  src/                  # importable analysis package - shared by notebooks, dashboard.py, and tests
    cleaning.py         # load/clean/validate/merge the three raw CSVs
    network.py          # graph construction, centrality, N-1 contingency analysis
    geo.py               # Folium map building
    bi.py                # business-intelligence proxy metrics
    viz.py               # chord diagram, heatmaps, animated map, comparison charts
  notebooks/            # narrated end-to-end analysis, 01 through 06
  dashboard.py          # Streamlit app (Overview / Network / Geography / Reliability / Search)
  data/                 # generated CSVs (utilities/substations/lines)
  outputs/              # charts, merged dataset, standalone HTML maps
  tests/                # pytest coverage for src/
  report.md             # written findings (2-3 pages)
  task_2_2_geospatial/  # a separate, self-contained geospatial-analysis sub-pipeline
                         # (its own generator/data/outputs - see its own README)
```

## Tests

```bash
pytest tests/
```

## Notes on the data

All business-intelligence and reliability metrics are explicitly labeled
as **proxies** — the synthetic dataset has no real load, population, or
outage-history data, so figures like "capacity concentration" or
"reliability risk" are structural leads for further investigation, not
verified operational facts. See `report.md` for the full caveat and
findings.
