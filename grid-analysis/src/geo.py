"""Geographic and geospatial analysis (Week 2 / Part A Task 2.2).

Builds the interactive Folium map, verifies line distances with an
independent geodesic calculation, categorizes lines by length, finds
proximity-based geographic clusters of substations, and summarizes regional
/ cross-border connectivity density.
"""
import folium
import networkx as nx
import pandas as pd
from geopy.distance import geodesic

VOLTAGE_COLORS = {
    11: "#2ca02c",
    33: "#1f77b4",
    69: "#ff7f0e",
    161: "#9467bd",
    330: "#d62728",
}
DEFAULT_COLOR = "#7f7f7f"

UTILITY_PALETTE = [
    "#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4",
    "#46f0f0", "#f032e6", "#bcf60c", "#fabebe", "#008080",
]


def _color_for_voltage(voltage):
    return VOLTAGE_COLORS.get(voltage, DEFAULT_COLOR)


def build_folium_map(substations, lines, utilities=None, center=(7.9, -1.0), zoom_start=6):
    """Build a Folium map with a voltage-tier layer for every substation/line,
    plus (if `utilities` is given) one additional layer per utility showing
    that utility's own line network - 'Utility Territory' from Task 2.2.
    """
    m = folium.Map(location=list(center), zoom_start=zoom_start, tiles="cartodbpositron")
    sub_lookup = substations.set_index("Substation ID")

    for voltage, color in VOLTAGE_COLORS.items():
        fg = folium.FeatureGroup(name=f"{voltage} kV substations")
        for _, row in substations[substations["Voltage (kV)"] == voltage].iterrows():
            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=5, color=color, fill=True, fill_color=color, fill_opacity=0.85,
                popup=folium.Popup(
                    f"<b>{row['Name']}</b><br>Region: {row['Region']}<br>"
                    f"Voltage: {row['Voltage (kV)']} kV<br>Capacity: {row['Capacity (MVA)']} MVA<br>"
                    f"Status: {row['Status']}",
                    max_width=250,
                ),
            ).add_to(fg)
        fg.add_to(m)

    lines_fg = folium.FeatureGroup(name="Transmission/distribution lines", show=True)
    for _, row in lines.iterrows():
        try:
            src = sub_lookup.loc[row["Source Substation ID"]]
            dst = sub_lookup.loc[row["Destination Substation ID"]]
        except KeyError:
            continue
        folium.PolyLine(
            locations=[[src["Latitude"], src["Longitude"]], [dst["Latitude"], dst["Longitude"]]],
            color=_color_for_voltage(row["Voltage (kV)"]), weight=2, opacity=0.6,
            tooltip=f"{row['Source Substation']} <-> {row['Destination Substation']} "
                    f"({row['Voltage (kV)']} kV, {row['Length (km)']} km, {row['Status']})",
        ).add_to(lines_fg)
    lines_fg.add_to(m)

    if utilities is not None:
        utility_ids = sorted(lines["Utility ID"].unique())
        utility_names = utilities.set_index("Utility ID")["Alias"]
        for i, utility_id in enumerate(utility_ids):
            color = UTILITY_PALETTE[i % len(UTILITY_PALETTE)]
            name = utility_names.get(utility_id, f"Utility {utility_id}")
            fg = folium.FeatureGroup(name=f"Territory: {name}", show=False)
            for _, row in lines[lines["Utility ID"] == utility_id].iterrows():
                try:
                    src = sub_lookup.loc[row["Source Substation ID"]]
                    dst = sub_lookup.loc[row["Destination Substation ID"]]
                except KeyError:
                    continue
                folium.PolyLine(
                    locations=[[src["Latitude"], src["Longitude"]], [dst["Latitude"], dst["Longitude"]]],
                    color=color, weight=3, opacity=0.8,
                    tooltip=f"{name}: {row['Source Substation']} <-> {row['Destination Substation']}",
                ).add_to(fg)
            fg.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


def verify_line_distances(substations, lines):
    """Independently recompute each line's length using geopy's geodesic
    formula (more accurate than the haversine approximation used by the
    generator) and compare it to the recorded `Length (km)`.
    """
    sub_lookup = substations.set_index("Substation ID")
    recomputed = []
    for _, row in lines.iterrows():
        try:
            src = sub_lookup.loc[row["Source Substation ID"]]
            dst = sub_lookup.loc[row["Destination Substation ID"]]
        except KeyError:
            recomputed.append(None)
            continue
        dist = geodesic((src["Latitude"], src["Longitude"]), (dst["Latitude"], dst["Longitude"])).km
        recomputed.append(round(dist, 1))

    result = lines[["Line ID", "Source Substation", "Destination Substation", "Length (km)"]].copy()
    result["Geodesic Distance (km)"] = recomputed
    result["Difference (km)"] = result["Length (km)"] - result["Geodesic Distance (km)"]
    result["Difference (%)"] = (result["Difference (km)"] / result["Geodesic Distance (km)"] * 100).round(1)
    return result


def categorize_line_distances(lines, short_max_km=20, long_min_km=100):
    """Bucket lines into Short / Medium / Long transmission runs (Task 2.2's
    'Distance Analysis'), and cross-tabulate against voltage tier.
    """
    df = lines.copy()

    def bucket(km):
        if km <= short_max_km:
            return "Short"
        if km >= long_min_km:
            return "Long"
        return "Medium"

    df["distance_category"] = df["Length (km)"].apply(bucket)
    counts = df["distance_category"].value_counts()
    by_voltage = pd.crosstab(df["distance_category"], df["Voltage (kV)"])
    return df, counts, by_voltage


def find_geographic_clusters(substations, radius_km=15):
    """Group substations into geographic clusters using proximity: any two
    substations within `radius_km` of each other are linked, and connected
    components of that proximity graph become clusters ('Substation
    Clustering' from Task 2.2). Returns substations with an added
    'geo_cluster' column.
    """
    G = nx.Graph()
    G.add_nodes_from(substations["Substation ID"])

    coords = substations.set_index("Substation ID")[["Latitude", "Longitude"]]
    ids = list(coords.index)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            dist = geodesic(tuple(coords.loc[a]), tuple(coords.loc[b])).km
            if dist <= radius_km:
                G.add_edge(a, b)

    clusters = sorted(nx.connected_components(G), key=len, reverse=True)
    cluster_of = {}
    for cluster_id, cluster in enumerate(clusters):
        for sid in cluster:
            cluster_of[sid] = cluster_id

    result = substations.copy()
    result["geo_cluster"] = result["Substation ID"].map(cluster_of)
    return result, clusters


def regional_connectivity(substations, lines):
    """Substation density per region, plus intra-regional vs cross-region /
    cross-border line counts - Task 2.2's 'Regional Connectivity' analysis.
    """
    density = substations.groupby("Region").agg(
        substation_count=("Substation ID", "count"),
        total_capacity_mva=("Capacity (MVA)", "sum"),
    ).reset_index().sort_values("substation_count", ascending=False)

    sub_region = substations.set_index("Substation ID")["Region"]
    src_region = lines["Source Substation ID"].map(sub_region)
    dst_region = lines["Destination Substation ID"].map(sub_region)
    is_cross_region = (src_region != dst_region)

    return {
        "density_by_region": density,
        "intra_regional_lines": int((~is_cross_region).sum()),
        "cross_regional_lines": int(is_cross_region.sum()),
    }


def geographic_gaps(substations):
    """Regions with below-median substation density (Task 2.2's 'Geographic
    Gaps'). This is an explicit PROXY: without real population or land-area
    data, substation count relative to other regions is the only available
    signal for "possibly underserved".
    """
    by_region = substations.groupby("Region").agg(
        substation_count=("Substation ID", "count"),
    ).reset_index()
    median_count = by_region["substation_count"].median()
    by_region["below_median_density"] = by_region["substation_count"] < median_count
    return by_region.sort_values("substation_count")
