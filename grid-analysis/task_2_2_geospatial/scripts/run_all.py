"""
Runs the full Task 2.2 geospatial pipeline end to end, in order:
  1. generate_dataset.py      -> data/utilities.csv, substations.csv, lines.csv
  2. task2_2_part1_geodesic.py -> outputs/lines_with_geodesic.csv
  3. task2_2_part2_spatial.py  -> outputs/regional_density.csv, substations_with_clusters.csv, ...
  4. task2_2_part3_map.py      -> outputs/ghana_grid_interactive_map.html
  5. task2_2_part4_charts.py   -> outputs/chart_*.png

Usage (from anywhere):
    python scripts/run_all.py
"""
import runpy
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

STEPS = [
    "generate_dataset.py",
    "task2_2_part1_geodesic.py",
    "task2_2_part2_spatial.py",
    "task2_2_part3_map.py",
    "task2_2_part4_charts.py",
]

for step in STEPS:
    print(f"\n{'=' * 70}\nRunning {step}\n{'=' * 70}")
    runpy.run_path(str(SCRIPTS_DIR / step), run_name="__main__")

print("\nAll done. Check the outputs/ folder for the map, charts, and CSVs.")
