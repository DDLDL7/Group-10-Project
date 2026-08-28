# GridCare-Lite — User Guide

> Also available as a standalone page: `docs/user-guides/gridcare-lite-guide.html` (open it directly in a browser).

## Installation

```bash
cd gridcare-lite
pip install -r requirements.txt
python main.py
```

The first launch creates `db/gridcare.db`, seeds four demo accounts, and
imports substation/line reference data from `../grid-analysis/data/`.

| Role | Username | Password |
|---|---|---|
| Administrator | `admin` | `Admin123!` |
| Engineer | `engineer` | `Engineer123!` |
| Technician | `technician` | `Technician123!` |
| Customer service | `customer_service` | `Service123!` |

## Logging in

Enter your username and password on the login screen and click **Log In**.
An incorrect username or password shows a clear error without revealing
which part was wrong. After logging in, you'll see a dashboard with only
the actions your role is permitted to perform.

## Engineer

1. **Report New Outage** — pick the affected substation from the list,
   describe the fault, choose a severity (Low/Medium/High/Critical), and
   click **Submit Outage**. The outage starts in status `Open`.
2. **View Outages** — a table of all outages, filterable by region and
   status, that refreshes on demand.

## Administrator

1. **View Outages** — same table as above.
2. **Assign Work Order** — pick an open outage, pick a technician, set a
   scheduled date (`YYYY-MM-DD`), and click **Assign Work Order**. The
   outage automatically moves to `In Progress`.
3. **Reports** — total/open/resolved outage counts, average resolution
   time in hours, and a breakdown of outages by region.

## Technician

**My Work Orders** shows only the work orders assigned to *you*. Select a
row, then:
- **Mark In Progress** — records that you've started the repair.
- **Mark Completed** — marks the work order Completed and automatically
  resolves the linked outage (setting its resolved timestamp).

You cannot update a work order assigned to a different technician, even by
selecting its row — the app checks this independently of what's shown on
screen.

## Customer service representative

1. **View Outages** — same table as above, so you can check whether a
   customer's report matches a known outage.
2. **Log Customer Complaint** — enter the customer's name, optionally the
   outage ID if known, and the complaint text, then **Save Complaint**.

## What happens if something goes wrong

- Selecting **Submit** with a required field empty shows a clear error and
  does not save anything.
- Entering a scheduled date that isn't `YYYY-MM-DD` is rejected before
  anything is written to the database.
- Referencing a non-existent substation or outage ID is rejected with a
  message, not a crash.
- Attempting an action your role doesn't permit (for example, by editing
  the app's code to skip a screen) is still blocked — role checks happen
  in the underlying logic, not just by hiding buttons.

## Logging out

Click **Log Out** on your dashboard at any time to return to the login
screen; any open outage-dashboard/reports/technician-orders windows close
automatically.
