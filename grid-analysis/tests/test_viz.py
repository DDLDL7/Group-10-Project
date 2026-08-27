import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless backend for tests

import matplotlib.figure
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.viz import (
    inter_region_flow_matrix, build_chord_diagram, build_line_density_heatmap,
    build_maintenance_heatmap, build_animated_commissioning_map, build_utility_comparison_chart,
)


def _merged_frame():
    return pd.DataFrame([
        {"Line ID": 1, "Source Region": "North", "Destination Region": "South",
         "Voltage (kV)": 33, "Status": "Active", "Utility Alias": "U1", "Capacity (MVA)": 50.0},
        {"Line ID": 2, "Source Region": "North", "Destination Region": "South",
         "Voltage (kV)": 33, "Status": "Under Maintenance", "Utility Alias": "U1", "Capacity (MVA)": 40.0},
        {"Line ID": 3, "Source Region": "South", "Destination Region": "South",
         "Voltage (kV)": 161, "Status": "Active", "Utility Alias": "U2", "Capacity (MVA)": 300.0},
    ])


def _substations_frame():
    return pd.DataFrame([
        {"Substation ID": 1, "Name": "A", "Latitude": 5.0, "Longitude": 0.0,
         "Voltage (kV)": 33, "Commissioning Year": 1980},
        {"Substation ID": 2, "Name": "B", "Latitude": 6.0, "Longitude": 1.0,
         "Voltage (kV)": 161, "Commissioning Year": 2015},
    ])


def test_inter_region_flow_matrix_counts_pairs():
    matrix = inter_region_flow_matrix(_merged_frame())
    assert matrix.loc["North", "South"] == 2
    assert matrix.loc["South", "South"] == 1


def test_build_chord_diagram_returns_figure():
    fig = build_chord_diagram(_merged_frame())
    assert isinstance(fig, matplotlib.figure.Figure)


def test_build_line_density_heatmap_returns_figure_with_expected_shape():
    fig = build_line_density_heatmap(_merged_frame())
    ax = fig.axes[0]
    assert isinstance(fig, matplotlib.figure.Figure)
    # one row per region, one column per voltage
    assert len(ax.get_yticklabels()) == 2
    assert len(ax.get_xticklabels()) == 2


def test_build_maintenance_heatmap_returns_figure():
    fig = build_maintenance_heatmap(_merged_frame())
    assert isinstance(fig, matplotlib.figure.Figure)


def test_build_animated_commissioning_map_has_one_frame_per_decade():
    fig = build_animated_commissioning_map(_substations_frame())
    assert isinstance(fig, go.Figure)
    # two different decades here
    assert len(fig.frames) == 2


def test_build_utility_comparison_chart_returns_figure():
    fig = build_utility_comparison_chart(_merged_frame())
    assert isinstance(fig, matplotlib.figure.Figure)
