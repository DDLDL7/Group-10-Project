# ClinicCare-Lite — User Guide

> Also available as a standalone page: `docs/user-guides/clinicare-lite-guide.html` (open it directly in a browser).

**Reminder:** this system is administrative and communication only. It does
not diagnose, interpret symptoms, or recommend treatment. Any automated
check on your submission only confirms a form was filled in correctly.

## Installation

```bash
cd clinicare-lite
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in a browser.

## Registering

1. Click **Register**.
2. Choose whether you're a **Clinician** or **Patient**.
3. Enter your 8-digit ID:
   - Clinicians: must end in `0000` (e.g. `12340000`).
   - Patients: must end in your registration year, 2022–2028 (e.g.
     `12342024`).
4. Patients only: enter the **clinician ID of the clinic you're joining**
   (a clinician must have already registered).
5. Enter your name, email, and a password (8+ characters, with an
   uppercase letter, lowercase letter, digit, and special character
   `!@#$%^&*`).
6. Log in with your new ID and password.

## Clinician guide

- **Dashboard**: patient count, task count, pending-review count, recent
  announcements.
- **+ New health task**: title, instructions, due date, assign to one of
  your registered patients, and (optionally) list the CSV/TXT column
  names you expect — used only for the structural completeness check.
- **Submissions**: filter by task/patient/status. **Preview** shows a CSV
  as a table or a TXT file as plain text (no preview for PDFs — download
  instead). **Review** lets you set a categorical outcome (`Pending`,
  `Reviewed — Normal`, `Needs Follow-up`, `Escalated`) plus free-text
  notes; the patient is notified automatically.
- **Messages**: one non-urgent conversation thread per patient. A
  persistent notice reminds both sides this channel isn't monitored
  continuously and isn't for emergencies.
- **Announcements**: post a clinic-wide notice, optionally emailing every
  registered patient.
- **Appointments**: schedule an appointment for a patient and update its
  status (`Scheduled`/`Attended`/`No-show`/`Cancelled`) — this feeds the
  no-show-rate analytic.
- **Analytics**: clinic-wide aggregates only — task completion rate,
  pending reviews, overdue submissions, average review turnaround,
  appointment no-show rate, and a monthly task-volume chart. Never a
  per-patient comparison.

## Patient guide

- **My Tasks**: every task assigned to you, its due date, and its status.
  Click **Submit** (or **View / resubmit**) to upload a `.txt`, `.csv`, or
  `.pdf` file (5 MB max). If the file looks structurally incomplete (e.g.
  a missing expected column), you'll see a note — this is not a medical
  assessment, only a form check.
- Once reviewed, you'll see the outcome and any clinician notes directly
  on your task list.
- **Messages**: a non-urgent conversation with your clinic's clinician,
  with the same "not monitored continuously" notice.
- **My Progress**: your own private engagement points, on-time/late task
  completion counts, and appointment attendance — visible only to you,
  never compared with any other patient.
- Toggle between **dark** and **colorful** themes from the navigation bar
  at any time.

## What happens if something goes wrong

- A weak password, a malformed ID, or a duplicate account ID is rejected
  with a clear message before anything is saved.
- An unsupported file type, an empty file, or a file over 5 MB is
  rejected before it's stored.
- Trying to reach another patient's task, submission, or conversation (by
  guessing a URL, for example) returns a "you don't have permission"
  page, not the data.
- Trying to reach a clinician-only or patient-only page as the wrong role
  is blocked the same way.
