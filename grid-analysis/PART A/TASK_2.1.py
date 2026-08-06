import pandas as pd
utilities = pd.read_csv('utilities.csv')
substations = pd.read_csv('substations.csv')
lines = pd.read_csv('lines.csv')
"""import networkx as nx

import scipy as sp
import matplotlib.pyplot as plt
from networkx.algorithms.community import greedy_modularity_communities


# ----------------------------------------
# Create an undirected graph
# ----------------------------------------
G = nx.Graph()

# ----------------------------------------
# Add substations as nodes
# ----------------------------------------
for _, row in substations.iterrows():
    G.add_node(
        row['Name'],
        region=row['Region'],
        voltage=row['Voltage (kV)'],
        latitude=row['Latitude'],
        longitude=row['Longitude'],
        capacity=row['Capacity (MVA)']
    )

# ----------------------------------------
# Add transmission lines as edges
# ----------------------------------------
for _, row in lines.iterrows():
    G.add_edge(
        row['Source Substation'],
        row['Destination Substation'],
        length=row['Length (km)'],
        voltage=row['Voltage (kV)']
    )

# ----------------------------------------
# Basic Network Statistics
# ----------------------------------------
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

# ----------------------------------------
# Bridge Lines
# ----------------------------------------
bridges = list(nx.bridges(G))

print("\nBridge Lines")

for bridge in bridges:
    print(bridge)

# ----------------------------------------
# Connected Components
# ----------------------------------------
components = list(nx.connected_components(G))

print("\nConnected Components:", len(components))

# ----------------------------------------
# Network Efficiency
# ----------------------------------------
print("\nGlobal Network Efficiency")
print(nx.global_efficiency(G))

# ----------------------------------------
# N-1 Contingency Analysis
# ----------------------------------------
top_hub = top_degree[0][0]

G_removed = G.copy()
G_removed.remove_node(top_hub)

print("\nN-1 Contingency Analysis")
print("-------------------------")
print("Removed Substation:", top_hub)

print("Components Before Removal:",
      nx.number_connected_components(G))

print("Components After Removal:",
      nx.number_connected_components(G_removed))

# ----------------------------------------
# Network Visualization
# ----------------------------------------
plt.figure(figsize=(14,10))

pos = nx.spring_layout(G, seed=42)

nx.draw_networkx_nodes(
    G,
    pos,
    node_size=300,
    node_color="lightblue"
)

nx.draw_networkx_edges(
    G,
    pos
)

nx.draw_networkx_labels(
    G,
    pos,
    font_size=7
)

plt.title("National Grid Network")
plt.axis("off")
plt.show()


"""
# ______________________________________________________________________________
import networkx as nx
import matplotlib.pyplot as plt


# Create an empty graph
G = nx.Graph()

# Go through every row in the substations dataset
for index, row in substations.iterrows():

    # Store each value in a separate variable
    substation_name = row["Name"]
    region = row["Region"]
    voltage = row["Voltage (kV)"]
    latitude = row["Latitude"]
    longitude = row["Longitude"]
    capacity = row["Capacity (MVA)"]

    # Add the substation as a node
    G.add_node(
        substation_name,
        region=region,
        voltage=voltage,
        latitude=latitude,
        longitude=longitude,
        capacity=capacity
    )

    # Go through every transmission line
for index, row in lines.iterrows():

    # Store the values
    source = row["Source Substation"]
    destination = row["Destination Substation"]
    length = row["Length (km)"]
    voltage = row["Voltage (kV)"]

    # Connect the two substations
    G.add_edge(
        source,
        destination,
        length=length,
        voltage=voltage
    )

    # Count the number of substations
number_of_nodes = G.number_of_nodes()

# Count the number of transmission lines
number_of_edges = G.number_of_edges()

# Display the results
print("Number of Substations:", number_of_nodes)
print("Number of Transmission Lines:", number_of_edges)


# _____________________________________________________________________
"""
# ==========================================
# TASK 2.1 - NETWORK ANALYSIS
# PART 1
# Create the Network Graph
# ==========================================

# Import the libraries
import networkx as nx
import matplotlib.pyplot as plt

# ==========================================
# Create an empty graph
# ==========================================

print("Creating the Network Graph...")

# Create an empty graph
G = nx.Graph()

# ==========================================
# Add every substation as a node
# ==========================================

print("\nAdding substations...")

# Go through every row in the substations table
for index, row in substations.iterrows():

    # Read the information from the current row
    substation_name = row["Name"]
    region = row["Region"]
    voltage = row["Voltage (kV)"]
    latitude = row["Latitude"]
    longitude = row["Longitude"]
    capacity = row["Capacity (MVA)"]

    # Add the node to the graph
    G.add_node(
        substation_name,
        region=region,
        voltage=voltage,
        latitude=latitude,
        longitude=longitude,
        capacity=capacity
    )

print("Finished adding substations.")

# ==========================================
# Add every transmission line as an edge
# ==========================================

print("\nAdding transmission lines...")

# Go through every row in the lines table
for index, row in lines.iterrows():

    # Read the information
    source_substation = row["Source Substation"]
    destination_substation = row["Destination Substation"]
    line_length = row["Length (km)"]
    line_voltage = row["Voltage (kV)"]

    # Add the transmission line
    G.add_edge(
        source_substation,
        destination_substation,
        length=line_length,
        voltage=line_voltage
    )

print("Finished adding transmission lines.")

# ==========================================
# Basic Network Statistics
# ==========================================

print("\n===================================")
print(" BASIC NETWORK STATISTICS")
print("===================================")

number_of_substations = G.number_of_nodes()
number_of_lines = G.number_of_edges()

print("Number of Substations :", number_of_substations)
print("Number of Transmission Lines :", number_of_lines)

# Count connected components
connected_components = nx.number_connected_components(G)

print("Connected Components :", connected_components)

# ==========================================
# Display all substations
# ==========================================

print("\n===================================")
print("LIST OF SUBSTATIONS")
print("===================================")

for node in G.nodes():
    print(node)

# ==========================================
# Display all transmission lines
# ==========================================

print("\n===================================")
print("LIST OF TRANSMISSION LINES")
print("===================================")

for edge in G.edges():
    print(edge)

# ==========================================
# Draw the Network
# ==========================================

print("\nDrawing the network...")

plt.figure(figsize=(14,10))

# Arrange the nodes automatically
position = nx.spring_layout(G, seed=42)

# Draw nodes
nx.draw_networkx_nodes(
    G,
    position,
    node_size=400,
    node_color="skyblue"
)

# Draw edges
nx.draw_networkx_edges(
    G,
    position,
    width=1
)

# Draw node labels
nx.draw_networkx_labels(
    G,
    position,
    font_size=7
)

plt.title("National Electricity Grid Network")
plt.axis("off")

plt.show()

print("\nPart 1 Complete.")
"""