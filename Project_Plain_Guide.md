# What We Are Building — Plain Guide

This explains what each part of the project actually does, without the technical words. Use this to explain the project to anyone, including people with no coding background.

## The project in one paragraph

We are building three connected pieces of work. One studies how Ghana's electricity grid is laid out and finds weak points in it. The other two are small working apps. One helps an electricity company track and fix power outages. The other helps a clinic manage patients, their tasks, and communication with their doctor. All three come from the same idea: take real information, understand it, then build something useful with it.

## Part 1: Grid Network Analysis

**What it is:** A study of how Ghana's electricity network is connected.

**What it does:** We take information about power stations (called substations) and the power lines that connect them. We look for patterns. Which areas have the most power stations. Which stations connect to the most other stations. Which parts of the country might be underserved.

Then we treat the whole grid like a map of connections, similar to how a map of roads shows which towns connect to which. Using this map, we can find the stations that matter most. If one of those important stations went down, we test what would happen to the rest of the network. Would it still work, or would parts of the country lose connection completely?

**Why it matters:** A real electricity company needs to know which parts of their network are fragile, so they know where to invest in backup connections. This is a small, safe version of the kind of study a real utility company does before deciding where to build a new line or upgrade an old station.

**What comes out of it:** Charts, an interactive map you can click around on, and a short report explaining what we found.

## Part 2: GridCare-Lite

**What it is:** A small desktop app for managing power outages, like an internal tool an electricity company's staff would use, not something customers see.

**What it does:** When there's a power outage, someone logs it into the app, saying which station is affected and how serious it is. A manager then assigns someone to go fix it and schedules the work. The person fixing it updates the app as they go, from "just started" to "fixed." Customer complaints can also be logged and linked to the outage causing them.

**Who uses it:** Four kinds of staff, each seeing only what they need. An engineer who reports problems. A manager who assigns the work. A technician who does the repair. A customer service person who handles complaints.

**Why it matters:** This is the kind of software that sits behind the scenes at a real utility, keeping track of what's broken, who's fixing it, and how long it takes, so nothing falls through the cracks.

## Part 3: ClinicCare-Lite

**What it is:** A small web app for a clinic to manage patients and communicate with them. It does not do anything medical. It never diagnoses, never gives medical advice, and never looks at symptoms. It only handles admin and messages.

**What it does:** A doctor (clinician) can give a patient a task, for example, "submit your blood pressure readings for this week." The patient uploads a file with that information. The doctor reviews it and marks it as normal, needs a follow-up, or something more urgent, then writes a short note. The patient sees that outcome and gets notified. Doctors and patients can also send each other simple, non-urgent messages, and the doctor can post announcements to all patients, like a clinic closing for a holiday.

Patients also get a private tracker showing their own progress, like how many tasks they completed on time. This is only visible to that one patient. It is never used to compare patients against each other, because that would expose private health information.

**Why it matters:** A lot of clinic communication (appointment reminders, form submissions, follow-up notes) doesn't need a doctor's direct attention every time. This app handles that admin side so the clinic runs smoother, while keeping the actual medical judgment fully in the doctor's hands.

## How the three parts connect

The station and line information from the Grid Network Analysis feeds directly into GridCare-Lite, so outages can only be logged against real, existing power stations. The two software apps, GridCare-Lite and ClinicCare-Lite, share the same underlying ideas, logins, different roles seeing different screens, tracking a task from start to finish, but they serve two very different worlds. One is about equipment and infrastructure. The other is about people and privacy. Building both shows we can apply the same core skills to different kinds of real-world problems.
