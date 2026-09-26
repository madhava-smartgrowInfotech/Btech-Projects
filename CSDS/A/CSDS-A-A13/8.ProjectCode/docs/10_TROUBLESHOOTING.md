# Troubleshooting

Start with the automatic check, which tells you what is wrong with the machine or `.env`:

```bat
venv\Scripts\python scripts\check_env.py --network
```

## Installing

| Problem | Fix |
|---|---|
| `setup.bat` says **Python 3.11 was not found** | Install Python 3.11 from python.org (64-bit installer) and tick *Add python.exe to PATH*. Run `setup.bat` again. `py -3.11 --version` should print 3.11.x. |
| **Node.js was not found** | Install the LTS version from nodejs.org, then open a *new* Command Prompt so the PATH is refreshed. |
| `pip` or `npm` fails with network errors | The first setup needs internet. Check the connection or proxy, then run `setup.bat` again - it resumes where it stopped. |
| `npm warn allow-scripts ... esbuild` | Already handled: `frontend/package.json` allows esbuild's install script. If you see errors about esbuild, delete `frontend\node_modules` and run `setup.bat` again. |
| Antivirus quarantines files in `venv` or `node_modules` | Allow the SeatWise folder, then run `setup.bat` again. |

## Starting

| Problem | Fix |
|---|---|
| **Port 8113 (or 5113) is already in use** | SeatWise may already be running: run `stop.bat`, then `run.bat`. If another program uses the port, close it. SeatWise always uses its own ports and never picks another one. |
| **SeatWise did not start in time** | Look at the two SeatWise windows for the error message. The usual cause is a missing setup step - run `setup.bat`. |
| API window: `JWT_SECRET in .env is missing or too short` | Run `setup.bat` (it generates one), or set a random value of at least 32 characters. |
| Web window stopped with `EBUSY ... watch` | Windows briefly locked a source file (for example while an editor or antivirus touched it). Close the window and run `run.bat` again. |
| Browser shows *Cannot reach the SeatWise server* | The API window was closed or stopped. Run `run.bat` again. |
| Blank page after an update | Stop SeatWise, delete `frontend\node_modules\.vite`, and start again. |

## Using

| Problem | Fix |
|---|---|
| Import says **Department X is unknown** / **Unknown course code(s)** | Import the courses first (or use the combined workbook, which imports in the right order). |
| Import says **... are both in the sitting ... but N candidates take both** | A candidate cannot sit two papers at once: move one course to another sitting in the timetable. Courses that really are one paper should share a `paper_group`. |
| **The data changed since this file was checked** | Something was imported after the check. Upload the file again. |
| **A plan could not be generated: ... usable seats** | Select more halls (or mark halls available under **Data > Halls**). |
| **... can seat at most N of them without two neighbours writing it** | One paper is too large for the selected halls under the neighbour rule. Add halls, or use 4-neighbour adjacency for that plan. |
| **... need an accessible seat but the selected halls have N** | Mark more accessible seats in the hall layouts (re-import halls) or select more halls. |
| Generation takes longer than usual | Very large sittings and 4-neighbour adjacency take longer (see the benchmark). `SOLVER_THREADS=0` uses every CPU thread. |
| **This move is not allowed** on the seat map | The reason is in the message: same paper next door, roll numbers too close, or someone who needs an accessible seat. Choose a green seat. |
| **This plan no longer meets every rule** | Candidates or registrations changed after the plan was made (someone has no seat). Generate a new version. |
| Plan cannot be published or deleted | Only drafts can be published; a published plan is replaced by publishing another version; plans with attendance are kept for the record. |
| **Verify** says the data changed | Candidates, halls or rules changed after the plan was made, so the seed now gives a different plan. That is expected - the stored seating is unaffected. |
| Invigilator sees **No halls assigned** | The plan must be **published** and the invigilator assigned to a hall (plan page > Halls > Invigilator). |
| **Attendance for this hall has been submitted** | The register is locked; an administrator can **Reopen** it. |
| Candidate lookup finds nothing | Only published plans are visible. Check the ID and that the sitting's plan is published. |
| **Too many lookups from this device** | Wait a minute. The limit is `LOOKUP_RATE_LIMIT_PER_MINUTE` in `.env`. |

## Tablets and phones

| Problem | Fix |
|---|---|
| The tablet cannot open `http://<pc-ip>:5113` | Both devices must be on the same network. Allow Node.js through Windows Firewall on private networks: *Windows Security > Firewall > Allow an app*. |
| QR codes on slips open `localhost` on phones | Set `PUBLIC_BASE_URL=http://<pc-ip>:5113` in `.env`, restart, and print the slips again. |
| No **Camera** button on the attendance screen | Browsers allow the camera only on `localhost` or HTTPS. Use a hand-held scanner (it types into the scan box) or type the ID. |

## Resetting

| Goal | How |
|---|---|
| Clear exam data | **Settings > Reset workspace**. |
| Brand-new database | `stop.bat`, then `venv\Scripts\python scripts\init_db.py --reset`. |
| Forgotten admin password | Another admin can reset it under **Team**. Otherwise reset the database (demo accounts are recreated). |

## Logs

- API: the *SeatWise API* window and `logs\seatwise.log` (rotating; one line per event, including every request with its status and duration).
- Web: the *SeatWise web* window.
- Browser: press F12 and open the Console.
