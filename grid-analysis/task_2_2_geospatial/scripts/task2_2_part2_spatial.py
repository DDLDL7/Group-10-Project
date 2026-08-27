"""
Task 2.2 - Geographic and Geospatial Analysis
Part 2: Regional density, coverage gaps, geographic clustering, utility territory
"""
from _paths import DATA_DIR, OUT_DIR
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN, KMeans

pd.set_option("display.width", 140)

utilities = pd.read_csv(DATA_DIR / "utilities.csv")
substations = pd.read_csv(DATA_DIR / "substations.csv")
lines = pd.read_csv(OUT_DIR / "lines_with_geodesic.csv")

ghana_subs = substations[substations["Country"] == "Ghana"].copy()

# ---------------------------------------------------------------------
# Regional connectivity / density comparison
# Approximate, widely-cited real-world land-area figures (km^2) for
# Ghana's pre-2018 ten regions are used ONLY to give the substation counts
# geographic context (substations per 1,000 km^2). These area figures are
# real-world reference numbers, NOT part of the synthetic dataset, and the
# substation/line figures themselves remain synthetic and illustrative.
# ---------------------------------------------------------------------
region_area_km2 = {
    "Greater Accra": 3245,
    "Ashanti": 24389,
    "Western": 23921,
    "Central": 9826,
    "Eastern": 19323,
    "Volta": 20570,
    "Bono": 39557,   # old undivided Brong-Ahafo
    "Northern": 70384,  # old undivided Northern
    "Upper East": 8842,
    "Upper West": 18476,
}

reg = ghana_subs.groupby("Region").agg(
    Substation_Count=("Substation ID", "count"),
    Avg_Capacity_MVA=("Capacity (MVA)", "mean"),
    Total_Capacity_MVA=("Capacity (MVA)", "sum"),
    Active_Count=("Status", lambda s: (s == "Active").sum()),
).reset_index()
reg["Area_km2"] = reg["Region"].map(region_area_km2)
reg["Substations_per_1000km2"] = (reg["Substation_Count"] / reg["Area_km2"] * 1000).round(3)
reg["Avg_Capacity_MVA"] = reg["Avg_Capacity_MVA"].round(1)
reg["Total_Capacity_MVA"] = reg["Total_Capacity_MVA"].round(1)
reg = reg.sort_values("Substations_per_1000km2", ascending=False)

print("=== Regional substation density (synthetic substation counts vs real-world area) ===")
print(reg.to_string(index=False))
reg.to_csv(OUT_DIR / "regional_density.csv", index=False)

# Geographic gaps: regions with low density are candidates for "underserved"
print("\n=== Candidate coverage gaps (lowest substations per 1000 km^2) ===")
print(reg.tail(3)[["Region", "Substation_Count", "Area_km2", "Substations_per_1000km2"]].to_string(index=False))

# ---------------------------------------------------------------------
# Utility territory: geographic footprint of each utility (via lines they operate)
# ---------------------------------------------------------------------
util_lookup = utilities.set_index("Utility ID")["Alias"]
lines["Utility Alias"] = lines["Utility ID"].map(util_lookup)

sub_region = substations.set_index("Substation ID")["Region"]
lines["Source Region"] = lines["Source Substation ID"].map(sub_region)
lines["Dest Region"] = lines["Destination Substation ID"].map(sub_region)

print("\n=== Utility territory: regions touched by each utility's lines ===")
for uid, alias in util_lookup.items():
    sub = lines[lines["Utility ID"] == uid]
    if sub.empty:
        continue
    regions_touched = sorted(set(sub["Source Region"]) | set(sub["Dest Region"]))
    print(f"{alias:8s} | lines: {len(sub):3d} | regions: {', '.join(regions_touched)}")

# ---------------------------------------------------------------------
# Cross-border / WAPP connectivity
# ---------------------------------------------------------------------
border_subs = substations[substations["Country"] != "Ghana"]
print(f"\n=== Cross-border (WAPP-style) nodes: {len(border_subs)} ===")
print(border_subs[["Substation ID", "Short Name", "Region", "Country", "Voltage (kV)"]].to_string(index=False))

cross_lines = lines[(lines["Source Region"].isin(border_subs["Region"])) |
                     (lines["Dest Region"].isin(border_subs["Region"]))]
print(f"\nCross-border interconnection lines: {len(cross_lines)}")
print(cross_lines[["Line ID", "Source Substation", "Destination Substation",
                    "Length (km)", "Utility Alias"]].to_string(index=False))

# ---------------------------------------------------------------------
# Geographic clustering (DBSCAN, haversine metric) - natural clusters
# ---------------------------------------------------------------------
coords = np.radians(ghana_subs[["Latitude", "Longitude"]].values)
kms_per_radian = 6371.0088
epsilon = 40 / kms_per_radian  # 40 km neighborhood radius

db = DBSCAN(eps=epsilon, min_samples=3, algorithm="ball_tree", metric="haversine").fit(coords)
ghana_subs["DBSCAN Cluster"] = db.labels_
n_clusters = len(set(db.labels_)) - (1 if -1 in db.labels_ else 0)
n_noise = int((db.labels_ == -1).sum())
print(f"\n=== DBSCAN geographic clustering (40 km radius, min 3 substations) ===")
print(f"Clusters found: {n_clusters}, isolated substations (noise): {n_noise}")
print(ghana_subs.groupby("DBSCAN Cluster").agg(
    n=("Substation ID", "count"),
    regions=("Region", lambda s: ", ".join(sorted(set(s))))
).to_string())

# ---------------------------------------------------------------------
# High-capacity substation clustering (KMeans) - where are the big nodes?
# ---------------------------------------------------------------------
threshold = ghana_subs["Capacity (MVA)"].quantile(0.75)
high_cap = ghana_subs[ghana_subs["Capacity (MVA)"] >= threshold].copy()
print(f"\n=== High-capacity substations (top quartile, >= {threshold:.1f} MVA): {len(high_cap)} ===")

k = min(4, len(high_cap))
km = KMeans(n_clusters=k, random_state=42, n_init=10)
high_cap["KMeans Cluster"] = km.fit_predict(high_cap[["Latitude", "Longitude"]].values)
print(high_cap[["Short Name", "Region", "Capacity (MVA)", "Voltage (kV)", "KMeans Cluster"]]
      .sort_values("KMeans Cluster").to_string(index=False))

ghana_subs.to_csv(OUT_DIR / "substations_with_clusters.csv", index=False)
high_cap.to_csv(OUT_DIR / "high_capacity_clusters.csv", index=False)
print("\nSaved substations_with_clusters.csv and high_capacity_clusters.csv")
