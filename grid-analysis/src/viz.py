# extra charts, chord diagram, heatmaps, animated map
import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MplPath


def inter_region_flow_matrix(merged):
    return pd.crosstab(merged["Source Region"], merged["Destination Region"])


def build_chord_diagram(merged, ax=None):
    # draws curved lines between regions that connect a lot
    flow = inter_region_flow_matrix(merged)
    regions = sorted(set(flow.index) | set(flow.columns))
    n = len(regions)
    angle_of = {r: 2 * math.pi * i / n for i, r in enumerate(regions)}
    pos = {r: (math.cos(a), math.sin(a)) for r, a in angle_of.items()}

    if ax is None:
        _, ax = plt.subplots(figsize=(9, 9))

    for r in regions:
        x, y = pos[r]
        ax.plot(x, y, "o", color="#1f77b4", markersize=8)
        ax.text(x * 1.12, y * 1.12, r, ha="center", va="center", fontsize=8)

    max_count = flow.values.max() if flow.size else 1
    seen = set()
    for src in flow.index:
        for dst in flow.columns:
            count = flow.loc[src, dst]
            if count == 0 or src == dst:
                continue
            pair = tuple(sorted((src, dst)))
            if pair in seen:
                continue
            seen.add(pair)
            x0, y0 = pos[src]
            x1, y1 = pos[dst]
            path = MplPath([(x0, y0), (0, 0), (x1, y1)], [MplPath.MOVETO, MplPath.CURVE3, MplPath.CURVE3])
            width = 0.5 + 4 * (count / max_count)
            ax.add_patch(PathPatch(path, facecolor="none", edgecolor="#d62728", alpha=0.5, linewidth=width))

    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-1.4, 1.4)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Inter-Regional Line Flow (chord diagram)")
    return ax.figure


def build_line_density_heatmap(merged, ax=None):
    table = pd.crosstab(merged["Source Region"], merged["Voltage (kV)"])
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(table.values, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(table.columns)))
    ax.set_xticklabels(table.columns)
    ax.set_yticks(range(len(table.index)))
    ax.set_yticklabels(table.index)
    ax.set_xlabel("Voltage (kV)")
    ax.set_title("Line Density: Region x Voltage Tier")
    ax.figure.colorbar(im, ax=ax, label="Line count")
    return ax.figure


def build_maintenance_heatmap(merged, ax=None):
    table = (
        merged.groupby(["Source Region", "Utility Alias"])["Status"]
        .apply(lambda s: (s == "Under Maintenance").mean())
        .unstack(fill_value=0)
    )
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(table.values, cmap="Reds", aspect="auto", vmin=0, vmax=max(table.values.max(), 0.01))
    ax.set_xticks(range(len(table.columns)))
    ax.set_xticklabels(table.columns)
    ax.set_yticks(range(len(table.index)))
    ax.set_yticklabels(table.index)
    ax.set_title("Under-Maintenance Rate: Region x Utility")
    ax.figure.colorbar(im, ax=ax, label="Under-maintenance rate")
    return ax.figure


def build_animated_commissioning_map(substations):
    # map that plays through decades showing grid growth
    df = substations.copy()
    df["decade"] = (df["Commissioning Year"] // 10 * 10).astype(int)
    frames = []
    for decade in sorted(df["decade"].unique()):
        cumulative = df[df["decade"] <= decade].copy()
        cumulative["frame"] = str(decade) + "s"
        frames.append(cumulative)
    animated_df = pd.concat(frames, ignore_index=True)

    fig = px.scatter_geo(
        animated_df, lat="Latitude", lon="Longitude", hover_name="Name",
        color="Voltage (kV)", animation_frame="frame",
        title="Grid Growth by Commissioning Decade (cumulative)",
        projection="natural earth",
    )
    return fig


def build_utility_comparison_chart(merged, ax=None):
    summary = merged.groupby("Utility Alias").agg(
        line_count=("Line ID", "count"),
        total_capacity_mva=("Capacity (MVA)", "sum"),
    ).sort_values("line_count", ascending=False)

    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(summary))
    width = 0.35
    ax2 = ax.twinx()
    ax.bar(x - width / 2, summary["line_count"], width, label="Line count", color="#1f77b4")
    ax2.bar(x + width / 2, summary["total_capacity_mva"], width, label="Total capacity (MVA)", color="#ff7f0e")
    ax.set_xticks(x)
    ax.set_xticklabels(summary.index, rotation=45, ha="right")
    ax.set_ylabel("Line count")
    ax2.set_ylabel("Total capacity (MVA)")
    ax.set_title("Utility Comparison: Line Count vs Total Capacity")
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
    return ax.figure
