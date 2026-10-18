"""Shared text used by the decks, the chapter documents, the report and (in condensed form) the paper: objectives and the literature table."""

# from 6.OBJECTIVES&PROBLEM STATEMENT.docx, verbatim
OBJECTIVES = [
    "Build a dataset of hand gesture images covering the target sign alphabet and common words.",
    "Preprocess images with segmentation, resizing and augmentation to improve generalisation.",
    "Design and train a CNN architecture for gesture classification.",
    "Optimise the model for real-time inference from a live camera feed.",
    "Convert recognised signs into on-screen text and synthesised speech output.",
    "Evaluate accuracy, per-class performance and inference latency on unseen signers.",
]

PROBLEM_POINTS = [
    "Communication between deaf and hearing people breaks down without a human interpreter.",
    "Interpreters are scarce, costly and unavailable for everyday spontaneous interaction.",
    "Recognition accuracy degrades with background clutter, lighting change and unseen signers.",
    "Many published systems classify static images only and cannot run in real time.",
]

PROBLEM_STATEMENT = ("Given a live webcam stream of a signer's hand, recognise the ASL fingerspelling letter being shown (and the control signs "
                     "space and delete), turn the letters into a sentence on screen and speak it aloud, fast enough to follow the signer and with "
                     "a stated, measured accuracy - through an application that a non-expert can run.")

# (Work, Approach, Data, Reported result, Limitation); only facts from the base paper or checked sources
LIT_TABLE = [
    ["Vo et al. 2026 [1] (base paper)", "MAG-KD: a small skeleton GCN student distilled from three GCN teachers with a hard correctness mask and an adaptive gate",
     "AUTSL (38,336 videos, 43 signers, 226 signs); WLASL-100", "94.25 +/- 0.19 % Top-1 on AUTSL with 0.48 M parameters; 66.33 +/- 0.54 % on WLASL-100; 33.13 FPS at 6.23 W on a Jetson Nano",
     "Needs a pose estimator in front of it; correctness mask needs ground-truth labels; video word signs, not fingerspelling"],
    ["Starner et al. 1998 [4]", "Hidden Markov models over features from a desk-mounted or wearable camera", "Sentence-level ASL video, restricted vocabulary",
     "Early real-time ASL recognition (figures not quoted here)", "Restricted vocabulary and grammar"],
    ["Pugeault and Bowden 2011 [5]", "Colour and depth from a Kinect sensor, Gabor-filter features, classification of fingerspelled letters", "ASL fingerspelling captured with a depth camera",
     "Real-time letter recognition (figures not quoted here)", "Needs a depth sensor"],
    ["Bheda and Radpour 2017 [6]", "Deep convolutional network on images of ASL letters and digits", "Static images of ASL letters and digits",
     "CNNs can classify static fingerspelling images (figures not quoted here)", "Static images only; no live pipeline"],
    ["Camgoz et al. 2018 [16]", "Neural sign language translation: sign video to spoken-language text", "Continuous sign video with sentence translations",
     "First end-to-end neural video-to-text translation (figures not quoted here)", "Needs large annotated video corpora"],
    ["Sincan and Keles 2020 [14]", "AUTSL: multi-modal Turkish Sign Language dataset with baselines", "38,336 videos, 43 signers, 226 signs, Kinect V2",
     "Benchmark used by the base paper", "Turkish signs, not ASL letters"],
    ["Li et al. 2020 [15]", "WLASL: word-level ASL video dataset and method comparison", "Large word-level ASL video collection",
     "Benchmark used by the base paper (WLASL-100 subset)", "Words in video; heavy models"],
    ["Rastgoo et al. 2021 [3]; Al Abdullah et al. 2024 [2]", "Surveys of deep-learning sign language recognition", "Review of datasets and methods",
     "Map the field: static, isolated-word and continuous recognition", "Reviews, no system of their own"],
]
