# Grid Network Analysis - Data Dictionary

Week 1 / Part A Task 1.3 deliverable: field-by-field description of the
three raw CSVs produced by `grid-analysis/generate_data.py` and loaded by
`grid-analysis/src/cleaning.py`. See `grid-analysis-erd.md` in this same
folder for how the three tables relate to each other.

## utilities.csv

| Column | Type | Description |
|---|---|---|
| Utility ID | integer (PK) | Unique identifier for the utility. Referenced by `lines.csv`'s `Utility ID`. |
| Name | text | Full legal name of the utility (e.g. "Electricity Company of Ghana"). |
| Alias | text | Common short name (e.g. "ECG", "GRIDCo"). |
| Code | text | Three-letter code used elsewhere in the dataset. |
| Type | text | One of `Generation`, `Transmission`, `Distribution`. |
| Country | text | Country (or countries) of operation. |
| Active | text | `Y` or `N` - whether the utility is currently operating. |

## substations.csv

| Column | Type | Description |
|---|---|---|
| Substation ID | integer (PK) | Unique identifier for the substation. Referenced by `lines.csv`'s `Source Substation ID` and `Destination Substation ID`. |
| Name | text | Full substation name (e.g. "Achimota Substation"). |
| Short Name | text | Place name, used for labelling on maps/graphs (e.g. "Achimota"). |
| Region | text | Administrative region (or bordering country, for cross-border nodes). |
| Country | text | Country. |
| Latitude | float | Decimal-degree latitude. Validated by `clean_and_validate()` to fall within `4.0` to `15.0` (approximate West African bounds). |
| Longitude | float | Decimal-degree longitude. Validated to fall within `-16.0` to `5.0`. |
| Voltage (kV) | integer | Nominal operating voltage: one of `11`, `33`, `69`, `161`, `330`. |
| Capacity (MVA) | float | Rated capacity in megavolt-amperes. |
| Commissioning Year | integer | Year the substation was notionally commissioned. |
| Type | text | One of `Distribution`, `Bulk Supply Point`, `Transmission` (derived from voltage tier). |
| Status | text | `Active` or `Inactive`. |

## lines.csv

| Column | Type | Description |
|---|---|---|
| Line ID | integer (PK) | Unique identifier for the line. |
| Utility ID | integer (FK) | Which utility owns/operates the line -> `utilities.csv: Utility ID`. |
| Source Substation ID | integer (FK) | One end of the line -> `substations.csv: Substation ID`. |
| Source Substation | text | Denormalized name of the source substation, for readability without a join. |
| Destination Substation ID | integer (FK) | The other end of the line -> `substations.csv: Substation ID`. |
| Destination Substation | text | Denormalized name of the destination substation. |
| Voltage (kV) | integer | Operating voltage of the line (the lower of its two endpoints' voltages). |
| Length (km) | float | Approximate line length, derived from the endpoints' coordinates via the haversine formula. |
| Capacity (MVA) | float | Rated transfer capacity. |
| Status | text | `Active` or `Under Maintenance`. |
| Line Type | text | `Overhead` or `Underground`. |

## Notes on data quality (Task 1.1)

- All three tables are produced by a **seeded** script (`random.seed(42)`),
  so every run of `generate_data.py` produces byte-identical CSVs.
- `src/cleaning.py`'s `clean_and_validate()` function checks, in this
  order: missing values, numeric-type coercion (on `Latitude`, `Longitude`,
  `Voltage (kV)`, `Capacity (MVA)`, `Commissioning Year`, `Length (km)`),
  duplicate rows, coordinate-range validity, and referential integrity of
  all three foreign keys described above. Running it on the generated
  dataset currently finds zero issues of any kind - see
  `notebooks/01_data_cleaning_and_eda.ipynb` for the executed report, and
  `tests/test_cleaning.py` for proof the checks work on deliberately broken
  data.
- `merge_all()` joins all three tables into one integrated, denormalized
  DataFrame (one row per line, enriched with both substations' details and
  the operating utility's details), saved to `outputs/merged_dataset.csv`.
