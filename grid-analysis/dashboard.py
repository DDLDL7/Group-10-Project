"""Streamlit dashboard for the National Electricity Grid Network Analysis.

Run with: streamlit run dashboard.py  (from inside grid-analysis/)

All computation is delegated to src/ so the dashboard, the notebooks, and the
tests share one implementation.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

from src.cleaning import load_raw, clean_and_validate, merge_all
from src.network import build_graph, compute_centrality, get_connected_components, n1_contingency
from src.geo import build_folium_map
from src.bi import utility_footprint, capacity_flags, underserved_regions, asset_age_profile

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
    "not verified measurements of the real Ghanaian grid."
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

# --------------------------------------------------------------------------
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

# --------------------------------------------------------------------------
with network_tab:
    st.subheader("Centrality measures")
    st.dataframe(centrality.loc[filtered_substations["Substation ID"]], width="stretch")

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

# --------------------------------------------------------------------------
with geography_tab:
    st.subheader("Substation and line map")
    grid_map = build_folium_map(filtered_substations, lines)
    st.iframe(grid_map._repr_html_(), height=600)

# --------------------------------------------------------------------------
with reliability_tab:
    st.subheader("Utility footprint by region")
    st.dataframe(utility_footprint(filtered_merged), width="stretch")

    st.subheader("Capacity flags (proxy — no real load data available)")
    st.dataframe(capacity_flags(filtered_substations), width="stretch")

    st.subheader("Underserved regions (proxy)")
    st.dataframe(underserved_regions(substations), width="stretch")

    st.subheader("Asset age profile")
    st.dataframe(asset_age_profile(substations), width="stretch")

# --------------------------------------------------------------------------
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
