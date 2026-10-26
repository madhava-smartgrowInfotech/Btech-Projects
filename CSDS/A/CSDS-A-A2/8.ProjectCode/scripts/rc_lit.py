"""Chapter 2 content: literature survey."""
from __future__ import annotations


def sec_lit_overview(d):
    d.h2("Overview of the Literature")
    d.paras(
        "The literature relevant to Attendance Magic falls into five groups: (1) face-recognition attendance systems, of which the base paper is "
        "an example; (2) attendance frameworks that add anti-spoofing or liveness checks; (3) the face detection, recognition and landmark models on which such "
        "systems rest; (4) liveness and anti-spoofing methods; and (5) the geodesy and web-security building blocks (distance on the Earth, tokens, "
        "password hashing). This chapter reviews each group, analyses the base paper in depth and ends with the research gap that the project addresses.",
        "A note on evidence. For the base paper the full text was read. For the 2025-2026 attendance works [2]-[5] the survey in the project's own "
        "documents lists title, year and venue; where it was possible to retrieve an abstract online ([3] and [5]) we report what the abstract states, and "
        "where it was not ([2] and [4]) we say so and make no claim about their methods or results.")


def sec_base_paper(d):
    d.h2("Base Paper Analysis")
    d.p("**Dharmaraj K B, Dhanushree C N, Revanth H V, Shashank N and Tejaswini P M, \"Real-Time Student Face Recognition Attendance System Using AI,\" "
        "IARJSET, vol. 12, no. 5, pp. 1067-1072, May 2025, DOI 10.17148/IARJSET.2025.125183 [1].**")
    d.h3("Problem and approach")
    d.p("The paper proposes to automate classroom attendance with face recognition so that students are identified as they appear in front of a webcam. During "
        "registration each student's face is captured from several angles and lighting conditions (the implementation section states 25 to 30 images per student, "
        "and the results section 50 or more) and labelled with the student ID. A recogniser is trained from these images; when a lecture starts, the webcam "
        "scans for faces and, when a match exceeds a confidence threshold, the attendance (student ID, date, time, subject) is logged.")
    d.h3("Method")
    d.table([
        ["Component", "What the paper uses"],
        ["Face detection", "Haar cascade classifier on the live webcam frame; the face is cropped and passed on"],
        ["Face recognition", "Local Binary Pattern Histogram (LBPH) recogniser trained from the registration images; a model file (.yml) is saved"],
        ["Interface", "Python and Tkinter desktop GUI: select subject, start recognition, view attendance, manual entry when recognition fails"],
        ["Feedback", "pyttsx3 text-to-speech announces recognised students and errors"],
        ["Storage", "Subject-wise, timestamped CSV files (or a relational database)"],
        ["Libraries", "Python, OpenCV, Tkinter, NumPy, Pandas, Matplotlib (attendance charts), pyttsx3"],
    ], "Method of the base paper", widths=[0.24, 0.76], font=10)
    d.h3("Reported results")
    d.table([
        ["Measure", "Reported value"],
        ["Recognition accuracy", "About 92-95% under well-lit, frontal conditions"],
        ["False negatives", "About 5-8%, mostly poor lighting or angled faces"],
        ["False positives", "0%: unregistered faces were shown as 'Unknown'"],
        ["Recognition speed", "Under 2 seconds per face; image capture about 1.5 s; training 2-5 s for 10+ students"],
        ["Hardware", "Basic hardware without external servers or a GPU"],
    ], "Results reported in the base paper", widths=[0.34, 0.66], font=10)
    d.p("The paper does not state how many students were tested, how many test images were used or how the accuracy was computed, so the figures can be "
        "taken as indicative of a small classroom test rather than as a benchmark.")
    d.h3("Strengths")
    d.bullets([
        "Simple and inexpensive: the system runs on a laptop with no GPU and no server.",
        "A manual-entry fallback and spoken feedback make it usable by non-technical staff.",
        "Attendance is stored per subject with timestamps and can be charted.",
        "The literature survey inside the paper (Haar+LBPH, CNN+SVM/KNN, VGG16/ResNet transfer learning, FaceNet+MTCNN, end-to-end CNN with a GUI) gives a clear picture of face-recognition choices.",
    ])
    d.h3("Limitations (our reading)")
    d.bullets([
        "**Identity only.** Nothing checks that the face is live. The abstract mentions resistance to impersonation, but the method section describes no liveness, anti-spoofing or challenge step, so a photograph that is recognised would be accepted.",
        "**No location or time-window logic.** Attendance is whatever the webcam in the room sees; there is no session link, no geo-fence and no device or roll restriction.",
        "**No duplicate-identity logic.** Identification is per frame; there is no comparison of new faces with those already recorded in the session.",
        "**Lighting and pose sensitivity.** The paper itself reports misses under poor lighting or angled faces, and LBPH is a texture method that is weaker than modern embedding models on look-alike or masked faces.",
        "**Training per student.** 25-50 images per student and a retraining step are needed whenever a student is added; embedding models need one reference photo.",
        "**Single machine.** A Tkinter application on the classroom computer: no student-side access, no web interface and no remote reporting.",
    ])
    d.h3("What Attendance Magic adopts and changes")
    d.p("Attendance Magic adopts the idea of face-based identity verification and the practical choices of local, GPU-free operation and a manual-friendly "
        "records view. It replaces the Haar+LBPH pipeline by pre-trained ArcFace embeddings [6] (one reference photo, no retraining) and adds what the base paper "
        "lacks: a time-bound session, a geo-fence, a random live challenge, a per-session duplicate check, device binding and an audit log, all delivered "
        "through a browser on the student's own phone.")


def sec_related(d):
    d.h2("Related Work")
    d.h3("Face-recognition attendance systems")
    d.p("The base paper [1] surveys five attendance systems published in 2024, which we summarise as the paper describes them. A Haar cascade with LBPH "
        "achieved over 99% accuracy in controlled conditions but dropped with poor lighting or occlusion. A hybrid of CNN feature extraction with SVM or "
        "KNN classifiers was flexible but computationally heavy. Transfer learning with VGG16 and ResNet coped with lighting and angle variation but needed "
        "substantial hardware. A FaceNet and MTCNN system produced high accuracy but could confuse similar-looking faces, which the authors say calls for "
        "additional verification. An end-to-end CNN system with a simple GUI and database integration was easy to use but reported no accuracy figures. "
        "The common thread is that identity is the only question being asked.")
    d.h3("Attendance with anti-spoofing and liveness")
    d.table([
        ["Work", "What is known", "What is not"],
        ["Shandilya and Shah, IJISRT 2026 [3]", "Smart attendance framework: ArcFace recognition through DeepFace, LBP texture analysis and eye-aspect-ratio blink detection for liveness, HSV colour analysis with K-Means for a dress-code check, parent notification; FastAPI back end, Streamlit dashboard, SQL database. Abstract reports 96.2% recognition, 97.1% liveness reliability for genuine users and 92.4% dress-code accuracy.", "Dataset and protocol beyond the abstract; no geo-fence or duplicate check is mentioned"],
        ["Salam et al., SIML 2025 [5]", "Automatic attendance with silent-face anti-spoofing: the anti-spoofing algorithm combines a CNN and the Fourier transform and runs on a Raspberry Pi 4, assessed in different light and distance conditions.", "Accuracy figures; attendance-session logic"],
        ["Classroom attendance with ResNet101 and ArcFace anti-spoofing, J. Intelligence and Knowledge Engineering 2026 [4]", "Title and venue only (listed in the project survey); the title indicates a ResNet101 anti-spoofing model with ArcFace recognition.", "Abstract could not be retrieved"],
        ["Review of recognition, liveness and dress-code techniques, IJRPR 2026 [2]", "Title and venue only; a review of techniques for smart attendance frameworks.", "Abstract could not be retrieved"],
    ], "Attendance works that add anti-spoofing", widths=[0.26, 0.50, 0.24], font=9)
    d.p("These works show that liveness for attendance is an active topic and that two families dominate: *passive* methods that judge a single image or "
        "frame (texture, frequency, learned anti-spoofing models) and *active* methods that ask the user to do something (blink, turn). Attendance Magic "
        "follows the active family because it needs no additional model and works on any camera, and it chooses the action at random so that it cannot be "
        "prepared in advance.")
    d.h3("Face detection, recognition and landmarks")
    d.bullets([
        "**ArcFace** [6] trains a deep network with an additive angular margin loss so that embeddings of one person cluster tightly on a hypersphere; verification is a cosine comparison. It is the recogniser inside InsightFace's `buffalo_l` model used here.",
        "**SCRFD** [7] is an efficient face detector that redistributes samples and computation across scales; InsightFace uses it as the detector in the same model pack.",
        "**FaceNet** [13] introduced direct embedding of faces with a triplet loss and the verification-by-distance idea that ArcFace later improved; it is the recogniser in one of the systems surveyed in [1].",
        "**MediaPipe Face Mesh** [8] predicts 468 three-dimensional face landmarks in real time on mobile devices; the project uses the landmarks (not the third coordinate) to compute head pose and mouth and eye aspect ratios.",
    ])
    d.h3("Liveness and anti-spoofing")
    d.bullets([
        "**Eye-aspect-ratio.** Soukupova and Cech [10] show that the ratio of eye height to eye width computed from landmarks drops sharply when the eye closes; the project uses it for the close-eyes challenge.",
        "**Blink-based anti-spoofing.** Pan et al. [11] detect eye blinks from an ordinary webcam to reject photographs, an early blink-based method; our challenge asks for a larger, random action instead of waiting for a blink.",
        "**Deep anti-spoofing.** The survey by Yu et al. [12] reviews learned presentation-attack detection (depth, rPPG, texture, domain generalisation) and notes the difficulty of generalising to unseen attack types.",
    ])
    d.h3("Location, tokens and passwords")
    d.bullets([
        "**Haversine.** Sinnott [14] gives the haversine formula for great-circle distance; Vincenty [15] gives the ellipsoidal solution, which we use only to measure how far the sphere approximation is off.",
        "**JWT.** RFC 7519 [16] defines the compact signed token used for sessions; the project adds a device claim and checks it on every request.",
        "**PBKDF2.** RFC 8018 [17] specifies password-based key derivation, used here with HMAC-SHA256 and 200,000 iterations.",
        "**Frameworks.** FastAPI [18], SQLAlchemy [19] and React [20] are the building blocks of the application.",
    ])
    d.h3("Dataset used for evaluation")
    d.p("Labeled Faces in the Wild (LFW) [9] is the standard unconstrained face-verification benchmark: 13,233 images of 5,749 people collected from news photographs, "
        "with a protocol of 6,000 labelled pairs. It is used here because it provides many different photographs of the same person, which is what an "
        "enrolment-versus-check-in comparison needs, and because it is public and reproducible.")


def sec_lit_algorithms(d):
    d.h2("Datasets and Algorithms Used in the Literature and in this Project")
    d.table([
        ["Task", "Algorithms in the literature", "Chosen for Attendance Magic", "Why"],
        ["Face detection", "Haar cascade [1]; MTCNN [1]; SCRFD [7]", "SCRFD (InsightFace)", "Accurate on small and non-frontal faces; bundled with the recogniser; CPU ONNX"],
        ["Face recognition", "LBPH [1]; FaceNet [13]; ArcFace [6]", "ArcFace R50, 512-d, cosine", "No per-student training; margin-trained embeddings separate identities; one reference photo"],
        ["Liveness", "Blink [11]; LBP + EAR [3]; CNN + Fourier [5]; deep models [12]", "Random active challenge on Face Mesh metrics", "No extra model; any camera; unpredictable; transparent thresholds"],
        ["Location", "Haversine [14]; ellipsoidal geodesics [15]", "Haversine + 15 m tolerance + accuracy gate", "Error 0.47% at campus scale, far below GPS noise; simple"],
        ["Session security", "Server sessions; JWT [16]", "JWT with device claim; PBKDF2 [17]", "Stateless API; token useless on another device"],
        ["Evaluation data", "Own classroom data [1]; LFW [9]", "LFW protocol and stills", "Public, reproducible, many photos per person"],
    ], "Algorithms in the literature and the choices made", widths=[0.15, 0.27, 0.26, 0.32], font=9)


def sec_lit_strengths(d):
    d.h2("Strengths and Limitations of Existing Approaches")
    d.table([
        ["Approach", "Strengths", "Limitations"],
        ["Haar + LBPH [1]", "Light, fast, no GPU", "Pose and light sensitive; per-student training; identity only"],
        ["CNN / transfer learning [1]", "Higher accuracy under variation", "Heavy; needs training data and hardware"],
        ["Embedding models (FaceNet, ArcFace) [6], [13]", "One reference photo; robust; cosine verification", "Can still be fooled by a photograph of the person"],
        ["Blink or LBP liveness [3], [11]", "Passive or nearly passive; cheap", "Replay of a video with blinks; no knowledge of location"],
        ["CNN + Fourier anti-spoofing [5]", "Learns spoof artefacts; runs on a Raspberry Pi", "Needs a trained model and data; narrower than a full attendance flow"],
        ["Shared link / QR", "Instant; works from phones", "No proof of who or where"],
    ], "Strengths and limitations of existing approaches", widths=[0.28, 0.32, 0.40], font=9.5)


def sec_gap(d):
    d.h2("Research Gap")
    d.p("Face-recognition attendance systems verify identity but rarely combine location verification, liveness challenges and duplicate-identity checks "
        "within one time-bound session. Specifically:")
    d.numbered([
        "The base paper [1] and the systems it surveys answer only *who is this face?*; no presence, liveness or duplicate-identity check is described.",
        "Recent anti-spoofing frameworks [3], [5] add a liveness module but, as far as their abstracts show, not a geo-fence, a roll restriction or a per-session comparison of the faces already recorded.",
        "Shared-link systems are fast but prove neither identity nor presence.",
        "Reported evidence is thin: small classroom tests in [1] and abstract-level figures elsewhere; we found no measurement of how a liveness challenge behaves against rotated or multiple photographs of the same person.",
    ])
    d.p("Attendance Magic fills this gap with a single session in which all checks are performed in sequence and logged, and it measures the thresholds and "
        "the weaknesses of its own checks on a public benchmark.")
