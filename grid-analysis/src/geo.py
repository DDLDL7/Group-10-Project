"""Geographic visualization: a standalone Folium map of the substation network."""
import folium

VOLTAGE_COLORS = {
    11: "#2ca02c",
    33: "#1f77b4",
    69: "#ff7f0e",
    161: "#9467bd",
    330: "#d62728",
}
DEFAULT_COLOR = "#7f7f7f"


def _color_for_voltage(voltage):
    return VOLTAGE_COLORS.get(voltage, DEFAULT_COLOR)


def build_folium_map(substations, lines, center=(7.9, -1.0), zoom_start=6):
    """Build a Folium map: substations as markers colored by voltage tier,
    lines as polylines between them."""
    m = folium.Map(location=list(center), zoom_start=zoom_start, tiles="cartodbpositron")

    sub_lookup = substations.set_index("Substation ID")

    for voltage, color in VOLTAGE_COLORS.items():
        fg = folium.FeatureGroup(name=f"{voltage} kV substations")
        for _, row in substations[substations["Voltage (kV)"] == voltage].iterrows():
            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=5,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.85,
                popup=folium.Popup(
                    f"<b>{row['Name']}</b><br>Region: {row['Region']}<br>"
                    f"Voltage: {row['Voltage (kV)']} kV<br>Capacity: {row['Capacity (MVA)']} MVA<br>"
                    f"Status: {row['Status']}",
                    max_width=250,
                ),
            ).add_to(fg)
        fg.add_to(m)

    lines_fg = folium.FeatureGroup(name="Transmission/distribution lines")
    for _, row in lines.iterrows():
        try:
            src = sub_lookup.loc[row["Source Substation ID"]]
            dst = sub_lookup.loc[row["Destination Substation ID"]]
        except KeyError:
            continue
        folium.PolyLine(
            locations=[[src["Latitude"], src["Longitude"]], [dst["Latitude"], dst["Longitude"]]],
            color=_color_for_voltage(row["Voltage (kV)"]),
            weight=2,
            opacity=0.6,
            tooltip=f"{row['Source Substation']} ↔ {row['Destination Substation']} "
                    f"({row['Voltage (kV)']} kV, {row['Length (km)']} km, {row['Status']})",
        ).add_to(lines_fg)
    lines_fg.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m
