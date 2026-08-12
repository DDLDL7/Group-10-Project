"""
Task 2.3: Business Intelligence and Reliability Analysis
==========================================================
Owner (per project spec): Team Member 2 — Data Analyst

Extracts business and reliability insights from the cleaned grid datasets:
    A. Utility Footprint Analysis   — who operates the most infrastructure, and where
    B. Capacity Utilization Mapping — which substations look under/over-provisioned
    C. Growth Opportunity Analysis  — which regions are thin on infrastructure
    D. Asset Age Profile            — how old the network is, region by region
    E. Reliability Proxy Analysis   — a composite "at-risk" score per substation

IMPORTANT CAVEAT (documented per the project brief): this dataset is synthetic.
There is no real load, demand, or outage-history data, so "utilization" and
"reliability" below are proxies built from the fields we do have (rated
capacity, connection count, maintenance status, commissioning year). They are
structural indicators, not measurements of real electrical behaviour — treat
every number here as "worth investigating further", not as a verified fact
about Ghana's actual grid.

Outputs:
    - Printed tables for every section (console)
    - 4 PNG charts (saved next to this script)
    - task_2_3_findings.md — a short auto-generated summary/recommendations doc
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

REFERENCE_YEAR = 2026  # ages computed "as of" 2026 — documented assumption

# ---------------------------------------------------------------------------
# 0. Load + join what we need
# ---------------------------------------------------------------------------
utilities = pd.read_csv('utilities.csv')
substations = pd.read_csv('substations.csv')
lines = pd.read_csv('lines.csv')

# Only consider substations/lines that are actually in service for the
# capacity- and footprint-style analyses. Decision, documented: "usable"
# infrastructure = Active status. Inactive/Under-Maintenance assets are kept
# in the reliability section instead, where their status is the whole point.
active_subs = substations[substations['Status'] == 'Active'].copy()

# Attach the source substation's Region to every line, and the owning
# utility's short Code, so we can slice lines by both region and operator.
lines_enriched = (
    lines
    .merge(substations[['Substation ID', 'Region']],
           left_on='Source Substation ID', right_on='Substation ID', how='left')
    .rename(columns={'Region': 'Source Region'})
    .drop(columns='Substation ID')
    .merge(utilities[['Utility ID', 'Code']], on='Utility ID', how='left')
)

print("=" * 70)
print("TASK 2.3 — BUSINESS INTELLIGENCE AND RELIABILITY ANALYSIS")
print("=" * 70)

# ---------------------------------------------------------------------------
# A. Utility Footprint Analysis
# ---------------------------------------------------------------------------
# Substations don't carry a "utility" field in this dataset — only lines do
# (Utility ID). So "footprint" is measured as: how many lines does each
# utility operate, how much of that is by region, and how much by voltage
# tier (a rough proxy for distribution vs. transmission-level presence).
print("\n--- A. Utility Footprint Analysis ---\n")

footprint_national = (
    lines_enriched.groupby('Code')
    .agg(lines_operated=('Line ID', 'count'),
         total_line_capacity_mva=('Capacity (MVA)', 'sum'))
    .sort_values('lines_operated', ascending=False)
)
print("Lines operated and total line capacity, by utility (national):")
print(footprint_national.round(1), "\n")

footprint_by_region = (
    lines_enriched.groupby(['Code', 'Source Region'])['Line ID']
    .count().rename('lines_operated').reset_index()
)
top_footprint_region = (
    footprint_by_region.sort_values('lines_operated', ascending=False).head(10)
)
print("Top 10 utility/region combinations by line count:")
print(top_footprint_region, "\n")

footprint_by_voltage = (
    lines_enriched.groupby(['Code', 'Voltage (kV)'])['Line ID']
    .count().unstack(fill_value=0)
)
print("Lines operated by utility, split by voltage tier:")
print(footprint_by_voltage, "\n")

top_utility = footprint_national.index[0]
print(f"Finding: {top_utility} operates the most lines nationally "
      f"({footprint_national.loc[top_utility, 'lines_operated']} of {len(lines)}).")

# ---------------------------------------------------------------------------
# B. Capacity Utilization Mapping
# ---------------------------------------------------------------------------
# Proxy for "utilization" (no real load data exists): compare each active
# substation's own rated capacity against the combined rated capacity of the
# lines connected to it. A substation whose connected lines carry far more
# capacity than the substation itself is rated for looks like a candidate for
# an upgrade; one whose connected lines are tiny relative to its own rating
# looks over-provisioned for what it actually serves.
print("\n--- B. Capacity Utilization Mapping (proxy) ---\n")

line_capacity_at_sub = pd.concat([
    lines.groupby('Source Substation ID')['Capacity (MVA)'].sum(),
    lines.groupby('Destination Substation ID')['Capacity (MVA)'].sum(),
]).groupby(level=0).sum().rename('connected_line_capacity_mva')

util_map = active_subs.merge(
    line_capacity_at_sub, left_on='Substation ID', right_index=True, how='left'
)
util_map['connected_line_capacity_mva'] = util_map['connected_line_capacity_mva'].fillna(0)
util_map['utilization_ratio'] = (
    util_map['connected_line_capacity_mva'] / util_map['Capacity (MVA)']
).round(2)

def flag_utilization(ratio):
    if ratio >= 3:
        return 'Potential upgrade candidate (under-provisioned)'
    if ratio <= 0.5:
        return 'Possibly over-provisioned'
    return 'Balanced'

util_map['utilization_flag'] = util_map['utilization_ratio'].apply(flag_utilization)

print("Utilization flag counts (active substations):")
print(util_map['utilization_flag'].value_counts(), "\n")

print("Top 10 potential upgrade candidates (connected line capacity far exceeds own rating):")
print(util_map.sort_values('utilization_ratio', ascending=False)
      [['Name', 'Region', 'Capacity (MVA)', 'connected_line_capacity_mva', 'utilization_ratio']]
      .head(10).to_string(index=False), "\n")

# Also keep the capacity-concentration view (which substations dominate their
# region's/the nation's installed capacity) — a related but distinct BI
# question: risk from concentration, not under/over-sizing.
total_capacity = active_subs['Capacity (MVA)'].sum()
active_subs['national_share_%'] = (active_subs['Capacity (MVA)'] / total_capacity * 100).round(2)
region_totals = active_subs.groupby('Region')['Capacity (MVA)'].transform('sum')
active_subs['regional_share_%'] = (active_subs['Capacity (MVA)'] / region_totals * 100).round(2)
concentration_risk = active_subs[active_subs['regional_share_%'] >= 50]
print(f"Substations carrying 50%+ of their region's capacity (single-point risk): "
      f"{len(concentration_risk)}")
print(concentration_risk[['Name', 'Region', 'Capacity (MVA)', 'regional_share_%']]
      .to_string(index=False), "\n")

# ---------------------------------------------------------------------------
# C. Growth Opportunity Analysis
# ---------------------------------------------------------------------------
# No population or land-area data exists for the regions, so "underserved" is
# necessarily a relative, infrastructure-only proxy: regions with the fewest
# active substations and the least installed capacity. Flag the bottom
# quartile as growth candidates, and say so explicitly in the caveat.
#
# Restricted to Ghana: the WAPP cross-border hubs (Benin, Togo, Guinea, ...)
# are each modelled as exactly one interconnection substation by design, so
# including them would just flag "every foreign hub" as a growth opportunity
# rather than surfacing genuinely thin domestic regions.
print("\n--- C. Growth Opportunity Analysis (proxy — infrastructure density only, Ghana regions) ---\n")

region_summary = (
    active_subs[active_subs['Country'] == 'Ghana'].groupby('Region')
    .agg(substation_count=('Substation ID', 'count'),
         total_capacity_mva=('Capacity (MVA)', 'sum'))
    .sort_values('substation_count')
)
growth_cutoff = region_summary['substation_count'].quantile(0.25)
region_summary['growth_candidate'] = region_summary['substation_count'] <= growth_cutoff
print("Active substations and installed capacity by region (ascending = thinnest first):")
print(region_summary.round(1), "\n")

growth_regions = region_summary[region_summary['growth_candidate']].index.tolist()
print(f"Finding: regions with the fewest active substations (bottom quartile, "
      f"<= {growth_cutoff:.1f} substations): {growth_regions}")

# ---------------------------------------------------------------------------
# D. Asset Age Profile
# ---------------------------------------------------------------------------
print("\n--- D. Asset Age Profile ---\n")

substations['age'] = REFERENCE_YEAR - substations['Commissioning Year']
bins = [0, 20, 40, np.inf]
labels = ['Modern', 'Mature', 'Legacy']
substations['age_band'] = pd.cut(substations['age'], bins=bins, labels=labels)

age_by_region = (
    substations.groupby('Region')['age']
    .agg(['mean', 'median', 'count'])
    .sort_values('mean', ascending=False)
)
print("Mean/median substation age by region (years, as of 2026):")
print(age_by_region.round(1), "\n")

age_band_profile = (
    substations.groupby('age_band', observed=True)
    .agg(count=('Substation ID', 'count'),
         mean_capacity_mva=('Capacity (MVA)', 'mean'),
         pct_active=('Status', lambda s: (s == 'Active').mean() * 100))
)
print("Profile by age band (Modern <=20y, Mature 21-40y, Legacy >40y):")
print(age_band_profile.round(1), "\n")

oldest_region = age_by_region.index[0]
print(f"Finding: {oldest_region} has the oldest infrastructure on average "
      f"({age_by_region.loc[oldest_region, 'mean']:.1f} years).")

# ---------------------------------------------------------------------------
# E. Reliability Proxy Analysis
# ---------------------------------------------------------------------------
# Composite, unweighted-toward-any-single-signal proxy combining:
#   - age              (older assets -> higher fault-risk proxy)
#   - degree (connections) (fewer connections -> less redundancy if it fails)
#   - regional maintenance share (more lines under maintenance nearby -> more
#     operational strain in that area right now)
# This is explicitly NOT a substitute for the formal centrality metrics
# computed with NetworkX in Task 2.1 — it's a lightweight, pandas-only signal
# for the BI report.
print("\n--- E. Reliability Proxy Analysis ---\n")

maintenance_share_by_region = (
    lines_enriched.groupby('Source Region')['Status']
    .apply(lambda s: (s == 'Under Maintenance').mean() * 100)
    .rename('pct_lines_under_maintenance')
)
print("Share of lines 'Under Maintenance', by region:")
print(maintenance_share_by_region.sort_values(ascending=False).round(1), "\n")

maintenance_share_by_utility = (
    lines_enriched.groupby('Code')['Status']
    .apply(lambda s: (s == 'Under Maintenance').mean() * 100)
    .rename('pct_lines_under_maintenance')
)
print("Share of lines 'Under Maintenance', by utility:")
print(maintenance_share_by_utility.sort_values(ascending=False).round(1), "\n")

degree = pd.concat([
    lines['Source Substation ID'], lines['Destination Substation ID']
]).value_counts().rename('degree')

risk = substations.merge(degree, left_on='Substation ID', right_index=True, how='left')
risk['degree'] = risk['degree'].fillna(0)
risk = risk.merge(maintenance_share_by_region, left_on='Region', right_index=True, how='left')
risk['pct_lines_under_maintenance'] = risk['pct_lines_under_maintenance'].fillna(0)

def normalize(series):
    span = series.max() - series.min()
    return (series - series.min()) / span if span else series * 0

risk['risk_score'] = (
    0.4 * normalize(risk['age'])
    + 0.4 * normalize(1 / (risk['degree'] + 1))
    + 0.2 * normalize(risk['pct_lines_under_maintenance'])
).round(3)

top_risk = risk.sort_values('risk_score', ascending=False).head(10)
print("Top 10 substations by composite reliability-risk proxy "
      "(older + fewer connections + more nearby maintenance = higher risk):")
print(top_risk[['Name', 'Region', 'age', 'degree', 'pct_lines_under_maintenance', 'risk_score']]
      .to_string(index=False), "\n")

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
footprint_national['lines_operated'].plot(kind='bar', ax=axes[0], color='#4C72B0')
axes[0].set_title('Lines Operated by Utility (national)')
axes[0].set_ylabel('Number of lines')
axes[0].set_xlabel('Utility')

footprint_by_voltage.plot(kind='bar', stacked=True, ax=axes[1], colormap='viridis')
axes[1].set_title('Lines Operated by Utility, by Voltage Tier')
axes[1].set_ylabel('Number of lines')
axes[1].set_xlabel('Utility')
axes[1].legend(title='Voltage (kV)')
plt.tight_layout()
plt.savefig('utility_footprint.png')
plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 5))
util_map['utilization_flag'].value_counts().plot(kind='bar', ax=ax, color='#DD8452')
ax.set_title('Capacity Utilization Flags (active substations, proxy)')
ax.set_ylabel('Number of substations')
plt.xticks(rotation=20, ha='right')
plt.tight_layout()
plt.savefig('capacity_utilization_flags.png')
plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 5))
substations['age_band'].value_counts().reindex(labels).plot(kind='bar', ax=ax, color='#55A868')
ax.set_title('Substation Count by Age Band (as of 2026)')
ax.set_ylabel('Number of substations')
plt.tight_layout()
plt.savefig('age_band_distribution.png')
plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 6))
top_risk.set_index('Name')['risk_score'].sort_values().plot(kind='barh', ax=ax, color='#C44E52')
ax.set_title('Top 10 Substations by Reliability-Risk Proxy')
ax.set_xlabel('Composite risk score (0-1, higher = more at-risk)')
plt.tight_layout()
plt.savefig('reliability_risk_top10.png')
plt.close(fig)

print("Saved charts: utility_footprint.png, capacity_utilization_flags.png, "
      "age_band_distribution.png, reliability_risk_top10.png")

# ---------------------------------------------------------------------------
# Auto-generated strategic recommendations document
# ---------------------------------------------------------------------------
upgrade_candidates = util_map[
    util_map['utilization_flag'] == 'Potential upgrade candidate (under-provisioned)'
]
report = f"""# Task 2.3 — Business Intelligence and Reliability Analysis: Findings

*Auto-generated from the synthetic grid dataset. All figures are structural
proxies computed from rated capacity, connection counts, and maintenance
status — not measurements of real load, demand, or outage history. Treat
every finding below as a lead for further investigation, not a verified
operational fact about Ghana's actual grid.*

## A. Utility Footprint
- **{top_utility}** operates the most lines nationally
  ({footprint_national.loc[top_utility, 'lines_operated']} of {len(lines)} total lines).
- See `utility_footprint.png` for the full per-utility / per-voltage-tier breakdown.

## B. Capacity Utilization
- {len(upgrade_candidates)} active substation(s) flagged as potential upgrade
  candidates (connected line capacity is at least 3x their own rated capacity).
- {len(concentration_risk)} active substation(s) carry 50%+ of their region's
  total installed capacity — a single-point concentration risk.

## C. Growth Opportunities
- Regions in the bottom quartile by active substation count (thinnest
  infrastructure): **{', '.join(growth_regions) if growth_regions else 'none'}**.
- This is an infrastructure-density proxy only — no population or land-area
  data was available to weight it against actual demand.

## D. Asset Age Profile
- **{oldest_region}** has the oldest infrastructure on average
  ({age_by_region.loc[oldest_region, 'mean']:.1f} years as of {REFERENCE_YEAR}).
- Legacy-band (>40 years) substations: {int(age_band_profile.loc['Legacy', 'count']) if 'Legacy' in age_band_profile.index else 0}.

## E. Reliability Proxy
- Highest composite risk-proxy substation: **{top_risk.iloc[0]['Name']}**
  ({top_risk.iloc[0]['Region']}, risk score {top_risk.iloc[0]['risk_score']:.2f}).
- See `reliability_risk_top10.png` for the full ranked list.

## Strategic Recommendations (draft — for team review)
1. Prioritise field verification of the upgrade-candidate substations in
   Section B before any capital planning decision is made from this proxy.
2. Treat the growth-opportunity regions in Section C as a starting shortlist
   for a proper demand study, not a standalone justification for investment.
3. Cross-check the top reliability-risk substations in Section E against the
   N-1 contingency results from Task 2.1 — a substation that is both
   high-risk here and structurally critical there deserves the closest
   attention.
"""

with open('task_2_3_findings.md', 'w') as f:
    f.write(report)

print("\nWrote strategic-recommendations summary to task_2_3_findings.md")
