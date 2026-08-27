# builds the grid as a graph and analyzes it
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
    # substations become nodes, lines become edges
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
    # figures out which substations matter most, a few different ways
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
    return sorted(nx.connected_components(G), key=len, reverse=True)


def largest_component_subgraph(G):
    # some stats only make sense on one connected piece
    largest = get_connected_components(G)[0]
    return G.subgraph(largest).copy()


def detect_communities(G):
    # groups substations that connect a lot to each other
    return [set(c) for c in nx.algorithms.community.greedy_modularity_communities(G)]


def find_bridges(G):
    # lines that would split the network if they went down
    return list(nx.bridges(G))


def network_summary(G):
    components = get_connected_components(G)
    largest = largest_component_subgraph(G)

    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "connected_components": len(components),
        "component_sizes": [len(c) for c in components],
        "largest_component_size": len(largest),
        "diameter_of_largest_component": nx.diameter(largest) if len(largest) > 1 else 0,
        "average_shortest_path_length_of_largest_component":
            nx.average_shortest_path_length(largest) if len(largest) > 1 else 0.0,
        "global_efficiency": nx.global_efficiency(G),
        "average_clustering_coefficient": nx.average_clustering(G),
        "num_communities": len(detect_communities(G)),
        "num_bridges": len(find_bridges(G)),
    }


def n1_contingency(G, node_id):
    # what happens to the network if this one substation goes down
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
