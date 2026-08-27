import sys
from pathlib import Path

import folium
import pandas as pd
import plotly.graph_objects as go
import pytest
from geopy.distance import geodesic

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.geo import (
    build_folium_map, verify_line_distances, categorize_line_distances,
    find_geographic_clusters, regional_connectivity, geographic_gaps,
    build_plotly_substation_map,
)


def _four_substation_frames():
    # a and b are close together, c and d are close together, but far apart from each other
    substations = pd.DataFrame([
        {"Substation ID": 1, "Name": "A", "Region": "North", "Country": "Ghana",
         "Latitude": 5.000, "Longitude": 0.000, "Voltage (kV)": 33, "Capacity (MVA)": 50.0,
         "Status": "Active"},
        {"Substation ID": 2, "Name": "B", "Region": "North", "Country": "Ghana",
         "Latitude": 5.001, "Longitude": 0.001, "Voltage (kV)": 33, "Capacity (MVA)": 50.0,
         "Status": "Active"},
        {"Substation ID": 3, "Name": "C", "Region": "South", "Country": "Ghana",
         "Latitude": 10.000, "Longitude": 0.000, "Voltage (kV)": 33, "Capacity (MVA)": 50.0,
         "Status": "Active"},
        {"Substation ID": 4, "Name": "D", "Region": "South", "Country": "Ghana",
         "Latitude": 10.001, "Longitude": 0.001, "Voltage (kV)": 33, "Capacity (MVA)": 50.0,
         "Status": "Active"},
    ])
    lines = pd.DataFrame([
        {"Line ID": 1, "Utility ID": 1, "Source Substation ID": 1, "Source Substation": "A",
         "Destination Substation ID": 2, "Destination Substation": "B",
         "Voltage (kV)": 33, "Length (km)": 0.2, "Capacity (MVA)": 80.0,
         "Status": "Active", "Line Type": "Overhead"},
        {"Line ID": 2, "Utility ID": 1, "Source Substation ID": 3, "Source Substation": "C",
         "Destination Substation ID": 4, "Destination Substation": "D",
         "Voltage (kV)": 33, "Length (km)": 0.2, "Capacity (MVA)": 80.0,
         "Status": "Active", "Line Type": "Overhead"},
        {"Line ID": 3, "Utility ID": 2, "Source Substation ID": 1, "Source Substation": "A",
         "Destination Substation ID": 3, "Destination Substation": "C",
         "Voltage (kV)": 161, "Length (km)": 556.0, "Capacity (MVA)": 200.0,
         "Status": "Active", "Line Type": "Overhead"},
    ])
    utilities = pd.DataFrame([
        {"Utility ID": 1, "Name": "Utility One", "Alias": "U1", "Code": "U1",
         "Type": "Distribution", "Country": "Ghana", "Active": "Y"},
        {"Utility ID": 2, "Name": "Utility Two", "Alias": "U2", "Code": "U2",
         "Type": "Transmission", "Country": "Ghana", "Active": "Y"},
    ])
    return utilities, substations, lines


def test_verify_line_distances_reports_expected_difference():
    utilities, substations, lines = _four_substation_frames()
    a = substations.set_index("Substation ID").loc[1]
    c = substations.set_index("Substation ID").loc[3]
    true_distance = geodesic((a["Latitude"], a["Longitude"]), (c["Latitude"], c["Longitude"])).km

    # line 3's length was set wrong on purpose to test this
    result = verify_line_distances(substations, lines)
    row = result.loc[result["Line ID"] == 3].iloc[0]

    assert row["Geodesic Distance (km)"] == pytest.approx(true_distance, abs=0.1)
    assert row["Difference (km)"] == pytest.approx(556.0 - true_distance, abs=0.1)


def test_categorize_line_distances_buckets_correctly():
    lines = pd.DataFrame([
        {"Line ID": 1, "Length (km)": 5.0, "Voltage (kV)": 33},
        {"Line ID": 2, "Length (km)": 50.0, "Voltage (kV)": 161},
        {"Line ID": 3, "Length (km)": 150.0, "Voltage (kV)": 330},
    ])
    categorized, counts, by_voltage = categorize_line_distances(lines)

    assert categorized.loc[categorized["Line ID"] == 1, "distance_category"].iloc[0] == "Short"
    assert categorized.loc[categorized["Line ID"] == 2, "distance_category"].iloc[0] == "Medium"
    assert categorized.loc[categorized["Line ID"] == 3, "distance_category"].iloc[0] == "Long"
    assert counts["Short"] == 1 and counts["Medium"] == 1 and counts["Long"] == 1


def test_find_geographic_clusters_groups_nearby_substations():
    utilities, substations, lines = _four_substation_frames()
    result, clusters = find_geographic_clusters(substations, radius_km=15)

    assert len(clusters) == 2
    assert sorted(len(c) for c in clusters) == [2, 2]
    # a and b should be one cluster, c and d another
    a_cluster = result.loc[result["Substation ID"] == 1, "geo_cluster"].iloc[0]
    b_cluster = result.loc[result["Substation ID"] == 2, "geo_cluster"].iloc[0]
    c_cluster = result.loc[result["Substation ID"] == 3, "geo_cluster"].iloc[0]
    assert a_cluster == b_cluster
    assert a_cluster != c_cluster


def test_regional_connectivity_counts_cross_region_lines():
    utilities, substations, lines = _four_substation_frames()
    summary = regional_connectivity(substations, lines)

    # lines 1 and 2 stay in one region, line 3 crosses over
    assert summary["intra_regional_lines"] == 2
    assert summary["cross_regional_lines"] == 1
    assert set(summary["density_by_region"]["Region"]) == {"North", "South"}


def test_geographic_gaps_flags_below_median_regions():
    substations = pd.DataFrame([
        {"Substation ID": i, "Region": region}
        for i, region in enumerate(
            ["A"] * 1 + ["B"] * 3 + ["C"] * 5, start=1
        )
    ])
    gaps = geographic_gaps(substations)

    assert gaps.set_index("Region").loc["A", "below_median_density"] == True
    assert gaps.set_index("Region").loc["B", "below_median_density"] == False
    assert gaps.set_index("Region").loc["C", "below_median_density"] == False


def test_build_folium_map_returns_map_with_utility_layers():
    utilities, substations, lines = _four_substation_frames()
    m = build_folium_map(substations, lines, utilities=utilities)

    assert isinstance(m, folium.Map)
    html = m._repr_html_()
    assert "leaflet" in html.lower()


def test_build_plotly_substation_map_plots_every_substation_colored_by_region():
    utilities, substations, lines = _four_substation_frames()
    fig = build_plotly_substation_map(substations, color_by="Region")

    assert isinstance(fig, go.Figure)
    # one line per region
    assert len(fig.data) == substations["Region"].nunique()
    total_points_plotted = sum(len(trace.lat) for trace in fig.data)
    assert total_points_plotted == len(substations)
