"""Chapter 8 content: results and output screens."""
from __future__ import annotations

from doc_common import CH_LABEL, CHALLENGES, CHARTS, FF, FV, GF, LT, LV, PB, SHOTS, pct

# file, caption, what it shows, shown in the main chapter (True) or only in Appendix C / the results document
SCREENS = [
    ("01_landing.png", "Landing page", "The public front page with the *Student check-in* and *Faculty* actions and live statistics read from `/api/stats` (sessions, check-ins, blocked attempts, students enrolled).", True),
    ("03_about.png", "How it works page", "A public page that explains the six checks (eligibility, device, location, live challenge, identity, duplicate) in the order a student meets them.", False),
    ("04_login_faculty.png", "Faculty sign-in", "Sign-in for faculty with a username or e-mail and a password; a student account used here is refused with a message that names the right portal.", False),
    ("05_login_student.png", "Student sign-in", "Sign-in for students with a roll number or username; the JWT issued on success is bound to the browser's device hash.", True),
    ("06_register_student.png", "Student registration with a reference face", "Registration asks for the name, roll number, password and a reference face photograph (camera or upload). The photo must contain exactly one frontal face with the mouth closed, otherwise the account is not created.", False),
    ("07_checkin_portal.png", "Check-in portal", "A student who has a session link or token pastes it here to open the check-in wizard.", False),
    ("09_create_session.png", "New session form with geo-fence preview", "Faculty enter the course, section, date, start time, duration, the classroom location (browser GPS or manual coordinates), the radius (10-500 m slider) and the allowed roll numbers; the map previews the fence and its 15 m tolerance ring.", True),
    ("10_session_share_qr.png", "Session created: link and QR code", "After creation the page shows the unique link and a QR code to display in class, with a summary of the window, radius and allowed rolls.", True),
    ("11_faculty_dashboard.png", "Faculty dashboard", "KPI tiles (2 sessions, 1 live, 7 check-ins, 11 blocked attempts, 18% blocked), check-ins per session, checks by stage (passed and blocked) and the latest verification attempts with reasons.", True),
    ("12_sessions_list.png", "Sessions list", "All sessions of the signed-in faculty with status, window, present count, expected count and blocked attempts.", False),
    ("13_session_records.png", "Live session: records", "The live session CS604 with 3 present of 5 expected (explicit roll list) and 7 blocked attempts out of 30 checks; the share link and QR code; the records table shows distance, GPS accuracy, challenge, liveness score, identity similarity and the maximum duplicate similarity, and lists absentees.", True),
    ("14_session_map.png", "Session map", "The geo-fence centre (red), the 60 m radius and the 15 m tolerance ring on an OpenStreetMap map, with the check-in positions of the present students (blue).", True),
    ("15_session_log.png", "Verification log", "Every attempt, newest first, with the roll number, stage, PASS or BLOCKED and the reason text; the blocked rows include the out-of-fence, challenge, identity and duplicate-face reasons.", True),
    ("16_session_analytics.png", "Session analytics", "Checks by stage (passed and blocked) and the distance of each present student from the centre, with the mean liveness score and the limit.", False),
    ("17_session_closed_records.png", "Closed session: records", "The closed session CS601: all four students present, with distance 7.7 m for each.", False),
    ("18_session_closed_log.png", "Closed session: verification log", "The log of the closed session, including the proxy attempt blocked as a duplicate face and the visitor whose roll number was not allowed.", False),
    ("19_students.png", "Students", "All students with roll number, enrolment status and number of bound devices, with search and a Manage action.", False),
    ("19b_students_manage.png", "Manage a student", "A drawer with the student's details, a button to remove device bindings and an upload to replace the reference face.", True),
    ("20_checkin_signin.png", "Check-in: sign in", "Step 1 of the student wizard: the session header (course, window, faculty) and the sign-in form.", False),
    ("21_checkin_location_step.png", "Check-in: location", "Step 2: the student taps *Get my location*; the browser fix is shown with its accuracy and the map shows the fence and the student's position.", True),
    ("22_checkin_challenge.png", "Check-in: random challenge", "Step 3: the random challenge ('Turn your head to your LEFT'), three tries left, and the two photo slots, each with a camera tab and an upload tab.", False),
    ("23_checkin_photos_ready.png", "Check-in: photos loaded", "Both photos loaded for a *turn left* challenge. The first photo was accepted as a good neutral frame.", True),
    ("24_checkin_marked.png", "Check-in: marked present", "Step 5: 'Marked. Present.' with the distance (shown as 8 m, 7.7 m in the record), the liveness score (1.00), the identity similarity (0.86, required at least 0.4) and the thresholds that applied.", True),
    ("25_checkin_outside_geofence.png", "Blocked: outside the geo-fence", "A student 556 m from the centre is told 'Outside geo-fence: you are 556 m away, limit is 75 m.' The map shows the position far outside the circle.", True),
    ("26_checkin_static_photo_rejected.png", "Blocked: static photo", "The same photograph submitted twice fails the challenge; the reason reports the measured and required values and a new random challenge is issued with two tries left.", True),
    ("27_checkin_locked.png", "Locked after three failed challenges", "After the third failed challenge the wizard stops and offers *Start over*.", False),
    ("28_checkin_identity_mismatch.png", "Blocked: face does not match", "A student presents another person's photographs; the face step reports that the face does not match the enrolled reference face for this roll number.", True),
    ("29_checkin_duplicate_face_blocked.png", "Blocked: duplicate face", "A second account enrolled with the same face passes the identity check but is stopped by the duplicate scan: 'This face has already marked attendance in this session as 23K91A6706 (similarity 1.00). Proxy attendance blocked.'", True),
    ("31_checkin_roll_not_allowed.png", "Blocked: roll number not allowed", "A student whose roll number is not on the session's list is stopped at the eligibility step.", False),
    ("30_api_docs.png", "Interactive API documentation", "The OpenAPI page generated by FastAPI at `/docs`, listing the 27 endpoints by tag.", False),
    ("32_excel_summary.png", "Excel export: Summary sheet", "Course, section, faculty, window, geo-fence centre, radius, present, absent and blocked-attempt counts.", True),
    ("33_excel_attendance.png", "Excel export: Attendance sheet", "One row per student with status, time, distance, accuracy, challenge, scores and device; absent students from the explicit list are included.", True),
    ("34_excel_verification_log.png", "Excel export: Verification Log sheet", "Every attempt with time, roll number, stage, PASS or BLOCKED, reason and device.", False),
]


def screens_block(d, items):
    for i, (fname, cap, desc, _) in enumerate(items):
        d.p(desc, size=11, line=1.15, keep_next=True, space_after=4)
        w = 5.4
        mh = 3.7
        d.figure(SHOTS / fname, cap, width=w, max_h=mh)


def sec_screens(d, all_screens=False, width=None):
    d.h2("Output Screens")
    d.p("All screens below are real captures of the running application at a width of 1440 px with demo data in it: two sessions, a closed one with four students "
        "present and a live one with three present and seven blocked attempts. Face photographs are public LFW images used as stand-ins for student photographs "
        "(their file names were anonymised) because the project holds no student photographs and no camera was attached; camera capture was replaced by the "
        "application's own *Upload photo* tab. Nothing is mocked up.")
    screens_block(d, [s for s in SCREENS if s[3] or all_screens])


def sec_engine_results(d):
    d.h2("Performance of the Verification Chain")
    d.p("Because nothing is trained, the usual learning curves do not exist. The chain is evaluated by measuring each decision on public images and, for "
        "liveness, by attacking it. All figures come from the scripts in `scripts/eval_*.py`; their raw output is in `docs/evaluation/`.")
    d.h3("Identity and duplicate thresholds (LFW verification protocol)")
    d.p(f"The standard LFW protocol has 6,000 pairs (3,000 same-person and 3,000 different-person). The product's own `embed()` rejected {FF['rejected']:,} of the "
        f"{FF['images']:,} images used ({pct(FF['rate'])}; {FF['reasons']['multiple_faces']:,} as 'more than one face', {FF['reasons']['no_face']} as 'no face'), which removed "
        f"{FV['pairs_dropped_no_single_face']:,} pairs and left {FV['pairs_scored']:,} scored pairs: {FV['genuine_pairs']:,} same-person and {FV['impostor_pairs']:,} different-person. "
        f"Same-person similarity has a mean of {FV['genuine_mean']:.3f} (SD {FV['genuine_std']:.3f}, 5th percentile {FV['genuine_p05']:.3f}); different-person similarity has a mean of "
        f"{FV['impostor_mean']:.3f} (SD {FV['impostor_std']:.3f}) and a maximum of {FV['impostor_max']:.3f}.")
    d.figure(CHARTS / "similarity_hist.png", "Cosine similarity of same-person and different-person LFW pairs with the two deployed thresholds", width=5.6)
    d.table([
        ["Threshold", "Same person accepted", "Same person rejected", "Different person accepted", "Pair accuracy"],
        *[[f"{r['threshold']:.2f}" + (" (identity)" if r["threshold"] == 0.4 else " (duplicate)" if r["threshold"] == 0.45 else ""), pct(r["tar"], 2), pct(r["frr"], 2), pct(r["far"], 2), pct(r["accuracy"], 2)]
          for r in FV["sweep"] if r["threshold"] in (0.20, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60)],
    ], "Behaviour of the similarity threshold on LFW (4,307 scored pairs)", widths=[0.22, 0.20, 0.20, 0.22, 0.16], font=9.5, align=["l", "c", "c", "c", "c"])
    d.p(f"The area under the ROC curve is {FV['auc']:.4f}. The equal error rate is {pct(FV['eer'], 2)} at a threshold of {FV['eer_threshold']:.2f}; the best single threshold on this data is "
        f"{FV['best_accuracy']['threshold']:.2f} with {pct(FV['best_accuracy']['accuracy'], 2)} accuracy; the 10-fold protocol gives {pct(FV['ten_fold_accuracy_mean'], 2)} "
        f"(SD {pct(FV['ten_fold_accuracy_std'], 2)}). The deployed identity threshold of 0.40 accepts {pct(FV['at_identity_threshold']['tar'])} of same-person pairs and none of the "
        f"{FV['impostor_pairs']:,} different-person pairs, because the highest different-person similarity ({FV['impostor_max']:.3f}) is far below 0.40. The duplicate threshold of 0.45 "
        f"flags {pct(FV['at_duplicate_threshold']['tar'])} of same-person pairs as the same face; the remaining {pct(FV['at_duplicate_threshold']['frr'])} would pass undetected when a person "
        "is photographed under very different conditions, which is the false-negative cost of a conservative threshold. The deployed thresholds therefore lie above the "
        "equal-error point and trade a small number of retakes for margin against look-alikes.")
    d.figure(CHARTS / "threshold_sweep.png", "False reject and false accept rates against the similarity threshold", width=5.4)
    d.h3("Liveness challenge")
    n = LV["A_neutral"]
    d.p(f"*Neutral frame.* Of 1,000 random LFW photographs, {n['accepted']} ({pct(n['rate'])}) satisfied the neutral-frame rule; the others were not frontal "
        f"({n['rejected_by']['not_frontal']}), had several faces ({n['rejected_by']['multiple_faces']}), an open mouth ({n['rejected_by']['mouth_open']}) or no face ({n['rejected_by']['no_face']}). "
        "These are press photographs taken for other purposes, so the figure says how strict the rule is, not how often students will pass it.")
    d.figure(CHARTS / "neutral_check.png", "Outcome of the neutral-frame check on 1,000 LFW photographs", width=4.4)
    st = LV["C_static_replay"]
    d.p(f"*Static replay.* When the same photograph is submitted as both the neutral and the challenge frame (329 accepted neutral frames), none passes any head, tilt or "
        f"mouth challenge. Close-eyes is the exception: {st['CLOSE_EYES']['passed']} of {st['CLOSE_EYES']['total']} ({pct(st['CLOSE_EYES']['rate'])}) pass because the photograph already "
        "shows closed eyes (EAR at or below 0.18).")
    d.h3("Attacks on the liveness check")
    r = LV["D_rotation_sweep"]
    d.p("*Rotated photograph.* Rotating a single photograph on screen by a signed angle changes the measured roll by exactly that angle. Rotations within 10 degrees pass "
        "neither tilt challenge; at 12 degrees (the threshold) about half pass; from 15 degrees the matching tilt challenge is passed by 98-99% of the 300 photographs. A student "
        "who holds a phone showing a photograph at a tilt can therefore pass a tilt challenge. The two tilt challenges are two of the eight random challenges.")
    d.figure(CHARTS / "rotation_sweep.png", "Pass rate of the tilt challenges when one photograph is rotated", width=5.2)
    d.p(f"*Photo bank.* An attacker who owns several real photographs of the victim in different poses can pick the pair that fits the issued challenge. On the {PB['victims']} LFW "
        "identities with at least 10 photographs (one photograph held out as the enrolled reference; up to five neutral candidates tried), the full chain "
        "(challenge, frame consistency at least 0.45 and identity at least 0.40) is passed as follows:")
    d.table([
        ["Challenge", "Static replay", "Photo bank: liveness only", "Photo bank: full chain"],
        *[[CH_LABEL[c], pct(LV["C_static_replay"][c]["rate"]), pct(PB["by_challenge"][c]["liveness_only_rate"]), pct(PB["by_challenge"][c]["full_chain_rate"])] for c in CHALLENGES],
    ], "Share of spoofing attempts that pass each challenge", widths=[0.28, 0.20, 0.26, 0.26], font=9.5, align=["l", "c", "c", "c"])
    d.figure(CHARTS / "attack_success.png", "Spoofing attempts that pass each challenge: a stolen photograph, and a bank of photographs", width=6.0)
    d.p("The result is mixed and is stated as such. The random challenge stops a single stolen photograph for seven of the eight actions. It does not stop an attacker "
        "who has collected several photographs of the victim: head-turn challenges are passed by about 94-96% of such attackers, mouth and eye challenges by about half. LFW "
        "identities with ten or more photographs are public figures with large photo collections, so these rates are an upper bound for ordinary students, but social media "
        "photographs make the scenario realistic. The attacker still has to be inside the geo-fence, use the victim's registered device and appear before the session closes; "
        "the system gives three tries and a fresh random challenge each time, so an attacker with a limited bank succeeds with a probability that depends on the draw.")
    d.h3("Geo-fence")
    g = GF["A_haversine_vs_vincenty"]
    d.p(f"The spherical haversine distance differs from the ellipsoidal Vincenty distance by a constant {g[0]['max_rel_error_pct']:.3f}% at latitude 17.385 degrees: "
        f"{g[3]['max_abs_error_m']:.2f} m at 75 m, {g[6]['max_abs_error_m']:.1f} m at 500 m and {g[7]['max_abs_error_m']:.1f} m at 1 km. A boundary sweep with a 60 m radius and 15 m tolerance accepts every point "
        "up to and including 75 m and rejects from 80 m (steps of 5 m); a fix with a reported accuracy of 150 m is accepted and one of 151 m is rejected.")
    d.p("GPS noise matters far more than the formula. A simulation (isotropic Gaussian error with standard deviation sigma per axis, 20,000 trials per point; an *assumed* model, not a field measurement) "
        "gives the probability that a student at a true distance is accepted:")
    kp = GF["C_gps_noise_simulation"]["key_points"]
    d.table([
        ["GPS error sigma", "At 40 m", "At 60 m", "At 100 m", "At 150 m"],
        *[[f"{s} m", pct(v["accept_at_40m"], 1), pct(v["accept_at_60m"], 1), pct(v["accept_at_100m"], 1), pct(v["accept_at_150m"], 1)] for s, v in kp.items()],
    ], "Simulated acceptance probability against GPS error", widths=[0.24, 0.19, 0.19, 0.19, 0.19], font=9.5, align=["l", "c", "c", "c", "c"])
    d.figure(CHARTS / "geofence_noise.png", "Simulated probability of acceptance against true distance for several GPS error magnitudes", width=5.4)
    d.p("With errors of 10 m or less a student standing 60 m from the centre is accepted about 92% of the time or more, and one 100 m away is almost never accepted; with 30 m errors, "
        "typical of indoor reception, 40% of students at 60 m would be rejected and 16% at 100 m accepted. Faculty should set the radius with the building and the "
        "expected GPS quality in mind. Real phone GPS error was not measured.")


def sec_product_results(d):
    d.h2("Application Results")
    d.table([
        ["Item", "Result"],
        ["Automated tests", "23 pytest tests passed; 41 of 41 API smoke checks passed"],
        ["Endpoints / tables / pages", "27 REST endpoints, 5 database tables, 12 React routes"],
        ["Code size", "core/ 1,229 lines, backend 626, Streamlit UI 581, tests 353, React source about 4,470 lines"],
        ["Check-in time (server, median)", f"{LT['C_http_ms']['checkin_total_after_login']['p50']:.0f} ms ({LT['C_http_ms']['checkin_total_after_login']['p95']:.0f} ms at the 95th percentile)"],
        ["Production build", "Vite build in 23 s; largest chunk 581 kB (194 kB gzipped)"],
        ["Demo run (UI)", "Session CS601: 4 present, 4 blocked attempts; session CS604: 3 present of 5 expected, 7 blocked attempts, 30 checks logged"],
        ["Identity similarities in the demo", "0.856, 0.628 and 0.593 for three students (different photographs of each person)"],
    ], "Application results", widths=[0.34, 0.66], font=9.5)


def sec_comparison(d):
    d.h2("Comparison with the Base Paper")
    d.p("The comparison is qualitative and the datasets differ. The base paper [1] reports its own classroom tests with a small, unstated number of students and the LBPH recogniser; "
        "this project reports threshold behaviour on the public LFW protocol with a pre-trained ArcFace recogniser. The figures are not comparable as accuracies and no numerical advantage is claimed.")
    d.table([
        ["Aspect", "Base paper [1]", "Attendance Magic"],
        ["Recogniser", "Haar cascade + LBPH trained on 25-50 images per student", "SCRFD + ArcFace R50, one reference photo per student, no training"],
        ["Reported identity result", "About 92-95% recognition, 5-8% false negatives, 0% false positives (own classroom data)", f"{pct(FV['at_identity_threshold']['tar'])} of same-person LFW pairs accepted, 0 of {FV['impostor_pairs']:,} different-person pairs accepted"],
        ["Speed", "Under 2 s per face", f"{LT['B_stage_ms']['insightface_embed']['p50']:.0f} ms per embedding; {LT['C_http_ms']['checkin_total_after_login']['p50']:.0f} ms for a whole check-in (server)"],
        ["Spoof resistance", "Not described", "Random challenge; single photograph passes 0% of 7 of 8 challenges; rotated and multiple photographs can pass (measured)"],
        ["Presence proof", "None", "GPS geo-fence with tolerance and accuracy gate"],
        ["Duplicate identity", "None", f"Duplicate scan; {pct(FV['at_duplicate_threshold']['tar'])} of same-person pairs flagged at 0.45"],
        ["Interface", "Tkinter desktop application on the classroom computer", "React web application on any browser; also the original Streamlit UI"],
        ["Storage", "CSV files", "Database, attempt log and Excel export with absentees"],
    ], "Comparison with the base paper (different datasets)", widths=[0.20, 0.38, 0.42], font=9)


def sec_samples(d):
    d.h2("Sample Inputs and Outputs")
    d.p("A successful check-in returns the following result (from the demo run; values rounded). The input is a GPS fix inside the fence and two photographs; the output is the "
        "record that appears in the faculty's table and in the Excel export.")
    d.table([
        ["Field", "Value", "Meaning"],
        ["Roll number / name", "23K91A6706 / A. Greeshma", "the signed-in student"],
        ["Distance", "7.7 m", "haversine distance from the fence centre (limit 75 m)"],
        ["GPS accuracy", "12 m", "browser-reported accuracy (limit 150 m)"],
        ["Challenge", "TURN_LEFT, score 1.00", "random challenge and its score"],
        ["Identity similarity", "0.856", "cosine between the live and the enrolled embedding (required at least 0.40)"],
        ["Maximum duplicate similarity", "none", "the first record of the session"],
        ["Device", "34d73fad11b1...", "first 12 characters of the device hash"],
    ], "Sample output of a successful check-in", widths=[0.28, 0.30, 0.42], font=9.5)
    d.p("Examples of blocked outputs from the verification logs of the two demo sessions:")
    d.table([
        ["Stage", "Reason stored"],
        ["location", "Outside geo-fence: you are 556 m away, limit is 75 m."],
        ["liveness", "Tilt left: measured -0.000, required 12.000 - not enough movement, try a bigger motion"],
        ["face (identity)", "Face does not match the enrolled reference face for this roll number (similarity ..., required >= 0.40)."],
        ["face (duplicate)", "This face has already marked attendance in this session as 23K91A6706 (similarity 1.00). Proxy attendance blocked."],
        ["eligibility", "Roll number 24K95A6710 is not allowed in this session."],
    ], "Sample blocked outputs", widths=[0.18, 0.82], font=9.5)


def sec_success_failure(d):
    d.h2("Success and Failure Analysis")
    d.h3("Where the system succeeds")
    d.bullets([
        "A genuine student inside the fence with a correct challenge and a clear photograph is recorded in about 0.56 s of server time.",
        "Forwarded links, remote marking, repeat marking, second devices, disallowed rolls, another person's face and a duplicate face were each blocked at the intended stage in every scripted scenario.",
        "A single stolen photograph fails seven of the eight challenges, and different-person pairs never reached the identity threshold on 2,166 LFW pairs.",
    ])
    d.h3("Where it fails or is weak")
    d.table([
        ["Case", "Observation", "Consequence"],
        ["Rotated photograph", "Passes tilt challenges at 15 degrees or more (98-99%)", "2 of 8 challenges are defeated by one photograph on a tilted screen"],
        ["Photo bank", "Passes the full chain 49-96% depending on the challenge", "A determined attacker with several photos can succeed; mitigated only by the geo-fence, device binding, time window and tries"],
        ["Close eyes with a blinking photograph", "8.2% of still photographs pass", "A photograph that already shows closed eyes passes this challenge"],
        ["Single-face rule", f"{pct(FF['rate'])} of LFW photos rejected", "Retakes needed; a bystander in the frame blocks the check-in"],
        ["Strict neutral frame", f"{pct(LV['A_neutral']['rate'])} of LFW press photos accepted", "Students must look straight, mouth closed"],
        ["Very different photographs of one person", f"{pct(FV['at_identity_threshold']['frr'], 1)} of same-person pairs fall below 0.40", "Rare false rejections; re-enrolment with a better reference photo fixes it"],
        ["Poor GPS", "A 30 m error rejects 40% of students at 60 m (simulation)", "Faculty should use a larger radius indoors"],
    ], "Weak points found by the experiments", widths=[0.26, 0.38, 0.36], font=9)


def sec_results_limits(d):
    d.h2("Limitations of the Results")
    d.bullets([
        "LFW photographs are news images, not selfies; the single-face and frontal-pose rates on student phone photographs are unknown.",
        "No live person performed any challenge. The genuine pass rate of each challenge, the time to complete a check-in and the number of retakes were not measured.",
        "The photo-bank attack uses public figures with many photographs; it is an upper bound for ordinary students.",
        "The GPS results are a simulation under an assumed noise model.",
        "Timings come from one machine that was running other applications; they are indicative.",
        "The comparison with the base paper is qualitative because its data, size and protocol are not given.",
    ])


def sec_objectives(d):
    d.h2("Objectives versus Outcomes")
    d.table([
        ["No.", "Objective", "Outcome", "Evidence"],
        ["1", "Time-bound sessions with configurable geo-fences", "Achieved", "Session form, link and QR, close; screens 09, 10, 13; unit and smoke tests"],
        ["2", "JWT, device identification, roll restrictions", "Achieved", "Token bound to device (401 from another device); device bindings; roll patterns; tests"],
        ["3", "GPS location against the session boundary", "Achieved; field accuracy not measured", "Haversine, tolerance, accuracy gate; boundary sweep; simulation only for GPS noise"],
        ["4", "Liveness by random facial challenge (MediaPipe)", "Achieved with a measured weakness", "8 challenges; single photo fails 7 of 8; rotated and multiple photos can pass; no live-person trial"],
        ["5", "Duplicate identities prevented with InsightFace embeddings", "Achieved", "Duplicate scan; proxy blocked in the UI run; 97.2% same-person pairs flagged at 0.45 (LFW)"],
        ["6", "Attendance summaries and Excel export", "Achieved", "Records, map, log, analytics, 3-sheet Excel with absentees"],
        ["7", "Verification by tests and measurement", "Achieved", "23 pytest tests, 41 smoke checks, LFW threshold evaluation, attack, latency and geo-fence experiments"],
    ], "Objectives against outcomes", widths=[0.06, 0.28, 0.20, 0.46], font=9)
