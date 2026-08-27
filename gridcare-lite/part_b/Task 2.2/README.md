# Task 2.2 — Geographic and Geospatial Analysis

Reproducible pipeline for the National Electricity Grid geospatial analysis
(CS 112 course project). The dataset generator is seeded (`random.seed(42)`),
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

## One-time setup (each teammate, once)

1. Install Python 3.10+ if you don't have it.
2. Clone the repo and go into it:
   ```bash
   git clone <your-repo-url>
   cd <repo-folder>
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Running it

From the repo root:
```bash
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

## Adding this to your team's GitHub repo

If your team already has a shared repo, from inside your local clone of it:

```bash
# copy this scripts/, data/, outputs/, requirements.txt, README.md into
# the repo folder (or into a subfolder like task2_2_geospatial/), then:
git checkout -b task2.2-geospatial
git add scripts/ data/ outputs/ requirements.txt README.md
git commit -m "Task 2.2: geospatial analysis pipeline + interactive map"
git push origin task2.2-geospatial
```

Then open a pull request into `main`/`develop` so the rest of the team can
review it before merging. If you don't have a repo yet:

```bash
cd <this folder>
git init
git add .
git commit -m "Initial commit: Task 2.2 geospatial analysis"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

## Why this runs the same on every laptop

- The dataset generator is seeded, so `data/*.csv` is identical for everyone.
- All scripts resolve paths relative to the repo root via `scripts/_paths.py`
  (using `__file__`), not the current working directory — so it doesn't
  matter whether a teammate runs `python scripts/run_all.py` from the repo
  root, from inside `scripts/`, or from an IDE's "Run" button.
- `requirements.txt` pins the packages (not exact versions) needed —
  if you want fully locked versions across the team, run
  `pip freeze > requirements-lock.txt` after installing and commit that too.

## Notes

- `data/` and `outputs/` are committed here so teammates and graders can see
  results without running anything. If your team prefers to regenerate
  everything locally instead of tracking generated files in git, add
  `data/` and `outputs/` to `.gitignore` and remove them from version control
  (`git rm -r --cached data outputs`).
