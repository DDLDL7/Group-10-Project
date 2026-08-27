import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bi import (
    utility_infrastructure_footprint, capacity_utilization_flags,
    line_maintenance_proportion, asset_age_profile, capacity_concentration,
    growth_opportunities, reliability_proxy,
)


def _merged_frame():
    return pd.DataFrame([
        {"Line ID": 1, "Source Substation ID": 1, "Source Substation": "A",
         "Source Region": "North", "Utility Alias": "U1", "Voltage (kV)": 33,
         "Status": "Active"},
        {"Line ID": 2, "Source Substation ID": 1, "Source Substation": "A",
         "Source Region": "North", "Utility Alias": "U1", "Voltage (kV)": 33,
         "Status": "Under Maintenance"},
        {"Line ID": 3, "Source Substation ID": 2, "Source Substation": "B",
         "Source Region": "South", "Utility Alias": "U2", "Voltage (kV)": 161,
         "Status": "Active"},
    ])


def _substations_frame():
    return pd.DataFrame([
        {"Substation ID": 1, "Name": "A", "Region": "North", "Voltage (kV)": 33,
         "Capacity (MVA)": 10.0, "Commissioning Year": 1970, "Status": "Active"},
        {"Substation ID": 2, "Name": "B", "Region": "North", "Voltage (kV)": 33,
         "Capacity (MVA)": 50.0, "Commissioning Year": 2000, "Status": "Active"},
        {"Substation ID": 3, "Name": "C", "Region": "North", "Voltage (kV)": 33,
         "Capacity (MVA)": 400.0, "Commissioning Year": 2020, "Status": "Inactive"},
        {"Substation ID": 4, "Name": "D", "Region": "South", "Voltage (kV)": 161,
         "Capacity (MVA)": 60.0, "Commissioning Year": 2010, "Status": "Active"},
    ])


def _lines_frame():
    return pd.DataFrame([
        {"Line ID": 1, "Source Substation": "A", "Destination Substation": "B",
         "Capacity (MVA)": 5.0, "Voltage (kV)": 33},
        {"Line ID": 2, "Source Substation": "B", "Destination Substation": "C",
         "Capacity (MVA)": 300.0, "Voltage (kV)": 33},
    ])


def test_utility_infrastructure_footprint_counts_by_region_and_voltage():
    merged = _merged_frame()
    by_region, by_voltage = utility_infrastructure_footprint(merged)

    top = by_region.iloc[0]
    assert top["Utility Alias"] == "U1"
    assert top["Source Region"] == "North"
    assert top["Line Count"] == 2

    assert by_voltage.loc["U1", 33] == 2
    assert by_voltage.loc["U2", 161] == 1


def test_capacity_utilization_flags_identifies_extremes():
    substations = _substations_frame()
    lines = _lines_frame()
    sub_flags, line_flags = capacity_utilization_flags(substations, lines)

    # substation 1 has low capacity, should be flagged
    assert sub_flags.loc[sub_flags["Substation ID"] == 1, "capacity_flag"].iloc[0] == \
        "Low capacity (upgrade candidate)"
    # substation 3 has high capacity, should be flagged
    assert sub_flags.loc[sub_flags["Substation ID"] == 3, "capacity_flag"].iloc[0] == "High capacity"


def test_line_maintenance_proportion_by_region_and_utility():
    merged = _merged_frame()
    by_region, by_utility = line_maintenance_proportion(merged)

    north_rate = by_region.loc[by_region["Source Region"] == "North", "under_maintenance_rate"].iloc[0]
    south_rate = by_region.loc[by_region["Source Region"] == "South", "under_maintenance_rate"].iloc[0]
    assert north_rate == 0.5  # one of two lines is under maintenance
    assert south_rate == 0.0

    u1_rate = by_utility.loc[by_utility["Utility Alias"] == "U1", "under_maintenance_rate"].iloc[0]
    assert u1_rate == 0.5


def test_asset_age_profile_buckets_by_decade():
    substations = _substations_frame()
    profile = asset_age_profile(substations)

    assert set(profile["decade"]) == {"1970s", "2000s", "2020s", "2010s"}
    row_1970s = profile.loc[profile["decade"] == "1970s"].iloc[0]
    assert row_1970s["substation_count"] == 1
    assert row_1970s["active_rate"] == 1.0

    row_2020s = profile.loc[profile["decade"] == "2020s"].iloc[0]
    assert row_2020s["active_rate"] == 0.0  # substation 3 is inactive


def test_capacity_concentration_reports_top_share():
    substations = _substations_frame()
    result = capacity_concentration(substations, top_fraction=0.25)

    # top 25% here is just the one biggest substation
    total = substations["Capacity (MVA)"].sum()
    assert result["num_substations_in_top_fraction"] == 1
    assert result["share_of_total_capacity"] == round(400.0 / total, 4)


def test_growth_opportunities_flags_low_density_low_capacity_regions():
    substations = _substations_frame()
    result = growth_opportunities(substations)

    # south has fewer substations and less capacity, should get flagged
    south_row = result.loc[result["Region"] == "South"].iloc[0]
    assert bool(south_row["growth_opportunity"]) is True


def test_reliability_proxy_ranks_older_maintenance_affected_substations_higher():
    substations = _substations_frame()
    merged = _merged_frame()
    result = reliability_proxy(substations, merged)

    # substation 1 is old and under maintenance, so it scores high
    top_id = result.iloc[0]["Substation ID"]
    assert top_id == 1
    sub1_score = result.loc[result["Substation ID"] == 1, "reliability_risk_score"].iloc[0]
    sub4_score = result.loc[result["Substation ID"] == 4, "reliability_risk_score"].iloc[0]
    assert sub1_score > sub4_score
