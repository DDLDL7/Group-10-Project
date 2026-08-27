# the interactive dashboard, run with: streamlit run dashboard.py
from pathlib import Path

import streamlit as st

from src.cleaning import load_raw, clean_and_validate, merge_all, utility_region_line_counts
from src.network import (
    build_graph, compute_centrality, get_connected_components, network_summary,
    detect_communities, find_bridges, n1_contingency,
)
from src.geo import build_folium_map, regional_connectivity, geographic_gaps, categorize_line_distances
from src.bi import (
    utility_infrastructure_footprint, capacity_utilization_flags,
    line_maintenance_proportion, asset_age_profile, capacity_concentration,
    growth_opportunities, reliability_proxy,
)

DATA_DIR = Path(__file__).resolve().parent / "data"

st.set_page_config(page_title="Grid Network Analysis", layout="wide")


@st.cache_data
def get_data():
    utilities, substations, lines = load_raw(DATA_DIR)
    utilities, substations, lines, report = clean_and_validate(utilities, substations, lines)
    merged = merge_all(utilities, substations, lines)
    return utilities, substations, lines, merged, report


@st.cache_resource
def get_graph(substations, lines):
    return build_graph(substations, lines)


utilities, substations, lines, merged, cleaning_report = get_data()
G = get_graph(substations, lines)
centrality = compute_centrality(G)

st.title("National Electricity Grid Network Analysis")
st.caption(
    "Synthetic, seeded dataset grounded in Ghana's grid (ECG, NEDCo, GRIDCo, VRA) and WAPP "
    "cross-border interconnections. Coordinates, capacities, and connections are illustrative — "
    "not verified measurements of the real Ghanaian grid. Every business-intelligence and "
    "reliability metric below is an explicit proxy."
)

with st.sidebar:
    st.header("Filters")
    regions = sorted(substations["Region"].unique())
    voltages = sorted(substations["Voltage (kV)"].unique())
    utility_names = sorted(utilities["Alias"].unique())

    selected_regions = st.multiselect("Region", regions, default=regions)
    selected_voltages = st.multiselect("Voltage (kV)", voltages, default=voltages)
    selected_utilities = st.multiselect("Utility", utility_names, default=utility_names)

filtered_substations = substations[
    substations["Region"].isin(selected_regions) & substations["Voltage (kV)"].isin(selected_voltages)
]
filtered_merged = merged[
    merged["Source Region"].isin(selected_regions) & merged["Utility Alias"].isin(selected_utilities)
]

overview_tab, network_tab, geography_tab, reliability_tab, search_tab = st.tabs(
    ["Overview", "Network", "Geography", "Reliability", "Search"]
)

with overview_tab:
    st.subheader("Executive summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Utilities", len(utilities))
    c2.metric("Substations", len(substations))
    c3.metric("Lines", len(lines))
    c4.metric("Total capacity (MVA)", f"{substations['Capacity (MVA)'].sum():,.0f}")

    c5, c6, c7 = st.columns(3)
    c5.metric("Active substations", int((substations["Status"] == "Active").sum()))
    c6.metric("Lines under maintenance", int((lines["Status"] == "Under Maintenance").sum()))
    c7.metric("Connected components", len(get_connected_components(G)))

    st.subheader("Substations by region")
    st.bar_chart(substations["Region"].value_counts())

    with st.expander("Data cleaning report"):
        st.json(cleaning_report)

with network_tab:
    st.subheader("Centrality measures")
    st.dataframe(centrality.loc[filtered_substations["Substation ID"]], width="stretch")

    st.subheader("Network structure summary")
    st.json(network_summary(G))

    with st.expander("Communities"):
        for i, community in enumerate(detect_communities(G)):
            names = [G.nodes[n]["name"] for n in community]
            st.write(f"Community {i} ({len(names)} substations): {', '.join(names)}")

    with st.expander("Bridge lines (single points of connection)"):
        bridges = find_bridges(G)
        st.write([f"{G.nodes[a]['name']} <-> {G.nodes[b]['name']}" for a, b in bridges])

    st.subheader("N-1 contingency check")
    sub_options = filtered_substations.set_index("Substation ID")["Name"].to_dict()
    default_id = centrality["degree_centrality"].idxmax()
    chosen_id = st.selectbox(
        "Substation to remove", options=list(sub_options.keys()),
        format_func=lambda sid: sub_options.get(sid, str(sid)),
        index=list(sub_options.keys()).index(default_id) if default_id in sub_options else 0,
    )
    if st.button("Run N-1 test"):
        result = n1_contingency(G, chosen_id)
        st.json(result)
        if result["network_fragmented"]:
            st.warning(
                f"Removing {result['removed_node_name']} fragments the network from "
                f"{result['components_before']} to {result['components_after']} components."
            )
        else:
            st.success(
                f"Removing {result['removed_node_name']} does not fragment the network — "
                "the remaining substations stay connected through alternate paths."
            )

with geography_tab:
    st.subheader("Substation and line map")
    grid_map = build_folium_map(filtered_substations, lines, utilities=utilities)
    st.iframe(grid_map._repr_html_(), height=600)

    st.subheader("Regional connectivity")
    connectivity = regional_connectivity(substations, lines)
    c1, c2 = st.columns(2)
    c1.metric("Intra-regional lines", connectivity["intra_regional_lines"])
    c2.metric("Cross-regional lines", connectivity["cross_regional_lines"])
    st.dataframe(connectivity["density_by_region"], width="stretch")

    st.subheader("Geographic gaps (proxy)")
    st.dataframe(geographic_gaps(substations), width="stretch")

    st.subheader("Distance categories")
    _, distance_counts, distance_by_voltage = categorize_line_distances(lines)
    st.bar_chart(distance_counts)

with reliability_tab:
    st.subheader("Utility footprint")
    footprint_region, footprint_voltage = utility_infrastructure_footprint(filtered_merged)
    st.dataframe(footprint_region, width="stretch")
    st.dataframe(footprint_voltage, width="stretch")

    st.subheader("Capacity utilization flags (proxy)")
    sub_flags, line_flags = capacity_utilization_flags(filtered_substations, lines)
    st.dataframe(sub_flags[sub_flags["capacity_flag"] != "Typical"], width="stretch")

    st.subheader("Lines under maintenance (proxy reliability signal)")
    maint_region, maint_utility = line_maintenance_proportion(merged)
    c1, c2 = st.columns(2)
    c1.dataframe(maint_region, width="stretch")
    c2.dataframe(maint_utility, width="stretch")

    st.subheader("Asset age profile")
    st.dataframe(asset_age_profile(substations), width="stretch")

    st.subheader("Capacity concentration")
    st.json(capacity_concentration(substations))

    st.subheader("Growth opportunities (proxy)")
    st.dataframe(growth_opportunities(substations), width="stretch")

    st.subheader("Reliability risk proxy (age + maintenance + centrality)")
    st.dataframe(reliability_proxy(substations, merged, centrality=centrality).head(10), width="stretch")

with search_tab:
    st.subheader("Substation lookup")
    query = st.text_input("Search by substation name or ID")
    if query:
        matches = substations[
            substations["Name"].str.contains(query, case=False, na=False)
            | substations["Substation ID"].astype(str).str.contains(query)
        ]
        st.dataframe(matches, width="stretch")

    st.subheader("Compare two utilities")
    col_a, col_b = st.columns(2)
    utility_a = col_a.selectbox("Utility A", utility_names, index=0)
    utility_b = col_b.selectbox(
        "Utility B", utility_names, index=min(1, len(utility_names) - 1),
    )
    comparison = (
        merged[merged["Utility Alias"].isin([utility_a, utility_b])]
        .groupby("Utility Alias")
        .agg(lines=("Line ID", "count"), total_capacity_mva=("Capacity (MVA)", "sum"))
    )
    st.dataframe(comparison, width="stretch")

    st.subheader("Utility/region breakdown")
    st.dataframe(utility_region_line_counts(merged), width="stretch")
