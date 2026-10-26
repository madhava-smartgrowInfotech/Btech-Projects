"""Chapter 8: Results and Output Screens (also document 14). Every number is built from facts.py (experiments/plantdoc/*.json)."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, PAIR, TAB
from .refs import cite

HC, HG, H0 = F.HC, F.HG, F.H0
C, CS, CT, MB, BL = F.C, F.CS, F.CT, F.MB, F.BL
RF, LR = BL["random_forest"], BL["logistic_regression"]
LAT = F.LAT
HCONF = F.HCONF
HALL = F.H


def pc(x, d=1):
    return f"{x * 100:.{d}f} %"


def mp(blk, key="accuracy", d=1):
    """mean +/- std in percent"""
    return F.pm(blk, key, d).replace("%", " %")


def mf(blk, key="macro_f1", d=3):
    return f"{blk[key]['mean']:.{d}f} ± {blk[key]['std']:.{d}f}"


def screen(name, caption, base=5.4, max_h=3.4):
    p = F.shot(name)
    return FIG(p, caption, F.shot_w(p, base, max_h))


def shot_pair(left, right, cap_l, cap_r, width=3.0):
    return PAIR([(F.shot(left), cap_l), (F.shot(right), cap_r)], width)


# sample inputs and outputs: PlantDoc test photographs run through predict() with PYTHONHASHSEED=0 (what run.bat uses), crop chosen as in the dataset folder
SAMPLES = [
    ["Apple_Scab_Leaf / 02343", "apple", "Apple - Apple scab", "97.2 %", "correct"],
    ["Corn_rust_leaf / 02432", "corn", "Corn (maize) - Common rust", "97.2 %", "correct"],
    ["Corn_leaf_blight / 02413", "corn", "Corn (maize) - Northern leaf blight", "97.2 %", "correct"],
    ["grape_leaf_black_rot / 02572", "grape", "Grape - Black rot", "91.4 %", "correct"],
    ["Potato_leaf_early_blight / 02448", "potato", "Potato - Early blight", "97.2 %", "correct"],
    ["Tomato_mold_leaf / 02554", "tomato", "Tomato - Leaf Mold", "97.2 %", "correct"],
    ["Tomato_leaf_late_blight / 02526", "tomato", "Tomato - healthy", "97.2 %", "wrong: a blighted leaf called healthy"],
    ["Apple_rust_leaf / 02361", "apple", "Apple - healthy", "97.2 %", "wrong: rust called healthy"],
    ["Tomato_leaf_bacterial_spot / 02517", "tomato", "Tomato - Leaf Mold", "97.2 %", "wrong: bacterial spot called mould"],
    ["Tomato_leaf_mosaic_virus / 02536", "tomato", "Tomato - healthy", "97.2 %", "wrong: mosaic virus called healthy"],
    ["Squash_Powdery_mildew_leaf / 02475", "squash", "no answer (HTTP 400 'could not be read as an image')", "-", "defect D1"],
    ["Blueberry_leaf / 02388", "blueberry", "no answer (HTTP 400 'could not be read as an image')", "-", "defect D1"],
]


def blocks():
    n_cls_test = 27
    best3 = sorted(((n, v) for n, v in MB["first_run"]["per_class"].items() if v["support"]), key=lambda kv: -kv[1]["f1"])[:6]
    worst = sorted(((n, v) for n, v in MB["first_run"]["per_class"].items() if v["support"]), key=lambda kv: kv[1]["f1"])[:6]
    cnn_best = sorted(((n, v) for n, v in C["first_run"]["per_class"].items() if v["support"]), key=lambda kv: -kv[1]["f1"])[:3]
    zero_f1 = sum(1 for n, v in C["first_run"]["per_class"].items() if v["support"] and v["f1"] == 0)
    d_ = F.DS["counts"]

    out = [
        H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS"),
        P("This chapter reports what AgriVision does when it is run: the screens a farmer sees, followed by the measured accuracy of the diagnosis. The two must be read together. The screens show a complete, "
          "working application. The measurements show that the diagnosis engine installed in it is not accurate, and what accuracy a trained network can reach on the same photographs. "
          "All accuracy figures are measured on the 236 photographs of the PlantDoc test folder; none of these photographs was used to fit or to select any model."),

        H2("8.1 What was measured and how"),
        P(f"Four things were measured, all by `scripts/run_experiments.py` on {F.HARDWARE}; software versions are listed in Chapter 6."),
        TAB("Engines evaluated", ["Engine", "What it is", "In the application?", "Runs"],
            [["Heuristic", "Colour and texture score in `agrivision/inference.py`", "yes (the only engine that ships)", "5 `PYTHONHASHSEED` values; 0 is what `run.bat` uses"],
             ["Compact CNN", "Network of `agrivision/train.py`, 189,655 parameters, trained here", "no (`agrivision/models/` is empty)", "3 seeds (42, 43, 44); 10 % of the training folder held out for early stopping"],
             ["MobileNetV2", "ImageNet weights, new 27-way head, top 30 layers fine-tuned", "no (reference experiment)", "3 seeds"],
             ["Colour/texture classifiers", "Random forest and logistic regression on hand-made features", "no (baseline)", "1 run each (seed 42)"]],
            widths=[1.3, 2.6, 1.5, 1.7], align=["l", "l", "l", "l"], size=9),
        P(f"Metrics: top-1 accuracy, top-3 accuracy, macro-F1 (mean of the per-class F1 over the {n_cls_test} classes that have test photographs), crop-level accuracy (was the right crop named?) and healthy-versus-diseased "
          f"accuracy. Chance and trivial baselines for the same split: always answering the most frequent class (Corn leaf blight, 12 photographs) gives {pc(HALL['majority_class_test'])}; guessing uniformly among the 38 classes "
          f"gives {pc(HALL['chance_general'])}; guessing uniformly among the candidate classes of the right crop gives {pc(HALL['chance_with_crop_hint'])}; always answering 'diseased' gives 61.9 % healthy-versus-diseased accuracy."),

        H2("8.2 Output screens"),
        P("The screens were captured at 1440 x 900 pixels (one at phone width) from the running application, signed in as the demonstration farmer, with real PlantDoc test photographs uploaded through the interface "
          "or the API so that the dashboard, history and analytics are not empty. Every result shown was produced by the heuristic engine; the sidebar says so on every screen ('Engine: colour/texture heuristic. No trained "
          "CNN is installed, so treat results as a first screen and confirm with your agri officer')."),
        H3("8.2.1 Landing, registration and sign-in"),
        shot_pair("01_landing_dark.png", "01_landing_light.png", "Landing page, dark theme: headline, call to action and the live counters (38 classes recognised).", "Landing page, light theme; the theme choice is remembered between visits.", 3.0),
        shot_pair("03_register.png", "06_login.png", "Register: name, email, password, region, language and main crop; the account is created with the role 'farmer'.", "Sign in, with the demonstration account shown as a hint; a wrong password shows the API's message.", 3.0),
        H3("8.2.2 Diagnosis"),
        shot_pair("02_landing_how_it_works.png", "07_detect_ready.png", "Landing page, 'how it works': upload, analyse, act - the three steps the application really performs.",
                  "Detect screen with a PlantDoc leaf chosen and the crop selected: JPG, PNG, JPEG or WEBP up to 10 MB are accepted.", 3.0),
        shot_pair("15_result_correct.png", "08_result.png", "Result for a Potato early blight photograph (correct): the top-1 class, severity high, 'urgent action' badge, the top-3 list and the engine note.",
                  "Result for a Tomato late blight photograph: the engine answers 'Tomato - healthy' with 97.20 %, a wrong answer shown with the same confidence as a right one.", 3.0),
        P("Both results show the same layout: the class, a confidence bar labelled 'Heuristic score (not a calibrated probability)', the top-3 predictions, the amber engine note, buttons for CSV, PDF, print and share, "
          "then the symptoms, lifecycle, prevention and the recommended treatments (chemical, organic and cultural, each with a cost per acre in rupees). For the correct case the advice is the knowledge-base card for early blight; "
          "for the wrong case it is the card for a healthy tomato, 'No treatment needed', which is the harm a wrong answer does."),
        shot_pair("16_error_blueberry.png", "12_profile.png", "Detect with the crop set to Blueberry: 'The diagnosis failed. That file could not be read as an image' for a valid photograph (defect D1).",
                  "Profile: name, region, interface language (English, Hindi, Marathi) and crops of interest; the language is saved to the account.", 3.0),
        H3("8.2.3 Dashboard, history, analytics and profile"),
        shot_pair("09_dashboard.png", "14_dashboard_light.png", "Dashboard, dark: total scans, healthy count, high-severity count, disease rate, quick actions and recent detections.", "Dashboard, light theme.", 3.0),
        shot_pair("10_history.png", "11_analytics.png", "History: one card per scan with image, class, severity, score and date; search, crop filter, All / Diseased / Healthy switch, per-scan PDF and delete, CSV export.",
                  "Analytics: disease distribution, severity split and a timeline of scans from the user's own history (Recharts).", 3.0),
        H3("8.2.4 Disease guide"),
        shot_pair("04_encyclopedia.png", "05_disease_detail.png", "Disease guide: the 38 classes with search and crop filter; it needs no sign-in.", "Disease detail (Tomato late blight): symptoms, lifecycle, three treatment options with costs and prevention.", 3.0),
        H3("8.2.5 Other languages and phone width"),
        shot_pair("17_dashboard_hindi.png", "18_mobile_dashboard.png", "Dashboard with the Hindi interface: menus, headings and counters are translated; the sentences below them stay in English because only 44 interface strings are translated.",
                  "Dashboard at phone width (390 x 844 px, Hindi interface): the sidebar becomes a bottom navigation bar and the cards stack in one column.", 2.9),

        H2("8.3 Dataset used for the measurements"),
        P(f"PlantDoc {cite('plantdoc')} is a set of photographs of leaves collected from the web, with real backgrounds, hands, soil, several leaves per photograph and uneven lighting. The local copy has "
          f"{F.NTRAIN:,} training and {F.NTEST} test photographs in 28 training folders; the test folder has 27 because it contains no photograph of Tomato two-spotted spider mites (the training folder has only two). "
          f"Class sizes range from 2 to {max(d_['train'].values())} training photographs (Figure below); the test folder has 4 to 12 photographs per class, so one photograph moves a class's recall by 8 to 25 percentage points. "
          f"Ten of the folders are healthy leaves and 18 are diseased; the test set holds 90 healthy and 146 diseased photographs."),
        FIG(F.fig("f09_class_distribution.png"), "PlantDoc class sizes in the local copy: 28 training folders and 27 test folders.", 4.6),
        P("The 28 folders map one to one onto the 38 classes of the knowledge base; ten knowledge-base classes (for example Apple black rot, Grape esca, Potato healthy, Tomato target spot) have no PlantDoc photograph "
          "and could not be measured."),

        H2("8.4 The diagnosis engine that ships: the heuristic"),
        P(f"With the right crop chosen, as a farmer would, the heuristic names the correct class for {mp(HC)} of the test photographs (mean and standard deviation over five hash seeds; "
          f"{pc(H0['accuracy'])} with seed 0, the value `run.bat` fixes). The right class is among its top three for {mp(HC, 'top3_accuracy')}, the right crop is named for {mp(HC, 'crop_accuracy')} and the macro-F1 is "
          f"{mf(HC)}. With the crop left on 'general' it names the correct class for {mp(HG)}, below the {pc(HALL['chance_general'])} expected from guessing among 38 classes."),
        TAB("Heuristic engine on the PlantDoc test split (236 photographs; five hash seeds)", ["Measure", "Crop chosen", "Crop 'general'"],
            [["Top-1 accuracy", mp(HC), mp(HG)],
             ["Top-3 accuracy", mp(HC, "top3_accuracy"), mp(HG, "top3_accuracy")],
             ["Macro-F1", mf(HC), mf(HG)],
             ["Right crop named", mp(HC, "crop_accuracy"), mp(HG, "crop_accuracy")],
             ["Healthy-versus-diseased accuracy", mp(HC, "healthy_vs_diseased_accuracy"), mp(HG, "healthy_vs_diseased_accuracy")],
             ["Healthy leaves called healthy", mp(HC, "healthy_recall"), mp(HG, "healthy_recall")],
             ["Diseased leaves called diseased", mp(HC, "diseased_recall"), mp(HG, "diseased_recall")],
             ["Photographs given no answer", pc(HC["failed_share"]["mean"]), pc(HG["failed_share"]["mean"])],
             ["Top-1 accuracy among answered photographs", mp(HC, "accuracy_on_answered"), mp(HG, "accuracy_on_answered")]],
            widths=[3.0, 1.9, 1.9], align=["l", "c", "c"], size=9.5),
        P(f"Three findings follow. First, the accuracy is below what guessing within the right crop would give ({pc(HALL['chance_with_crop_hint'])}); part of the reason is the {pc(HC['failed_share']['mean'])} of photographs on which "
          f"the engine fails (defect D1), but even among the photographs it answers only {mp(HC, 'accuracy_on_answered')} are right. Second, the engine does not separate healthy from diseased leaves: only "
          f"{mp(HC, 'healthy_recall')} of healthy leaves are called healthy, and the healthy-versus-diseased accuracy of {mp(HC, 'healthy_vs_diseased_accuracy')} is lower than the 61.9 % obtained by always saying 'diseased'. "
          f"Third, the answers are stable with respect to the only random element, the hash jitter: the standard deviation over five hash seeds is about one percentage point, so the low accuracy is not a seed effect."),

        H2("8.5 The compact CNN of the training script"),
        P(f"`agrivision/train.py` defines a small network of five depthwise-separable convolution blocks with batch normalisation, max pooling and dropout, a global-average-pooling head and a 256-unit dense layer, "
          f"with flip, rotation, zoom and contrast augmentation inside the model. Counted by TensorFlow it has {C['params']['mean']:,.0f} parameters (the script's docstring says about 1.1 million, defect D6). "
          f"It was trained on the 224 x 224 photographs with Adam at 1e-3, batch 32, up to 60 epochs with early stopping on the validation accuracy (patience 8) and learning-rate halving on a validation-loss plateau, "
          f"for three seeds. Validation data were 10 % of the training folder, chosen per seed, never the test folder."),
        TAB("Compact CNN on the PlantDoc test split", ["Run", "Accuracy", "Macro-F1", "Top-3", "Right crop", "Healthy vs diseased", "Epochs", "Train time"],
            [["Held-out validation, 3 seeds", mp(C), mf(C), mp(C, "top3_accuracy"), mp(C, "crop_accuracy"), mp(C, "healthy_vs_diseased_accuracy"), f"{C['epochs_run']['mean']:.0f}", f"{C['train_seconds']['mean']:.0f} s"],
             ["Shipped protocol (test folder as validation), seed 42", pc(CS["accuracy"]["mean"]), f"{CS['macro_f1']['mean']:.3f}", pc(CS["top3_accuracy"]["mean"]), pc(CS["crop_accuracy"]["mean"]), pc(CS["healthy_vs_diseased_accuracy"]["mean"]), f"{CS['epochs_run']['mean']:.0f}", f"{CS['train_seconds']['mean']:.0f} s"],
             ["No learning-rate decay, patience 20, seed 42", pc(CT["accuracy"]["mean"]), f"{CT['macro_f1']['mean']:.3f}", pc(CT["top3_accuracy"]["mean"]), pc(CT["crop_accuracy"]["mean"]), pc(CT["healthy_vs_diseased_accuracy"]["mean"]), f"{CT['epochs_run']['mean']:.0f}", f"{CT['train_seconds']['mean']:.0f} s"]],
            widths=[2.0, 0.75, 0.75, 0.7, 0.7, 0.8, 0.55, 0.65], align=["l", "c", "c", "c", "c", "c", "c", "c"], size=8.5),
        P(f"The network learns very little: training accuracy is only {mp(C, 'train_accuracy')} and the best validation accuracy {mp(C, 'best_val_accuracy')}, so it under-fits rather than memorises. Neither the shipped "
          f"protocol (which selects checkpoints on the test photographs and so cannot be taken at face value, defect D5) nor a variant without learning-rate decay changes the picture: all runs lie between 11 and 14 % "
          f"accuracy. On the test set {zero_f1} of the {n_cls_test} classes have F1 = 0 for seed 42; the best are " + ", ".join(f"{n.replace('_', ' ')} ({v['f1']:.2f})" for n, v in cnn_best) + ". The network does separate healthy from "
          f"diseased better than the heuristic ({mp(C, 'healthy_vs_diseased_accuracy')}) but mostly by calling leaves diseased (diseased recall {mp(C, 'diseased_recall')}, healthy recall {mp(C, 'healthy_recall')}). "
          f"A single photograph takes a median of {C['latency_ms_median']['mean']:.0f} ms on the CPU."),
        FIG(F.fig("f04_cnn_training_curves.png"), "Training and validation accuracy and loss of the compact CNN, seed 42: both stay low.", 5.4),

        H2("8.6 MobileNetV2 with ImageNet weights"),
        P(f"As a reference for what the same data can support, MobileNetV2 {cite('mobilenet')} pre-trained on ImageNet {cite('imagenet')} was given a new 28-way output layer. First only the head was trained (up to 20 epochs, "
          f"learning rate 1e-3), then the last 30 layers were unfrozen and trained at 1e-4 (up to 12 epochs), with the same augmentation and the same 10 % validation split. This is not part of the application; "
          f"it measures what is within reach. The model has {MB['params']['mean']:,.0f} parameters, trained in {MB['train_seconds']['mean']:.0f} s on average and needs a median of {MB['latency_ms_median']['mean']:.0f} ms per photograph on the CPU."),
        TAB("MobileNetV2 on the PlantDoc test split (3 seeds)", ["Stage", "Accuracy", "Macro-F1", "Top-3", "Right crop", "Healthy vs diseased"],
            [["Head only", mp(MB, "head_only_accuracy"), mf(MB, "head_only_macro_f1"), "-", "-", "-"],
             ["Head + top 30 layers fine-tuned", mp(MB), mf(MB), mp(MB, "top3_accuracy"), mp(MB, "crop_accuracy"), mp(MB, "healthy_vs_diseased_accuracy")]],
            widths=[2.2, 1.0, 1.1, 0.9, 0.9, 1.2], align=["l", "c", "c", "c", "c", "c"], size=9.5),
        P(f"Accuracy is {mp(MB)} with macro-F1 {mf(MB)}; the right class is among the top three for {mp(MB, 'top3_accuracy')} of the photographs, the right crop is named for {mp(MB, 'crop_accuracy')} "
          f"and healthy and diseased leaves are told apart {mp(MB, 'healthy_vs_diseased_accuracy')} of the time (healthy recall {mp(MB, 'healthy_recall')}, diseased recall {mp(MB, 'diseased_recall')}). "
          f"Fine-tuning adds only about {(MB['accuracy']['mean'] - MB['head_only_accuracy']['mean']) * 100:.1f} points over the head alone. The three seeds give "
          + ", ".join(f"{v * 100:.1f} %" for v in MB["accuracy"]["values"]) + f" (Figure below), against " + ", ".join(f"{v * 100:.1f} %" for v in C["accuracy"]["values"]) + " for the compact CNN."),
        TAB("Best and worst classes of MobileNetV2 (seed 42, F1 on the test photographs)", ["Best", "F1", "n", "Worst", "F1", "n"],
            [[b[0].replace("_", " "), f"{b[1]['f1']:.2f}", str(b[1]["support"]), w[0].replace("_", " "), f"{w[1]['f1']:.2f}", str(w[1]["support"])] for b, w in zip(best3, worst)],
            widths=[2.3, 0.5, 0.4, 2.5, 0.5, 0.4], align=["l", "c", "c", "l", "c", "c"], size=9),
        P("The easy classes are those with a distinctive crop and a large visible symptom (Strawberry, grape leaves and grape black rot, corn rust, raspberry, squash powdery mildew). The classes with F1 = 0 "
          "(tomato bacterial spot, tomato mosaic virus and bell pepper leaf spot) are diseases that look alike on a small leaf photograph: in the confusion matrix (Figure below) six of the nine bacterial-spot photographs are called Septoria leaf spot, three of the ten mosaic-virus photographs are called leaf mould, and the nine bell-pepper leaf-spot photographs are scattered over several tomato and apple classes. "
          "This agrees with the PlantDoc authors' remark that Tomato bacterial spot and Septoria are hard to separate by visual features alone."),
        FIG(F.fig("f02_confusion_matrix_mobilenet.png"), "Confusion matrix of MobileNetV2 (seed 42) on the 236 test photographs; the diagonal holds the correct answers.", 5.2),
        FIG(F.fig("f03_per_class_f1.png"), "Per-class F1 of MobileNetV2 and of the compact CNN (seed 42); the number of test photographs is in brackets.", 5.0),
        FIG(F.fig("f10_seed_variation.png"), "Test accuracy of the three training seeds of each network: the gap between the networks is far larger than the variation between seeds.", 4.4),

        H2("8.7 Colour-and-texture classifiers"),
        P(f"To see how much a classifier can get from the same kind of cues as the heuristic, a random forest ({cite('rf')}, 300 trees) and a logistic regression were trained on 43 hand-made features per photograph (HSV histograms, "
          f"grey-level mean and spread, edge-magnitude statistics and per-channel means and spreads). The random forest reaches {pc(RF['accuracy'])} accuracy with macro-F1 {RF['macro_f1']:.3f}, top-3 {pc(RF['top3_accuracy'])}, "
          f"right crop {pc(RF['crop_accuracy'])} and healthy-versus-diseased accuracy {pc(RF['healthy_vs_diseased_accuracy'])}; the logistic regression reaches {pc(LR['accuracy'])} (macro-F1 {LR['macro_f1']:.3f}). "
          "Learning the weights from data roughly doubles what hand-set weights achieve, which supports the conclusion that the heuristic's rules, not just the dataset, are the weak point. Both stay far below a pre-trained network."),

        H2("8.8 Comparison of all engines"),
        TAB("All engines on the PlantDoc test split", ["Engine", "Accuracy", "Macro-F1", "Top-3", "Right crop", "Healthy vs diseased"],
            [["Always the most frequent class", pc(HALL["majority_class_test"]), "-", "-", "-", "61.9 %"],
             ["Shipped heuristic, crop chosen", mp(HC), mf(HC), mp(HC, "top3_accuracy"), mp(HC, "crop_accuracy"), mp(HC, "healthy_vs_diseased_accuracy")],
             ["Shipped heuristic, crop 'general'", mp(HG), mf(HG), mp(HG, "top3_accuracy"), mp(HG, "crop_accuracy"), mp(HG, "healthy_vs_diseased_accuracy")],
             ["Logistic regression on colour/texture", pc(LR["accuracy"]), f"{LR['macro_f1']:.3f}", pc(LR["top3_accuracy"]), pc(LR["crop_accuracy"]), pc(LR["healthy_vs_diseased_accuracy"])],
             ["Compact CNN of train.py (3 seeds)", mp(C), mf(C), mp(C, "top3_accuracy"), mp(C, "crop_accuracy"), mp(C, "healthy_vs_diseased_accuracy")],
             ["Random forest on colour/texture", pc(RF["accuracy"]), f"{RF['macro_f1']:.3f}", pc(RF["top3_accuracy"]), pc(RF["crop_accuracy"]), pc(RF["healthy_vs_diseased_accuracy"])],
             ["MobileNetV2 head only (3 seeds)", mp(MB, "head_only_accuracy"), mf(MB, "head_only_macro_f1"), "-", "-", "-"],
             ["**MobileNetV2 fine-tuned (3 seeds)**", mp(MB), mf(MB), mp(MB, "top3_accuracy"), mp(MB, "crop_accuracy"), mp(MB, "healthy_vs_diseased_accuracy")]],
            widths=[2.4, 1.0, 1.0, 0.9, 0.9, 1.0], align=["l", "c", "c", "c", "c", "c"], size=8.5),
        FIG(F.fig("f01_model_comparison.png"), "Accuracy and macro-F1 of every engine measured, with chance and majority-class lines.", 5.8),
        FIG(F.fig("f05_healthy_vs_diseased.png"), "Healthy leaves called healthy and diseased leaves called diseased, per engine (the random forest's healthy recall was not stored).", 4.4),
        P(f"Only the transfer-learning network is clearly useful, at about {MB['accuracy']['mean'] * 100:.0f} % top-1 and {MB['top3_accuracy']['mean'] * 100:.0f} % top-3. The shipped heuristic is the worst engine measured; "
          "the compact CNN as scripted is barely better; the data themselves are the second limit, as the next section places it in context."),

        H2("8.9 Does the displayed confidence mean anything?"),
        P(f"Every result screen shows a confidence bar. For the {HCONF['n']} test photographs the heuristic can answer with the right crop chosen, the mean displayed confidence is {pc(HCONF['mean_conf'], 0)}, "
          f"because the engine maps its score into the range 0.62 to 0.99 and most photographs saturate near 0.972. Accuracy within the confidence bins is {HCONF['acc_by_bin'][1]:.0f} % for 0.80 to 0.90 (n = {HCONF['count_by_bin'][1]}), "
          f"{HCONF['acc_by_bin'][2]:.0f} % for 0.90 to 0.95 (n = {HCONF['count_by_bin'][2]}) and {HCONF['acc_by_bin'][3]:.0f} % for 0.95 to 1.00 (n = {HCONF['count_by_bin'][3]}); there is no photograph below 0.80. "
          f"The most confident bin is not the most accurate. In addition the three scores shown for a photograph add up to more than 102 % on {pc(HCONF['share_sum_over_102'], 0)} of these photographs and reach "
          f"{pc(HCONF['max_sum'], 0)} (defect D2). The interface compensates in part: the bar is labelled 'Heuristic score (not a calibrated probability)' and an amber note says that the score 'saturates near 97 % for most photos'. "
          "A farmer reading only the large number would still be misled."),
        FIG(F.fig("f07_heuristic_confidence.png"), "Left: accuracy of the heuristic within confidence bins. Right: sum of the three scores shown for each photograph.", 5.4),

        H2("8.10 Comparison with the base paper and the companion papers"),
        P(f"The base paper chosen by the batch, Foliagen {cite('base')}, is a framework that generates annotated foliage images from single-leaf photographs and uses them to train and fine-tune VGG19, ResNet50, "
          f"DenseNet121, Swin Transformer and CBAM-ConvNeXt on soybean and tomato; it reports up to 98 % accuracy on natural soybean foliage when 5 % of that dataset is added to the generated data, on two RTX 6000 Ada GPUs. "
          f"AgriVision does not implement it: there is no image generation, no foliage-level image and no soybean foliage dataset here, and the numbers of the two works are not comparable. "
          f"What the project takes from the base paper is its motivation (disease classifiers trained on single-leaf photographs do not transfer to field images, and annotated field data are scarce) and its finding "
          f"that pre-training and fine-tuning help; the {MB['accuracy']['mean'] * 100:.0f} % of the fine-tuned MobileNetV2 against {C['accuracy']['mean'] * 100:.0f} % of the network trained from scratch is consistent with that."),
        TAB("Reported results and this project, with the differences stated", ["Work", "Task and data", "Reported result", "Comparable?"],
            [[f"Foliagen {cite('base')}", "Generated foliage images; soybean and tomato; natural foliage test set", "Up to 98 % with 5 % real images added", "No: different task, crops, data and GPUs"],
             [f"PD36-C {cite('pd36c')}", "Compact CNN, 1,250,694 parameters; New Plant Diseases Dataset, 87 k lab-style images, 38 classes", "99.53 % average test accuracy", "No: laboratory backgrounds, 38 classes, 37 times more images"],
             [f"Kanakala and Ningappa {cite('lstm')}", "CNN and LSTM; 70,295 training and 17,572 validation images, 38 classes", "CNN 96.4 % validation, LSTM 93.43 %", "No: random split of a lab-style collection"],
             [f"PlantDoc paper {cite('plantdoc')}", "Same photographs; VGG16, InceptionV3, InceptionResNetV2; 100 x 100 px", "Cropped leaves 44.5 to 70.5 %; raw photographs, VGG16, 13.7 to 29.7 %", "Closest: same data, different split and cropping"],
             ["AgriVision, shipped heuristic", "PlantDoc test split, crop chosen", mp(HC), "-"],
             ["AgriVision, compact CNN of train.py", "PlantDoc test split", mp(C), "-"],
             ["AgriVision, MobileNetV2 reference", "PlantDoc test split, raw uncropped photographs", mp(MB), "Inside the PlantDoc paper's range"]],
            widths=[1.5, 2.3, 1.6, 1.4], align=["l", "l", "l", "l"], size=8.5),
        P("The honest reading is that field photographs are much harder than the clean images behind the 96 to 99.5 % figures of the companion papers, that this project's best model sits where the PlantDoc authors' "
          "own models sit, and that the novelty of this project is the application around the diagnosis, not the accuracy."),

        H2("8.11 Sample inputs and outputs"),
        P("The table lists twelve PlantDoc test photographs, run through the application's `predict()` with the crop set to the photograph's own crop and `PYTHONHASHSEED=0`. 'Shown' is the top-1 answer and the "
          "confidence printed on the result screen."),
        TAB("Input photographs and what AgriVision printed", ["PlantDoc folder / file", "Crop chosen", "Top-1 shown", "Confidence", "Verdict"], SAMPLES,
            widths=[2.2, 0.8, 2.0, 0.8, 1.6], align=["l", "c", "l", "c", "l"], size=8.5),
        P("The correct answers come with the same 97.2 % as the wrong ones: the engine's score saturates, so the number cannot be used to tell them apart."),

        H2("8.12 Success and failure analysis"),
        H3("8.12.1 Where it works"),
        B("**Application behaviour.** All 39 integration checks pass; accounts, upload, history, search, exports, analytics and deletion behave as specified, a diagnosis returns in a median of "
          f"{LAT['detect_client_ms']['median']:.0f} ms on the test PC and the interface works from 360 to 1440 px.",
          "**Distinctive lesions on a known crop.** The heuristic is right on photographs with strong brown or yellow lesion colour on a large leaf, for example apple scab, corn rust, corn leaf blight, grape black rot, "
          "potato early blight and tomato leaf mould in the table above; 25 of the 160 answerable test photographs are named correctly.",
          f"**Transfer learning.** MobileNetV2 names the right class for about half of the photographs and the right crop for {MB['crop_accuracy']['mean'] * 100:.0f} %, and separates healthy from diseased leaves {MB['healthy_vs_diseased_accuracy']['mean'] * 100:.0f} % of the time."),
        H3("8.12.2 Where it fails"),
        B("**Diseased leaves called healthy.** The heuristic's healthy score rewards green area; a blighted leaf that is still mostly green is called healthy (late blight, rust and mosaic virus in the table). Only "
          f"{mp(HC, 'diseased_recall')} of diseased leaves are called diseased.",
          f"**Crop choices with fewer than three classes** give no answer at all ({pc(HC['failed_share']['mean'])} of the test photographs; screenshot 16).",
          "**Diseases that look alike.** Even the best model gives F1 = 0 for tomato bacterial spot, tomato mosaic virus and bell pepper leaf spot.",
          "**Rare classes.** Several classes with fewer than 60 training photographs are weak (bell pepper F1 0.17, tomato mosaic virus 0.00 for MobileNetV2), although some small classes (grape) are easy; Tomato two-spotted spider mites (2 training photographs, no test photograph) cannot be learned or measured.",
          "**Field conditions.** PlantDoc photographs have soil, hands, several leaves and watermarks (the potato example carries one); none of the models is told where the leaf is."),
        H2("8.13 Limitations of these results"),
        B("236 test photographs and 4 to 12 per class: one photograph changes a class's recall by 8 to 25 points, and the accuracy figures have a sampling error of several points that was not computed.",
          "Three training seeds for the compact CNN and MobileNetV2, one run for the shipped-protocol, no-decay and classical baselines; no significance test.",
          "The heuristic was evaluated with the crop supplied by the folder name; a farmer may choose wrongly, which would lower its figures further.",
          "PlantDoc is the only dataset; the local test folder is the official one (as shipped in the HF mirror) and shares no photograph with the training folder by construction, but PlantDoc is web-scraped and near-duplicates may exist; this was not checked.",
          "No photographs of the project team's own, no field trial, no user study, no measurement of the advice's correctness.",
          "Time and latency numbers come from one PC that also ran other jobs during training; accuracy numbers are not affected."),
        H2("8.14 Objectives against outcomes"),
        TAB("The six objectives of the batch (6.OBJECTIVES&PROBLEM STATEMENT) and what was achieved", ["#", "Objective", "Outcome"],
            [["1", "Assemble a labelled dataset of healthy and diseased crop leaf images across target crops", "**Achieved** with a public dataset: PlantDoc, 2,578 photographs, 28 classes, 13 crops. Not self-collected."],
             ["2", "Preprocess and augment the images", "**Partly.** Resize to 224 px and flip, rotation, zoom and contrast augmentation inside the training script; the application's heuristic only resizes to 256 px."],
             ["3", "Train a CNN to classify leaf images into disease categories", f"**Trained but not accurate.** {mp(C)} for the script's network; {mp(MB)} for the transfer-learning reference. Neither is installed in the application."],
             ["4", "Map each disease to a treatment and fertiliser recommendation", "**Treatment mapping achieved** for all 38 classes (chemical, organic, cultural, prevention, cost). **Fertiliser, yield and weather advice not implemented.** Advice not checked by an agronomist."],
             ["5", "Deliver diagnosis and advice through a web interface with multilingual support", "**Web interface achieved** (12 pages, 16 API routes). **Multilingual for interface strings only** (English, Hindi, Marathi); disease and treatment text is English."],
             ["6", "Evaluate accuracy per disease class and validate recommendations against agronomic guidance", "**Per-class accuracy measured** (Sections 8.4 to 8.6). **Recommendations not validated.**"]],
            widths=[0.3, 2.6, 3.9], align=["c", "l", "l"], size=9),
        P("In one sentence: the application is complete, the knowledge base is useful as a reference, and the diagnosis is the part that still has to be built; Chapter 10 lists how."),
    ]
    return out
