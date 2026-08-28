"""Reusable business-intelligence / reliability functions (Task 2.3).

These are parameterized equivalents of the analysis in
`task_2_3_business_intelligence.py`, extracted into importable functions so
the same logic can back both that standalone report script and the
Streamlit dashboard's Reliability tab, instead of being duplicated.
All figures here are structural proxies computed from rated capacity,
connection counts, and maintenance status - not measurements of real load,
demand, or outage history.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_REFERENCE_YEAR = 2026


def enrich_lines(lines: pd.DataFrame, substations: pd.DataFrame, utilities: pd.DataFrame) -> pd.DataFrame:
    return (
        lines
        .merge(substations[["Substation ID", "Region"]],
               left_on="Source Substation ID", right_on="Substation ID", how="left")
        .rename(columns={"Region": "Source Region"})
        .drop(columns="Substation ID")
        .merge(utilities[["Utility ID", "Code"]], on="Utility ID", how="left")
    )


def utility_footprint(lines_enriched: pd.DataFrame) -> pd.DataFrame:
    return (
        lines_enriched.groupby("Code")
        .agg(lines_operated=("Line ID", "count"),
             total_line_capacity_mva=("Capacity (MVA)", "sum"))
        .sort_values("lines_operated", ascending=False)
    )


def _flag_utilization(ratio: float) -> str:
    if ratio >= 3:
        return "Potential upgrade candidate (under-provisioned)"
    if ratio <= 0.5:
        return "Possibly over-provisioned"
    return "Balanced"


def capacity_utilization(substations: pd.DataFrame, lines: pd.DataFrame) -> pd.DataFrame:
    active_subs = substations[substations["Status"] == "Active"].copy()
    line_capacity_at_sub = pd.concat([
        lines.groupby("Source Substation ID")["Capacity (MVA)"].sum(),
        lines.groupby("Destination Substation ID")["Capacity (MVA)"].sum(),
    ]).groupby(level=0).sum().rename("connected_line_capacity_mva")

    util_map = active_subs.merge(line_capacity_at_sub, left_on="Substation ID", right_index=True, how="left")
    util_map["connected_line_capacity_mva"] = util_map["connected_line_capacity_mva"].fillna(0)
    util_map["utilization_ratio"] = (
        util_map["connected_line_capacity_mva"] / util_map["Capacity (MVA)"]
    ).round(2)
    util_map["utilization_flag"] = util_map["utilization_ratio"].apply(_flag_utilization)
    return util_map


def concentration_risk(substations: pd.DataFrame, threshold_pct: float = 50.0) -> pd.DataFrame:
    active_subs = substations[substations["Status"] == "Active"].copy()
    region_totals = active_subs.groupby("Region")["Capacity (MVA)"].transform("sum")
    active_subs["regional_share_%"] = (active_subs["Capacity (MVA)"] / region_totals * 100).round(2)
    return active_subs[active_subs["regional_share_%"] >= threshold_pct]


def growth_opportunities(substations: pd.DataFrame, country: str = "Ghana") -> pd.DataFrame:
    active_subs = substations[substations["Status"] == "Active"]
    if country:
        active_subs = active_subs[active_subs["Country"] == country]
    region_summary = (
        active_subs.groupby("Region")
        .agg(substation_count=("Substation ID", "count"), total_capacity_mva=("Capacity (MVA)", "sum"))
        .sort_values("substation_count")
    )
    cutoff = region_summary["substation_count"].quantile(0.25)
    region_summary["growth_candidate"] = region_summary["substation_count"] <= cutoff
    return region_summary


def asset_age_profile(substations: pd.DataFrame, reference_year: int = DEFAULT_REFERENCE_YEAR):
    substations = substations.copy()
    substations["age"] = reference_year - substations["Commissioning Year"]
    bins = [0, 20, 40, np.inf]
    labels = ["Modern", "Mature", "Legacy"]
    substations["age_band"] = pd.cut(substations["age"], bins=bins, labels=labels)

    age_by_region = (
        substations.groupby("Region")["age"].agg(["mean", "median", "count"]).sort_values("mean", ascending=False)
    )
    age_band_profile = substations.groupby("age_band", observed=True).agg(
        count=("Substation ID", "count"),
        mean_capacity_mva=("Capacity (MVA)", "mean"),
        pct_active=("Status", lambda s: (s == "Active").mean() * 100),
    )
    return substations, age_by_region, age_band_profile


def _normalize(series: pd.Series) -> pd.Series:
    span = series.max() - series.min()
    return (series - series.min()) / span if span else series * 0


def reliability_risk(substations: pd.DataFrame, lines: pd.DataFrame, lines_enriched: pd.DataFrame,
                      reference_year: int = DEFAULT_REFERENCE_YEAR) -> pd.DataFrame:
    substations_aged, _, _ = asset_age_profile(substations, reference_year)

    maintenance_share_by_region = (
        lines_enriched.groupby("Source Region")["Status"]
        .apply(lambda s: (s == "Under Maintenance").mean() * 100)
        .rename("pct_lines_under_maintenance")
    )

    degree = pd.concat([
        lines["Source Substation ID"], lines["Destination Substation ID"]
    ]).value_counts().rename("degree")

    risk = substations_aged.merge(degree, left_on="Substation ID", right_index=True, how="left")
    risk["degree"] = risk["degree"].fillna(0)
    risk = risk.merge(maintenance_share_by_region, left_on="Region", right_index=True, how="left")
    risk["pct_lines_under_maintenance"] = risk["pct_lines_under_maintenance"].fillna(0)

    risk["risk_score"] = (
        0.4 * _normalize(risk["age"])
        + 0.4 * _normalize(1 / (risk["degree"] + 1))
        + 0.2 * _normalize(risk["pct_lines_under_maintenance"])
    ).round(3)
    return risk.sort_values("risk_score", ascending=False)


def maintenance_share_by_utility(lines_enriched: pd.DataFrame) -> pd.Series:
    return (
        lines_enriched.groupby("Code")["Status"]
        .apply(lambda s: (s == "Under Maintenance").mean() * 100)
        .rename("pct_lines_under_maintenance")
        .sort_values(ascending=False)
    )
