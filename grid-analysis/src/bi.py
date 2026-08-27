# business type stats, all just estimates not real measurements
import pandas as pd


def utility_infrastructure_footprint(merged):
    # which utility runs the most stuff, by region and voltage
    by_region = (
        merged.groupby(["Utility Alias", "Source Region"])
        .size().reset_index(name="Line Count")
        .sort_values("Line Count", ascending=False)
    )
    by_voltage = pd.crosstab(merged["Utility Alias"], merged["Voltage (kV)"])
    return by_region, by_voltage


def capacity_utilization_flags(substations, lines, low_pct=0.25, high_pct=0.75):
    # flags stuff that seems low or high capacity for its voltage tier
    def _flag(df, capacity_col, voltage_col, id_cols):
        out = df.copy()
        low = out.groupby(voltage_col)[capacity_col].transform(lambda s: s.quantile(low_pct))
        high = out.groupby(voltage_col)[capacity_col].transform(lambda s: s.quantile(high_pct))
        out["capacity_flag"] = "Typical"
        out.loc[out[capacity_col] <= low, "capacity_flag"] = "Low capacity (upgrade candidate)"
        out.loc[out[capacity_col] >= high, "capacity_flag"] = "High capacity"
        return out[id_cols + [capacity_col, voltage_col, "capacity_flag"]]

    substation_flags = _flag(
        substations, "Capacity (MVA)", "Voltage (kV)", ["Substation ID", "Name", "Region"],
    )
    line_flags = _flag(
        lines, "Capacity (MVA)", "Voltage (kV)", ["Line ID", "Source Substation", "Destination Substation"],
    )
    return substation_flags, line_flags


def line_maintenance_proportion(merged):
    by_region = (
        merged.groupby("Source Region")["Status"]
        .apply(lambda s: (s == "Under Maintenance").mean())
        .reset_index(name="under_maintenance_rate")
        .sort_values("under_maintenance_rate", ascending=False)
    )
    by_utility = (
        merged.groupby("Utility Alias")["Status"]
        .apply(lambda s: (s == "Under Maintenance").mean())
        .reset_index(name="under_maintenance_rate")
        .sort_values("under_maintenance_rate", ascending=False)
    )
    return by_region, by_utility


def asset_age_profile(substations):
    # groups substations by the decade they were built
    df = substations.copy()
    df["decade"] = (df["Commissioning Year"] // 10 * 10).astype(int).astype(str) + "s"
    profile = df.groupby("decade").agg(
        substation_count=("Substation ID", "count"),
        avg_capacity_mva=("Capacity (MVA)", "mean"),
        active_rate=("Status", lambda s: (s == "Active").mean()),
    ).reset_index().sort_values("decade")
    return profile


def capacity_concentration(substations, top_fraction=0.1):
    # how much capacity sits in just the top substations
    sorted_capacity = substations["Capacity (MVA)"].sort_values(ascending=False)
    n_top = max(1, int(len(sorted_capacity) * top_fraction))
    top_share = sorted_capacity.head(n_top).sum() / sorted_capacity.sum()
    return {
        "top_fraction": top_fraction,
        "num_substations_in_top_fraction": n_top,
        "share_of_total_capacity": round(float(top_share), 4),
    }


def growth_opportunities(substations):
    # regions that seem underbuilt compared to others
    by_region = substations.groupby("Region").agg(
        substation_count=("Substation ID", "count"),
        total_capacity_mva=("Capacity (MVA)", "sum"),
    ).reset_index()
    count_median = by_region["substation_count"].median()
    capacity_median = by_region["total_capacity_mva"].median()
    by_region["growth_opportunity"] = (
        (by_region["substation_count"] <= count_median)
        & (by_region["total_capacity_mva"] <= capacity_median)
    )
    return by_region.sort_values(["growth_opportunity", "substation_count"], ascending=[False, True])


def reliability_proxy(substations, merged, centrality=None):
    # rough risk score, mixes age, maintenance, and network importance
    lines_under_maint = (
        merged[merged["Status"] == "Under Maintenance"]
        .groupby("Source Substation ID").size()
    )

    df = substations.copy()
    df["lines_under_maintenance"] = df["Substation ID"].map(lines_under_maint).fillna(0).astype(int)
    df["age_years"] = 2026 - df["Commissioning Year"]

    if centrality is not None:
        df = df.merge(
            centrality[["degree_centrality", "betweenness_centrality"]],
            left_on="Substation ID", right_index=True, how="left",
        )
        df[["degree_centrality", "betweenness_centrality"]] = df[
            ["degree_centrality", "betweenness_centrality"]
        ].fillna(0)
    else:
        df["degree_centrality"] = 0.0
        df["betweenness_centrality"] = 0.0

    age_norm = (df["age_years"] - df["age_years"].min()) / max(
        1, (df["age_years"].max() - df["age_years"].min())
    )
    df["reliability_risk_score"] = (
        0.3 * age_norm
        + 0.3 * (df["lines_under_maintenance"] > 0).astype(float)
        + 0.4 * df["betweenness_centrality"]
    ).round(4)

    cols = ["Substation ID", "Name", "Region", "age_years", "Status",
            "lines_under_maintenance", "betweenness_centrality", "reliability_risk_score"]
    return df[cols].sort_values("reliability_risk_score", ascending=False)
