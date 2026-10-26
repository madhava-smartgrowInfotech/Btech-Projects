"""Build 19.IEEE_Paper.docx: a six-page, two-column IEEE conference paper on Attendance Magic.

    python scripts/build_paper.py        then   python scripts/paper_finish.py   (page count + PDF through Word)

Every number comes from docs/REPORT_FACTS.md and docs/evaluation/*.json (all measured on 2026-10-15 on one CPU-only desktop).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paper_kit as K  # noqa: E402
from doc_common import BATCH, ROOT  # noqa: E402

OUT = BATCH / "19.IEEE_Paper.docx"
PAPER = ROOT / "docs" / "paper"

K.TITLE = "Attendance Magic: Geo-Fenced Attendance with Live Challenge Verification and Measured Spoofing Limits"
K.ABSTRACT = (
    "Classroom attendance is still taken by roll call or by links and QR codes that can be forwarded to absent students, and "
    "face-recognition systems answer only who a face is, not whether a live person is present at the right place. This paper "
    "presents Attendance Magic, a browser-based system in which a faculty member opens a time-bound, geo-fenced session and a "
    "student checks in from a phone through a fixed chain: eligibility and device binding, a GPS geo-fence, a random live facial "
    "challenge judged on face-mesh landmarks, and ArcFace identity and duplicate-face checks. Nothing is trained; pre-trained "
    "models run on a CPU. On the Labeled Faces in the Wild protocol the identity check reached an AUC of 0.9992 and accepted "
    "no impostor pair at its deployed thresholds. A static photo failed seven of eight challenges, but a rotated photo passed "
    "the tilt challenges and an attacker holding several photos of the victim passed the full chain in 49% to 96% of trials "
    "depending on the challenge. A complete check-in took a median of 564 ms of server time after sign-in."
)
K.KEYWORDS = "attendance system, face verification, geo-fencing, liveness detection, photo-bank attack, random challenge"


def build():
    P = K.Paper()
    P.front()
    P.abstract()

    # ---------------------------------------------------------------- I
    P.h1("I. Introduction")
    P.para("Attendance decides whether a student may sit an examination and is the first sign that a student is falling behind, yet the "
           "way it is captured is a trade-off between time and trust. Calling the roll costs teaching minutes and invites a friend to "
           "answer for an absentee. A shared link or QR code is fast but proves neither who is using it nor where they are, because it "
           "can be forwarded or photographed. Camera-based recognition removes the roll call, but a recognised face on a webcam is not "
           "proof of a live person, and nothing in it ties the person to the classroom. The base paper [1] describes such a desktop "
           "system, built on a Haar cascade and an LBPH recogniser, that logs attendance to subject-wise files; the questions of liveness, "
           "location and duplicate identities are left open.")
    P.para("This paper presents Attendance Magic, in which a faculty member creates a time-bound session with a geo-fence and a list of "
           "allowed roll numbers, and each student completes a short check-in on their own phone. Its contributions are:", after=2)
    P.numbered([
        "a single check-in chain of eligibility and device binding, geo-fence, random live challenge, identity match and a per-session "
        "duplicate-face check, with every stage logged and a plain reason given for every refusal;",
        "an application with a React front end, a thin FastAPI back end of 27 endpoints and a faculty view of records, map, log, analytics and Excel export;",
        "a calibration of the face thresholds on the 6,000-pair LFW protocol [9] with the real pipeline;",
        "a measured account of what the liveness challenge does not stop: a rotated photo and a bank of photos of the victim.",
    ])
    P.para("Section II reviews the literature, Section III describes the method, Section IV reports measurements and Section V concludes.", before=2)
    P.h2("A. System Hardware")
    P.para("All measurements were taken on one desktop with an Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB of memory, no "
           "discrete GPU (the integrated graphics were not used) and Windows 11 Pro. Other desktop applications were running, so "
           "timings carry some variance.")
    P.h2("B. Software Requirements")
    P.para("The back end runs on Python 3.11.9 with FastAPI [18], SQLAlchemy [19] over SQLite, PyJWT, MediaPipe 0.10.21 [8], InsightFace "
           "2.0 with ONNX Runtime 1.31 on the CPU, OpenCV and openpyxl. The front end is React 19 [20] with Vite, Leaflet and Recharts. "
           "Tests use pytest 9.1.1.")

    # ---------------------------------------------------------------- II
    P.h1("II. Literature Survey")
    P.para("**Base paper.** Dharmaraj et al. [1] automate attendance with a webcam. Each student registers 25 to 30 face images (50 or "
           "more in the results section); a Haar cascade detects faces and an LBPH recogniser trained on the registrations identifies "
           "them; a Tkinter interface, spoken feedback and subject-wise CSV files complete the system. They report about 92-95% accuracy "
           "in well-lit frontal conditions, 5-8% false negatives, 0% false positives and under 2 s per face, but state neither the "
           "number of students tested nor how accuracy was computed. Their method has no liveness, location or duplicate-identity "
           "step, and a new student means retraining.")
    P.para("**Attendance with anti-spoofing.** Shandilya and Shah [3] combine ArcFace recognition, LBP texture analysis and blink "
           "detection with a dress-code check and report, in the abstract, 96.2% recognition and 97.1% liveness reliability for genuine "
           "users. Salam et al. [5] use a CNN with the Fourier transform for silent anti-spoofing on a Raspberry Pi. A ResNet101 and "
           "ArcFace classroom system [4] and a review of smart-attendance techniques [2] are in our batch survey, but we could read "
           "only their titles and so state no result for them. None of the works we could read mentions a geo-fence or a comparison "
           "against faces already recorded in the session.")
    P.para("**Recognition, landmarks and liveness.** FaceNet [13] and ArcFace [6] map faces to embeddings compared by distance or "
           "cosine; ArcFace's angular margin tightens identity clusters, and its detector companion SCRFD [7] finds small faces. "
           "MediaPipe Face Mesh [8] gives 468 landmarks in real time on mobile devices. The eye aspect ratio [10] falls sharply when an "
           "eye closes, and blink detection from an ordinary webcam [11] was an early defence against photographs; Yu et al. [12] survey "
           "learned presentation-attack detection and note poor generalisation to unseen attacks. For location, the haversine formula "
           "[14] is the usual spherical distance and Vincenty's method [15] the ellipsoidal reference. Labeled Faces in the Wild [9] "
           "is the standard unconstrained verification benchmark.")
    P.para("**Passive and active liveness.** Liveness checks fall into two families. Passive methods judge a single image or frame by "
           "texture, frequency content or a learned model [3], [5], [12]; they need no action from the user but need a trained model "
           "and data, and they generalise poorly to attacks unseen in training [12]. Active methods ask the user to do something, such "
           "as blink [11] or close the eyes [10]; they work on any camera with a landmark model, but a replayed video can contain the "
           "action. Attendance Magic follows the active family and makes the action random, so that it cannot be prepared in advance, "
           "and it then measures how far that choice protects it.")
    P.para("**Earlier attendance systems.** The base paper [1] also summarises five 2024 systems: a Haar and LBPH system that reached "
           "over 99% in controlled light but fell with poor lighting or occlusion, a CNN with SVM or KNN classifiers that was flexible "
           "but heavy, VGG16 and ResNet transfer learning that needed substantial hardware, a FaceNet [13] and MTCNN system that could "
           "confuse similar faces and so called for extra verification, and an end-to-end CNN with a GUI that reported no accuracy. In "
           "every case identity is the only question asked.")
    P.table([["Work", "Approach", "Data", "Reported result", "Limitation"],
             ["[1] base paper", "Haar + LBPH, Tkinter, CSV", "Own classroom set", "92-95% accuracy", "Identity only; no liveness"],
             ["[3] 2026", "ArcFace, LBP, blink, dress code", "Not read", "96.2% recog.; 97.1% liveness", "No geo-fence in abstract"],
             ["[5] 2025", "CNN + Fourier anti-spoof", "Not read", "Not read", "Hardware-bound; no session logic"],
             ["[4], [2] 2026", "ResNet101 + ArcFace; review", "Not retrieved", "Not retrieved", "Titles only"],
             ["[11] 2007, [10] 2016", "Blink; eye aspect ratio", "Webcam video", "Not reproduced", "Replayed blinks; no location"],
             ["This work", "Session chain + random challenge", "LFW pairs", "AUC 0.9992", "Photo-bank attack"]],
            "Related work", widths=[0.16, 0.25, 0.17, 0.22, 0.20], size=6.5)
    P.para("**Location, tokens and passwords.** The haversine formula [14] gives great-circle distance on a sphere and is accurate to "
           "a fraction of a percent at campus scale, so Vincenty's ellipsoidal solution [15] is needed here only as a yardstick. "
           "Stateless JSON Web Tokens [16] suit a REST back end, and PBKDF2 [17] with a high iteration count is the standard "
           "defence for stored passwords. The attendance systems above do not describe binding a token to a device, which is what "
           "stops a signed-in session from being handed to a classmate's phone.")
    P.para("**Gap.** The reviewed systems verify identity, and some add a liveness module, but we found none that joins a "
           "time-bound faculty session, a geo-fence, a random challenge, a per-session duplicate-face check and a device restriction in "
           "one logged chain, and none that measures how its own liveness check fails.")

    # ---------------------------------------------------------------- III
    P.h1("III. Methodology")
    P.h2("A. Architecture and Flow")
    P.para("Fig. 1 shows the architecture. The React app captures the camera image and the GPS fix and sends the device identifier and "
           "a bearer token; the FastAPI layer is thin and calls the core services, which hold all rules; five SQLite tables store "
           "users, sessions, records, device bindings and a log of every verification attempt. MediaPipe Face Mesh and InsightFace "
           "buffalo_l (SCRFD detector, ArcFace-R50 recogniser, 512-d embeddings) are used as released: no model is trained or "
           "fine-tuned here. Fig. 2 gives the check-in flow, in which every stage must pass and writes a log row.")
    P.figure(PAPER / "fig1_architecture.png", "System architecture of Attendance Magic.", width=3.4)
    P.figure(PAPER / "fig2_flow.png", "Main check-in flow with deployed thresholds.", width=3.4)
    P.h2("B. Eligibility, Device Binding and Security")
    P.para("A check-in starts only if the session is live, the signed-in user is a student whose roll number matches a faculty pattern, "
           "no record exists yet and the device has not marked another roll in the session. The device hash is a SHA-256 of the user-agent, "
           "language and client-hint headers plus a browser identifier; a student may bind one device. Passwords use PBKDF2-HMAC-SHA256 "
           "with 200,000 iterations [17]; the session token is a JWT [16] carrying the device hash and is rejected from any other device.")
    P.h2("C. Geo-Fence")
    P.para("The distance between the reported fix (φ₂, λ₂) and the session centre (φ₁, λ₁) is the haversine distance [14] with R = 6,371 km:")
    P.eq("d = 2R · asin √( sin²(Δφ/2) + cos φ₁ cos φ₂ sin²(Δλ/2) )", 1)
    P.para("A fix is accepted if d ≤ r + 15 m, where r is the faculty radius (default 60 m), and the reported GPS accuracy is at most 150 m.", indent=False)
    P.h2("D. Random Live Challenge")
    P.para("The server draws one of eight challenges: turn left or right, look up or down, tilt left or right, open the mouth or close "
           "the eyes. The student takes a neutral photo and a challenge photo. Face Mesh landmarks give the yaw, the pitch, the roll "
           "and the mouth and eye aspect ratios; for example")
    P.eq("yaw = (x_{nose} − x_{L}) / (x_{R} − x_{L}) − 0.5", 2)
    P.para("The neutral photo must contain one face with |yaw| ≤ 0.10 and a mouth aspect ratio MAR ≤ 0.25. The challenge passes if the "
           "change from the neutral photo reaches the threshold: |Δyaw| ≥ 0.12, Δpitch ≥ 0.08, Δroll ≥ 12°, MAR ≥ 0.35 or eye aspect ratio "
           "EAR ≤ 0.18. The liveness score is min(1, measured/threshold). A failure issues a new random challenge, and three failures lock the wizard.", indent=False)
    P.h2("E. Identity and Duplicate Check")
    P.para("Both photos are embedded and L2-normalised; similarity is the cosine, s = e₁ · e₂. Exactly one face is required in each "
           "photo (a second face is tolerated only if narrower than half the largest). Three tests must pass: the two photos show the "
           "same person (s ≥ 0.45), the live face matches the enrolled reference (s ≥ 0.40), and the maximum similarity to any other "
           "embedding recorded in the session stays below 0.45, so one person cannot mark two rolls. The decision is a deterministic "
           "threshold rule, chosen so that every refusal can be explained to the student; the thresholds are calibrated in Section IV.")

    P.h2("F. Decision Rule and Operating Point")
    P.para("Taking a check-in as accepted only when all stages pass, the decision can be written as")
    P.eq("A = E ∧ (d ≤ r + 15) ∧ L ∧ (s_{c} ≥ 0.45) ∧ (s_{id} ≥ 0.40) ∧ (max_{j} s_{j} < 0.45)", 3)
    P.para("where E is eligibility, L the challenge outcome, s_c the frame-consistency similarity, s_id the identity similarity and s_j the "
           "similarity to the j-th embedding already recorded in the session. A conjunction can only lower acceptance, so each "
           "added stage trades a possible retake for a closed route to a proxy. The two similarity thresholds are checked against the LFW "
           "protocol in Section IV-B. The duplicate threshold is the higher one: two photographs of the same person score "
           "far above it (a repeated photograph scored 1.00 in the demonstration), whereas two different people scored near zero (impostor mean 0.004).", indent=False)
    P.h2("G. Application and Implementation")
    P.para("The 27 endpoints fall into four groups: health, configuration, statistics and QR generation; authentication (login, "
           "registration with a reference face, token check); faculty routes for sessions, dashboard, students, export and device reset; and "
           "the student wizard (state, start, location, neutral photo, liveness, face, retake, reset). The wizard state is kept on the "
           "server for each student, so a client cannot skip a stage, and eligibility is checked again immediately before the record "
           "is written. A unique constraint on (session, student) makes a second record impossible even if two requests race. A session "
           "is upcoming, live, expired or closed according to its window and a close flag; times are stored in UTC and shown in "
           "Asia/Kolkata. Every stage writes a row with its reason to the log, and the Excel export has three sheets: summary, "
           "attendance and verification log. All thresholds live in one configuration file and can be overridden through the "
           "environment. A weakness we keep is the placeholder default for the token-signing secret, which must be replaced before a real deployment.")
    P.para("The design follows three choices. Deterministic thresholds on landmarks and cosine similarity were preferred to a learned "
           "spoof classifier because every refusal can then be explained to the student and no spoof data set is needed. Pre-trained "
           "embeddings were preferred to per-student training because one reference photo suffices and adding a student needs no "
           "retraining. A thin API over a service layer was preferred because the same services also serve the original Streamlit interface, "
           "which is kept and covered by two interface tests.")

    # ---------------------------------------------------------------- IV
    P.h1("IV. Results")
    P.h2("A. Test Conditions")
    P.para("No model was trained, so there is no training split; the figures evaluate pre-trained components inside the product's "
           "own functions. Identity thresholds were measured on the LFW verification protocol [9]: 6,000 pairs over 7,701 images. "
           "The product rejects an image unless it has exactly one face, which dropped 1,208 images (15.7%) and left 4,307 scored pairs "
           "(2,141 genuine, 2,166 impostor). LFW images are cropped press photographs, not selfies, so the retake rate on real "
           "phone selfies was not measured. No live person or camera took part: liveness was studied with still photographs only.")
    P.para("Every measurement can be repeated: one script per experiment (verification, liveness, photo-bank attack, geo-fence and latency) "
           "writes a JSON file next to the documentation, the thresholds are read from the same configuration the product uses, and the "
           "random seed of the neutral-frame sample is fixed (7). The LFW archive is downloaded separately and is not redistributed. "
           "Latency figures come from 40 repetitions per stage on the machine described in Section I-A.")
    P.h2("B. Identity and Duplicate Thresholds")
    P.table([["Measure", "Result"],
             ["Identity AUC / EER (threshold 0.19)", "0.9992 / 0.30%"],
             ["10-fold accuracy (LFW protocol)", "99.82% ± 0.22"],
             ["At 0.40 (identity): TAR / FAR", "98.69% / 0.00%"],
             ["At 0.45 (duplicate): TAR / FAR", "97.15% / 0.00%"],
             ["Largest impostor similarity", "0.246"],
             ["Neutral frames accepted (1,000 LFW images)", "32.9%"],
             ["Static photo, tilt/turn/look/mouth", "0% pass"],
             ["Static photo, close eyes", "8.2% pass"],
             ["Rotated photo, tilt, ≥ 15°", "98-99% pass"],
             ["Photo-bank attack, full chain", "48.7-95.5%"],
             ["Haversine error vs Vincenty", "0.47% (0.35 m at 75 m)"],
             ["AI time per check-in, p50 / p95", "368 / 525 ms"],
             ["Server time after sign-in, p50 / p95", "564 / 806 ms"],
             ["Tests: pytest / API smoke", "23 / 23; 41 / 41"]],
            "Measured results (CPU only, LFW stills)", widths=[0.64, 0.36], size=7)
    P.para("The genuine similarities averaged 0.673 (SD 0.107) and the impostor similarities 0.004 (SD 0.058). At the deployed identity "
           "threshold of 0.40 no impostor pair of 2,166 was accepted, since the largest impostor score was 0.246, while 1.3% of genuine "
           "pairs would need a retake. At 0.45 a second roll marked with the same person's face is caught in 97.2% of cases; "
           "the remaining 2.8% pass undetected. The thresholds are therefore conservative against the EER point of 0.19, "
           "trading some retakes for safety (Fig. 3a).")
    P.figure(PAPER / "fig3_results.png", "(a) Genuine and impostor acceptance against threshold; (b) photo-bank attack success.", width=3.4)
    P.para("The one-face rule explains the dropped pairs: 1,197 images contained more than one face and 11 none. This matters for "
           "deployment because a retake is the only cost, but the retake rate on real selfies is unknown. When the same person was "
           "photographed differently in the interface run, identity similarities were 0.59 to 0.86, comfortably above 0.40. Embedding "
           "an image took a mean 281 ms (p95 547 ms) while other jobs loaded the machine and a median of 176 ms on a lightly loaded one.")
    P.h2("C. Liveness and Attacks")
    P.para("Of 1,000 random LFW images, 32.9% satisfied the neutral-frame rule (499 were not frontal, 92 had several faces, 79 an open "
           "mouth), which is a property of press photographs rather than of cooperating students. Replaying one photo as both frames "
           "failed every challenge except close-eyes, which 8.2% of photos passed because the eyes were already closed. Two attacks "
           "defeat the check. Rotating a photo on screen changes the measured roll by exactly the rotation: rotations within ±10° "
           "passed 0% of the time, 12° passed 51% and 15° or more passed 98-99% of tilt challenges. Second, an attacker who holds "
           "several photos of the victim in different poses can choose the pair that fits the challenge; against the full chain, "
           "including frame consistency and a held-out enrolled photo, 154 victims with at least ten photos were passed in "
           "95.5% (turn left), 94.2%, 79.9%, 72.7%, 70.1%, 69.5%, 48.7% and 52.6% of trials (Fig. 3b) with up to five neutral "
           "candidates. These are public figures with many photographs, so an ordinary student is probably safer, but the result "
           "shows that a random challenge stops a single stolen photo, not a prepared bank. Because the challenge is random and three tries are "
           "allowed, an attacker still needs the easy challenge to be drawn. The genuine-user pass rate was not measured.")
    P.para("On the neutral frames that passed, the measured yaw had mean 0.001 and SD 0.053, the pitch 0.354 (SD 0.055), the roll −0.9° "
           "(SD 6.9°), the mouth aspect ratio 0.095 (SD 0.086) and the eye aspect ratio 0.283 (SD 0.069). The tilt threshold of 12° is "
           "therefore about 1.7 standard deviations of the roll spread across neutral photographs, so a deliberate tilt is detectable "
           "while a modest rotation of a photo is also enough to reach it. The close-eyes threshold of 0.18 lies well below the natural eye aspect ratio of "
           "0.283, which is the margin that keeps open eyes from passing.")
    P.h2("D. Geo-Fence and Performance")
    P.para("The boundary sweep accepted every distance up to 75 m and refused from 80 m; a GPS accuracy of 150 m was accepted and 151 m "
           "refused. Real phone GPS error was not measured. A simulation with Gaussian error of 10 m per axis accepted a student at "
           "60 m in 92.3% of trials and one at 100 m in 0.5%; at 20 m error these became 72.3% and 8.5%, so indoor drift can turn "
           "honest students away and the faculty radius should allow for it. The haversine distance differs from Vincenty by a "
           "constant 0.47%. Of the check-in, InsightFace embedding dominates at 176 ms (p50) per photo; a 5,000-face duplicate scan "
           "takes 41 ms. Model loading is 0.81 s for Face Mesh and 1.55 s for InsightFace. Latency was measured in-process, so network time is excluded; "
           "no concurrency test was done.")
    P.para("Through the API on the same machine (in-process client, 40 complete check-ins, p50 / p95), login took 105 / 123 ms, the "
           "eligibility step 12.6 / 14.8 ms, the location step 8.0 / 9.8 ms, the liveness step with two uploads 23.1 / 26.6 ms and the "
           "face step including the record 521 / 759 ms, so the face stage, which contains two embeddings and the duplicate scan, "
           "accounts for about nine tenths of a check-in. The challenge mathematics itself costs 4 microseconds. The duplicate scan "
           "grows linearly with the session: 0.14 ms for 10 faces, 5.7 ms for 500 and 11.9 ms for 1,000. A loaded machine raised the "
           "InsightFace median to 277 ms, so the timings should be read as indicative.")
    P.h2("E. Testing and Output Screens")
    P.para("The pytest suite (23 tests) and the end-to-end API smoke test with the real models (41 checks) all passed. In a "
           "scenario matrix of ten cases one genuine check-in passed and nine proxy attempts were stopped at the intended stage: "
           "a repeat mark, a student 556 m away, a static photo, another person's face, one face under a second roll, a roll not on "
           "the list, a second device, a token used from another device and three failed challenges. Fig. 4 shows the success screen "
           "of a real session run (distance 8 m, liveness 1.00, identity 0.86) and Fig. 5 a refused attempt with the reason given "
           "and two tries left. The faces in the screens are LFW stand-ins, since no student photographs were stored.")
    P.figure(PAPER / "fig4_marked.png", "Check-in success: distance, liveness and identity scores.", width=3.4)
    P.figure(PAPER / "fig5_rejected.png", "Refused challenge with reason and tries left.", width=3.4)
    P.para("In the interface run with two sessions, the closed session CS601 recorded 4 of 4 students present and 4 blocked attempts "
           "(outside the fence, a static photo, a duplicate face and a roll not allowed); the live session CS604, with an explicit list of "
           "five rolls, had 3 present, 7 blocked attempts and 30 checks logged. A failed liveness stage fails closed: the student sees "
           "the measured value and the required value, for example an eye aspect ratio of 0.244 against 0.180, and receives a new challenge.")
    P.para("Failure cases follow from these numbers. A genuine student can be turned away by a one-face rule (a second face wider than "
           "half the largest, or none), by an eye aspect ratio that stays above 0.18 when the eyes are not shut firmly, by GPS drift near "
           "the fence edge, or by a similarity below 0.40, which affected 1.3% of genuine LFW pairs. In every case the screen states the "
           "measured value and the limit and issues a retry; after three failed challenges the wizard locks and the student starts again. "
           "An attacker is stopped by a single stolen photograph (in seven of the eight challenges), by a second device, by a forwarded link without a matching roll and "
           "device, and by a second roll marked with the same face, but not by the two attacks of Section IV-C.")
    P.h2("F. Comparison with the Base Paper")
    P.para("The base paper [1] reports 92-95% accuracy on its own classroom images with a Haar and LBPH pipeline; this work reports "
           "verification on LFW pairs with ArcFace embeddings. The datasets, protocols and tasks differ, so no number here is "
           "claimed to beat theirs. The comparison is of scope: [1] answers who the face is, whereas this system also checks presence, "
           "location, liveness and duplicates and measures its own weaknesses. Observed limits are the 15.7% of LFW images that the "
           "one-face rule rejects, the tilt and photo-bank attacks, simulated rather than field GPS, a single-process SQLite server and "
           "no user study.")

    # ---------------------------------------------------------------- V
    P.h1("V. Conclusion")
    P.para("Attendance Magic turns attendance into a time-bound, geo-fenced session in which a student must be eligible, inside the "
           "fence, respond to a random facial challenge and match an enrolled face that no one else has already used. Against the six "
           "objectives, all stages are implemented, tested (23 of 23 tests, 41 of 41 smoke checks) and logged, and a check-in needs "
           "about 0.56 s of server time after sign-in on a CPU. The main finding is double: the identity thresholds separate people "
           "cleanly on LFW (AUC 0.9992, no impostor accepted at 0.40), yet the liveness challenge is only as strong as the attacker's "
           "photo collection, and a rotated photo defeats the tilt challenges. Other limits are the absence of a live-person trial, "
           "field GPS data, HTTPS phone tests and load tests.")
    P.para("Objectives against outcomes: time-bound geo-fenced sessions, JWT with device and roll restrictions, the GPS check, the random "
           "liveness challenge, the duplicate-identity check and the summaries with Excel export are all implemented and were exercised end to end. "
           "What is not shown is equally clear: that genuine students pass the challenges at an acceptable rate, that phone GPS behaves "
           "as the simulation assumes, and that the system survives many simultaneous check-ins.")
    P.para("Practical use follows from the findings. The face thresholds can stay as deployed; the tilt challenges should be "
           "dropped or paired with a screen-reflection check; the radius should be set above the expected GPS error of the room; and "
           "the system should be treated as one layer, with spot roll calls for sessions that matter.")
    P.para("Future work: texture or depth anti-spoofing and a live video challenge; removing tilt challenges or checking for screens; "
           "a user study measuring genuine pass rates and retakes; GPS-spoof detection and field calibration of the radius; and "
           "HTTPS deployment with a server database and load testing.")

    P.references()
    P.d.core_properties.title = K.TITLE
    P.d.core_properties.author = "Batch A2"
    P.d.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    build()
