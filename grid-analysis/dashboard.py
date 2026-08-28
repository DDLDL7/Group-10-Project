"""GridPulse: the National Electricity Grid Network Analysis dashboard.

Run with:
    streamlit run dashboard.py

Tabs: Overview, Network, Geography, Reliability, Search - per the project
brief's required dashboard structure. Every number on this page comes from
the synthetic, seeded dataset in data/ - see the "About this data" note in
the sidebar before treating anything here as a real operational finding.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import business_intelligence as bi
from src import cleaning, geo, network

DATA_DIR = Path(__file__).resolve().parent / "data"

st.set_page_config(page_title="GridPulse — National Grid Analysis", layout="wide")


# ---------------------------------------------------------------------
# Cached data / graph loading
# ---------------------------------------------------------------------

@st.cache_data
def load_data():
    utilities, substations, lines = cleaning.load_raw(DATA_DIR)
    utilities, substations, lines, report = cleaning.clean_and_validate(utilities, substations, lines)
    merged = cleaning.merge_all(utilities, substations, lines)
    lines_enriched = bi.enrich_lines(lines, substations, utilities)
    return utilities, substations, lines, merged, lines_enriched, report


@st.cache_resource
def build_graph(_substations, _lines):
    return network.build_graph(_substations, _lines)


utilities, substations, lines, merged, lines_enriched, clean_report = load_data()
G = build_graph(substations, lines)

st.sidebar.title("GridPulse")
st.sidebar.caption(
    "National Electricity Grid Network Analysis — CS 112 course project. "
    f"{len(substations)} substations · {len(lines)} lines · {len(utilities)} utilities."
)
with st.sidebar.expander("About this data", expanded=False):
    st.write(
        "This dashboard runs entirely on a **synthetic, seeded** dataset "
        "(`random.seed(42)`) grounded in real Ghanaian/WAPP geography and "
        "utility names, but with illustrative coordinates, capacities, and "
        "connections. Treat every figure as a structural proxy for "
        "teaching network analysis, not a verified measurement of Ghana's "
        "actual electricity grid."
    )

tab_overview, tab_network, tab_geography, tab_reliability, tab_search = st.tabs(
    ["Overview", "Network", "Geography", "Reliability", "Search"]
)


# ---------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------

with tab_overview:
    st.header("Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Substations", len(substations))
    col2.metric("Lines", len(lines))
    col3.metric("Utilities", len(utilities))
    col4.metric("Regions/countries", substations["Region"].nunique())

    active_pct = (substations["Status"] == "Active").mean() * 100
    maintenance_pct = (lines["Status"] == "Under Maintenance").mean() * 100
    col1, col2 = st.columns(2)
    col1.metric("Active substations", f"{active_pct:.1f}%")
    col2.metric("Lines under maintenance", f"{maintenance_pct:.1f}%")

    left, right = st.columns(2)
    with left:
        st.subheader("Substations by region")
        st.bar_chart(substations["Region"].value_counts())
    with right:
        st.subheader("Voltage-level distribution")
        st.bar_chart(substations["Voltage (kV)"].value_counts().sort_index())

    left, right = st.columns(2)
    with left:
        st.subheader("Top substations by number of connections")
        degree = pd.concat([lines["Source Substation"], lines["Destination Substation"]]).value_counts().head(10)
        st.bar_chart(degree)
    with right:
        st.subheader("Lines operated per utility")
        code_by_id = utilities.set_index("Utility ID")["Code"]
        st.bar_chart(lines["Utility ID"].map(code_by_id).value_counts())

    with st.expander("Data-cleaning report"):
        st.write("Duplicates removed:", clean_report["duplicates_found"])
        st.write("Invalid coordinates found:", clean_report["invalid_coordinates"])
        st.write("Referential-integrity issues:", clean_report["referential_integrity"])


# ---------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------

with tab_network:
    st.header("Network analysis")

    summary = network.network_summary(G)
    cols = st.columns(4)
    cols[0].metric("Nodes", summary["nodes"])
    cols[1].metric("Edges", summary["edges"])
    cols[2].metric("Connected components", summary["connected_components"])
    cols[3].metric("Bridges", summary["num_bridges"])
    cols = st.columns(4)
    cols[0].metric("Diameter (largest component)", summary["diameter_of_largest_component"])
    cols[1].metric("Avg. shortest path", f"{summary['average_shortest_path_length_of_largest_component']:.2f}")
    cols[2].metric("Global efficiency", f"{summary['global_efficiency']:.3f}")
    cols[3].metric("Communities detected", summary["num_communities"])

    st.subheader("Critical substations (centrality ranking)")
    centrality = network.compute_centrality(G)
    st.dataframe(centrality.head(15), use_container_width=True)

    st.subheader("N-1 contingency analysis")
    st.caption(
        "Removes one substation and measures whether the network fragments into "
        "more separate pieces — a simplified educational proxy for the real "
        "contingency studies grid operators run before scheduling maintenance."
    )
    name_by_id = {n: G.nodes[n].get("name", n) for n in G.nodes}
    default_node = centrality.index[0]
    chosen_name = st.selectbox(
        "Substation to remove",
        options=list(name_by_id.keys()),
        format_func=lambda sid: name_by_id[sid],
        index=list(name_by_id.keys()).index(default_node),
    )
    result = network.n1_contingency(G, chosen_node := chosen_name)
    c1, c2, c3 = st.columns(3)
    c1.metric("Components before", result["components_before"])
    c2.metric("Components after", result["components_after"])
    c3.metric("Network fragmented?", "Yes" if result["network_fragmented"] else "No")

    with st.expander("Show network graph (largest component)"):
        largest = network.largest_component_subgraph(G)
        fig, ax = plt.subplots(figsize=(9, 7))
        pos = nx.spring_layout(largest, seed=42)
        nx.draw(largest, pos, ax=ax, node_size=60, node_color="#3b82f6", edge_color="#c9cdd6", with_labels=False)
        st.pyplot(fig)
        plt.close(fig)


# ---------------------------------------------------------------------
# Geography
# ---------------------------------------------------------------------

with tab_geography:
    st.header("Geography")

    color_by = st.radio("Colour substations by", ["Voltage (kV)", "Region", "Status"], horizontal=True)
    fig = geo.build_plotly_substation_map(substations, color_by=color_by)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Interactive national map (voltage tiers + utility territories)")
    with st.spinner("Building map..."):
        folium_map = geo.build_folium_map(substations, lines, utilities=utilities)
    st.components.v1.html(folium_map.get_root().render(), height=550, scrolling=False)

    left, right = st.columns(2)
    with left:
        st.subheader("Line length categories")
        _, counts, by_voltage = geo.categorize_line_distances(lines)
        st.bar_chart(counts)
    with right:
        st.subheader("Regional connectivity density")
        conn = geo.regional_connectivity(substations, lines)
        st.dataframe(conn["density_by_region"], use_container_width=True)
        st.caption(
            f"Intra-regional lines: {conn['intra_regional_lines']} · "
            f"Cross-region/border lines: {conn['cross_regional_lines']}"
        )

    st.subheader("Underserved-region proxy (below-median substation density)")
    st.dataframe(geo.geographic_gaps(substations), use_container_width=True)


# ---------------------------------------------------------------------
# Reliability
# ---------------------------------------------------------------------

with tab_reliability:
    st.header("Reliability & business intelligence")
    st.caption(
        "All figures below are structural proxies from rated capacity, connection "
        "counts, and maintenance status — not real load or outage-history data."
    )

    left, right = st.columns(2)
    with left:
        st.subheader("Utility footprint")
        footprint = bi.utility_footprint(lines_enriched)
        st.bar_chart(footprint["lines_operated"])
    with right:
        st.subheader("Capacity utilization flags")
        util_map = bi.capacity_utilization(substations, lines)
        st.bar_chart(util_map["utilization_flag"].value_counts())

    left, right = st.columns(2)
    with left:
        st.subheader("Growth-opportunity regions (Ghana, active substations)")
        st.dataframe(bi.growth_opportunities(substations), use_container_width=True)
    with right:
        st.subheader("Asset age bands")
        aged, age_by_region, age_band_profile = bi.asset_age_profile(substations)
        st.bar_chart(aged["age_band"].value_counts().reindex(["Modern", "Mature", "Legacy"]))

    st.subheader("Top 10 substations by composite reliability-risk proxy")
    risk = bi.reliability_risk(substations, lines, lines_enriched)
    st.dataframe(
        risk[["Name", "Region", "age", "degree", "pct_lines_under_maintenance", "risk_score"]].head(10),
        use_container_width=True,
    )

    st.subheader(f"Substations concentrating 50%+ of their region's capacity")
    st.dataframe(bi.concentration_risk(substations), use_container_width=True)


# ---------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------

with tab_search:
    st.header("Search")

    st.subheader("Substation finder")
    query = st.text_input("Search by name, region, or country")
    filtered = substations
    if query:
        mask = (
            substations["Name"].str.contains(query, case=False, na=False)
            | substations["Region"].str.contains(query, case=False, na=False)
            | substations["Country"].str.contains(query, case=False, na=False)
        )
        filtered = substations[mask]
    st.dataframe(filtered, use_container_width=True)

    st.subheader("Utility comparison")
    codes = utilities["Code"].tolist()
    chosen = st.multiselect("Compare utilities", codes, default=codes[:3])
    if chosen:
        code_to_id = utilities.set_index("Code")["Utility ID"]
        comparison = lines_enriched[lines_enriched["Code"].isin(chosen)].groupby("Code").agg(
            lines_operated=("Line ID", "count"),
            total_capacity_mva=("Capacity (MVA)", "sum"),
            avg_line_length_km=("Length (km)", "mean"),
        ).round(1)
        st.dataframe(comparison, use_container_width=True)
        st.bar_chart(comparison["lines_operated"])
    else:
        st.info("Select one or more utilities above to compare them.")
