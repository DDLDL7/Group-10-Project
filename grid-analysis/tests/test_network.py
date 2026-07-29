import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.network import build_graph, compute_centrality, get_connected_components, n1_contingency


def _star_graph_frames():
    """Hub (id 1) connected to four spokes (ids 2-5) — removing the hub
    should fragment the network from 1 component into 4 isolated ones."""
    substations = pd.DataFrame([
        {"Substation ID": sid, "Name": f"Sub {sid}", "Region": "Test Region",
         "Country": "Ghana", "Voltage (kV)": 33, "Capacity (MVA)": 50.0, "Status": "Active"}
        for sid in range(1, 6)
    ])
    lines = pd.DataFrame([
        {"Line ID": lid, "Source Substation ID": 1, "Destination Substation ID": spoke,
         "Length (km)": 10.0, "Voltage (kV)": 33, "Capacity (MVA)": 80.0,
         "Status": "Active", "Line Type": "Overhead"}
        for lid, spoke in enumerate(range(2, 6), start=1)
    ])
    return substations, lines


def test_build_graph_node_and_edge_counts_match_input():
    substations, lines = _star_graph_frames()
    G = build_graph(substations, lines)

    assert G.number_of_nodes() == len(substations)
    assert G.number_of_edges() == len(lines)
    assert G.nodes[1]["region"] == "Test Region"
    assert G.edges[1, 2]["voltage"] == 33


def test_build_graph_skips_lines_with_unknown_substations():
    substations, lines = _star_graph_frames()
    bad_line = pd.DataFrame([{
        "Line ID": 99, "Source Substation ID": 1, "Destination Substation ID": 999,
        "Length (km)": 1.0, "Voltage (kV)": 33, "Capacity (MVA)": 10.0,
        "Status": "Active", "Line Type": "Overhead",
    }])
    lines_with_bad = pd.concat([lines, bad_line], ignore_index=True)
    G = build_graph(substations, lines_with_bad)

    assert G.number_of_edges() == len(lines)  # the bad line is silently dropped, not crashed on
    assert 999 not in G.nodes


def test_centrality_values_fall_in_unit_interval():
    substations, lines = _star_graph_frames()
    G = build_graph(substations, lines)
    df = compute_centrality(G)

    for col in ["degree_centrality", "betweenness_centrality", "closeness_centrality",
                "pagerank", "clustering_coefficient"]:
        assert (df[col] >= 0).all() and (df[col] <= 1).all()

    # the hub (node 1) should have the highest degree centrality
    assert df["degree_centrality"].idxmax() == 1


def test_n1_contingency_detects_fragmentation_on_star_graph():
    substations, lines = _star_graph_frames()
    G = build_graph(substations, lines)

    assert len(get_connected_components(G)) == 1

    result = n1_contingency(G, node_id=1)

    assert result["components_before"] == 1
    assert result["components_after"] == 4
    assert result["network_fragmented"] is True
    assert sorted(result["component_sizes_after"]) == [1, 1, 1, 1]


def test_n1_contingency_raises_for_unknown_node():
    substations, lines = _star_graph_frames()
    G = build_graph(substations, lines)

    with pytest.raises(ValueError):
        n1_contingency(G, node_id=12345)
