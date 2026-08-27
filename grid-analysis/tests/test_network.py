import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.network import (
    build_graph, compute_centrality, get_connected_components, largest_component_subgraph,
    detect_communities, find_bridges, network_summary, n1_contingency,
)


def _star_graph_frames():
    # one hub connected to four other nodes
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


def _two_component_frames():
    # two separate triangles, not connected
    substations = pd.DataFrame([
        {"Substation ID": sid, "Name": f"Sub {sid}", "Region": "Test Region",
         "Country": "Ghana", "Voltage (kV)": 33, "Capacity (MVA)": 50.0, "Status": "Active"}
        for sid in range(1, 7)
    ])
    edges = [(1, 2), (2, 3), (1, 3), (4, 5), (5, 6), (4, 6)]
    lines = pd.DataFrame([
        {"Line ID": lid, "Source Substation ID": a, "Destination Substation ID": b,
         "Length (km)": 10.0, "Voltage (kV)": 33, "Capacity (MVA)": 80.0,
         "Status": "Active", "Line Type": "Overhead"}
        for lid, (a, b) in enumerate(edges, start=1)
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

    # the hub should score highest
    assert df["degree_centrality"].idxmax() == 1


def test_connected_components_on_two_separate_triangles():
    substations, lines = _two_component_frames()
    G = build_graph(substations, lines)
    components = get_connected_components(G)

    assert len(components) == 2
    assert sorted(len(c) for c in components) == [3, 3]


def test_largest_component_subgraph():
    substations, lines = _two_component_frames()
    G = build_graph(substations, lines)
    sub = largest_component_subgraph(G)

    assert sub.number_of_nodes() == 3
    assert set(sub.nodes) in ({1, 2, 3}, {4, 5, 6})


def test_find_bridges_on_star_graph():
    # every edge here is a bridge
    substations, lines = _star_graph_frames()
    G = build_graph(substations, lines)
    bridges = find_bridges(G)

    assert len(bridges) == 4


def test_find_bridges_on_triangle_has_none():
    # a triangle has no bridges
    substations, lines = _two_component_frames()
    G = build_graph(substations, lines)
    bridges = find_bridges(G)

    assert len(bridges) == 0


def test_detect_communities_covers_every_node():
    substations, lines = _two_component_frames()
    G = build_graph(substations, lines)
    communities = detect_communities(G)

    all_nodes = set().union(*communities)
    assert all_nodes == set(G.nodes)


def test_network_summary_on_star_graph():
    substations, lines = _star_graph_frames()
    G = build_graph(substations, lines)
    summary = network_summary(G)

    assert summary["nodes"] == 5
    assert summary["edges"] == 4
    assert summary["connected_components"] == 1
    assert summary["largest_component_size"] == 5
    assert summary["diameter_of_largest_component"] == 2
    assert summary["average_shortest_path_length_of_largest_component"] == pytest.approx(1.6)
    assert summary["global_efficiency"] == pytest.approx(0.7)
    assert summary["num_bridges"] == 4


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
