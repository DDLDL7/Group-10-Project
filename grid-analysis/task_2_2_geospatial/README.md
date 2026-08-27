# Task 2.2 — Geographic and Geospatial Analysis

Reproducible pipeline for the National Electricity Grid geospatial analysis
(CS 112 course project), living alongside the rest of
[grid-analysis](../). The dataset generator is seeded (`random.seed(42)`),
so everyone on the team who runs this produces byte-for-byte identical data.

## Folder structure

```
.
├── requirements.txt
├── scripts/
│   ├── _paths.py                    # shared path helper — do not run directly
│   ├── generate_dataset.py          # step 1: builds data/*.csv
│   ├── task2_2_part1_geodesic.py    # step 2: distance recompute + categorization
│   ├── task2_2_part2_spatial.py     # step 3: density, gaps, clustering, utility territory
│   ├── task2_2_part3_map.py         # step 4: interactive Folium map
│   ├── task2_2_part4_charts.py      # step 5: static charts
│   └── run_all.py                   # runs steps 1-5 in order
├── data/                            # generated CSVs (utilities/substations/lines)
└── outputs/                         # map, charts, and derived CSVs
```

## Running it

From inside this folder (`grid-analysis/task_2_2_geospatial/`):
```bash
pip install -r requirements.txt
python scripts/run_all.py
```
This regenerates everything in `data/` and `outputs/`, including
`outputs/ghana_grid_interactive_map.html` — open that file directly in a
browser to view the interactive map.

You can also run any single step on its own, e.g. just the charts:
```bash
python scripts/task2_2_part4_charts.py
```
(Run `generate_dataset.py`, then `part1`, then `part2` first at least once —
later steps read files the earlier ones produce.)

## Why this runs the same on every laptop

- The dataset generator is seeded, so `data/*.csv` is identical for everyone.
- All scripts resolve paths relative to this folder via `scripts/_paths.py`
  (using `__file__`), not the current working directory — so it doesn't
  matter whether a teammate runs `python scripts/run_all.py` from here,
  from inside `scripts/`, or from an IDE's "Run" button.

## Notes

- `data/` and `outputs/` are committed here so teammates and graders can see
  results without running anything.
- This pipeline is independent of the main `grid-analysis/src/` package —
  it uses its own dataset generator and its own `data/`/`outputs/` folders,
  scoped to this subfolder.
