# National Electricity Grid Network Analysis — Written Report

CS 112 Final Course Project · Grid Network Analysis component

## 1. Dataset description

The analysis uses three related CSVs produced by `generate_data.py`, a
seeded (`random.seed(42)`) synthetic-data generator grounded in Ghanaian
geography and real utility names (ECG, NEDCo, GRIDCo, VRA) plus WAPP-style
cross-border interconnection points. The dataset is illustrative, not
survey data: coordinates, capacities, commissioning years, and connections
are fictional stand-ins for the kind of numbers a real grid operator would
work with.

The cleaned dataset (`grid-analysis/data/`) contains:

| Table | Rows | Key fields |
|---|---|---|
| `utilities.csv` | 10 | Utility ID, Name, Alias, Code, Type, Country, Active |
| `substations.csv` | 44 | Substation ID, Name, Region, Country, Latitude/Longitude, Voltage (kV), Capacity (MVA), Commissioning Year, Type, Status |
| `lines.csv` | 55 | Line ID, Utility ID, Source/Destination Substation, Voltage (kV), Length (km), Capacity (MVA), Status, Line Type |

The 44 substations span 18 regions/countries (Ghana's ten administrative
regions plus cross-border nodes in Côte d'Ivoire, Togo, Benin, Burkina
Faso, and Guinea). Voltage levels are concentrated at 161 kV (11
substations) and 330 kV (10), with the remainder at 69/33/11 kV
distribution tiers. 43 of 44 substations are Active; 53 of 55 lines are
Active, with 2 Under Maintenance.

## 2. Data cleaning and validation

`src/cleaning.py` implements the cleaning pipeline used by both the
notebooks and this dashboard:

- **Missing values** — every column is checked with `isnull().sum()` and
  reported, even though the generator itself produces complete rows (the
  point is to demonstrate the check, since a real asset register would not
  be this clean).
- **Numeric coercion** — `Latitude`, `Longitude`, `Voltage (kV)`,
  `Capacity (MVA)`, `Commissioning Year` (substations) and `Voltage (kV)`,
  `Length (km)`, `Capacity (MVA)` (lines) are coerced with
  `pd.to_numeric(errors="coerce")`, and any resulting `NaN`s are counted.
- **Duplicates** — exact duplicate rows are dropped from all three tables
  (none were found in the generated data).
- **Coordinate range validation** — latitude/longitude are checked against
  an approximate West African bounding box (4–15°N, -16–5°E) covering
  Ghana and the WAPP cross-border points; no out-of-range coordinates were
  found.
- **Referential integrity** — every `Source Substation ID` and
  `Destination Substation ID` in `lines.csv` is checked against
  `substations.csv`'s primary key, and every `Utility ID` in `lines.csv`
  against `utilities.csv`; no orphaned records were found in this run.

All three tables are then merged into one denormalized view
(`merge_all`), joining each line to its source/destination substation
details and operating utility, and validated again for join-related row
loss.

## 3. Exploratory data analysis — key findings

- **Regional distribution**: Greater Accra and Ashanti have the densest
  substation coverage; several single-substation cross-border nodes exist
  by design (they represent WAPP interconnection points, not full
  regional grids).
- **Voltage mix**: transmission-tier substations (161/330 kV) make up
  roughly half the network, reflecting the deliberate inclusion of
  inter-regional backbone lines and cross-border links alongside local
  distribution infrastructure.
- **Utility footprint**: GRIDCo (`GRD`) operates the most lines nationally
  (24 of 55, 6,037 MVA of combined line capacity), consistent with its
  role as the transmission-level operator connecting other utilities'
  distribution networks.
- **Reliability proxies** (Task 2.3): substations were scored on a
  composite proxy combining asset age, inverse connectivity, and regional
  maintenance share. The highest-risk substation in this run was
  **Winneba Substation** (risk score 0.66). 26 active substations were
  flagged as potential upgrade candidates (connected line capacity ≥3×
  their own rating); 4 were flagged as possibly over-provisioned.

## 4. Network analysis

`src/network.py` builds an **undirected** NetworkX graph — substations as
nodes, lines as edges — since AC power can flow either direction along a
line depending on system conditions.

**Structural summary**: 44 nodes, 55 edges, **3 connected components**
(one large component of 42 substations, plus two isolated single-node
components), diameter 14 (largest component), average shortest path
length 5.41, global efficiency 0.244, average clustering coefficient
0.37, 10 detected communities, and 21 bridge lines (single points of
connection whose removal alone would split the network further).

**Critical substations** by degree/betweenness centrality: **Cape Coast**,
**Kumasi Central**, **Achimota**, and **Mallam** rank highest, consistent
with their roles as regional hubs connecting several other substations
and, in Cape Coast and Kumasi's case, sitting on paths between regions.

**N-1 contingency analysis**: removing the top-centrality substation
(Cape Coast, betweenness 0.53) split the network from 3 components to
**5**, with the largest remaining piece shrinking from 42 to 20 nodes —
i.e. the network **does fragment** under this specific single-node
removal. This is a useful (if sobering) teaching result: a network that is
already only loosely meshed at its edges, with 21 bridge lines, has
little redundancy to absorb the loss of a well-connected hub. A more
resilient design would add parallel/looped connections around
high-betweenness nodes like Cape Coast so a single failure could be
routed around rather than isolating whole sub-regions.

## 5. Limitations

- All figures are computed from **synthetic, seeded data** and must not be
  presented as verified facts about Ghana's actual grid.
- Graph centrality and the N-1 test are **structural proxies**, not
  power-flow, protection-coordination, or transient-stability studies;
  they say nothing about real electrical load, voltage stability, or
  protection behaviour.
- The reliability-risk score is an unweighted, unvalidated composite of
  three proxy signals (age, connectivity, regional maintenance share) with
  arbitrary 0.4/0.4/0.2 weights — useful for ranking candidates for
  further investigation, not as a standalone maintenance-priority
  decision.
- The two single-node "components" are an artifact of the generator's
  random connection probability, not a real islanded network condition.

## 6. Where to find the supporting code

- Cleaning/validation/merge: `src/cleaning.py` (tested in `tests/test_cleaning.py`)
- Network analysis: `src/network.py` (tested in `tests/test_network.py`)
- Geographic analysis: `src/geo.py` (tested in `tests/test_geo.py`)
- Business intelligence / reliability: `src/business_intelligence.py`,
  `task_2_3_business_intelligence.py` (full findings in
  `task_2_3_findings.md`)
- Interactive dashboard (Overview / Network / Geography / Reliability /
  Search tabs): `dashboard.py` — run with `streamlit run dashboard.py`
- Notebooks walking through each stage: `notebooks/01`–`04`
