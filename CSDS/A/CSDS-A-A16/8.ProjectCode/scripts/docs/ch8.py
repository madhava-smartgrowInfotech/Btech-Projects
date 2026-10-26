"""Chapter 8: Results and output screens for Mosaic. Every number is read from facts.py (F.BASE, F.FIN, F.ABL, F.SYN, F.GAN, F.DET, F.APIM, F.TESTS);
nothing is typed in except labels and the base-paper / literature values that come from the PDFs (recorded in refs.REF_NOTES and F.BP)."""
import os
import statistics

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, PAIR, TAB
from .refs import CITE as C

SH = F.shot
BASIC = F.BASIC
LAB = [k.capitalize() for k in BASIC]


def pc(x, d=2):
    return f"{x * 100:.{d}f} %"


def S(name, caption, base=5.6, max_h=3.9):
    return FIG(SH(name), caption, F.shot_w(SH(name), base, max_h))


def screens(a, b):
    """Two screenshots: side by side in the report, one under the other in the chapter document."""
    if F.REPORT:
        return [PAIR([(SH(a[0]), a[1]), (SH(b[0]), b[1])], 3.0)]
    return [S(*a), S(*b)]


def fig(name, caption, w=5.4):
    return FIG(F.fig(name), caption, w)


def figpair(a, b):
    """Two result figures side by side in the report, one under the other in the chapter document."""
    if F.REPORT:
        return [PAIR([(F.fig(a[0]), a[1]), (F.fig(b[0]), b[1])], 3.1)]
    return [fig(a[0], a[1], 4.4), fig(b[0], b[1], 4.4)]


def _welch(a, b):
    try:
        from scipy import stats
        t = stats.ttest_ind(a, b, equal_var=False)
        return float(t.statistic), float(t.pvalue)
    except Exception:  # noqa: BLE001
        return None, None


def blocks():
    Bs, Fn = F.BASE, F.FIN
    pcB, pcF = Bs["per_class"], Fn["per_class"]
    cm = Fn["confusion_matrix"]
    ix = {k: i for i, k in enumerate(BASIC)}
    row_sum = [sum(r) for r in cm]

    def rate(true, pred):
        return cm[ix[true]][ix[pred]] / row_sum[ix[true]]

    cp = Fn["compound_on_real_test"]
    S_, G, D = F.SYN, F.GAN, F.DET
    fm = S_["final_model"]
    ro = [F.ABL[f"real_only_s{s}"] for s in (1, 2, 3) if f"real_only_s{s}" in F.ABL]
    sy = [F.ABL[f"synth_s{s}"] for s in (1, 2, 3) if f"synth_s{s}" in F.ABL]
    acc_r, acc_s = [x["accuracy"] for x in ro], [x["accuracy"] for x in sy]
    f1_r, f1_s = [x["macro_f1"] for x in ro], [x["macro_f1"] for x in sy]
    ta, pa = _welch(acc_s, acc_r)
    tf, pf = _welch(f1_s, f1_r)
    fr = G["frechet_distance_stage1_features"]
    best_t = max(fm, key=lambda t: fm[t]["micro_f1"])
    n_ok = sum(1 for k in BASIC if rate(k, k) > 0)  # classes with any correct prediction
    b = [H1("8. RESULTS AND OUTPUT SCREENS")]

    # ------------------------------------------------------------------ 8.1
    b += [H2("8.1 What was measured and how"),
          P("Five sets of measurements are reported. (1) The model the product serves, `classifier_final.pt`, on the FER2013 test set "
            f"({F.DATA['n_test']:,} real faces, seven basic labels), compared with the single-label stage-1 backbone that is the 'single-label baseline' of objective 4. "
            f"(2) A seeded ablation that retrains the final stage with and without the synthetic faces ({len(ro)} seeds each). (3) The behaviour of the eleven compound outputs on real faces and on freshly generated compound faces. "
            "(4) The quality of the conditional GAN. (5) The serving path: face detection and the output screens of the running application."),
          P(f"The data is the FER2013 partition shipped by the Hugging Face mirror `Jeneral/fer-2013`: {F.DATA['n_train']:,} training and {F.DATA['n_test']:,} test faces of 48 x 48 pixels with seven labels [{C['fer2013']}]. "
            "The product's training script prints the test accuracy after every epoch, so the test set doubles as a validation set; it is never used to choose a model or a threshold in this work, and all runs use the training script's fixed hyper-parameters. "
            f"Disgust is rare ({F.DATA['class_counts']['train']['disgust']:,} training and {F.DATA['class_counts']['test']['disgust']} test faces), so per-class figures for it are noisy. The majority-class rate on the test set is {pc(F.DATA['test_majority_baseline'])} (always answering 'happy')."),
          P("All numbers come from `experiments/**/metrics.json`, written by `scripts/run_experiments.py` and `scripts/measure_api.py`, and are copied into `docs/REPORT_FACTS.md`. The hardware was an Intel Core i5-12500 with 15.7 GB of RAM and no GPU, "
            "shared with other jobs. **FER2013 contains no compound-emotion labels**, so no accuracy for compound emotions on real faces can be reported; Section 8.5 says what can and cannot be measured instead."),
          *([] if F.REPORT else [fig("fig_class_distribution.png", "Class distribution of the FER2013 training and test sets used in all experiments.", 5.0)])]

    # ------------------------------------------------------------------ 8.2
    smp = [("happy_01", "Happy", "Happy", "47 %", "correct"), ("neutral_02", "Neutral", "Fear", "24 %", "wrong"), ("sad_03", "Sad", "Sad", "48 %", "correct"), ("angry_04", "Angry", "Angry", "75 %", "correct"),
           ("fear_05", "Fear", "Fear", "44 %", "correct"), ("disgust_06", "Disgust", "Angry", "48 %", "wrong"), ("surprise_07", "Surprise", "Fear", "52 %", "wrong")]
    b += [H2("8.2 Output screens"),
          P("The screens below were captured from the production build of the console with a signed-in demo account and real data. The uploaded faces are FER2013 test images, enlarged fivefold onto a grey 640 x 360 canvas so that the face detector can find them; "
            "two further uploads are faces synthesised by the project's cEmoGAN. The seven real faces were the first detectable face of each class in a random order, a small illustration and not a sample from which an accuracy could be estimated."),
          ]
    b += screens(("08_result_happy.png", "Result for a happy face: the card names Happy (47 % confidence); the bar chart shows Surprise (44 %) as the runner-up; every compound bar reads 0 %. The thumbnail is a broken image (defect F6, Chapter 7)."),
                 ("09_result_angry.png", "Result for an angry face: Angry is dominant with 75 % confidence, the highest of the seven samples."))
    b += [P("The first two screens show the interface working as designed. The dominant card gives the highest of the 18 sigmoid outputs, the bar chart lists the seven basic emotions sorted by confidence, and the lower panel lists the six strongest compound emotions. "
            "Because the sigmoid outputs are independent, the basic confidences do not sum to one: for the happy face Happy and Surprise together exceed 90 %, which is what a multi-label model is expected to do. What is **not** as intended is the compound panel, "
            f"where the highest compound probability averages {cp['mean_top_compound_confidence']:.5f} over the real test set (Section 8.5).")]
    b += screens(("12_result_neutral_misread.png", "A neutral face read as Fear (24 % confidence, the lowest of the samples): a low-confidence error, typical of the confusion between neutral, sad and fear."),
                 ("16_result_no_face.png", "A native 48 x 48 face: the Haar detector finds nothing, the API answers 200 with face_detected false and the console shows 'No face was detected in that image'."))
    b += screens(("14_result_gan_happily_surprised.png", "A face synthesised by the cEmoGAN under the condition 'happily surprised'. The image is a blurred blob, classified Sad (53 %); the happily-surprised bar shows 1 %."),
                 ("17_history.png", "History page: one card per analysis, newest first, with the dominant label, confidence and time; the entry without a face is listed as 'No face detected'."))
    b += [S("18_history_detail.png", "History detail route /app/history/[id], opened by typing its address because no link leads to it; it re-renders the stored result.", 5.0, 3.6)]
    b += [TAB("The seven real faces of the walk-through (dominant label returned by the running API).",
              ["Sample", "True label", "Dominant label", "Confidence", "Outcome"],
              [[f"`{s}.jpg`", t, d, c, o] for s, t, d, c, o in smp],
              widths=[1.3, 1.1, 1.3, 1.0, 1.0], align=["l", "l", "l", "c", "c"], size=10),
          P("A real API response (anonymous call, so `id` is null and nothing is stored) for the first sample, abridged to the first three entries of each list:"),
          CODE('POST /api/analyze  (multipart field "image" = happy_01.jpg)\n'
               "200 OK\n"
               '{ "id": null, "face_detected": true,\n'
               '  "basic_emotions": [ {"key":"happy","label":"Happy","confidence":0.4733},\n'
               '                      {"key":"surprise","label":"Surprise","confidence":0.438},\n'
               '                      {"key":"fear","label":"Fear","confidence":0.113}, ... 7 items ],\n'
               '  "compound_emotions": [ {"key":"angrily_disgusted","label":"Angrily Disgusted","confidence":0.0000}, ... 11 items ],\n'
               '  "dominant": {"key":"happy","label":"Happy","confidence":0.4733,"kind":"basic"},\n'
               '  "thumbnail_url": null }\n'
               "\n"
               'POST /api/analyze  (native 48x48 face)\n'
               '200 OK  { "id": null, "face_detected": false, "basic_emotions": [], "compound_emotions": [], "dominant": null, "thumbnail_url": null }', 8)]

    # ------------------------------------------------------------------ 8.3
    drows = [[k.capitalize(), f"{pcB[k]['f1']:.3f}", f"{pcF[k]['precision']:.3f}", f"{pcF[k]['recall']:.3f}", f"{pcF[k]['f1']:.3f}", str(pcF[k]["support"])] for k in BASIC]
    b += [H2("8.3 Basic-emotion recognition"),
          TAB("Seven-class results on the FER2013 test set (7,178 faces).",
              ["Model", "Accuracy", "Macro-F1", "Weighted-F1"],
              [["Single-label baseline: stage-1 softmax CNN, 5 epochs", pc(Bs["accuracy"]), f"{Bs['macro_f1']:.4f}", f"{Bs['weighted_f1']:.4f}"],
               ["Final 18-output multi-label CNN (shipped), argmax over the seven basic outputs", pc(Fn["accuracy"]), f"{Fn['macro_f1']:.4f}", f"{Fn['weighted_f1']:.4f}"],
               ["Majority class ('happy') for reference", pc(F.DATA["test_majority_baseline"]), "-", "-"]],
              widths=[3.7, 0.9, 0.9, 0.9], align=["l", "c", "c", "c"], size=10),
          P(f"The shipped multi-label model reaches {pc(Fn['accuracy'])} accuracy and {Fn['macro_f1']:.3f} macro-F1, against {pc(Bs['accuracy'])} and {Bs['macro_f1']:.3f} for the single-label baseline: "
            f"{(Fn['accuracy'] - Bs['accuracy']) * 100:.1f} points of accuracy and {Fn['macro_f1'] - Bs['macro_f1']:.3f} of macro-F1 in favour of the final model, on {Fn['parameters']:,} parameters. Both are far above the majority rate, "
            f"and both are in the range of a small CNN on this noisy dataset: the lightweight CNN of a recent comparative study reaches 51.6 % on FER-2013, ahead of HOG with an SVM (44.0 %) and LBP with logistic regression (25.0 %) [{C['galkaduwa']}]. "
            "That study uses its own split and training schedule, so the comparison is indicative only."),
          fig("fig_confusion_final.png", "Normalised confusion matrix of the final model on the FER2013 test set (counts and row percentages).", 4.6),
          TAB("Per-class results of the final model, with the baseline's F1 for comparison.",
              ["Class", "Baseline F1", "Final precision", "Final recall", "Final F1", "Test faces"], drows,
              widths=[1.0, 0.9, 1.1, 1.0, 0.9, 0.9], align=["l", "c", "c", "c", "c", "c"], size=10),
          fig("fig_per_class_f1.png", "Per-class F1 of the single-label baseline and of the final multi-label model.", 5.2),
          P(f"Happy ({pcF['happy']['f1']:.2f}) and surprise ({pcF['surprise']['f1']:.2f}) are recognised best; angry, neutral and sad sit around 0.5; fear is weak ({pcF['fear']['f1']:.2f}). "
            f"Disgust is the extreme case: precision is {pcF['disgust']['precision']:.2f} but recall only {pcF['disgust']['recall']:.2f}, because the model predicts it {cm[ix['disgust']][ix['disgust']]} times in {row_sum[ix['disgust']]} true cases and almost always (and correctly) when it does; "
            f"{rate('disgust', 'angry') * 100:.0f} % of disgust faces are read as angry. The two-way confusions that dominate the matrix are fear with sad ({rate('fear', 'sad') * 100:.0f} % of fear faces are read as sad, "
            f"{rate('sad', 'fear') * 100:.0f} % of sad faces as fear) and neutral with sad ({rate('neutral', 'sad') * 100:.0f} % of neutral faces read as sad). The baseline had a different error profile, with much better disgust recall "
            f"({pcB['disgust']['recall']:.2f}) at the price of low precision; a plausible reason is that the stage-1 softmax loss is class-weighted while the final model's binary cross-entropy is not, but this was not isolated."),
          fig("fig_confusion_baseline.png", "Normalised confusion matrix of the single-label baseline, for comparison with the final model.", 4.4)]

    # ------------------------------------------------------------------ 8.4
    srows = [[f"seed {s}", pc(ro[i]["accuracy"]), f"{ro[i]['macro_f1']:.4f}", pc(sy[i]["accuracy"]), f"{sy[i]['macro_f1']:.4f}"] for i, s in enumerate(range(1, len(ro) + 1))]
    srows.append(["mean ± std", F.mstd(acc_r) + " %", F.mstd(f1_r, 2, True), F.mstd(acc_s) + " %", F.mstd(f1_s, 2, True)])
    b += [H2("8.4 Does the synthetic data help? A seeded ablation"),
          P(f"The 'multi-label beats single-label' result of Section 8.3 has two possible causes: the synthetic compound faces, or simply the five extra epochs of training on top of the stage-1 weights. To separate them, the final stage was retrained "
            f"from the same backbone with the same hyper-parameters, **with** 200 synthetic faces per compound class (the product recipe) and **without** any synthetic data (the compound targets are then always zero), for {len(ro)} seeds each. "
            "Both variants have 18 outputs; only the training set differs."),
          TAB("Final-stage retraining with and without the synthetic faces (FER2013 test set, seven basic labels).",
              ["Run", "Real only: accuracy", "Real only: macro-F1", "Real + synthetic: accuracy", "Real + synthetic: macro-F1"], srows,
              widths=[1.1, 1.2, 1.2, 1.3, 1.3], align=["l", "c", "c", "c", "c"], size=9.5),
          fig("fig_ablation.png", "Ablation over seeds: test accuracy and macro-F1 with and without synthetic compound faces; dots are single seeds, bars the mean.", 5.6),
          P(f"With synthetic data the mean accuracy is {pc(statistics.mean(acc_s))} against {pc(statistics.mean(acc_r))} without, a difference of {(statistics.mean(acc_s) - statistics.mean(acc_r)) * 100:.2f} points that is smaller than the seed-to-seed spread of the real-only runs "
            f"(standard deviation {statistics.stdev(acc_r) * 100:.2f} points)" + (f" (Welch t = {ta:.2f}, p = {pa:.2f}, n = {len(ro)} per group)" if ta is not None else "") + ". "
            f"Macro-F1 is {'lower' if statistics.mean(f1_s) < statistics.mean(f1_r) else 'higher'} with synthetic data ({statistics.mean(f1_s):.3f} against {statistics.mean(f1_r):.3f}"
            + (f", p = {pf:.2f}" if pf is not None else "") + "). With three seeds the test has little power, so the honest conclusion is **no detectable effect of the synthetic data on basic-emotion recognition**; "
            f"the improvement from {pc(Bs['accuracy'])} to about 58 % is reproduced by the real-only control and is therefore attributable to the additional training, not to the generated faces. "
            "This is consistent with the generator's quality (Section 8.6): 2,200 blurred images among 30,909 cannot be expected to change what the network learns about real faces."),
          ]
    sweep = [(0, "real_only_s1"), (50, "synth50_s1"), (200, "synth_s1"), (800, "synth800_s1")]
    if all(k in F.ABL for _, k in sweep):
        b += [TAB("Effect of the number of synthetic faces per compound class (seed 1).",
                  ["Synthetic per class", "Accuracy", "Macro-F1", "Mean top compound probability on real faces"],
                  [[str(n), pc(F.ABL[k]["accuracy"]), f"{F.ABL[k]['macro_f1']:.4f}", f"{F.ABL[k]['compound_on_real_test']['mean_top_compound_confidence']:.5f}"] for n, k in sweep],
                  widths=[1.5, 1.0, 1.0, 2.6], align=["c", "c", "c", "c"], size=10),
              fig("fig_synth_sweep.png", "Accuracy and macro-F1 against the number of synthetic faces per compound class (single seed).", 4.6),
              P("The sweep uses one seed per point, so differences of one or two points are within the seed noise shown above; the table is a check that the number of synthetic faces chosen by the product (200) is not an unlucky value, not a tuning result.")]
    else:
        b += [P("A sweep over the number of synthetic faces per class (50 and 800 as well as 200) was planned as a single-seed check; it had not finished when this chapter was built and is therefore not reported.")]

    # ------------------------------------------------------------------ 8.5
    trows = [[t, f"{v['micro_f1']:.3f}", f"{v['macro_f1']:.3f}", f"{v['exact_match_ratio']:.3f}", pc(v["compound_recall"], 1), f"{v['compound_roc_auc_macro']:.3f}"] for t, v in fm.items()]
    ctrl = S_.get("real_only_control")
    b += [H2("8.5 Compound emotions"),
          H3("8.5.1 On real faces"),
          P(f"On the {cp['n']:,} real test faces the largest compound probability averages {cp['mean_top_compound_confidence']:.5f}. No face has any compound output at or above 0.3 ({pc(cp['any_compound_ge_0.3'])}) or 0.5 ({pc(cp['any_compound_ge_0.5'])}), "
            f"and the dominant label, the maximum of all 18 outputs, is a compound label for {pc(cp['dominant_is_compound'])} of faces. The compound scores also carry no information about the face: the mean score is {cp['mean_score_true_basic_is_component']:.6f} when the true basic emotion is one of the two "
            f"components of the compound and {cp['mean_score_true_basic_not_component']:.6f} when it is not, and the top-ranked compound contains the true basic label for {pc(cp['top_compound_contains_true_basic'])} of faces, below the {pc(cp['chance_top_compound_contains_true_basic'])} that a random compound would achieve. "
            "In short, on real faces the shipped product is a seven-class recogniser whose compound panel always reads about zero (screens 08, 09 and 12)."),
          H3("8.5.2 On synthetic compound faces"),
          P(f"Real compound ground truth is unavailable, so the only labelled compound data are the faces the project's own generator produces. A hold-out of {S_['n']:,} fresh generated faces ({S_['per_compound_class']} per compound class, a seed not used in training) "
            "carries the training-style labels (two basic bits and one compound bit). This is a weak test, because the labels are defined by the generator's own condition, and it is the same kind of evaluation as the base paper's (Section 8.7). "
            "The multi-label scores at several thresholds are:"),
          TAB("Final model on the synthetic hold-out, over all 18 labels.", ["Threshold", "Micro-F1", "Macro-F1", "Exact-match ratio", "Compound recall", "Compound ROC-AUC (macro)"], trows,
              widths=[0.8, 0.9, 0.9, 1.1, 1.1, 1.3], align=["c", "c", "c", "c", "c", "c"], size=9.5),
          fig("fig_compound_threshold.png", "Synthetic hold-out: micro-F1 and compound recall against the decision threshold (left) and compound ROC-AUC compared with the real-only control and with chance (right).", 5.6),
          P(f"Micro-F1 peaks at {fm[best_t]['micro_f1']:.3f} at threshold {best_t}, and that figure is almost entirely the basic bits; the exact-match ratio is {fm['0.5']['exact_match_ratio']:.3f} at every threshold tried, i.e. the model never reproduces a full three-bit label set. "
            f"Compound recall is {pc(fm['0.05']['compound_recall'], 0)} at 0.05 only because nearly every output exceeds that low threshold; at 0.1 it falls to {pc(fm['0.1']['compound_recall'], 1)}. "
            f"The macro ROC-AUC of the eleven compound outputs is {fm['0.5']['compound_roc_auc_macro']:.3f}, which is chance level: the model cannot say *which* compound class a generated face was synthesised for."
            + (f" The real-only control scores {ctrl['compound_roc_auc_macro']:.3f}, so the synthetic training changed the compound outputs on generated faces (mean probability {fm['0.5']['mean_compound_prob_on_true_compound']:.3f} against {ctrl['mean_compound_prob_on_true_compound']:.5f}) without teaching it to discriminate between them." if ctrl else "") +
            f" The dominant label is the correct compound for {pc(fm['0.5']['dominant_is_correct_compound'])} of generated faces."),
          P("What the network appears to have learned from the synthetic data is to detect that an image looks generated (and to raise all compound outputs a little for it), not to tell compounds apart. "
            "Two causes are visible in the data: the 2,200 synthetic faces are 7 % of the training set and each compound bit is positive in only 0.65 % of rows, so binary cross-entropy is minimised by predicting small probabilities everywhere; "
            "and the generator does not produce distinguishable faces for different conditions (Section 8.6).")]

    # ------------------------------------------------------------------ 8.6
    b += [H2("8.6 Quality of the conditional GAN"),
          P(f"The generator ({G['generator_parameters']:,} parameters) was trained for 10 epochs on 2,800 faces (400 per class) with final discriminator and generator losses of 0.773 and 3.724 (training log). "
            "Its images are shown against real faces in the next three figures; the first two grids have one row per basic emotion in the order angry, disgust, fear, happy, sad, surprise, neutral, and the third has one row per compound class in taxonomy order, starting with happily surprised."),
          *figpair(("fig_grid_real_basic.png", "Real FER2013 training faces, one row per basic emotion."),
                   ("fig_grid_generated_basic.png", "Generator output for the same seven one-hot conditions: blurred, low-contrast face-like patterns.")),
          fig("fig_grid_generated_compound.png", "Generator output for the eleven compound conditions (0.5 / 0.5 on the two component emotions).", 4.4),
          P("Visually the output is not photographic: faces are blurred, with eyes and mouth as dark patches and mottled backgrounds. Two measurements make this objective. First, **does the generator obey its condition?** "
            f"The stage-1 classifier reads the intended emotion on {pc(G['mean_basic_conditional_accuracy'], 1)} of 500 generated faces per class on average, against 14.3 % by chance; the per-class values range from "
            f"{min(v['stage1_accuracy_on_generated'] for v in G['basic'].values()) * 100:.1f} % to {max(v['stage1_accuracy_on_generated'] for v in G['basic'].values()) * 100:.1f} %, which means that the classifier agrees with the condition only for angry, fear and sad and almost never for happy, surprise, disgust or neutral. "
            f"For the compound conditions the classifier's top class lies in the intended pair for {pc(G['mean_compound_top1_in_pair'], 1)} of faces (chance {pc(G['chance_top1_in_pair'], 1)}) and its top two classes equal the pair for {pc(G['mean_compound_top2_equals_pair'], 1)} (chance {pc(G['chance_top2_equals_pair'], 1)}); "
            f"the best pairs are sadly fearful and sadly angry ({G['compound']['sadly_fearful']['stage1_top1_in_pair'] * 100:.0f} % and {G['compound']['sadly_angry']['stage1_top1_in_pair'] * 100:.0f} %), while happily surprised ({G['compound']['happily_surprised']['stage1_top1_in_pair'] * 100:.0f} %), happily disgusted ({G['compound']['happily_disgusted']['stage1_top1_in_pair'] * 100:.0f} %) and disgustedly surprised ({G['compound']['disgustedly_surprised']['stage1_top1_in_pair'] * 100:.0f} %) are essentially never recognised."),
          fig("fig_gan_fidelity.png", "Condition fidelity of the generator, judged by the stage-1 classifier: one-hot conditions (left) and compound conditions (right).", 5.6),
          P(f"Second, **how far are generated faces from real ones?** The Fréchet distance between 2,800 generated faces and 2,800 real training faces, computed in the 256-dimensional feature space of the stage-1 CNN, is {fr['generated_basic_vs_real_train_subset']:.1f} for the one-hot conditions "
            f"and {fr['generated_compound_vs_real_train_subset']:.1f} for the compound conditions, against {fr['real_test_vs_real_train_subset']:.1f} for real test faces measured the same way. This is not an Inception-based FID [{C['fid']}] and its values are not comparable with published FIDs; "
            f"it only says that generated faces are roughly {fr['generated_basic_vs_real_train_subset'] / fr['real_test_vs_real_train_subset']:.0f} times further from the real distribution than a real held-out face is. The pixel-wise standard deviation within a class is {G['pixelwise_std_within_class']['generated']:.1f} for generated and "
            f"{G['pixelwise_std_within_class']['real']:.1f} for real faces, so the generator has not collapsed to a single image, but in the grids the variation looks mostly like changes in brightness and blur rather than in facial structure."),
          P(f"The base paper's generator adds an encoder that keeps a face's identity while the label changes, and reports that 94-99 % of generated images keep an identity similarity above 0.7 [{C['base']}]. Mosaic's generator has no encoder and no identity input: the latent vector is random noise, "
            "so identity preservation, the core of objective 1, is neither implemented nor measured.")]

    # ------------------------------------------------------------------ 8.7
    b += [H2("8.7 Comparison with the base paper and related work"),
          P(f"The base paper [{C['base']}] reports, for its recogniser trained on cEmoGAN images, f-beta scores of 0.99, 0.99 and 0.80 and exact-match ratios of 100 %, 99 % and 68.7 % on CK+, JAFFE and MUG, against 0.45, 0.60 and 0.51 f-beta for an EfficientNet-B0 baseline. "
            "**These numbers cannot be compared with Mosaic's**, for four reasons, stated here as plainly as possible:"),
          N("**Different data.** The base paper uses three laboratory datasets (CK+, JAFFE, MUG) and, for MUG at least, builds two-emotion ground truth by morphing peak frames; Mosaic uses FER2013, 36,000 uncontrolled web faces at 48 x 48 pixels with basic labels only.",
            "**Different test images.** The base paper scores its recogniser on a 30 % split of 15,000 images produced by the same generator that produced its training images; Mosaic's basic-emotion figures are on real held-out photographs, and its only compound figures are on a generated hold-out.",
            "**Different labels.** The base paper's compound classes have morphed ground truth; Mosaic has none for real faces.",
            "**Different resources.** The base paper trained on an Intel i9-9900K with an NVIDIA RTX A6000; Mosaic's generator was trained for ten epochs on a CPU."),
          P(f"The one place where the two evaluations are of the same kind is the generated hold-out. There the base paper obtains exact-match ratios of 68.7-100 % and Mosaic obtains {fm['0.5']['exact_match_ratio']:.3f} at every threshold (best micro-F1 {fm[best_t]['micro_f1']:.3f}) and chance-level compound ROC-AUC: "
            "the reproduction of the *idea* (generate compound faces, train a multi-label CNN on them) did not reproduce the *result*. The reasons are the generator's weakness (Section 8.6), the very small share of synthetic data, and the absence of the encoder."),
          TAB("Mosaic against the base paper and the related results quoted in this report.",
              ["Work", "Data and labels", "Test images", "Reported result", "Comparable with Mosaic?"],
              [[f"Khine et al. [{C['base']}]", "CK+, JAFFE, MUG; morphed compound labels", "Generated by their cEmoGANs", "f-beta 0.99 / 0.99 / 0.80; EMR 100 / 99 / 68.7 %", "No (different data and test images)"],
               [f"Galkaduwa [{C['galkaduwa']}]", "FER-2013, 7 basic labels", "FER-2013 test split", "CNN 51.6 %, HOG+SVM 44.0 %, LBP 25.0 %", "Loosely (same dataset, own split)"],
               [f"Liu et al. [{C['abaw7']}]", "RAF-DB compound, 7 classes, real labels", "RAF-DB validation", "Accuracy 60.4-64.3 %, F1 51.5-55.4 %", "No (real compound labels, other data)"],
               ["Mosaic baseline", "FER2013, 7 basic labels", "FER2013 test (7,178)", f"{pc(Bs['accuracy'], 1)}, macro-F1 {Bs['macro_f1']:.3f}", "-"],
               ["Mosaic final model", "FER2013, 7 basic labels", "FER2013 test (7,178)", f"{pc(Fn['accuracy'], 1)}, macro-F1 {Fn['macro_f1']:.3f}", "-"],
               ["Mosaic compound outputs", "Synthetic compound labels only", "Generated hold-out (1,100)", f"EMR {fm['0.5']['exact_match_ratio']:.3f}; compound AUC {fm['0.5']['compound_roc_auc_macro']:.2f}", "Same kind as the base paper's; far lower"]],
              widths=[1.3, 1.4, 1.2, 1.5, 1.3], align=["l", "l", "l", "l", "l"], size=8.5)]

    # ------------------------------------------------------------------ 8.8
    b += [H2("8.8 Face detection and the serving path"),
          P(f"The product does not classify the uploaded image directly: a Haar cascade must first find a face. On enlarged FER2013 faces it succeeds for {pc(D['haar_detection_rate_scale_3x'], 0)} of images (3x) and for none of the native 48-pixel images; "
            f"on the {D['detected_at_3x']} detected faces the final model scores {pc(D['accuracy_via_haar_crop_on_detected'], 1)} through the product path, against {pc(D['accuracy_direct_64px_on_same_images'], 1)} when the same images are resized directly "
            f"(Figure in Chapter 7). A real user's photograph is larger and sharper than a FER2013 face, so the detection rate on such photographs would probably be higher, but this was not measured: no photograph from outside the dataset was used."),
          P(f"End-to-end the API answers an analysis in {next(l for l in F.APIM['latency'] if 'anonymous' in l['label'])['p50_ms']:.0f} ms at the median (Chapter 7), so the cost of classification is negligible against the cost of getting a usable face into the network.")]

    # ------------------------------------------------------------------ 8.9
    b += [H2("8.9 Success and failure analysis"),
          H3("8.9.1 What worked"),
          B(f"A complete application: registration, token authentication, upload and webcam capture, a seven-bar basic chart, a compound panel, a dominant card, per-user history with thumbnails, all running locally, {F.TESTS['tests']} automated tests passing.",
            f"Basic-emotion recognition at {pc(Fn['accuracy'], 1)} accuracy, with happy and surprise recognised well (F1 {pcF['happy']['f1']:.2f} and {pcF['surprise']['f1']:.2f}).",
            f"Fast serving: {next(l for l in F.APIM['latency'] if 'anonymous' in l['label'])['p50_ms']:.0f} ms median per analysis on a CPU.",
            "A reproducible measurement set: every number in this chapter is regenerated by two scripts from the stored checkpoints and the dataset."),
          H3("8.9.2 What failed"),
          B(f"**Compound emotions**: inert on real faces (maximum compound probability {cp['mean_top_compound_confidence']:.5f}) and at chance level on generated faces (ROC-AUC {fm['0.5']['compound_roc_auc_macro']:.2f}); the dominant label is never a compound.",
            f"**The generator** does not follow its condition ({pc(G['mean_basic_conditional_accuracy'], 0)} against 14 % chance) and produces blurred faces.",
            f"**Disgust** is recalled for only {pc(pcF['disgust']['recall'], 0)} of faces and fear confused with sad; neutral is often read as sad or fear (screen 12).",
            f"**Face detection** misses {pc(1 - D['haar_detection_rate_scale_3x'], 0)} of enlarged faces, and the crop it produces lowers accuracy by about {(D['accuracy_direct_64px_on_same_images'] - D['accuracy_via_haar_crop_on_detected']) * 100:.0f} points.",
            "**Interface defects**: broken thumbnail on every result card, unreachable history-detail page, redirect to the login page on a hard reload, no-face answered 200 where the contract says 422, undecodable uploads answered 500."),
          ]

    # ------------------------------------------------------------------ 8.10
    b += [H2("8.10 Limitations of these results"),
          B("**Single dataset**: FER2013 only; no other basic-emotion dataset and no compound dataset was available (RAF-DB, which has compound labels, was not available to this project).",
            "**No compound ground truth on real faces**, hence no accuracy for the product's headline feature.",
            f"**Few seeds**: {len(ro)} seeds per ablation arm; differences below about 2 points cannot be resolved.",
            "**The test set doubles as validation** in the training scripts' printout; it was not used for selection here, but there is no separate validation split.",
            "**Short training**: five epochs per stage and a ten-epoch GAN on a CPU; longer training might change both the basic accuracy and the generator, but this was not tried.",
            "**FER2013 label noise**: the labels of FER2013 are noisy, so the attainable accuracy is well below 100 %; no human-accuracy figure was measured here.",
            "**No real-world photographs and no users**: the walk-through uses dataset faces and generated faces only."),
          ]

    # ------------------------------------------------------------------ 8.11
    sw = f"{pc(statistics.mean(acc_r), 1)} real-only against {pc(statistics.mean(acc_s), 1)} with synthetic faces"
    b += [H2("8.11 Objectives versus outcomes"),
          TAB("The five objectives of the batch and what was measured.",
              ["No.", "Objective", "Outcome", "Evidence"],
              [["1", "Generate identity-preserving facial images with complex emotions using cEmoGANs", "**Not achieved.** A conditional GAN exists and was trained, but it has no identity encoder and does not obey its condition",
                f"{pc(G['mean_basic_conditional_accuracy'], 0)} condition accuracy (chance 14 %); Fréchet distance {fr['generated_basic_vs_real_train_subset']:.0f} vs {fr['real_test_vs_real_train_subset']:.0f}"],
               ["2", "Enlarge the complex-emotion dataset with generated images", "**Partly.** 2,200 synthetic compound images were produced and added to the training set, but they are not distinguishable by class and carry no real labels",
                f"Compound ROC-AUC {fm['0.5']['compound_roc_auc_macro']:.2f}; no effect on basic accuracy ({sw})"],
               ["3", "Train a CNN multi-label classifier for basic and complex emotions", "**Implemented**; basic emotions work, compound outputs are inert",
                f"{pc(Fn['accuracy'], 1)} basic accuracy; maximum compound probability {cp['mean_top_compound_confidence']:.5f} on real faces"],
               ["4", "Evaluate recognition performance against single-label baselines", "**Done, with caveats.** The multi-label model beats the single-label baseline, but a real-only control shows that the extra epochs, not the synthetic images, explain the gain",
                f"{pc(Bs['accuracy'], 1)} -> {pc(Fn['accuracy'], 1)}; ablation {sw}"],
               ["5", "Provide an interface for emotion recognition from uploaded images", "**Achieved** (with the front-end defects of Chapter 7)",
                f"19 captured screens; {F.TESTS['tests']} tests pass; median analysis {next(l for l in F.APIM['latency'] if 'anonymous' in l['label'])['p50_ms']:.0f} ms"]],
              widths=[0.4, 1.7, 2.3, 2.1], align=["c", "l", "l", "l"], size=9)]

    # ------------------------------------------------------------------ 8.12
    b += [H2("8.12 Summary of findings"),
          N(f"Mosaic recognises the seven basic emotions at {pc(Fn['accuracy'], 1)} accuracy (macro-F1 {Fn['macro_f1']:.3f}) on {F.DATA['n_test']:,} real FER2013 faces, {(Fn['accuracy'] - Bs['accuracy']) * 100:.1f} points above its single-label baseline.",
            f"The gain comes from additional training, not from the generated faces: real-only retraining scores {pc(statistics.mean(acc_r), 1)} (± {statistics.stdev(acc_r) * 100:.1f}) and retraining with synthetic faces {pc(statistics.mean(acc_s), 1)} (± {statistics.stdev(acc_s) * 100:.1f}).",
            "The compound-emotion output, the purpose of the project, is not functional: it is zero on real faces and cannot rank compound classes on synthetic ones.",
            "The conditional GAN is under-trained and ignores most of its condition; identity preservation was not implemented.",
            "The application around the model works and is fast, with a short list of front-end and API defects documented in Chapter 7.",
            "A faithful reproduction of the base paper's result would need an identity-preserving generator trained far longer on a laboratory dataset, a real compound test set, and a larger share of compound data in training; these are taken up in Chapter 10.")]
    return b
