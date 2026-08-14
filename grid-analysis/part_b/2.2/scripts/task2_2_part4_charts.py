"""
Task 2.2 - Geographic and Geospatial Analysis
Part 4: Static charts - distance distribution, regional density, clustering
"""
from _paths import DATA_DIR, OUT_DIR
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

plt.rcParams.update({"figure.dpi": 130, "font.size": 10})

lines = pd.read_csv(OUT_DIR / "lines_with_geodesic.csv")
reg = pd.read_csv(OUT_DIR / "regional_density.csv")
subs = pd.read_csv(OUT_DIR / "substations_with_clusters.csv")
high_cap = pd.read_csv(OUT_DIR / "high_capacity_clusters.csv")

# ------------------------------------------------------------------
# Chart 1: Distance distribution - histogram + category counts
# ------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

axes[0].hist(lines["Length (km)"], bins=14, color="#3498db", edgecolor="white")
axes[0].axvline(40, color="#e67e22", linestyle="--", linewidth=1.2, label="Short/Medium (40 km)")
axes[0].axvline(100, color="#e74c3c", linestyle="--", linewidth=1.2, label="Medium/Long (100 km)")
axes[0].set_xlabel("Line length (km)")
axes[0].set_ylabel("Number of lines")
axes[0].set_title("Distribution of transmission/distribution\nline lengths")
axes[0].legend(fontsize=8)

order = ["Short (<=40 km)", "Medium (41-100 km)", "Long (>100 km)"]
counts = lines["Distance Category"].value_counts().reindex(order)
colors = ["#2ecc71", "#f39c12", "#e74c3c"]
bars = axes[1].bar(order, counts.values, color=colors)
axes[1].set_ylabel("Number of lines")
axes[1].set_title("Lines by distance category")
axes[1].set_xticklabels(order, rotation=15, ha="right")
for b, v in zip(bars, counts.values):
    axes[1].text(b.get_x() + b.get_width() / 2, v + 0.4, str(int(v)), ha="center", fontsize=9)

plt.tight_layout()
plt.savefig(OUT_DIR / "chart_distance_distribution.png", bbox_inches="tight")
plt.close()
print("Saved chart_distance_distribution.png")

# ------------------------------------------------------------------
# Chart 2: Regional substation density (per 1000 km^2 of real-world area)
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 5))
reg_sorted = reg.sort_values("Substations_per_1000km2")
bar_colors = ["#e74c3c" if v < reg["Substations_per_1000km2"].median() else "#3498db"
              for v in reg_sorted["Substations_per_1000km2"]]
ax.barh(reg_sorted["Region"], reg_sorted["Substations_per_1000km2"], color=bar_colors)
ax.set_xlabel("Substations per 1,000 km$^2$ (real-world area, illustrative)")
ax.set_title("Regional substation density\n(red = below-median density → potential coverage gap)")
plt.tight_layout()
plt.savefig(OUT_DIR / "chart_regional_density.png", bbox_inches="tight")
plt.close()
print("Saved chart_regional_density.png")

# ------------------------------------------------------------------
# Chart 3: Geographic clustering visualization (DBSCAN clusters, lat/lon)
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.5, 7.5))
cluster_palette = {-1: "#bdbdbd", 0: "#e74c3c", 1: "#3498db", 2: "#2ecc71", 3: "#f39c12"}
for label, grp in subs.groupby("DBSCAN Cluster"):
    color = cluster_palette.get(label, "#9b59b6")
    lbl = "Isolated (noise)" if label == -1 else f"Cluster {label}"
    ax.scatter(grp["Longitude"], grp["Latitude"], s=60, color=color, label=lbl,
               edgecolor="white", linewidth=0.5)
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_title("Geographic clusters of substations\n(DBSCAN, 40 km radius, min 3 substations)")
ax.legend(fontsize=8, loc="lower left")
ax.set_aspect("equal", adjustable="datalim")
plt.tight_layout()
plt.savefig(OUT_DIR / "chart_dbscan_clusters.png", bbox_inches="tight")
plt.close()
print("Saved chart_dbscan_clusters.png")

# ------------------------------------------------------------------
# Chart 4: High-capacity substation KMeans clusters
# ------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.5, 7.5))
for label, grp in high_cap.groupby("KMeans Cluster"):
    color = cluster_palette.get(label, "#9b59b6")
    sizes = grp["Capacity (MVA)"] * 1.2
    ax.scatter(grp["Longitude"], grp["Latitude"], s=sizes, color=color,
               label=f"Group {label}", alpha=0.8, edgecolor="white", linewidth=0.6)
    for _, r in grp.iterrows():
        ax.annotate(r["Short Name"], (r["Longitude"], r["Latitude"]),
                    fontsize=7, xytext=(4, 4), textcoords="offset points")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_title("High-capacity substations (top quartile)\ngrouped by KMeans (bubble size = capacity)")
ax.legend(fontsize=8, loc="lower left")
ax.set_aspect("equal", adjustable="datalim")
plt.tight_layout()
plt.savefig(OUT_DIR / "chart_highcapacity_clusters.png", bbox_inches="tight")
plt.close()
print("Saved chart_highcapacity_clusters.png")
