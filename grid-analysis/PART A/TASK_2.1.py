import pandas as pd
utilities = pd.read_csv('utilities.csv')
substations = pd.read_csv('substations.csv')
lines = pd.read_csv('lines.csv')
import networkx as nx

import scipy as sp
import matplotlib.pyplot as plt
from networkx.algorithms.community import greedy_modularity_communities



# Create an undirected graph

G = nx.Graph()


# Add substations as nodes
for index, row in substations.iterrows():
    G.add_node(
        row['Name'],
        region=row['Region'],
        voltage=row['Voltage (kV)'],
        latitude=row['Latitude'],
        longitude=row['Longitude'],
        capacity=row['Capacity (MVA)']
    )




for index, row in lines.iterrows():
    G.add_edge(
        row['Source Substation'],
        row['Destination Substation'],
        length=row['Length (km)'],
        voltage=row['Voltage (kV)']
    )


print("Network Statistics")
print("-----------------------------")
print("Number of Nodes:", G.number_of_nodes())
print("Number of Edges:", G.number_of_edges())

# ----------------------------------------
# Centrality Measures
# ----------------------------------------
degree = nx.degree_centrality(G)
betweenness = nx.betweenness_centrality(G)
closeness = nx.closeness_centrality(G)
pagerank = nx.pagerank(G)

# ----------------------------------------
# Top 10 Degree Centrality
# ----------------------------------------
print("\nTop 10 Substations by Degree Centrality")

top_degree = sorted(
    degree.items(),
    key=lambda x: x[1],
    reverse=True
)[:10]

for node, value in top_degree:
    print(node, round(value, 4))

# ----------------------------------------
# Top 10 Betweenness
# ----------------------------------------
print("\nTop 10 Betweenness Centrality")

top_between = sorted(
    betweenness.items(),
    key=lambda x: x[1],
    reverse=True
)[:10]

for node, value in top_between:
    print(node, round(value, 4))

# ----------------------------------------
# Top 10 Closeness
# ----------------------------------------
print("\nTop 10 Closeness Centrality")

top_close = sorted(
    closeness.items(),
    key=lambda x: x[1],
    reverse=True
)[:10]

for node, value in top_close:
    print(node, round(value, 4))

# ----------------------------------------
# Top 10 PageRank
# ----------------------------------------
print("\nTop 10 PageRank")

top_page = sorted(
    pagerank.items(),
    key=lambda x: x[1],
    reverse=True
)[:10]

for node, value in top_page:
    print(node, round(value, 4))

# ----------------------------------------
# Network Diameter and Average Path Length
# ----------------------------------------
if nx.is_connected(G):
    print("\nNetwork Diameter:", nx.diameter(G))
    print("Average Path Length:", nx.average_shortest_path_length(G))
else:
    print("\nNetwork is not fully connected.")
    largest = max(nx.connected_components(G), key=len)
    G2 = G.subgraph(largest)

    print("Largest Component Diameter:", nx.diameter(G2))
    print("Largest Component Average Path Length:",
          nx.average_shortest_path_length(G2))

# ----------------------------------------
# Clustering Coefficient
# ----------------------------------------
print("\nAverage Clustering Coefficient")
print(nx.average_clustering(G))

# ----------------------------------------
# Community Detection
# ----------------------------------------
communities = greedy_modularity_communities(G)

print("\nNumber of Communities:", len(communities))

for i, community in enumerate(communities, start=1):
    print(f"Community {i}: {len(community)} substations")


# Bridge Lines

bridges = list(nx.bridges(G))

print("\nBridge Lines")

for bridge in bridges:
    print(bridge)

# Connected Components

components = list(nx.connected_components(G))

print("\nConnected Components:", len(components))

# Network Efficiency

print("\nGlobal Network Efficiency")
print(nx.global_efficiency(G))

# N-1 Contingency Analysis

top_hub = top_degree[0][0]

G_removed = G.copy()
G_removed.remove_node(top_hub)

print("\nN-1 Contingency Analysis")
print("-------------------------")
print("Removed Substation:", top_hub)

print("Components Before Removal:",nx.number_connected_components(G))

print("Components After Removal:",nx.number_connected_components(G_removed))

# Network Visualization

plt.figure(figsize=(14,10))

pos = nx.spring_layout(G, seed=42)

nx.draw_networkx_nodes(G,pos,node_size=300,node_color="lightblue")

nx.draw_networkx_edges(G,pos)

nx.draw_networkx_labels(G,pos,font_size=7)

plt.title("National Grid Network")
plt.axis("off")
plt.show()


