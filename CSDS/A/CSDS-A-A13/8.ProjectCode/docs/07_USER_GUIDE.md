# User guide

A walkthrough of every screen. Start SeatWise with `run.bat` and open http://localhost:5113.

Every screen works from phone width (360 px) up. Lists show skeletons while loading, a helpful message when empty, and a *Try again* button when something fails. The sun/moon button switches between light, dark and system theme.

---

## Home page (`/`)

The public front page:

- The **Get started** button takes you to sign-in, or straight to your dashboard if you are signed in.
- **Find my seat** leads to the candidate lookup.
- The figures below the hero are the latest engine benchmark results: conflicts avoided, solve time, roll-to-seat correlation and number of runs.

## Sign in and request an account (`/login`, `/register`)

- **Sign in** with email and password. While demo accounts are enabled, **Demo workspace** buttons sign you in as the exam controller or as an invigilator in one click.
- **Request an account** creates an invigilator account in *Waiting for approval*. An administrator approves it under **Team**; until then sign-in explains that the request is pending.

## Dashboard (`/app`)

**Administrators** see:
- **Getting started** steps, until they are all done: import, generate, publish, attendance.
- The **hero figure**: same-paper neighbours avoided across published sittings compared with roll-order seating.
- Tiles for candidates seated, sittings published, average solve time, attendance, plans meeting every rule, and halls.
- **Attendance by sitting** and **Solve time per plan** charts.
- The list of **Sittings** with their plan status and share marked.
- **Busiest halls**.

Every chart has a table view (the grid icon).

**Invigilators** see their **next hall** with a *Take attendance* button, and their totals.

## Import data (`/app/import`)

1. **What are you importing?** Choose *Everything* (a workbook with Courses, Halls, Candidates and Timetable sheets), or a single kind. Import courses before candidates and the timetable, because they refer to course codes.
2. **How should it be applied?**
   - *Add and update* (the default) adds new rows and updates rows whose code already exists.
   - *Replace existing* removes everything of that kind first. This is refused while plans exist.
3. **Upload the file.** Drop it on the area or click to choose. SeatWise checks every row immediately; nothing is saved yet.

The **report** shows, for each sheet, the rows, new and updated counts, and badges for errors and warnings. The problems table gives the sheet, row, column and what to fix. Errors block the import. Warnings do not: for example, a hall without accessible seats gets the front-row default. **Preview** shows the first rows as SeatWise read them. Click **Import N rows** to apply. The data is checked again at that moment in case something changed.

**Templates & samples** offers empty templates (one per kind, or combined) and the fictional sample data. **Recent imports** lists every upload and whether it was applied.

Checks include: required columns, formats, duplicate codes and IDs, unknown departments or courses, seat labels outside the layout, seats both blocked and accessible, aisle positions, end time before start, a shared-paper group split over sittings, a candidate with two papers in one sitting, and sittings larger than all halls together.

## Data (`/app/data`)

| Tab | What it shows |
|---|---|
| **Candidates** | Search by roll number or name, filter by department, page through. Click a row for courses and published seats. ♿ marks candidates who need an accessible seat. |
| **Courses** | Course, department, number of candidates, sitting and shared-paper group. |
| **Halls** | A card per hall with a mini layout (accessible seats highlighted, blocked seats outlined, aisles as gaps), seats, accessible seats and the *per paper* ceiling - the most candidates of one paper that fit without neighbours sharing it. The switch makes a hall available or unavailable for new plans. |
| **Timetable** | Every sitting with its papers and candidate counts, and a link to plan it. |

## Sittings & plans (`/app/sessions`, `/app/sessions/:id`)

The list shows every sitting with its candidates, papers and plan status.

**Generate a plan:**

1. **Rules.** The summary line shows the defaults; click *Change* to adjust them for this plan:
   - neighbours: 8 or 4
   - roll-number gap
   - department mix
   - hall usage: compact or balanced
2. **Halls.** All available halls are ticked; untick any you cannot use. The line under the heading warns if the seats are fewer than the candidates.
3. **Random seed.** Draw a new one, or type a seed - for example one drawn in front of witnesses.
4. **Generate plan.** Progress stages are shown while the engine works (a few seconds). If a plan is impossible, you get the reason and what to change. For example: *"Paper X has 180 candidates, but the selected halls can seat at most 150 of them without two neighbours writing it. Select more halls or switch to 4-neighbour adjacency."*

**Plan versions:** each generation creates a new version, and older versions stay until you delete them. The selected version shows:

- **Actions:**
  - *Seat maps*
  - *Publish*: candidates can then look it up, and invigilators see their halls. Publishing replaces the previously published version.
  - *Verify*: re-runs the engine with the stored seed and confirms the result is identical.
  - *Exports*
  - *Delete*: drafts and replaced versions only.
- **Scorecard:**
  - same-paper neighbours
  - roll-gap violations
  - conflicts avoided compared with roll-order seating
  - accessible seating
  - solve time
  - halls used and seats filled
- **Halls table:** seats used, papers (colour-coded), and an **invigilator** picker per hall. Each invigilator can supervise only one hall per sitting. SeatWise assigns invigilators automatically and evenly.
- **Audit fingerprints:** input data, engine result, current seating (which changes after manual moves) and engine version.

## Seat maps (`/app/plans/:plan/halls/:hall`)

- The **front of the hall** is at the top; rows are lettered from the front and seats numbered from the left. Aisles are gaps, dashed hatched seats are not in use, and ♿ marks accessible seats.
- Each seat shows its label, roll number and course. The coloured top edge and tint show the paper, and the legend lists the papers with counts. Click a paper in the legend to highlight it.
- **Find a candidate** highlights a seat by roll number or name. The **- / +** buttons change the seat size, and on phones the map scrolls inside its panel.
- **Moving candidates** (administrators, current versions):
  - *Drag* a candidate onto another seat, or *tap* a seat and then the destination. The keyboard works too: Tab to a seat, Enter to pick it up, Enter on the destination, Esc to cancel.
  - While a candidate is picked up, every other seat turns **green** (the move keeps every rule) or **red**. Point at a red seat to read why: same paper next door, roll numbers too close, or not an accessible seat for someone who needs one.
  - Dropping on a red seat is refused with the reason. Dropping on a green seat moves the candidate, or swaps if the seat is taken. Every move is written to the audit trail.
- The side panel shows the selected candidate, the move verdict, and the hall's figures and invigilator.
- **Chart PDF** downloads this hall's seating chart.

Invigilators can open their own halls read-only.

## Exports (`/app/exports`)

Choose a plan (published or draft) and **All halls** or one hall, then download:

| Export | Contents |
|---|---|
| **Seating charts** (PDF) | One landscape page per hall: the grid colour-coded by paper with roll numbers, the paper legend, the invigilator, and a stamp with plan version, seed and seating fingerprint. |
| **Hall-wise lists** (Excel) | A summary sheet, one sheet per hall (seat, roll number, name, department, course, accessible, signature), and a **Door list** in roll-number order. |
| **Invigilator sheets** (PDF) | Per hall: papers and counts, instructions, and the seat-by-seat list with *Present* and *Signature* columns. |
| **Seat slips with QR codes** (PDF) | Six per page: name, roll number, course, when, hall, building, seat, and a QR code that opens the candidate's lookup page. |
| **Attendance report** (Excel) | Present, absent and not-marked counts by hall and course, and per candidate who marked them and when. |

## Attendance (`/app/attendance`, `/app/attendance/:plan/:hall`)

The list shows the halls you supervise (administrators see all of them), grouped by sitting, with progress bars. Open a hall to take attendance. The screen is built for tablets:

- **Counters:** present, absent and to mark.
- **Scan or type:** the box keeps focus.
  - A hand-held QR/barcode scanner types the slip's code and presses Enter, which marks the candidate present.
  - You can also type a roll number.
  - SeatWise tells you if the candidate sits in another hall, and where.
  - Where the browser allows the camera, a **Camera** button scans slips directly.
- **List view:** large *Present* / *Absent* buttons for each seat. Tap again to clear a mark.
- **Seat map view:** tap a seat to cycle present, absent, cleared.
- **Filters and search:** *To mark*, *Present*, *Absent*, and a search box.
- **Bottom bar:**
  - **Mark remaining absent** (with confirmation).
  - **Submit** locks the register once everyone is marked. An administrator can **Reopen** it.

The screen refreshes every few seconds, so several devices and the controller's dashboard stay in step.

## Find my seat (`/lookup`, `/lookup/:id`)

This page is public; no sign-in is needed.

1. Enter a candidate ID (roll number). Letter case does not matter.
2. For every **published** exam, you see:
   - whether it is upcoming, today or completed
   - date and time, course
   - the **seat** in large type, the hall, building and floor
   - a mini map of the hall with your seat highlighted, and a sentence such as *"Row C, seat 4 from the left, facing the front"*
3. **Seat slip (PDF)** downloads the slip with its QR code; **QR code** shows the code on screen.

Only a shortened name is shown ("Maya F."), and never an email or date of birth. Lookups are rate-limited per device.

## Analytics (`/app/analytics`)

| Tab | What it shows |
|---|---|
| **Plans** | Choose a plan to see: SeatWise compared with roll-order seating (same paper, roll gap, accessible, same department), seats filled per hall, departments in each hall, and attendance per hall. |
| **Engine performance** | The latest benchmark: hard rules satisfied, solve time for a typical sitting, conflicts avoided compared with roll order, roll-to-seat correlation, charts (solve time by size, same-paper pairs by method, predictability), the full results table, time-budget tuning, run details and the charts saved with the run. |

## Audit trail (`/app/audit`)

Every plan (with its seed), failed attempt, publication, verification, seat move, invigilator change, export, import, rule change, account change and attendance submission, newest first. Filter by type or open a single plan's history. Entries cannot be edited.

## Team (`/app/team`)

- **Waiting for approval:** approve or decline invigilator requests.
- **Accounts:** role, status and last sign-in. The ⋯ menu makes a person an administrator or invigilator, resets their password, or disables and enables the account. The last active administrator cannot be removed.
- **Add person** creates an active account with a temporary password.

## Settings (`/app/settings`)

| Section | What it does |
|---|---|
| **Default seating rules** | Neighbours (8 or 4), roll-number gap, department mix, hall usage, and accessible seats per hall (used when a hall file lists none). Each plan keeps a copy of the rules it was made with. |
| **Reset workspace** | Deletes all exam data - candidates, courses, halls, timetable, plans, attendance - after you type RESET. Accounts, settings and the audit trail stay. |
