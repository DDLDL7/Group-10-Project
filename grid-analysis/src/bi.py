"""Business-intelligence and reliability proxies.

The synthetic dataset has no real load, population, or power-flow data, so
every function here is an explicit *proxy* metric — a structural stand-in
for a real operational measure, not a verified engineering finding. Each
function documents what it approximates and why.
"""
import pandas as pd


def utility_footprint(merged):
    """Line count per utility per source region — a proxy for infrastructure footprint."""
    return (
        merged.groupby(["Utility Alias", "Source Region"])
        .size()
        .reset_index(name="Line Count")
        .sort_values("Line Count", ascending=False)
    )


def capacity_flags(substations, low_pct=0.25, high_pct=0.75):
    """Flag substations whose capacity is unusually low/high for their voltage tier.

    Proxy for "upgrade candidate" (low) vs "over-provisioned" (high) — real
    utilization would require actual load data, which this dataset lacks.
    """
    df = substations.copy()
    tier_low = df.groupby("Voltage (kV)")["Capacity (MVA)"].transform(lambda s: s.quantile(low_pct))
    tier_high = df.groupby("Voltage (kV)")["Capacity (MVA)"].transform(lambda s: s.quantile(high_pct))

    df["capacity_flag"] = "Typical"
    df.loc[df["Capacity (MVA)"] <= tier_low, "capacity_flag"] = "Low capacity (upgrade candidate)"
    df.loc[df["Capacity (MVA)"] >= tier_high, "capacity_flag"] = "High capacity"
    return df[["Substation ID", "Name", "Region", "Voltage (kV)", "Capacity (MVA)", "capacity_flag"]]


def underserved_regions(substations):
    """Regions with substation count or total capacity below the cross-region median.

    Proxy for "growth opportunity" — with no population/demand data, low
    infrastructure density is the only signal available.
    """
    by_region = substations.groupby("Region").agg(
        substation_count=("Substation ID", "count"),
        total_capacity_mva=("Capacity (MVA)", "sum"),
    ).reset_index()

    count_median = by_region["substation_count"].median()
    capacity_median = by_region["total_capacity_mva"].median()

    by_region["underserved_proxy"] = (
        (by_region["substation_count"] < count_median)
        & (by_region["total_capacity_mva"] < capacity_median)
    )
    return by_region.sort_values("substation_count")


def asset_age_profile(substations):
    """Bucket Commissioning Year into decades, cross-tabbed with region and status."""
    df = substations.copy()
    df["decade"] = (df["Commissioning Year"] // 10 * 10).astype(int).astype(str) + "s"
    return pd.crosstab(df["decade"], [df["Region"], df["Status"]])
