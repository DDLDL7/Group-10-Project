# Grid Network Analysis — Test Report

Run with `cd grid-analysis && pytest tests/`. **Result: 23/23 passed.**
Tests use small, hand-built DataFrames/graphs (not the full generated
dataset) so failures point precisely at the function under test.
The dashboard (`dashboard.py`) and the standalone BI script
(`task_2_3_business_intelligence.py`) were additionally run end-to-end
against the real generated dataset as a smoke test (see below).

## Data cleaning & validation (`tests/test_cleaning.py`)

| Test | Objective | Input | Expected | Actual | Result |
|---|---|---|---|---|---|
| `test_numeric_coercion_and_failure_reporting` | Numeric columns coerced, non-numeric values counted as coercion failures | Substation/line rows with a non-numeric value in a numeric column | Column coerced to numeric dtype; failure count reported in the cleaning report | As expected | PASS |
| `test_duplicates_are_dropped` | Duplicate rows removed | Duplicate substation row | Row count reduced by the duplicate; count reported | As expected | PASS |
| `test_invalid_coordinates_and_referential_integrity_are_caught` | Out-of-range coordinates and orphaned FKs detected | A substation outside the West Africa bounding box; a line referencing a non-existent substation/utility ID | Both flagged in the cleaning report, not silently dropped | As expected | PASS |
| `test_merge_all_enriches_lines_with_names_and_utility_info` | Merge produces one denormalized row per line | Small utilities/substations/lines set | Merged frame includes source/destination substation names and utility name/code | As expected | PASS |
| `test_utility_region_line_counts_groups_and_sorts_correctly` | Utility/region line-count aggregation | Merged frame with known utility/region combinations | Grouped counts correct and sorted descending | As expected | PASS |

## Network analysis (`tests/test_network.py`)

| Test | Objective | Input | Expected | Actual | Result |
|---|---|---|---|---|---|
| `test_build_graph_node_and_edge_counts_match_input` | Graph construction (nodes/edges) | Small substations/lines set | `G.number_of_nodes()`/`number_of_edges()` match row counts | As expected | PASS |
| `test_build_graph_skips_lines_with_unknown_substations` | Referential integrity honoured during graph build | A line referencing a substation not in the node set | That edge is skipped, not added with a dangling endpoint | As expected | PASS |
| `test_centrality_values_fall_in_unit_interval` | Centrality metric calculation | Small connected graph | All degree/betweenness/closeness/PageRank values in `[0, 1]` | As expected | PASS |
| `test_connected_components_on_two_separate_triangles` | Connected-component detection | Two disjoint 3-node triangles | 2 components, each size 3 | As expected | PASS |
| `test_largest_component_subgraph` | Largest-component extraction | Graph with components of different sizes | Returned subgraph matches the largest component | As expected | PASS |
| `test_find_bridges_on_star_graph` | Bridge detection | Star graph (every edge is a bridge) | All edges reported as bridges | As expected | PASS |
| `test_find_bridges_on_triangle_has_none` | Bridge detection (negative case) | Triangle (no bridges) | Empty bridge list | As expected | PASS |
| `test_detect_communities_covers_every_node` | Community detection | Small graph | Every node assigned to exactly one community | As expected | PASS |
| `test_network_summary_on_star_graph` | Whole-network summary metrics | Star graph | Diameter, avg. path length, efficiency, clustering match known star-graph values | As expected | PASS |
| `test_n1_contingency_detects_fragmentation_on_star_graph` | **N-1 contingency analysis** | Remove the star graph's centre node | Component count increases (network fragments) | As expected | PASS |
| `test_n1_contingency_raises_for_unknown_node` | N-1 input validation | Node ID not in the graph | `ValueError` | As expected | PASS |

## Geographic analysis (`tests/test_geo.py`)

| Test | Objective | Input | Expected | Actual | Result |
|---|---|---|---|---|---|
| `test_verify_line_distances_reports_expected_difference` | Independent geodesic distance recomputation | Known coordinate pair | Recomputed distance and % difference match hand-calculated value | As expected | PASS |
| `test_categorize_line_distances_buckets_correctly` | Distance categorization | Lines of known short/medium/long lengths | Bucketed into the correct category | As expected | PASS |
| `test_find_geographic_clusters_groups_nearby_substations` | Proximity clustering | Substations within/outside a radius | Nearby substations share a `geo_cluster`, distant ones don't | As expected | PASS |
| `test_regional_connectivity_counts_cross_region_lines` | Cross-region line counting | Lines spanning one vs. two regions | Correct intra- vs. cross-regional counts | As expected | PASS |
| `test_geographic_gaps_flags_below_median_regions` | Underserved-region proxy | Regions with known substation counts | Below-median regions flagged | As expected | PASS |
| `test_build_folium_map_returns_map_with_utility_layers` | Interactive map construction | Small dataset + utilities | Folium `Map` object returned with expected layer count | As expected | PASS |
| `test_build_plotly_substation_map_plots_every_substation_colored_by_region` | Plotly map construction | Small substation set | One trace per region, all substations plotted | As expected | PASS |

## End-to-end smoke tests (manual, against the real dataset)

| Check | Expected | Actual | Result |
|---|---|---|---|
| Full data pipeline (load → clean → merge → graph → centrality → N-1 → geo → BI) | No exceptions on the real 44-substation/55-line dataset | Ran cleanly; see `REPORT.md` for the resulting figures | PASS |
| `streamlit run dashboard.py --server.headless true` | Starts and serves without a startup traceback | `Uvicorn server started`, `You can now view your Streamlit app` | PASS |
| `python task_2_3_business_intelligence.py` | Runs end-to-end, writes 5 charts + `task_2_3_findings.md` | Completed, all outputs written to `outputs/charts/` | PASS |

## Defects found and corrected during this build pass

| Defect | How found | Corrective action | Retest |
|---|---|---|---|
| No Streamlit dashboard existed despite being a required deliverable (and listed in `requirements.txt`) | Directory inspection | Built `dashboard.py` with the required Overview/Network/Geography/Reliability/Search tabs, reusing `src/` | Started cleanly (see above) |
| No written findings report existed | Directory inspection | Wrote `REPORT.md` covering dataset description, cleaning, EDA, network analysis (incl. N-1), and limitations | — |
| Root-level duplicate `utilities.csv`/`substations.csv`/`lines.csv` (byte-identical to `data/*.csv`) and several individually-authored exploratory scripts scattered at the repo root reading from bare relative paths | Directory inspection | Verified duplicates were byte-identical, removed them; moved exploratory scripts into `legacy_scripts/` with corrected relative paths (kept, not deleted, as individual contribution evidence) | Re-ran each moved script; `task_2_3_business_intelligence.py` re-run from its corrected path, output unchanged |
