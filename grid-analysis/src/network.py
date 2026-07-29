"""NetworkX graph construction, centrality measures, and N-1 contingency analysis.

The grid is modelled as an undirected graph: AC power can flow either way
along a line depending on system conditions, unlike a scheduled flight with
a fixed origin/destination.
"""
import networkx as nx
import pandas as pd

NODE_ATTR_COLS = {
    "Name": "name",
    "Region": "region",
    "Country": "country",
    "Voltage (kV)": "voltage",
    "Capacity (MVA)": "capacity",
    "Status": "status",
}

EDGE_ATTR_COLS = {
    "Length (km)": "length_km",
    "Voltage (kV)": "voltage",
    "Capacity (MVA)": "capacity",
    "Status": "status",
    "Line Type": "line_type",
}


def build_graph(substations, lines):
    """Build an undirected graph: nodes = substations (keyed by Substation ID), edges = lines."""
    G = nx.Graph()

    for _, row in substations.iterrows():
        attrs = {attr: row[col] for col, attr in NODE_ATTR_COLS.items()}
        G.add_node(row["Substation ID"], **attrs)

    for _, row in lines.iterrows():
        src, dst = row["Source Substation ID"], row["Destination Substation ID"]
        if src not in G.nodes or dst not in G.nodes:
            continue
        attrs = {attr: row[col] for col, attr in EDGE_ATTR_COLS.items()}
        G.add_edge(src, dst, line_id=row["Line ID"], **attrs)

    return G


def compute_centrality(G):
    """Return a DataFrame of per-substation network metrics, indexed by Substation ID."""
    degree = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G)
    closeness = nx.closeness_centrality(G)
    pagerank = nx.pagerank(G)
    clustering = nx.clustering(G)

    df = pd.DataFrame({
        "name": {n: G.nodes[n].get("name") for n in G.nodes},
        "region": {n: G.nodes[n].get("region") for n in G.nodes},
        "degree_centrality": degree,
        "betweenness_centrality": betweenness,
        "closeness_centrality": closeness,
        "pagerank": pagerank,
        "clustering_coefficient": clustering,
    })
    df.index.name = "substation_id"
    return df.sort_values("degree_centrality", ascending=False)


def get_connected_components(G):
    """Return connected components as a list of node-id sets, largest first."""
    return sorted(nx.connected_components(G), key=len, reverse=True)


def n1_contingency(G, node_id):
    """Remove node_id from a copy of G and compare connectivity before/after.

    Returns a dict with component counts and component sizes before/after,
    framed as a structural resilience proxy, not a real power-flow study.
    """
    if node_id not in G.nodes:
        raise ValueError(f"Node {node_id!r} not found in graph")

    before_components = get_connected_components(G)

    G_minus = G.copy()
    G_minus.remove_node(node_id)
    after_components = get_connected_components(G_minus)

    return {
        "removed_node": node_id,
        "removed_node_name": G.nodes[node_id].get("name"),
        "components_before": len(before_components),
        "components_after": len(after_components),
        "component_sizes_before": [len(c) for c in before_components],
        "component_sizes_after": [len(c) for c in after_components],
        "network_fragmented": len(after_components) > len(before_components),
    }
