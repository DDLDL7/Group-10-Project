# Task 2.3 — Business Intelligence and Reliability Analysis: Findings

*Auto-generated from the synthetic grid dataset. All figures are structural
proxies computed from rated capacity, connection counts, and maintenance
status — not measurements of real load, demand, or outage history. Treat
every finding below as a lead for further investigation, not a verified
operational fact about Ghana's actual grid.*

## A. Utility Footprint
- **GRD** operates the most lines nationally
  (24 of 55 total lines).
- See `utility_footprint.png` for the full per-utility / per-voltage-tier breakdown.

## B. Capacity Utilization
- 26 active substation(s) flagged as potential upgrade
  candidates (connected line capacity is at least 3x their own rated capacity).
- 15 active substation(s) carry 50%+ of their region's
  total installed capacity — a single-point concentration risk.

## C. Growth Opportunities
- Regions in the bottom quartile by active substation count (thinnest
  infrastructure): **Upper West, Northern, Upper East**.
- This is an infrastructure-density proxy only — no population or land-area
  data was available to weight it against actual demand.

## D. Asset Age Profile
- **Upper West** has the oldest infrastructure on average
  (49.0 years as of 2026).
- Legacy-band (>40 years) substations: 13.

## E. Reliability Proxy
- Highest composite risk-proxy substation: **Winneba Substation**
  (Central, risk score 0.66).
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
