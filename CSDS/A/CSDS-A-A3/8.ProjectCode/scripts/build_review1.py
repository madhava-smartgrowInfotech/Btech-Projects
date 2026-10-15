"""Build 7.Review_1_PPT.pptx from D:\\abstracts\\Templates\\Review_1_PPT.pptx (16 slides)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deckkit import (fill, put_picture, replace_chart, replace_everywhere, set_notes, set_paras, set_table, shape, style_chart, table_size)  # noqa: E402
from doc_common import (BATCH, BASE_PAPER, COLLEGE, DEPT, DIAG, GUIDE, GUIDE_DESIG, PRODUCT, REFERENCES, STUDENTS, TITLE, YEAR)  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.util import Emu  # noqa: E402

SRC = r"D:\abstracts\Templates\Review_1_PPT.pptx"
OUT = BATCH / "7.Review_1_PPT.pptx"
KEYWORDS = "phishing detection, URL classification, crowdsourced threat intelligence"


def build():
    prs = Presentation(SRC)
    S = list(prs.slides)
    replace_everywhere(prs, {"The Hidden Risk of Social Media": PRODUCT})
    cp = prs.core_properties
    cp.title, cp.subject, cp.author, cp.keywords = f"{PRODUCT}: Review 1", TITLE, "Batch A3", KEYWORDS
    cp.category = cp.comments = cp.content_status = ""
    cp.last_modified_by = "Batch A3"

    # 1 title
    s = S[0]
    set_paras(shape(s, 2), PRODUCT)
    set_paras(shape(s, 3), TITLE, 26)
    set_paras(shape(s, 6), [f"{n}  {r}" for n, r in STUDENTS], 15)
    set_paras(shape(s, 8), f"{GUIDE}, {GUIDE_DESIG}")
    set_paras(shape(s, 9), [DEPT, f"{COLLEGE}  \u00b7  Batch A3 (CSE-DS, Section A)  \u00b7  {YEAR}"], 13)
    set_notes(s, "Review 1 covers problem identification and research for PhishGuard, a phishing URL detection system that combines machine learning with crowdsourced threat intelligence.")

    # 2 contents (tiles unchanged)
    set_notes(S[1], "Nine parts: the abstract, the base paper and related work, existing approaches, the gap, the problem statement and objectives, the approach, expected outcomes and references.")

    # 3 abstract
    s = S[2]
    set_paras(shape(s, 2), "Abstract: a detector that keeps learning")
    fill(s, 8, "Phishing sites steal credentials by imitating trusted pages, and new domains appear daily and live only hours. Blacklists miss zero-day URLs, fixed rules are easy to evade, and models trained once go stale.", 16)
    fill(s, 13, "Follow the base paper's three stages: extract lexical, structural and domain features from the URL, classify with machine learning (Random Forest, XGBoost, Logistic Regression), and refine the system with crowdsourced threat intelligence.", 16)
    fill(s, 18, "A web application that checks a URL in real time, explains the verdict, accepts community reports, imports public feeds and retrains itself, with the best model reloaded without a restart.", 16)
    set_notes(s, "The abstract in one slide: the problem of static detection, the three-stage idea of the base paper, and the system we deliver.")

    # 4 base paper
    s = S[3]
    fill(s, 5, BASE_PAPER, 14)
    set_paras(shape(s, 7), "Method")
    fill(s, 8, "Three phases: Extractor (URL features; known patterns answered directly), Detection (ML classifier; unknown inputs flagged as novel) and Updating by crowdsourcing (novel URLs verified by a human, added to the training set, model retrained). Model: LSTM with attention plus a dense branch.", 14)
    set_paras(shape(s, 10), "Data and reported results")
    fill(s, 11, "PhiUSIIL dataset, 235,804 URLs, 54 features (34 kept). Reported accuracy 99.8 %, F1 0.9988; 5-fold cross-validation; learning-curve simulation of crowd data growth; about 0.20 ms per URL.", 14)
    set_paras(shape(s, 13), "Limits and future work")
    fill(s, 14, "One dataset; crowd loop only simulated; real-world validation needed. Future work: scalability, defences against adversarial misuse of the crowd channel, multimodal and multilingual input, privacy and explainability.", 14)
    set_notes(s, "The base paper is a framework paper: its headline number is 99.8 % on one benchmark, and its crowd loop is evaluated by simulation. Our implementation is smaller and URL-only.")

    # 5 literature survey
    s = S[4]
    rows = [["Work", "Approach", "Data", "Reported result"],
            ["Aldhuwayhi and Alromih, 2026 (base) [1]", "LSTM-attention + dense network; crowd feedback loop", "PhiUSIIL, 235,804 URLs", "Accuracy 99.8 %, F1 0.9988"],
            ["Vajrobol et al., 2024 [6]", "Mutual information + logistic regression", "PhiUSIIL", "99.97 % with 5 features (per [1])"],
            ["Etem and Teke, 2024 [7]", "t-SNE reduction + decision tree", "51-feature URL set", "99.7 % (per [1])"],
            ["Alnemari and Alshammari, 2023 [8]", "Classical classifiers; Random Forest best", "UCI phishing domains", "97.3 % (per [1])"],
            ["Priya et al., 2024 [11]", "Random Forest / LR browser extension", "11,055 URLs", "97 % (per [1])"],
            ["Assefa and Katarya, 2022 [14]", "Autoencoder, 16 features", "Small URL set", "91.24 % (per [1])"],
            ["Batch survey [2]-[5]", "Phishing URL detection with ML, DL and RL, 2023-2025", "Not retrieved", "Listed by title only"]]
    sz = table_size(rows, 1164, 460, [0.26, 0.32, 0.2, 0.22], 13, 9)
    set_table(shape(s, 6), rows, sz, header_size=sz)
    set_notes(s, "Rows [6] to [14] are described as summarised in the base paper. Works [2] to [5] come from the batch survey; their abstracts were not retrieved, so no results are claimed for them.")

    # 6 supporting evidence
    s = S[5]
    set_paras(shape(s, 2), "Supporting evidence: ML works on static benchmarks")
    cats = ["Vajrobol [6]", "Rathee [10]", "Base paper [1]", "Etem [7]", "Fan [13]", "Alnemari [8]", "Priya [11]", "Assefa [14]"]
    vals = [99.97, 99.87, 99.80, 99.70, 99.16, 97.30, 97.00, 91.24]
    ch = replace_chart(s, 4, cats, [("Reported accuracy (%)", vals)], number_format="0.0")
    style_chart(ch, "Reported accuracy of related work on static datasets (%)", ["3F3FBF"], number_format="0.0", legend=False, label_pt=9, axis_title="accuracy (%)")
    ch.value_axis.minimum_scale = 85
    ch.value_axis.maximum_scale = 100
    set_paras(shape(s, 8), "Takeaway")
    fill(s, 9, "Machine learning on URL and related features reaches 91 % to 99.97 % on public benchmarks, so classifiers can recognise phishing without a blacklist.", 15)
    set_paras(shape(s, 13), "Caveat")
    fill(s, 14, "All figures are reported by the authors on different, static datasets and were taken from the base paper's survey; they are not a common benchmark and say little about new attacks.", 15)
    set_notes(s, "The accuracies are those quoted in the base paper for each work. They support the choice of ML but also show the gap: every number comes from a fixed dataset.")

    # 7 existing system
    s = S[6]
    set_paras(shape(s, 2), "Existing system and current approaches")
    steps = ["Link received", "Check blacklist", "Apply fixed rules", "Block or allow", "User reports site", "Staff update list"]
    for sid, t in zip((5, 8, 11, 14, 17, 20), steps):
        fill(s, sid, t, 14)
    set_paras(shape(s, 24), "Blacklists and manual reports")
    fill(s, 25, "Browsers and mail filters check a URL against lists such as Google Safe Browsing and PhishTank. A site is blocked only after someone reports it and the list is updated by hand.", 16)
    set_paras(shape(s, 29), "Rules and one-time models")
    fill(s, 30, "Rule-based filters flag fixed patterns such as IP hosts or keywords. Some systems use a classifier trained once on a fixed dataset and never updated.", 16)
    set_notes(s, "How links are checked today: lists, fixed rules and models that are trained once.")

    # 8 limitations
    s = S[7]
    set_paras(shape(s, 2), "Limitations of existing methods")
    for tid, bid, ttl, body in [
        (7, 8, "Zero-day blind spot", "A blacklist cannot detect a URL that has not been reported yet."),
        (12, 13, "Slow updates", "Manually updated databases lag behind campaigns whose domains live only hours."),
        (17, 18, "Easy to evade", "Fixed rules break with small changes to the URL; models trained once degrade as patterns evolve."),
        (22, 23, "False positives", "Legitimate sites get blocked, which reduces user trust.")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 16)
    set_notes(s, "Four limitations from the batch survey: zero-day blindness, slow updates, easy evasion and false positives.")

    # 9 research gap
    s = S[8]
    gaps = [("Static data", "Most detectors train once on historical datasets, so they are obsolete on arrival [1]."),
            ("No adaptation", "Few systems retrain automatically from new threat data."),
            ("Crowd unused", "Collective user reports are rarely a live, structured input to the model [1]."),
            ("Evidence", "Reported accuracy comes from fixed benchmarks; real-world validation is still missing."),
            ("Explanation", "Systems that give a bare label do not tell the user why a link is suspicious.")]
    for (lid, tid), (lab, txt) in zip([(5, 6), (8, 9), (11, 12), (14, 15), (17, 18)], gaps):
        set_paras(shape(s, lid), lab)
        fill(s, tid, txt, 17)
    set_notes(s, "Research gap: static blacklist-based detection fails on zero-day URLs, and few systems combine lexical, structural and domain features with continuously updated crowdsourced threat feeds.")

    # 10 problem statement
    s = S[9]
    fill(s, 5, "Given a URL, produce a verdict (phishing, suspicious or safe) with a probability and an explanation, using a classifier trained on labelled URLs and a store of community-confirmed verdicts that can override the classifier and feed its retraining; and serve it in real time through a web interface.", 22)
    set_paras(shape(s, 8), "A URL string")
    set_paras(shape(s, 11), "Verdict, probability, red flags")
    set_paras(shape(s, 14), "Community reports, public feeds")
    set_notes(s, "Input is a URL; output is a verdict with reasons; the community channel supplies fresh evidence.")

    # 11 objectives
    s = S[10]
    fill(s, 4, ["Collect and preprocess a dataset of phishing and legitimate URLs.",
                "Extract lexical, structural and domain-based URL features.",
                "Train and compare Random Forest, XGBoost and Logistic Regression classifiers.",
                "Integrate crowdsourced threat intelligence for newly reported phishing URLs.",
                "Refine the model continuously as new threat data arrives.",
                "Provide real-time URL classification through a simple web interface."], 20, bullet=True)
    set_notes(s, "The six objectives of the project.")

    # 12 proposed approach
    s = S[11]
    for tid, bid, ttl, body in [
        (7, 8, "1. Extract", "47 offline features from the URL: lexical, structural and domain; plus red flags."),
        (12, 13, "2. Classify", "Random Forest, XGBoost and Logistic Regression on one split; best F1 is deployed."),
        (17, 18, "3. Community", "Reports are voted; two net votes or a trusted feed confirm a URL, which overrides the model."),
        (22, 23, "4. Refine", "Confirmed URLs join the training data; models are retrained and hot-reloaded.")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 14)
    set_paras(shape(s, 27), "Web application")
    shape(s, 28).height = Emu(44 * 9525)
    fill(s, 28, "Flask API (port 8103) and React interface (port 5103): check, batch, report, threat intelligence, models, activity.", 16)
    set_notes(s, "The approach follows the three phases of the base paper and adds an explanation and a web interface.")

    # 13 architecture
    s = S[12]
    put_picture(s, DIAG / "01_system_architecture.png", (215, 118, 790, 482), remove_ids=(4,), name="System architecture diagram")
    set_paras(shape(s, 5), "Proposed architecture: React interface, Flask API with the detection modules, local storage")
    set_notes(s, "Browser to React to Flask. The detector, features, threat-intelligence store and retraining modules sit behind the API; storage is SQLite plus model files.")

    # 14 expected outcomes
    s = S[13]
    for tid, bid, ttl, body in [
        (7, 8, "Catches unseen URLs", "A trained model scores URLs that no list contains (target: F1 above 90 %)."),
        (12, 13, "Real time", "A verdict in well under a second."),
        (17, 18, "Zero-day response", "A confirmed community verdict acts on the next check."),
        (22, 23, "Self-improving", "Confirmed URLs retrain the model and it reloads without a restart."),
        (27, 28, "Explainable", "Every verdict shows red flags and a reason."),
        (32, 33, "Honest evaluation", "Three models compared fairly; limits reported plainly.")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 16)
    set_notes(s, "Expected outcomes are stated as targets at this stage and are measured in the later reviews.")

    # 15 references
    s = S[14]
    fill(s, 4, [f"[{i}] {r}" for i, r in enumerate(REFERENCES[:14], 1)], 14, min_pt=8, bullet=True, gap_pt=2)
    set_notes(s, "References [1] to [14]; the full list is in the report.")

    # 16 thank you
    set_notes(S[15], "Thank you. Questions are welcome.")
    prs.save(OUT)
    print("saved", OUT, len(prs.slides._sldIdLst), "slides")


if __name__ == "__main__":
    build()
