# Legacy exploratory scripts

These are early, individual exploratory scripts from team members working
through the Week 1–2 tasks before the analysis was consolidated into the
tested `src/` package + `notebooks/` + `dashboard.py`. They're kept here
(rather than deleted) as evidence of individual contribution and working
history, per the project's contribution-evidence requirement — but they
are **not** the supported/current pipeline.

For the current, tested analysis, use:

- `../src/cleaning.py`, `../src/geo.py`, `../src/network.py`,
  `../src/business_intelligence.py` — the reusable, tested modules
- `../notebooks/01`–`04` — the walkthrough notebooks
- `../dashboard.py` — the interactive Streamlit dashboard
- `../REPORT.md` — the written findings report

Each script here reads from `../data/*.csv` and writes its charts to
`outputs/` (this folder's own `outputs/`, not `../outputs/`) so they can
still be run standalone from inside `legacy_scripts/` if needed:

```bash
cd legacy_scripts
python examined_data.py
```
