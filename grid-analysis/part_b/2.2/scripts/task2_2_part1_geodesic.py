"""
Task 2.2 - Geographic and Geospatial Analysis
Part 1: Load data, recompute geodesic distances, categorize lines by length
"""
from _paths import DATA_DIR, OUT_DIR
import pandas as pd
import numpy as np
from geopy.distance import geodesic

pd.set_option("display.width", 140)

utilities = pd.read_csv(DATA_DIR / "utilities.csv")
substations = pd.read_csv(DATA_DIR / "substations.csv")
lines = pd.read_csv(DATA_DIR / "lines.csv")

print("=== Dataset shapes ===")
print("utilities:", utilities.shape, " substations:", substations.shape, " lines:", lines.shape)

# ---------------------------------------------------------------------
# Recompute line distances using the geodesic (Karney) formula and
# compare against the "Length (km)" field already present in lines.csv
# ---------------------------------------------------------------------
sub_coords = substations.set_index("Substation ID")[["Latitude", "Longitude"]]

def geodesic_km(row):
    try:
        a = tuple(sub_coords.loc[row["Source Substation ID"]])
        b = tuple(sub_coords.loc[row["Destination Substation ID"]])
        return geodesic(a, b).km
    except KeyError:
        return np.nan

lines["Geodesic Distance (km)"] = lines.apply(geodesic_km, axis=1).round(2)
lines["Route Factor"] = (lines["Length (km)"] / lines["Geodesic Distance (km)"]).round(3)

print("\n=== Straight-line (geodesic) vs recorded route length ===")
print(lines[["Line ID", "Source Substation", "Destination Substation",
             "Length (km)", "Geodesic Distance (km)", "Route Factor"]].head(10).to_string(index=False))

print("\nRoute factor summary (recorded length / straight-line distance):")
print(lines["Route Factor"].describe().round(3))
print("\nInterpretation: a route factor of 1.00 means the line runs perfectly straight; "
      "values above 1.00 reflect the routing/terrain allowance baked into the synthetic "
      "generator (1.05-1.30x for regional/meshed lines). No line in this dataset should "
      "have a route factor below 1.0, since a line cannot be shorter than the straight-line "
      "distance between its two endpoints.")

bad_routes = lines[lines["Route Factor"] < 0.999]
print(f"\nLines with an impossible route factor (<1.0): {len(bad_routes)}")

# ---------------------------------------------------------------------
# Distance categorization: short / medium / long transmission runs
# ---------------------------------------------------------------------
# Thresholds chosen using both domain convention (short local feeders vs.
# long interregional/cross-border backbones) and the empirical distribution.
print("\n=== Length (km) distribution (recorded) ===")
print(lines["Length (km)"].describe().round(1))
print("\nQuantiles (25/50/75/90):")
print(lines["Length (km)"].quantile([0.25, 0.5, 0.75, 0.9]).round(1))

SHORT_MAX = 40      # local/regional distribution runs
MEDIUM_MAX = 100     # inter-town / sub-regional runs
# > MEDIUM_MAX        long-distance backbone / cross-border runs

def categorize(km):
    if km <= SHORT_MAX:
        return "Short (<=40 km)"
    elif km <= MEDIUM_MAX:
        return "Medium (41-100 km)"
    else:
        return "Long (>100 km)"

lines["Distance Category"] = lines["Length (km)"].apply(categorize)

print("\n=== Line counts by distance category ===")
cat_counts = lines["Distance Category"].value_counts().reindex(
    ["Short (<=40 km)", "Medium (41-100 km)", "Long (>100 km)"])
print(cat_counts)

print("\n=== Distance category vs voltage level (cross-tab) ===")
print(pd.crosstab(lines["Distance Category"], lines["Voltage (kV)"]))

lines.to_csv(OUT_DIR / "lines_with_geodesic.csv", index=False)
print("\nSaved lines_with_geodesic.csv")
