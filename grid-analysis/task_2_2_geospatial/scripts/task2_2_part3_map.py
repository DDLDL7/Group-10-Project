"""
Task 2.2 - Geographic and Geospatial Analysis
Part 3: Interactive multi-layer Folium map
  Layers:
   1. National substations (colored by voltage level)
   2. Line-density heatmap
   3. Utility-specific network layers (ECG, NEDCo, GRIDCo, VRA, + cross-border utilities)
   4. Geographic (DBSCAN) clusters + high-capacity substation clusters
   5. Regional connectivity / cross-border interconnections
"""
from _paths import DATA_DIR, OUT_DIR
import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster

utilities = pd.read_csv(DATA_DIR / "utilities.csv")
substations = pd.read_csv(OUT_DIR / "substations_with_clusters.csv")  # has DBSCAN Cluster for Ghana subs
substations_all = pd.read_csv(DATA_DIR / "substations.csv")
lines = pd.read_csv(OUT_DIR / "lines_with_geodesic.csv")
high_cap = pd.read_csv(OUT_DIR / "high_capacity_clusters.csv")

util_lookup = utilities.set_index("Utility ID")["Alias"]
sub_by_id = substations_all.set_index("Substation ID")

voltage_colors = {
    11: "#2ecc71",    # green
    33: "#3498db",    # blue
    69: "#9b59b6",    # purple
    161: "#e67e22",   # orange
    330: "#e74c3c",   # red
}

def voltage_color(v):
    return voltage_colors.get(v, "#7f8c8d")

def voltage_radius(v):
    return 4 + (v / 330) * 8

# Centered roughly on Ghana
m = folium.Map(location=[7.9, -1.2], zoom_start=6.4, tiles="CartoDB positron")

# --------------------------------------------------------------
# Layer 1: National substations colored by voltage level
# --------------------------------------------------------------
fg_subs = folium.FeatureGroup(name="1. Substations by Voltage Level", show=True)
for _, r in substations_all.iterrows():
    popup = (f"<b>{r['Name']}</b><br>Region: {r['Region']} ({r['Country']})<br>"
             f"Voltage: {r['Voltage (kV)']} kV<br>Capacity: {r['Capacity (MVA)']} MVA<br>"
             f"Type: {r['Type']}<br>Status: {r['Status']}<br>Commissioned: {r['Commissioning Year']}")
    folium.CircleMarker(
        location=[r["Latitude"], r["Longitude"]],
        radius=voltage_radius(r["Voltage (kV)"]),
        color=voltage_color(r["Voltage (kV)"]),
        fill=True, fill_color=voltage_color(r["Voltage (kV)"]), fill_opacity=0.85,
        weight=1.5,
        popup=folium.Popup(popup, max_width=280),
        tooltip=r["Short Name"],
    ).add_to(fg_subs)
fg_subs.add_to(m)

# Voltage legend
legend_html = """
<div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999; background: white;
            padding: 10px 14px; border: 1px solid #999; border-radius: 6px; font-size: 12px;">
<b>Voltage Level (kV)</b><br>
""" + "".join(
    f'<span style="display:inline-block;width:10px;height:10px;background:{c};'
    f'border-radius:50%;margin-right:6px;"></span>{v} kV<br>'
    for v, c in voltage_colors.items()
) + "</div>"
m.get_root().html.add_child(folium.Element(legend_html))

# --------------------------------------------------------------
# Layer 2: Line-density heatmap (weighted by number of lines through midpoint)
# --------------------------------------------------------------
heat_points = []
for _, ln in lines.iterrows():
    s = sub_by_id.loc[ln["Source Substation ID"]]
    d = sub_by_id.loc[ln["Destination Substation ID"]]
    mid_lat = (s["Latitude"] + d["Latitude"]) / 2
    mid_lon = (s["Longitude"] + d["Longitude"]) / 2
    heat_points.append([mid_lat, mid_lon, ln["Capacity (MVA)"] / 100])
    # also add several interpolated points along the line so the heatmap shows corridors
    for f in (0.25, 0.5, 0.75):
        lat = s["Latitude"] + (d["Latitude"] - s["Latitude"]) * f
        lon = s["Longitude"] + (d["Longitude"] - s["Longitude"]) * f
        heat_points.append([lat, lon, ln["Capacity (MVA)"] / 200])

fg_heat = folium.FeatureGroup(name="2. Line-Density Heatmap", show=False)
HeatMap(heat_points, radius=18, blur=22, max_zoom=8).add_to(fg_heat)
fg_heat.add_to(m)

# --------------------------------------------------------------
# Layer 3: Utility-specific network maps (one sub-layer per utility)
# --------------------------------------------------------------
utility_colors = {
    "ECG": "#1f77b4", "NEDCo": "#ff7f0e", "GRIDCo": "#2ca02c", "VRA": "#d62728",
    "CIE": "#9467bd", "CEB": "#8c564b", "SBEE": "#e377c2", "EDG": "#7f7f7f",
    "SONABEL": "#bcbd22", "EPC": "#17becf",
}
for uid, alias in util_lookup.items():
    u_lines = lines[lines["Utility ID"] == uid]
    if u_lines.empty:
        continue
    fg_u = folium.FeatureGroup(name=f"3. Utility Network - {alias}", show=False)
    color = utility_colors.get(alias, "#333333")
    for _, ln in u_lines.iterrows():
        s = sub_by_id.loc[ln["Source Substation ID"]]
        d = sub_by_id.loc[ln["Destination Substation ID"]]
        folium.PolyLine(
            locations=[[s["Latitude"], s["Longitude"]], [d["Latitude"], d["Longitude"]]],
            color=color, weight=2 + ln["Voltage (kV)"] / 110, opacity=0.8,
            tooltip=(f"{alias}: {ln['Source Substation']} - {ln['Destination Substation']} "
                     f"({ln['Length (km)']} km, {ln['Voltage (kV)']} kV, {ln['Status']})"),
        ).add_to(fg_u)
    fg_u.add_to(m)

# --------------------------------------------------------------
# Layer 4: Geographic clusters (DBSCAN) + high-capacity KMeans clusters
# --------------------------------------------------------------
fg_clusters = folium.FeatureGroup(name="4. Geographic Clusters (DBSCAN)", show=False)
cluster_palette = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]
for _, r in substations.iterrows():
    label = r["DBSCAN Cluster"]
    color = "#bdbdbd" if label == -1 else cluster_palette[int(label) % len(cluster_palette)]
    folium.CircleMarker(
        location=[r["Latitude"], r["Longitude"]],
        radius=7, color=color, fill=True, fill_color=color, fill_opacity=0.9, weight=1,
        tooltip=f"{r['Short Name']} - Cluster {label if label != -1 else 'isolated'}",
    ).add_to(fg_clusters)
fg_clusters.add_to(m)

fg_highcap = folium.FeatureGroup(name="4b. High-Capacity Substation Clusters", show=False)
for _, r in high_cap.iterrows():
    color = cluster_palette[int(r["KMeans Cluster"]) % len(cluster_palette)]
    folium.Marker(
        location=[r["Latitude"], r["Longitude"]],
        icon=folium.Icon(color="darkred", icon="bolt", prefix="fa"),
        popup=f"<b>{r['Short Name']}</b><br>{r['Capacity (MVA)']} MVA, {r['Voltage (kV)']} kV<br>"
              f"KMeans group {r['KMeans Cluster']}",
        tooltip=r["Short Name"],
    ).add_to(fg_highcap)
fg_highcap.add_to(m)

# --------------------------------------------------------------
# Layer 5: Cross-border / WAPP interconnections
# --------------------------------------------------------------
fg_border = folium.FeatureGroup(name="5. Cross-Border WAPP Interconnections", show=True)
border_ids = set(substations_all[substations_all["Country"] != "Ghana"]["Substation ID"])
for _, r in substations_all[substations_all["Country"] != "Ghana"].iterrows():
    folium.Marker(
        location=[r["Latitude"], r["Longitude"]],
        icon=folium.Icon(color="black", icon="flag", prefix="fa"),
        popup=f"<b>{r['Name']}</b><br>{r['Country']}<br>{r['Voltage (kV)']} kV",
        tooltip=r["Short Name"],
    ).add_to(fg_border)

for _, ln in lines.iterrows():
    if ln["Source Substation ID"] in border_ids or ln["Destination Substation ID"] in border_ids:
        s = sub_by_id.loc[ln["Source Substation ID"]]
        d = sub_by_id.loc[ln["Destination Substation ID"]]
        folium.PolyLine(
            locations=[[s["Latitude"], s["Longitude"]], [d["Latitude"], d["Longitude"]]],
            color="black", weight=3, opacity=0.75, dash_array="6,6",
            tooltip=f"Cross-border: {ln['Source Substation']} - {ln['Destination Substation']} "
                    f"({ln['Length (km)']} km)",
        ).add_to(fg_border)
fg_border.add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

title_html = """
<div style="position: fixed; top: 12px; left: 60px; z-index: 9999; background: white;
            padding: 8px 16px; border: 1px solid #999; border-radius: 6px;">
<b>Ghana National Electricity Grid — Interactive Geospatial Map</b><br>
<span style="font-size:11px;color:#555;">Synthetic/illustrative dataset — Task 2.2</span>
</div>
"""
m.get_root().html.add_child(folium.Element(title_html))

m.save(str(OUT_DIR / "ghana_grid_interactive_map.html"))
print("Saved ghana_grid_interactive_map.html")
