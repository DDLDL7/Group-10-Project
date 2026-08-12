import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.cleaning import clean_and_validate, merge_all, utility_region_line_counts


def _sample_frames():
    utilities = pd.DataFrame([
        {"Utility ID": 1, "Name": "Electricity Company of Ghana", "Alias": "ECG",
         "Code": "ECG", "Type": "Distribution", "Country": "Ghana", "Active": "Y"},
    ])
    substations = pd.DataFrame([
        {"Substation ID": 1, "Name": "Achimota Substation", "Short Name": "Achimota",
         "Region": "Greater Accra", "Country": "Ghana", "Latitude": "5.614", "Longitude": "-0.224",
         "Voltage (kV)": 33, "Capacity (MVA)": "50.0", "Commissioning Year": 2001,
         "Type": "Distribution", "Status": "Active"},
        {"Substation ID": 2, "Name": "Tema Substation", "Short Name": "Tema",
         "Region": "Greater Accra", "Country": "Ghana", "Latitude": "5.669", "Longitude": "-0.017",
         "Voltage (kV)": 33, "Capacity (MVA)": "not_a_number", "Commissioning Year": 2005,
         "Type": "Distribution", "Status": "Active"},
        {"Substation ID": 3, "Name": "Out Of Bounds Substation", "Short Name": "OOB",
         "Region": "Nowhere", "Country": "Nowhere", "Latitude": "80.0", "Longitude": "150.0",
         "Voltage (kV)": 33, "Capacity (MVA)": "10.0", "Commissioning Year": 2010,
         "Type": "Distribution", "Status": "Active"},
    ])
    lines = pd.DataFrame([
        {"Line ID": 1, "Utility ID": 1, "Source Substation ID": 1, "Source Substation": "Achimota",
         "Destination Substation ID": 2, "Destination Substation": "Tema",
         "Voltage (kV)": 33, "Length (km)": "12.0", "Capacity (MVA)": "80.0",
         "Status": "Active", "Line Type": "Overhead"},
        {"Line ID": 2, "Utility ID": 1, "Source Substation ID": 1, "Source Substation": "Achimota",
         "Destination Substation ID": 999, "Destination Substation": "Ghost",
         "Voltage (kV)": 33, "Length (km)": "5.0", "Capacity (MVA)": "40.0",
         "Status": "Active", "Line Type": "Overhead"},
        # exact duplicate of line 1
        {"Line ID": 1, "Utility ID": 1, "Source Substation ID": 1, "Source Substation": "Achimota",
         "Destination Substation ID": 2, "Destination Substation": "Tema",
         "Voltage (kV)": 33, "Length (km)": "12.0", "Capacity (MVA)": "80.0",
         "Status": "Active", "Line Type": "Overhead"},
    ])
    return utilities, substations, lines


def test_numeric_coercion_and_failure_reporting():
    utilities, substations, lines = _sample_frames()
    _, clean_subs, clean_lines, report = clean_and_validate(utilities, substations, lines)

    assert pd.api.types.is_float_dtype(clean_subs["Latitude"])
    assert pd.api.types.is_float_dtype(clean_lines["Length (km)"])
    # "not_a_number" must coerce to NaN, not raise
    assert clean_subs.loc[clean_subs["Substation ID"] == 2, "Capacity (MVA)"].isnull().all()
    assert report["numeric_coercion_failures"]["substations"]["Capacity (MVA)"] == 1


def test_duplicates_are_dropped():
    utilities, substations, lines = _sample_frames()
    _, _, clean_lines, report = clean_and_validate(utilities, substations, lines)

    assert report["duplicates_found"]["lines"] == 1
    assert len(clean_lines) == 2  # one duplicate pair collapses to one row


def test_invalid_coordinates_and_referential_integrity_are_caught():
    utilities, substations, lines = _sample_frames()
    _, _, _, report = clean_and_validate(utilities, substations, lines)

    assert report["invalid_coordinates"] == 1
    assert 3 in report["invalid_coordinate_substation_ids"]
    assert 2 in report["referential_integrity"]["invalid_destination_substation_lines"]


def test_merge_all_enriches_lines_with_names_and_utility_info():
    utilities, substations, lines = _sample_frames()
    _, clean_subs, clean_lines, _ = clean_and_validate(utilities, substations, lines)
    merged = merge_all(utilities, clean_subs, clean_lines)

    row = merged.loc[merged["Line ID"] == 1].iloc[0]
    assert row["Source Name"] == "Achimota Substation"
    assert row["Destination Name"] == "Tema Substation"
    assert row["Utility Alias"] == "ECG"


def test_utility_region_line_counts_groups_and_sorts_correctly():
    merged = pd.DataFrame([
        {"Utility Code": "ECG", "Source Region": "Greater Accra"},
        {"Utility Code": "ECG", "Source Region": "Greater Accra"},
        {"Utility Code": "ECG", "Source Region": "Ashanti"},
        {"Utility Code": "GRD", "Source Region": "Greater Accra"},
    ])
    counts = utility_region_line_counts(merged)

    # busiest combination (ECG / Greater Accra, count 2) must come first
    top = counts.iloc[0]
    assert top["Utility Code"] == "ECG"
    assert top["Source Region"] == "Greater Accra"
    assert top["Line Count"] == 2

    # every other combination should have a lower count than the top row
    assert (counts["Line Count"].iloc[1:] <= 1).all()
    assert len(counts) == 3  # three distinct (utility, region) combinations
