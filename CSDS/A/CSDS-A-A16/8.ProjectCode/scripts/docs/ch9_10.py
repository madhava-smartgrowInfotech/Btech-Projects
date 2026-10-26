"""Chapters 9 (Conclusion) and 10 (Future scope), plus the shared block lists used by documents 9, 10, 12 and 15.

Every number is read from scripts/docs/facts.py (experiments/**/metrics.json and the pytest junit file) when the blocks are built.
Code listings are read from the repository files at build time, so they are exact copies of what is in 8.ProjectCode.
"""
import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, TAB
from .refs import CITE as R


def pc(x, d=1):
    return f"{x * 100:.{d}f} %"


def src(rel, start, end=None, include_end=False):
    """Text of a repository file from the first line containing `start` up to (not including) the first later line containing `end`."""
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        lines = f.read().split("\n")
    a = next(i for i, ln in enumerate(lines) if start in ln)
    b = len(lines)
    if end:
        b = next(i for i in range(a + 1, len(lines)) if end in lines[i]) + (1 if include_end else 0)
    return "\n".join(lines[a:b]).rstrip()


def _lat(sub):
    return next(r for r in F.APIM["latency"] if sub in r["label"])


def _v():
    """All numbers used in the prose, computed from the facts files."""
    cp = F.FIN["compound_on_real_test"]
    s05 = F.SYN["final_model"]["0.5"]
    ctrl = F.SYN.get("real_only_control", {})
    ro_acc, sy_acc = F.abl_vals("real_only", "accuracy"), F.abl_vals("synth", "accuracy")
    ro_f1, sy_f1 = F.abl_vals("real_only", "macro_f1"), F.abl_vals("synth", "macro_f1")
    auc_sy = [F.ABL[f"synth_s{s}"]["synthetic_holdout_thr0.5"]["compound_roc_auc_macro"] for s in (1, 2, 3) if f"synth_s{s}" in F.ABL]
    g = F.GAN
    d = F.DET
    v = {
        "acc_b": pc(F.BASE["accuracy"], 2), "acc_f": pc(F.FIN["accuracy"], 2), "f1_b": f"{F.BASE['macro_f1']:.3f}", "f1_f": f"{F.FIN['macro_f1']:.3f}",
        "gain": f"{(F.FIN['accuracy'] - F.BASE['accuracy']) * 100:.2f}",
        "n_test": f"{F.DATA['n_test']:,}", "n_train": f"{F.DATA['n_train']:,}",
        "maj": pc(F.DATA["test_majority_baseline"]),
        "ro_acc": F.mstd(ro_acc), "sy_acc": F.mstd(sy_acc), "ro_f1": F.mstd(ro_f1), "sy_f1": F.mstd(sy_f1),
        "n_seeds": len(ro_acc),
        "diff_acc": f"{(sum(sy_acc) / len(sy_acc) - sum(ro_acc) / len(ro_acc)) * 100:+.2f}",
        "diff_f1": f"{(sum(sy_f1) / len(sy_f1) - sum(ro_f1) / len(ro_f1)) * 100:+.2f}",
        "cp_mean": f"{cp['mean_top_compound_confidence']:.5f}", "cp_n": f"{cp['n']:,}",
        "cp_ge3": pc(cp["any_compound_ge_0.3"], 2), "cp_dom": pc(cp["dominant_is_compound"], 2),
        "cp_top_true": pc(cp["top_compound_contains_true_basic"]), "cp_chance": pc(cp["chance_top_compound_contains_true_basic"]),
        "auc05": f"{s05['compound_roc_auc_macro']:.3f}", "auc_ctrl": f"{ctrl.get('compound_roc_auc_macro', 0.5):.3f}",
        "auc_sy_mean": f"{sum(auc_sy) / len(auc_sy):.3f}" if auc_sy else "n/a",
        "syn_prob": f"{s05['mean_compound_prob_on_true_compound']:.3f}", "ctrl_prob": f"{ctrl.get('mean_compound_prob_on_true_compound', 0):.5f}",
        "syn_emr": f"{s05['exact_match_ratio']:.3f}", "syn_rec05": pc(s05["compound_recall"], 1),
        "syn_micro05": f"{s05['micro_f1']:.3f}",
        "gan_basic": pc(g["mean_basic_conditional_accuracy"], 1), "gan_t1": pc(g["mean_compound_top1_in_pair"], 1), "gan_t2": pc(g["mean_compound_top2_equals_pair"], 1),
        "gan_t2c": pc(g["chance_top2_equals_pair"], 1), "gan_t1c": pc(g["chance_top1_in_pair"], 1),
        "fd_gen": f"{g['frechet_distance_stage1_features']['generated_basic_vs_real_train_subset']:.1f}",
        "fd_real": f"{g['frechet_distance_stage1_features']['real_test_vs_real_train_subset']:.1f}",
        "gen_params": f"{g['generator_parameters']:,}", "cnn_params": f"{F.FIN['parameters']:,}",
        "haar1": pc(d["haar_detection_rate_scale_1x"], 0), "haar3": pc(d["haar_detection_rate_scale_3x"], 1),
        "det_pipe": pc(d["accuracy_via_haar_crop_on_detected"], 1), "det_direct": pc(d["accuracy_direct_64px_on_same_images"], 1), "det_n": d["detected_at_3x"],
        "synth_share": pc(2200 / (F.DATA["n_train"] + 2200), 1),
        "t_total": F.TESTS["tests"] if F.TESTS else "n/a", "t_fail": (F.TESTS["failures"] + F.TESTS["errors"]) if F.TESTS else "n/a",
        "probe_ok": F.APIM["probes_ok"], "probe_n": F.APIM["probes_total"],
        "lat_an": f"{_lat('analyze anonymous')['p50_ms']:.1f}", "lat_an95": f"{_lat('analyze anonymous')['p95_ms']:.1f}",
        "lat_auth": f"{_lat('authenticated (face')['p50_ms']:.1f}", "lat_login": f"{_lat('login')['p50_ms']:.0f}",
        "lat_hist": f"{_lat('history?limit')['p50_ms']:.1f}",
        "disg_rec": pc(F.FIN["per_class"]["disgust"]["recall"], 1), "disg_n": f"{F.DATA['class_counts']['train']['disgust']:,}",
        "happy_f1": f"{F.FIN['per_class']['happy']['f1']:.3f}", "fear_f1": f"{F.FIN['per_class']['fear']['f1']:.3f}",
        "surp_f1": f"{F.FIN['per_class']['surprise']['f1']:.3f}",
    }
    for key, name in (("synth50_s1", "s50"), ("synth800_s1", "s800")):
        if key in F.ABL:
            x = F.ABL[key]
            v[name] = f"{pc(x['accuracy'], 2)} accuracy and {x['macro_f1']:.3f} macro-F1"
    return v


def _sweep_sentence(v):
    if "s50" in v and "s800" in v:
        return (f"A single-seed sweep of the number of synthetic faces per compound class gives {v['s50']} at 50, {pc(F.ABL['synth_s1']['accuracy'], 2)} accuracy and "
                f"{F.ABL['synth_s1']['macro_f1']:.3f} macro-F1 at 200 and {v['s800']} at 800 (seed 1 throughout), so no dose-response is visible.")
    return "A larger sweep of the number of synthetic faces per compound class was not completed in time and is not reported."


# ---------------------------------------------------------------------------- shared lists
def _objective_rows():
    v = _v()
    return [
        ["1. Generate identity-preserving facial images with complex emotions using cEmoGANs", "Not achieved",
         f"A conditional GAN ({v['gen_params']} parameters) was trained for 10 epochs on 2,800 faces, but the code has no encoder and no identity term, and the generator does not obey its condition: "
         f"the stage-1 classifier reads the intended emotion on {v['gan_basic']} of one-hot generated faces (chance 14.3 %) and the Fréchet distance in feature space is {v['fd_gen']} against {v['fd_real']} for real test faces. Identity preservation was not measured."],
        ["2. Enlarge the complex-emotion dataset with generated images", "Nominal only",
         f"2,200 synthetic images (200 per compound class, {v['synth_share']} of the 30,909 training images) were added with three target bits each. They carry no verified compound content, "
         "so the dataset is larger but not richer in complex emotions."],
        ["3. Train a CNN multi-label classifier for basic and complex emotions", "Implemented; compound outputs inert",
         f"18 sigmoid outputs, {v['cnn_params']} parameters, basic accuracy {v['acc_f']}. On {v['cp_n']} real test faces the largest compound probability averages {v['cp_mean']} and none reaches 0.3; "
         f"on 1,100 synthetic hold-out faces the compound ROC-AUC is {v['auc05']} (chance 0.5)."],
        ["4. Evaluate recognition performance against single-label baselines", "Done; the gain is not due to the GAN",
         f"Final model {v['acc_f']} against the single-label baseline {v['acc_b']}, but a control trained the same way without synthetic images scores {v['ro_acc']} % (mean ± std over {v['n_seeds']} seeds) against {v['sy_acc']} % with them. "
         "The gain over the baseline comes from five further epochs, not from the generated faces."],
        ["5. Provide an interface for emotion recognition from uploaded images", "Achieved, with defects",
         f"Next.js console (landing, register, login, analyse by upload or webcam, history) over a FastAPI service; {v['t_total']} automated tests pass, {v['probe_ok']} of {v['probe_n']} malformed-input probes behave as expected, "
         f"analysis takes a median of {v['lat_an']} ms. Defects: broken thumbnail image, unreachable history-detail page, HTTP 500 on undecodable uploads, 200 instead of 422 when no face is found."],
    ]


def _findings():
    v = _v()
    return [
        f"**Extra training with a multi-label head beats the single-label baseline.** Accuracy rises from {v['acc_b']} to {v['acc_f']} (+{v['gain']} points) and macro-F1 from {v['f1_b']} to {v['f1_f']} on the {v['n_test']} FER2013 test faces (always predicting 'happy' scores {v['maj']}). Per-class F1 is highest for happy ({v['happy_f1']}) and surprise ({v['surp_f1']}) and lowest for fear ({v['fear_f1']}) and disgust, which has {v['disg_n']} training images and a recall of {v['disg_rec']}.",
        f"**The generated faces do not explain that gain.** Over {v['n_seeds']} seeds the same recipe without synthetic images scores {v['ro_acc']} % accuracy and {v['ro_f1']} % macro-F1; with 200 synthetic faces per compound class it scores {v['sy_acc']} % and {v['sy_f1']} % ({v['diff_acc']} and {v['diff_f1']} points). Both differences are within the seed-to-seed spread. {_sweep_sentence(v)}",
        f"**Compound outputs are inert on real faces.** On {v['cp_n']} real test faces the largest compound probability averages {v['cp_mean']}; {v['cp_ge3']} of the faces have any compound output at or above 0.3, and the argmax rule that picks the dominant emotion chooses a compound label for {v['cp_dom']} of them. The score of a compound does not depend on whether the true basic label is one of its components, and the top compound contains the true label {v['cp_top_true']} of the time against a chance level of {v['cp_chance']}.",
        f"**Compound outputs cannot rank the synthetic classes either.** On the synthetic hold-out the macro ROC-AUC is {v['auc05']} for the shipped model (mean {v['auc_sy_mean']} over the retrained models) and {v['auc_ctrl']} for the real-only control; no threshold gives an exact match. The compound head did learn that generated faces differ from real ones (mean compound probability {v['syn_prob']} on synthetic compounds against {v['ctrl_prob']} for the control) but not which compound each one is.",
        f"**The generator does not follow its condition.** The stage-1 classifier recognises the intended basic emotion on {v['gan_basic']} of generated faces (chance 14.3 %); for compound conditions its top-two labels equal the requested pair {v['gan_t2']} of the time against {v['gan_t2c']} by chance. Ten epochs on 2,800 faces were not enough to produce usable faces.",
        f"**The serving path does not match the training data.** Haar detection finds {v['haar1']} of native 48x48 FER2013 faces and {v['haar3']} after a threefold upscale. On the {v['det_n']} faces it does find, accuracy through the product path is {v['det_pipe']} against {v['det_direct']} when the same images are resized directly.",
        f"**The software is tested and fast.** {v['t_total']} pytest tests pass; {v['probe_ok']} of {v['probe_n']} malformed-input probes behave as expected (two documented defects aside); analysis takes a median of {v['lat_an']} ms anonymously and {v['lat_auth']} ms when the result is stored, and a bcrypt login takes about {v['lat_login']} ms.",
        f"**Scores are not comparable with the base paper.** The base paper [{R['base']}] reports f-beta 0.99, 0.99 and 0.80 on CK+, JAFFE and MUG, measured on 15,000 images produced by its own generator. Mosaic is scored on real, uncontrolled FER2013 faces for basic emotions and on its own synthetic faces for compounds, so neither number supports a claim of better or worse.",
    ]


def _limitations():
    v = _v()
    return [
        ("No identity preservation and a weak generator", f"The code has no encoder and no identity loss. The conditional GAN was trained for 10 epochs on 2,800 faces and does not obey its condition ({v['gan_basic']} of one-hot conditions recognised, chance 14.3 %); its faces are blurry (Fréchet distance {v['fd_gen']} against {v['fd_real']} for real faces)."),
        ("Compound emotions have no real ground truth", f"FER2013 has only basic labels, so the 11 compound outputs were never scored on real faces. On real faces they stay near zero (mean maximum {v['cp_mean']}); on synthetic faces they sit at chance (ROC-AUC {v['auc05']})."),
        ("Synthetic labels are assumptions", "A synthetic face is labelled with both condition emotions and the compound. Because the generator ignores its condition, many of those labels are wrong, which may explain why the head cannot separate the classes."),
        ("Small, noisy, imbalanced training data", f"FER2013 is 48x48 grayscale with known label noise; disgust has {v['disg_n']} training images (1.5 %) and a recall of {v['disg_rec']}. The test set also served as the per-epoch validation printout; no checkpoint was selected on it."),
        ("Short training on a CPU", "Every model was trained for five or ten epochs on a shared CPU (about two minutes per epoch). No hyper-parameter search, augmentation or learning-rate schedule was tried, and the baseline reaches only 50.56 %."),
        ("Training and serving framing differ", f"Training faces are aligned 48x48 FER crops; serving uses a Haar crop of a photograph. Detection finds none of the native 48-pixel faces and {v['haar3']} after upscaling, and accuracy on detected faces drops from {v['det_direct']} to {v['det_pipe']}."),
        ("One face, grayscale, still images", "Only the largest detected face is analysed; there is no tracking, colour, video or multi-face handling. The webcam tab was not exercised in the headless captures."),
        ("The decision rule favours basic labels", "`dominant` is the argmax over all 18 sigmoid outputs; with compound outputs near zero the rule always returns a basic emotion, and the unused `threshold` argument of `analyze_image_bytes` has no effect."),
        ("Application defects", "A hard reload of `/app` redirects to the login page in development mode; the result thumbnail is a relative URL that resolves against the UI origin and shows a broken image; `/app/history/[id]` exists but no link reaches it; `/api/analyze` answers 200 where `API_CONTRACT.md` says 422, and an undecodable file produces HTTP 500; the e-mail address is not validated."),
        ("Local, single-user deployment", "The service runs on one machine with SQLite, CORS for `localhost:3000` only, a development secret key unless `MOSAIC_SECRET_KEY` is set, no rate limiting and no `.env.example` or start scripts."),
    ]


def _not_measured():
    return [
        ["Identity preservation of generated faces", "The code has no identity encoder; the base paper's face-recognition similarity test was not run."],
        ["Inception score, Fréchet inception distance and BRISQUE as in the base paper", "Only a Fréchet distance in the stage-1 CNN's feature space was computed; it is not comparable with published FID."],
        ["Recognition of compound emotions on real faces", "No real compound ground truth was available (RAF-DB compound and C-EXPR-DB need a licence)."],
        ["Action-unit analysis of the generated faces", "The base paper's check with an AU recogniser was not run."],
        ["Colour, pose, occlusion and demographic robustness", "FER2013 is grayscale and frontal-ish; no subgroup or fairness audit was done."],
        ["Webcam capture path", "The captures are headless; the webcam tab was opened but no camera frame was analysed."],
        ["Multiple faces in one image", "Only the largest face is analysed; the case was not tested."],
        ["Behaviour on GPU or at scale", "Everything ran on a shared CPU; throughput under concurrent users was not measured."],
        ["Usability with real users", "No user study; the console was exercised by the team only."],
        ["Security review of the API", "Malformed-input probes and tests only; no penetration test, rate limiting or token revocation."],
    ]


# ---------------------------------------------------------------------------- novelty and contributions
def novelty_blocks():
    bp = F.BP
    v = _v()
    return [
        H2("What the base paper does"),
        P(f"The base paper [{R['base']}] proposes analysis by synthesis for complex emotion estimation. Its generator, cEmoGANs, combines an encoder that maps a face to an identity-bearing latent vector with a conditional GAN driven by a six-dimensional multi-hot emotion label; "
          f"blended labels (for example happiness plus surprise) are used to synthesise complex expressions while keeping identity. A small CNN with sigmoid outputs is then trained on the generated images. "
          f"It is evaluated on {bp['datasets']}. Its result: {bp['result']}. Image quality is reported with an Inception score, a Fréchet inception distance and BRISQUE; identity is checked with a face-recognition cosine similarity ({bp['identity']})."),
        P(f"Training used {bp['hardware']}. Unconstrained photographs are tested only qualitatively, against Py-Feat."),
        H2("What Mosaic adds and what it simplifies"),
        TAB("Mosaic against the base paper", ["Aspect", "Base paper", "Mosaic"],
            [["Goal", "Estimate complex emotions from a face by analysis by synthesis", "The same idea built as a working product: accounts, upload and webcam, history"],
             ["Generator", "cEmoGANs: encoder for identity + conditional GAN, learning rates 1e-4 / 1e-5", f"Conditional GAN only ({v['gen_params']} parameters), no encoder, one-hot conditions, Adam 2e-4, 10 epochs"],
             ["Condition for compounds", "Two active bits of a 6-d label; training images are morphed pairs", "Seven-dimensional soft vector, 0.5 on each component, used only at synthesis time"],
             ["Data", "CK+, JAFFE, MUG (laboratory); 15,000 generated images", f"FER2013 ({v['n_train']} train, {v['n_test']} test, uncontrolled 48x48); 2,200 generated images"],
             ["Classifier", "Small CNN, sigmoid outputs; EfficientNet-B0 baseline", f"Four-block CNN, 18 sigmoid outputs ({v['cnn_params']} parameters); single-label CNN baseline"],
             ["Labels", "Six basic emotions, 15 complex types", "Seven basic (with neutral) and 11 compound types"],
             ["Reported result", "f-beta 0.99 / 0.99 / 0.80 and exact match 100 % / 99 % / 68.7 % on generated test images", f"Basic accuracy {v['acc_f']} on real test faces; compound outputs at chance on synthetic faces"],
             ["Controls", "EfficientNet-B0 and StyleGAN-trained models", f"Seeded real-only control ({v['n_seeds']} seeds) and a threshold sweep on a synthetic hold-out"],
             ["Serving path", "None", f"Haar detection, FastAPI, JWT, SQLite history, Next.js UI; detection and framing study"]],
            widths=[1.1, 2.6, 2.7], align=["l", "l", "l"], size=9.5),
        P("The datasets, label sets and evaluation protocols differ, so the table compares designs, not scores."),
        H2("What is new here and what is not"),
        B("**New in this project relative to the base paper:** a complete, tested application around the idea; an honest measurement layer that includes a seeded real-only control, a synthetic hold-out with a threshold sweep, a conditional-fidelity check of the generator and a study of the Haar serving path; and the documented finding that, at this scale, the generated faces neither help basic recognition nor teach the compound outputs.",
          f"**Not new:** the conditional GAN [{R['cgan']}], the convolutional classifier, multi-label learning with sigmoid outputs [{R['multilabel']}], the compound-emotion taxonomy [{R['du2014']}], FER2013 [{R['fer2013']}], and the Viola-Jones cascade [{R['viola']}].",
          "**Not carried over from the base paper:** the identity encoder, the morphed-pair ground truth, the Inception and FID evaluation, and the action-unit analysis. Objective 1 of the batch (identity-preserving generation) is therefore not met."),
        P(f"Related work is consistent with this reading. Disentangling GANs separate identity from expression for single-label recognition [{R['cdgan']}], [{R['nstgan']}]; compound recognition on real data has so far relied on real compound labels, for example RAF-DB [{R['rafdb']}] in the ABAW7 ensemble [{R['abaw7']}]. "
          f"Galkaduwa [{R['galkaduwa']}] reports 51.6 % for a light CNN on FER-2013, close to the {v['acc_b']} of Mosaic's single-label baseline; the splits and training budgets may differ, so this is a sanity check, not a comparison."),
    ]


def _contributions():
    v = _v()
    return [
        ("A complete analysis-by-synthesis pipeline in one repository.", f"Face detection, a 7-class backbone, a conditional GAN, synthesis of 2,200 compound faces and an 18-output multi-label classifier, trainable with one command (`python -m app.ml.run_pipeline`) and served by a FastAPI application."),
        ("A usable emotion-analysis product.", f"JWT accounts with bcrypt hashing, optional-auth analysis, per-user history with thumbnails, a Next.js console with an upload and webcam capture widget, a basic-emotion chart and compound bars; median analysis time {v['lat_an']} ms on the test PC."),
        ("A controlled test of whether generated faces help.", f"A seeded real-only control (seeds 1 to {v['n_seeds']}): {v['ro_acc']} % without and {v['sy_acc']} % with synthetic faces, so the effect on basic accuracy is not distinguishable from noise; {_sweep_sentence(v)}"),
        ("An evaluation of compound outputs that does not need real compound labels.", f"Behaviour on {v['cp_n']} real faces, a synthetic hold-out scored by ROC-AUC and a threshold sweep, and a conditional-fidelity and Fréchet-distance check of the generator. Together they show the compound head is inert ({v['cp_mean']} on real faces, AUC {v['auc05']} on synthetic)."),
        ("A serving-path study.", f"Haar detection finds {v['haar1']} of native faces and {v['haar3']} after upscaling, and accuracy falls from {v['det_direct']} to {v['det_pipe']} on the faces it finds, which identifies training/serving mismatch as a first-order weakness."),
        ("Tests, probes and documentation.", f"{v['t_total']} pytest tests, {v['probe_n']} malformed-input probes with timings, eleven diagrams, 19 real screenshots, and a list of nine defects found in the product."),
    ]


def contribution_blocks():
    out = [P("The project makes six contributions. Each is stated with the measurement that supports it; none claims more than the measurements show.")]
    out.append(N(*[f"**{t}** {d}" for t, d in _contributions()]))
    out.append(P("What the contributions do not include: a new learning algorithm, identity-preserving generation, a new dataset, or evidence that compound emotions are recognised on real faces."))
    return out


# ---------------------------------------------------------------------------- scope and limitations
def scope_blocks():
    return [
        H2("In scope"),
        B("Estimation of seven basic and eleven compound emotion scores for the largest face in a single still image (JPEG or PNG), returned as 18 independent sigmoid probabilities with a dominant label.",
          "Haar-cascade face detection, 64x64 grayscale preprocessing and a four-block CNN running on the CPU.",
          "Offline training of a 7-class backbone, a conditional GAN on 2,800 faces and a final multi-label classifier on 28,709 real plus 2,200 synthetic faces (FER2013).",
          "User accounts with JWT tokens, per-user analysis history with face thumbnails, and anonymous analysis through the API.",
          "A Next.js console (landing, register, login, analyse, history) and a FastAPI service with eight endpoints and a health check.",
          "Evaluation on the FER2013 test set, a seeded real-only control, a synthetic hold-out, API latency and abuse probes, as reported in Chapter 8."),
        H2("Out of scope"),
        B("Identity-preserving generation: the code has no identity encoder, so objective 1 of the batch is not implemented as in the base paper.",
          "Real compound-emotion ground truth (RAF-DB compound, C-EXPR-DB, CFEE): none was available, so compound outputs cannot be scored on real faces.",
          "Video, tracking, several faces per image, colour or 3-D input, audio or text cues.",
          "Clinical, safety or hiring decisions: the model is not validated for any such use and its accuracy is 58 % on seven classes.",
          "Cloud deployment, multi-tenant operation, rate limiting, token revocation or password reset.",
          "Demographic fairness analysis and consent management for stored images (only a cropped face thumbnail is stored)."),
        H2("Deployment boundary"),
        TAB("Where the system is meant to run", ["Item", "Boundary"],
            [["Host", "One Windows PC, Python 3.11, CPU only (measured on an Intel Core i5-12500 class machine, 15.7 GB RAM, shared with other jobs)"],
             ["Servers", "FastAPI on port 8000 by default (8116 in this documentation run), Next.js on 3000"],
             ["Storage", "One SQLite file, three checkpoint files, a folder of JPEG thumbnails"],
             ["Network", "No outbound calls at run time; CORS admits localhost:3000 and 127.0.0.1:3000"],
             ["Users", "A handful of accounts on one machine"]],
            widths=[1.4, 5.0], align=["l", "l"], size=10),
    ]


def assumption_blocks():
    return [
        P("The design and the measurements rest on the following assumptions. Where an assumption could not be checked it is marked."),
        B("FER2013 labels are correct enough to score basic emotions against, although the dataset is known to contain label noise (not checked here).",
          "A compound expression can be approximated by conditioning a generator on its two basic emotions at 0.5 each, as the base paper does with two active label bits. This assumption failed in practice: the generator does not follow its condition.",
          "A synthetic face should carry three positive targets: its two basic emotions and the compound. The classifier therefore treats the labels as independent sigmoid outputs.",
          "The largest Haar detection is the face of interest (an assumption for photos with several people; untested).",
          "A 64x64 grayscale crop is enough information for seven basic emotions at the accuracy reported; no higher resolution was tried.",
          "The test PC (shared CPU, 15.7 GB) represents a modest user machine; latency figures are upper bounds because other jobs kept the CPU busy.",
          "Uploaded images are not stored; only the cropped grayscale face of a signed-in user's analysis is kept as a thumbnail."),
    ]


def limitation_blocks():
    out = [P("Each limitation below was found while building or measuring the system, and each is stated with the number that shows it."),
           N(*[f"**{t}.** {d}" for t, d in _limitations()]),
           P("The next two figures show the limitation that matters most: the generator's failure to follow its condition and the chance-level compound ranking on synthetic faces."),
           FIG(F.fig("fig_gan_fidelity.png"), "Conditional fidelity of the cEmoGAN: share of generated faces read as the requested emotion (left) and as a member of the requested compound pair (right).", 5.6),
           FIG(F.fig("fig_compound_threshold.png"), "Synthetic hold-out: F1 and compound recall by decision threshold, and compound ROC-AUC against chance.", 5.6)]
    return out


def not_measured_blocks():
    return [P("Gaps are listed instead of being filled with plausible numbers. Each row says why the quantity is missing."),
            TAB("Quantities that were not measured", ["Quantity", "Reason"], _not_measured(), widths=[2.6, 3.8], align=["l", "l"], size=10)]


# ---------------------------------------------------------------------------- code walk-throughs
def walkthrough_blocks():
    return [
        H2("The inference function: analyze_image_bytes()"),
        P("`analyze_image_bytes()` in `app/ml/inference.py` is the one function every request passes through. It decodes the upload with Pillow, converts it to BGR for OpenCV, asks the Haar detector for the largest face and returns early with `face_detected` false when there is none. "
          "Otherwise it preprocesses the crop, runs the 18-output network, applies a sigmoid, builds the two sorted lists and chooses the dominant label as the argmax over all 18 probabilities."),
        CODE(src("backend/app/ml/inference.py", "def analyze_image_bytes"), 7.6),
        P("Three details matter. The `threshold` argument is accepted but never used. The dominant label is the maximum over basic and compound outputs together, so with near-zero compound probabilities it is always a basic emotion. "
          "A non-image upload raises inside Pillow and is not caught, which is why the API answers HTTP 500 for such files."),
        H2("The router: persistence and thumbnail"),
        P("`routers/analyze.py` reads the multipart file, calls the inference function and, when a valid token is present, inserts an `Analysis` row, writes the cropped face to `media/thumbs/<id>.jpg` and stores the path. Anonymous callers receive the same body with `id` null."),
        CODE(src("backend/app/routers/analyze.py", "async def analyze", "    return analysis_to_response(record)", True), 7.6),
        H2("Synthesising compound training faces"),
        P("`synthesize()` builds, for each of the eleven compound classes, a condition vector with 0.5 on each of the two component emotions, samples Gaussian noise, runs the generator and writes a three-bit target (both basics and the compound). "
          "The generator itself was trained only on one-hot conditions, so the blended condition is an extrapolation."),
        CODE(src("backend/app/ml/synthesize_compound.py", "def synthesize", "    return np.concatenate", True), 7.6),
        H2("Training the final classifier"),
        P("The final stage copies the backbone's convolutional weights into an 18-output network, then trains on real faces (one basic bit each) and synthetic faces with binary cross-entropy on the logits. The compound bits are positive only for the 2,200 synthetic rows, "
          f"about {_v()['synth_share']} of the data, which is why the compound outputs settle near zero for real faces."),
        CODE(src("backend/app/ml/train_final_classifier.py", "    criterion = nn.BCEWithLogitsLoss()", "        # Validation"), 7.6),
        H2("Tokens and the optional-user dependency"),
        P("Passwords are hashed with bcrypt through passlib; access tokens are HS256 JWTs with a seven-day expiry and the user id as subject. The dependency `get_current_user_optional` returns `None` for a missing or invalid token, which is how `/api/analyze` serves anonymous callers, while `get_current_user` raises 401."),
        CODE(src("backend/app/security.py", "def create_access_token"), 7.6),
        CODE(src("backend/app/deps.py", "def _resolve_user"), 7.6),
    ]


# ---------------------------------------------------------------------------- decisions
def decision_blocks():
    v = _v()
    return [
        P("Each decision is given with the reason it was taken and what the measurements say about it."),
        H2("4.1 Haar cascade instead of a deep face detector"),
        P(f"The Haar cascade ships with OpenCV, needs no extra weights and runs in a few milliseconds on a CPU [{R['viola']}], [{R['opencv']}]. The price is recall: it finds none of the native 48-pixel FER faces and {v['haar3']} after a threefold upscale, "
          "and the crop differs from the training framing. A modern detector with landmark alignment would be the first upgrade."),
        H2("4.2 64x64 grayscale input"),
        P("FER2013 faces are 48x48 grayscale. Resizing to 64 gives the four pooling stages an integer 4x4 map at the end and keeps the network small (770,130 parameters at 18 outputs). Colour and higher resolution were not tried because the training data has neither."),
        H2("4.3 Sigmoid outputs with binary cross-entropy"),
        P(f"Complex emotions co-occur with their components, so each of the 18 labels is an independent Bernoulli variable, as in the base paper [{R['base']}] and in multi-label learning generally [{R['multilabel']}]. "
          "A softmax would force a single winner. The cost is that probabilities are not normalised and, with 2,200 compound-positive rows out of 30,909, the compound outputs are strongly shrunk toward zero."),
        H2("4.4 A 0.5 / 0.5 condition for compound synthesis"),
        P(f"The generator takes a seven-dimensional condition. For a compound class the two component entries are set to 0.5, which keeps the vector's sum equal to the one-hot training value. The base paper activates two bits of a six-dimensional label [{R['base']}]. "
          f"Here the generator was never trained on such mixtures and the stage-1 classifier recovers the requested pair only {v['gan_t2']} of the time, so the decision did not produce usable compound faces."),
        H2("4.5 Initialising the final network from the backbone"),
        P("Transfer from the 7-class backbone gives the final network a head start on basic emotions. It also means the final model has had ten epochs in total, against five for the baseline, which is why the real-only control (same initialisation, no synthetic images) was needed to judge the GAN."),
        H2("4.6 Argmax over all 18 outputs for the dominant label"),
        P(f"The rule is simple and always yields one label, but it presumes compound probabilities are on the same scale as basic ones. With a maximum of about {v['cp_mean']} on real faces they never win. Per-label thresholds calibrated on real compound data would be needed."),
        H2("4.7 SQLite with JSON columns for history"),
        P(f"One file, no server, and one row per analysis keeps a history read to a single query: listing 20 items takes a median of {v['lat_hist']} ms. The trade-off is that emotion lists cannot be queried relationally."),
        H2("4.8 Optional authentication for analysis"),
        P("Anyone can call `/api/analyze`; a valid token merely adds persistence. This keeps the demo friction-free but means the endpoint has no rate limit and no ownership check beyond the optional user."),
        H2("4.9 CPU-only training and inference"),
        P(f"The target machine has no GPU. The CNN has {v['cnn_params']} parameters and a request takes {v['lat_an']} ms at the median, so a CPU is enough for serving; training took about two minutes per epoch while other jobs shared the processor, which is why training budgets are small."),
        H2("4.10 A Next.js client with a persisted token"),
        P("The console keeps the token in a persisted zustand store and sends it as a Bearer header. The guard runs before the store is read on a hard reload in development mode, which sends the user back to the login page; in the production build the session survived a reload in the probe run."),
    ]


# ---------------------------------------------------------------------------- conclusion
def _chapter9_core():
    v = _v()
    return [
        H2("9.1 Summary of the work"),
        P(f"The batch asked for a system that generates realistic complex-emotion data and recognises several emotions in a single face. The project delivered Mosaic: a face detector, a conditional GAN, synthesis of 2,200 compound-labelled faces, an 18-output multi-label CNN, a FastAPI service with accounts and history, "
          f"and a Next.js console, backed by {v['t_total']} passing tests and {v['probe_ok']} of {v['probe_n']} expected probe results."),
        P(f"In the documentation phase the product was measured more strictly than it had been built. The final classifier reaches {v['acc_f']} accuracy on {v['n_test']} real FER2013 test faces, against {v['acc_b']} for the single-label baseline. "
          f"A control trained without synthetic images scores {v['ro_acc']} % against {v['sy_acc']} % with them, so the generated faces do not account for the gain. The compound outputs are inert on real faces (mean maximum {v['cp_mean']}) and at chance on synthetic faces (ROC-AUC {v['auc05']}). "
          "The engineering works as designed; the central scientific claim of the batch, that generated complex expressions teach a classifier to recognise complex emotions, was not reproduced at this scale."),
        H2("9.2 Objectives achieved and not achieved"),
        TAB("Batch objectives against the outcome", ["Objective", "Status", "Evidence"], _objective_rows(), widths=[1.9, 1.0, 3.7], align=["l", "c", "l"], size=9.5),
        P("The statuses are strict. 'Nominal' means the step ran but produced nothing of the quality the objective requires; 'inert' means the outputs exist but carry no signal in the measurements."),
        H2("9.3 Key findings"),
        N(*_findings()),
        P("The two findings that most change how the system should be read are the seeded comparison with and without synthetic faces (Figure in Section 8.4) and the behaviour of the compound outputs on the synthetic hold-out (Figure in Section 8.5)."),
        H2("9.4 Practical applications"),
        P("As built, Mosaic is a teaching and prototyping platform for affective computing: it shows the full path from a photo to a stored, explained result, and it makes the pitfalls of synthetic augmentation visible with real numbers. "
          "The basic-emotion output (58 % accuracy over seven classes, strongest for happy and surprise) could support exploratory interfaces, such as classroom or human-computer-interaction demonstrations, where errors are tolerable. "
          "The intended use cases (well-being applications, driver monitoring, customer-experience analysis) would need far higher accuracy, validated compound labels, consent handling and fairness testing first; Mosaic is not suitable for them as it stands."),
        H2("9.5 Known limitations"),
        P("The limitations are listed in full in Chapter 1, Chapter 8 and the Scope and Limitations document. The ones that matter most for reading the results are:"),
        B(*[f"**{t}.**" for t, _ in _limitations()[:6]]),
    ]


def _strip(blocks, drop_prefix=None):
    """Chapter blocks without their chapter numbers on H2 headings (for the shared chapter-document text)."""
    out = []
    for b in blocks:
        if b[0] == "h2":
            if drop_prefix and b[1].startswith(drop_prefix):
                continue
            out.append(("h2", b[1].split(" ", 1)[1]))
        else:
            out.append(b)
    return out


def conclusion_blocks():
    core = _strip(_chapter9_core(), None)
    i = next(n for n, b in enumerate(core) if b[0] == "h2" and b[1] == "Known limitations")
    return core[:i] + [core[i], N(*[f"**{t}.** {d}" for t, d in _limitations()])]


def chapter9_blocks():
    return [H1("9. CONCLUSION")] + _chapter9_core()


# ---------------------------------------------------------------------------- chapter 10
def _future_improvements():
    v = _v()
    return [
        f"**Make the generator work first.** Train the conditional GAN for far more than 10 epochs on more than 2,800 faces, add an identity encoder and a reconstruction or identity loss as in the base paper [{R['base']}], widen the networks, and verify with a condition-fidelity test (target well above {v['gan_basic']}) and a Fréchet distance close to the real-versus-real reference of {v['fd_real']} before any synthetic face is used for training.",
        f"**Use real compound labels.** Evaluate and fine-tune on RAF-DB compound faces [{R['rafdb']}] or the C-EXPR-DB set used in ABAW7 [{R['abaw7']}] (both need a licence); only then can the compound outputs be scored on real faces.",
        "**Rebalance the loss for compound labels.** Positive-weight or oversample the compound-positive rows, use focal loss, and calibrate per-label thresholds on a validation set instead of taking an argmax over all 18 outputs.",
        f"**Match the training and serving framing.** Replace the Haar cascade by a landmark-based detector with alignment, train on the same crops used at serving time, and re-measure the drop from {v['det_direct']} to {v['det_pipe']}.",
        "**Train longer with augmentation and a schedule.** The baseline reaches only 50.56 % after five epochs; a deeper backbone, flips, crops and a cosine schedule are standard remedies on FER2013.",
        f"**Evaluate generated faces properly.** Report, for every synthetic-data experiment, a real-only control with several seeds, a held-out real test set, and the condition-fidelity score of the generator. In this work the control scored {_v()['ro_acc']} % against {_v()['sy_acc']} % with synthetic faces, a difference that a single run could easily have presented as a gain.",
        "**Scale the synthetic set deliberately.** Once generated faces pass the fidelity test, sweep the number per class over a wide range (the 50 and 800 runs here were a first step), and mix real and synthetic rows with a ratio chosen on validation data rather than a fixed 200 per class.",
        "**Fix the defects found in this work.** Resolve the thumbnail URL against the API origin, link the history list to the detail page, return 422 for no face and 400 for undecodable files, validate e-mail addresses, read the persisted token before the route guard runs, and add `.env.example`, `setup.bat` and `run.bat`.",
    ]


def _future_features():
    return [
        "**Several faces per image** with a bounding box and result for each face, and video or webcam streaming with temporal smoothing.",
        "**Intensity and valence-arousal outputs** alongside the categorical labels, using AffectNet-style annotations.",
        f"**Explanations:** class-activation maps or saliency overlays so that a user can see which facial regions drive a prediction, as the base paper suggests for future interpretability work [{R['base']}].",
        "**Export and sharing:** CSV or PDF export of the history, with an option to delete all stored thumbnails.",
        "**Consent and privacy controls:** an explicit consent screen, optional thumbnail storage and a data-retention setting.",
        "**Multimodal cues:** combine the face with voice or text, as surveyed for multimodal emotion recognition [" + str(R['su']) + "].",
    ]


def _future_scale():
    return [
        "**Server-side hardening:** a production ASGI setup, a secret key from the environment, rate limiting, token refresh and revocation, and HTTPS.",
        "**Database:** move from SQLite to PostgreSQL if several users or instances are needed, and normalise the score arrays if queries over scores become useful.",
        f"**Packaging:** a Docker image for the API and the UI, and a CI job that runs the {_v()['t_total']} tests and a smoke analysis.",
        "**Acceleration:** export the 770,130-parameter CNN to ONNX or run it on a GPU for batch workloads; at the measured median of about 19 ms per image a CPU is already adequate for light use.",
        "**Monitoring:** log latency, the share of requests without a face and the distribution of predicted emotions to detect drift.",
    ]


def _future_research():
    return [
        f"**Diffusion and StyleGAN-class generators** [{R['stargan']}], [{R['ganimation']}] for expression synthesis with identity control, compared with cEmoGANs on real compound recognition.",
        "**Label-efficient compound learning:** learn compound emotions as compositions of action units or of basic-emotion embeddings so that few real compound labels are needed.",
        f"**Evaluation of synthetic data:** a standard protocol (real-only control, several seeds, a real compound test set, a conditional-fidelity check) for papers that claim gains from generated faces, since the base paper scores on its own generated images.",
        "**Calibration of multi-label emotion scores:** investigate whether independent sigmoid outputs can be calibrated (for example by temperature scaling per label) so that a probability of 0.3 for a compound has a stable meaning across datasets.",
        "**Fairness and cultural variation:** test whether compound emotion estimates differ across ethnicity, age and gender, an issue the base paper itself flags.",
        f"**Cross-dataset generalisation:** train on FER2013 and test on AffectNet [{R['affectnet']}] and RAF-DB to measure the domain gap that a Haar-cropped photograph exposes.",
    ]


def _chapter10_core():
    return [
        H2("10.1 Improvements to the existing system"),
        P("The improvements below follow directly from the measurements; the first three would change the headline results."),
        N(*_future_improvements()),
        P("The order matters. Until the generator follows its condition, adding more synthetic faces cannot help, and until real compound labels are used, no change to the compound head can be verified. "
          "A realistic plan is therefore: repair the generator and its test, obtain a licensed compound dataset, retrain with weighted loss and calibrated thresholds, and only then change the serving path."),
        H2("10.2 Additional features"),
        P("The features below extend what a user can do with an emotion estimate. None of them requires changing the data model beyond adding columns or a second table."),
        B(*_future_features()),
        H2("10.3 Scalability and deployment"),
        P("Mosaic is a single-machine demonstration. The measured median analysis time is small, so the first scaling concern is operational rather than computational: security, storage and observability."),
        B(*_future_scale()),
        H2("10.4 Further research"),
        P("The work also raises research questions that go beyond this implementation. Each can be tested with the measurement tools already in `scripts/run_experiments.py`: the seeded control, the synthetic hold-out and the conditional-fidelity check."),
        B(*_future_research()),
    ]


def future_blocks():
    return _strip(_chapter10_core())


def chapter10_blocks():
    return [H1("10. FUTURE SCOPE")] + _chapter10_core()
