"""Loading, cleaning, validation, and merging for the grid-analysis datasets.

Ports and extends the ad-hoc checks that used to live in "examined data.py"
into reusable functions shared by the notebooks, the dashboard, and the tests.
"""
from pathlib import Path

import numpy as np
import pandas as pd

# Approximate West African bounding box (covers Ghana and the WAPP
# cross-border points used in generate_data.py: Guinea, Burkina Faso,
# Cote d'Ivoire, Togo, Benin, Nigeria).
LAT_BOUNDS = (4.0, 15.0)
LON_BOUNDS = (-16.0, 5.0)

NUMERIC_SUBSTATION_COLS = ["Latitude", "Longitude", "Voltage (kV)", "Capacity (MVA)",
                           "Commissioning Year"]
NUMERIC_LINE_COLS = ["Voltage (kV)", "Length (km)", "Capacity (MVA)"]


def load_raw(data_dir):
    """Load the three raw CSVs from data_dir into DataFrames."""
    data_dir = Path(data_dir)
    utilities = pd.read_csv(data_dir / "utilities.csv")
    substations = pd.read_csv(data_dir / "substations.csv")
    lines = pd.read_csv(data_dir / "lines.csv")
    return utilities, substations, lines


def clean_and_validate(utilities, substations, lines):
    """Clean the three DataFrames and validate cross-table relationships.

    Returns (utilities, substations, lines, report) where the returned
    frames are cleaned copies and report is a dict summarizing every
    issue found (and fixed, where fixable).
    """
    report = {}

    utilities = utilities.copy()
    substations = substations.copy()
    lines = lines.copy()

    # --- missing values -----------------------------------------------
    report["missing_values"] = {
        "utilities": utilities.isnull().sum().to_dict(),
        "substations": substations.isnull().sum().to_dict(),
        "lines": lines.isnull().sum().to_dict(),
    }

    # --- numeric coercion ------------------------------------------------
    for col in NUMERIC_SUBSTATION_COLS:
        substations[col] = pd.to_numeric(substations[col], errors="coerce")
    for col in NUMERIC_LINE_COLS:
        lines[col] = pd.to_numeric(lines[col], errors="coerce")

    coercion_failures = {
        "substations": {c: int(substations[c].isnull().sum()) for c in NUMERIC_SUBSTATION_COLS},
        "lines": {c: int(lines[c].isnull().sum()) for c in NUMERIC_LINE_COLS},
    }
    report["numeric_coercion_failures"] = coercion_failures

    # --- duplicates -------------------------------------------------------
    report["duplicates_found"] = {
        "utilities": int(utilities.duplicated().sum()),
        "substations": int(substations.duplicated().sum()),
        "lines": int(lines.duplicated().sum()),
    }
    utilities = utilities.drop_duplicates().reset_index(drop=True)
    substations = substations.drop_duplicates().reset_index(drop=True)
    lines = lines.drop_duplicates().reset_index(drop=True)

    # --- coordinate range validation ---------------------------------------
    lat_ok = substations["Latitude"].between(*LAT_BOUNDS)
    lon_ok = substations["Longitude"].between(*LON_BOUNDS)
    bad_coords = substations[~(lat_ok & lon_ok)]
    report["invalid_coordinates"] = int(len(bad_coords))
    report["invalid_coordinate_substation_ids"] = bad_coords["Substation ID"].tolist()

    # --- relational integrity ----------------------------------------------
    valid_substation_ids = set(substations["Substation ID"])
    valid_utility_ids = set(utilities["Utility ID"])

    bad_source = lines[~lines["Source Substation ID"].isin(valid_substation_ids)]
    bad_dest = lines[~lines["Destination Substation ID"].isin(valid_substation_ids)]
    bad_utility = lines[~lines["Utility ID"].isin(valid_utility_ids)]

    report["referential_integrity"] = {
        "invalid_source_substation_lines": bad_source["Line ID"].tolist(),
        "invalid_destination_substation_lines": bad_dest["Line ID"].tolist(),
        "invalid_utility_lines": bad_utility["Line ID"].tolist(),
    }

    return utilities, substations, lines, report


def merge_all(utilities, substations, lines):
    """Merge the three tables into one integrated, denormalized DataFrame.

    Each row is a line, enriched with its source/destination substation
    details (name, region, country) and its operating utility's name/code.
    """
    sub_cols = ["Substation ID", "Name", "Region", "Country"]

    merged = lines.merge(
        substations[sub_cols], left_on="Source Substation ID", right_on="Substation ID",
        how="left", suffixes=("", "_source"),
    ).drop(columns=["Substation ID"]).rename(columns={
        "Name": "Source Name", "Region": "Source Region", "Country": "Source Country",
    })

    merged = merged.merge(
        substations[sub_cols], left_on="Destination Substation ID", right_on="Substation ID",
        how="left",
    ).drop(columns=["Substation ID"]).rename(columns={
        "Name": "Destination Name", "Region": "Destination Region", "Country": "Destination Country",
    })

    merged = merged.merge(
        utilities[["Utility ID", "Name", "Alias", "Code"]], on="Utility ID", how="left",
    ).rename(columns={"Name": "Utility Name", "Alias": "Utility Alias", "Code": "Utility Code"})

    return merged
