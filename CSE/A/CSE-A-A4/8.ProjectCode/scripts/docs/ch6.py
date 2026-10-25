"""Chapter 6: Methodology and Software Implementation. methodology_blocks() feeds document 9, application_blocks() feeds document 12."""

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB
from .refs import cite as c


def _lat(key):
    return F.LATENCY[key]["median_ms"]


def methodology_blocks():
    S, sv = F.SPLIT, F.SERVING
    ds = F.DATASET
    sd = F.SEEDS
    ens = F.SAVED["ensemble"]
    t_pcd, t_sas, t_qs = (sd[k]["elapsed_sec"]["mean"] for k in ("classical", "sa", "qa"))
    n_tr, n_te = S["train"][0], S["test"][0]
    b = []

    # ------------------------------------------------------------------ 6.1
    b += [H2("6.1 Overall methodology"),
          P("SecurePay AI follows the method of the base paper "
            f"{c('base')}: a Gaussian-Bernoulli restricted Boltzmann machine classifier (GRBMC) is trained on a balanced set of card transactions with three different procedures "
            "for estimating the model's negative-phase statistics - classical persistent contrastive divergence (PCD), simulated-annealing sampling (SAS) and quantum sampling (QS). "
            "The project adds what the paper does not describe: a complete preprocessing pipeline that can be re-run from the interface, an ensemble of the three trained models, "
            "a three-band decision rule for live scoring, a REST API, a web application, and a measured comparison against conventional classifiers. The work is organised in seven steps."),
          N("**Acquire data.** Generate a synthetic, balanced file of 39,000 transactions that imitates the paper's balanced set (the real data is proprietary).",
            "**Preprocess.** One-hot encode the categorical fields, z-score the numeric fields, drop highly correlated columns, balance the classes, rank the features with a random forest and keep the 18 best, then split 80/20 with stratification.",
            "**Train.** Fit three GRBMC models (PCD, SAS, QS) epoch by epoch, scoring the held-out split after every epoch and writing the metric history to disk.",
            "**Decide.** Average the three fraud probabilities and map the result to approve, challenge or decline.",
            "**Serve.** Expose the pipeline and the models through a Flask API with 16 routes and a React interface.",
            "**Evaluate.** Report precision, recall, F1 and ROC-AUC rather than accuracy alone, against Logistic Regression, Random Forest and XGBoost, across five random seeds, across decision thresholds and on a variant with 1 % fraud.",
            "**Document.** Regenerate every number in the documentation from `experiments/metrics.json` so that nothing is typed by hand."),
          FIG(F.diag("10_flowchart_training.png"), "Core algorithm: preprocessing and the per-epoch training loop of the three GRBMC trainers.", 5.3),
          P("Two properties of the method deserve to be stated at the start. First, the three trainers share one model class and one prediction rule; they differ only in how the negative phase "
            "of the gradient is sampled, so any difference in their results is a difference in sampling. Second, the SAS and QS samplers in this project are *simplified classical approximations* "
            "written in NumPy: they are not the path-integral Monte Carlo procedure of the paper's simulator and they do not call quantum hardware. Section 6.6 spells out the differences, "
            "and every later chapter refers to QS as *quantum-inspired* for that reason.")]

    # ------------------------------------------------------------------ 6.2
    b += [H2("6.2 Dataset"),
          P(f"The base paper's data are 145 million real transactions from a Brazilian payments company, of which about 19 thousand are fraudulent; the authors undersampled it manually to a 39 thousand-row set with a 50/50 split {c('base')}. "
            "That data is not public, so this project generates a synthetic file with the same size and balance. `backend/synthetic_data.py` draws the legitimate and the fraudulent class from different distributions "
            f"with a seeded NumPy generator (seed 42). The saved file `data/creditcard_synthetic.csv` has **{ds['rows']:,} rows and {ds['columns']} columns**: {ds['fraud']:,} fraudulent and {ds['legit']:,} legitimate transactions. "
            "No licence restriction applies because every value is generated."),
          TAB("Columns of the synthetic transaction file", ["Column(s)", "Type", "Legitimate class", "Fraudulent class"],
              [["Amount", "continuous", "|N(80, 60)| (mean {:.2f} in the file)".format(ds["amount_mean_legit"]), "|N(350, 250)| (mean {:.2f} in the file)".format(ds["amount_mean_fraud"])],
               ["Time", "integer seconds, 0 to 7,776,000", "uniform over 90 days", "uniform over 90 days"],
               ["Merchant_Category", "7 categories", "mostly Grocery 25 %, Restaurant 20 %, Fuel 15 %, Online 15 %", "mostly Online 35 %, Electronics 25 %, Travel 15 %"],
               ["Transaction_Type", "Chip, Contactless, Online, Swipe", "Chip 40 %, Contactless 30 %, Online 20 %, Swipe 10 %", "Online 60 %, Contactless 15 %, Swipe 15 %, Chip 10 %"],
               ["Card_Present", "0 / 1", "present in 80 % of rows", "present in 30 % of rows"],
               ["Country_Match", "0 / 1", "match in 95 % of rows", "match in 60 % of rows"],
               ["V1 ... V22", "continuous, standard normal", "N(0, 1); V1 raised slightly with Amount", "N(0, 1) with shifts on V3 (+1.5), V7 (-1.2), V10 (+1.0), V14 (-0.8), V17 (+1.3)"],
               ["Class", "0 / 1", "0 = legitimate", "1 = fraud"]],
              widths=[1.2, 1.35, 1.9, 1.95], size=9.5),
          P("The columns V1 to V22 imitate the anonymised principal-component features that published card datasets use; here they carry no meaning other than the shifts listed in the table. "
            "The web interface labels V3, V14 and V17 as *history signal*, *location variance* and *spending pattern* to make the form readable, but those are friendly names for synthetic features and not real card-holder attributes. "
            "Because the classes are generated from different distributions the problem is easier than real fraud, and the results in Chapter 8 must be read with that in mind."),
          FIG(F.fig("f01_dataset_overview.png"), "Synthetic dataset: class balance, transaction amount by class, and fraud rate by merchant category and by channel.", 5.7),
          P("The file is balanced by construction. The base paper started from an extremely imbalanced stream and found that SMOTE and Tomek links performed poorly because the minority class was tiny, "
            f"so it fell back to manual undersampling {c('base', 'smote', 'tomek')}. To see what happens when this project's pipeline meets a realistic imbalance, the experiment script also builds a variant "
            f"with {F.IMB['rows']:,} rows of which 1 % are fraud (390 fraudulent rows); it is used only for evaluation in Chapter 8 and is never loaded by the application.")]

    # ------------------------------------------------------------------ 6.3
    b += [H2("6.3 Preprocessing"),
          P("The preprocessing code is `backend/preprocessing.py`, function `full_pipeline`. The application's start-up code and the experiment script both apply it to an 8,000-row random sample of the file "
            f"(`random_state = 42`), which keeps the interactive steps fast. The steps follow Section III-A of the base paper {c('base')} and are summarised below with the real shapes they produce."),
          TAB("Preprocessing steps and the data shapes they produce", ["Step", "What the code does", "Shape afterwards"],
              [["1. Sample", "`df.sample(8000, random_state=42)` from the 39,000-row file", "8,000 x 29 (28 features + Class)"],
               ["2. One-hot encoding", "`pd.get_dummies` on Merchant_Category (7) and Transaction_Type (4), float dtype", "8,000 x 38 (37 features + Class)"],
               ["3. Z-score", "`StandardScaler` fitted on the 24 numeric columns (Amount, Time, V1 to V22); the 2 binary and 11 dummy columns stay 0/1", "unchanged"],
               ["4. Correlation filter", "drop any column whose absolute correlation with an earlier column exceeds 0.95", "no column dropped (37 features)"],
               ["5. Balancing", "`manual` (default): keep all fraud rows and a random legitimate sample of size min(n_fraud, n_legit); `smote` and `tomek` are optional", "8,000 rows (the sample is already balanced, so nothing is removed)"],
               ["6. Feature ranking", "random forest (200 trees, seed 42) on the balanced set; keep the 18 highest importances", f"8,000 x {S['train'][1]} + Class"],
               ["7. Split", "`train_test_split(test_size = 0.2, stratify = y, random_state = 42)`", f"train {S['train'][0]:,} x {S['train'][1]} ({S['train_fraud']:,} fraud); test {S['test'][0]:,} x {S['test'][1]} ({S['test_fraud']} fraud)"]],
              widths=[1.2, 3.6, 1.6], size=9.5),
          P("**Z-score.** Gaussian visible units expect inputs with zero mean and unit variance, so every numeric column x is replaced by"),
          EQ("z = (x - μ) / s"),
          P("where μ and s are the column mean and standard deviation of the 8,000-row sample. The fitted scaler is stored in `models/pipeline.pkl` together with the kept column names and the importance table, "
            "so that the serving code can transform a new transaction the same way. Section 6.10 describes a defect in how the batch route uses that scaler."),
          P(f"**Feature ranking.** The base paper ranks features with CatBoost {c('catboost')}. CatBoost is not in this project's requirements, so `feature_importance_filter` falls back to a random forest {c('breiman')} "
            "when the import fails; that is what ran here. The ten strongest features are Amount, V3, Card_Present, V17, V7, Country_Match, V10, Transaction_Type_Online, V14 and Transaction_Type_Chip, which matches the way the generator separates the classes. "
            "The 18 kept features are " + ", ".join(S["features"]) + ". The merchant dummy for Grocery and the low-importance columns V1, V6, V16, V2, V11, V4 and V19 are included only because 18 slots are requested."),
          FIG(F.fig("f11_feature_importance.png"), "Random-forest feature importance for the ten strongest of the 18 selected features.", 4.6),
          P("**Order of operations.** Scaling, balancing and feature ranking are all fitted on the whole 8,000-row sample *before* the train/test split, so the test rows have influenced the scaler and the feature ranking. "
            "On this balanced synthetic file the effect is small (the scaler statistics barely move and the ranking is dominated by the same features), but it is a leak that a careful pipeline would avoid by fitting on the training rows only. "
            "The experiments in Chapter 8 that compare strategies on the 1 % variant do split first and fit the scaler and the resampler on the training rows only.")]

    # ------------------------------------------------------------------ 6.4
    b += [H2("6.4 Algorithm choice and justification"),
          P("The choice of model is the base paper's, and this section records why it was kept and what was added beside it."),
          B(f"**Why a GRBM classifier.** A restricted Boltzmann machine is an energy-based network whose energy function can be written as a quadratic unconstrained binary optimisation (QUBO) problem {c('base', 'hinton06', 'fischer')}. "
            f"Adding a label layer joined to the hidden units turns the generative model into a classifier {c('larochelle')}, and Gaussian visible units let it read z-scored continuous features {c('liao')}. "
            "The structure is small (a few thousand weights), trains in seconds on a CPU and gives a probability that can be thresholded.",
            f"**Why three trainers.** Contrastive divergence and its persistent variant approximate the negative phase with Gibbs sampling {c('cd', 'pcd', 'guide')}. Replacing the Gibbs chain by an annealing sampler is the idea the paper evaluates on a D-Wave simulator and on quantum hardware {c('adachi', 'ajagekar')}. "
            "Keeping all three in one code base makes the comparison direct: same data, same model class, same evaluation.",
            "**Why simulate rather than call hardware.** Quantum annealing hardware was not available to the project. The sampler is therefore a classical program that mimics the annealing schedule and a transverse-field tunnelling term. "
            f"This keeps the structure of the paper's experiment but cannot test its claim about quantum advantage; the project makes no such claim {c('base')}.",
            f"**Why an ensemble.** The three models make different errors (Chapter 8), and averaging their probabilities gives a smoother score than any single model. The ensemble also lets the interface show per-model scores beside the combined verdict.",
            f"**Why also run Logistic Regression, Random Forest and XGBoost.** The batch objectives ask for these classifiers {c('shi', 'rfpaper', 'xgb')}. They are trained by `scripts/run_experiments.py` on exactly the same split so that the RBM is judged against standard baselines instead of against itself. "
            "They are not part of the shipped application."),
          P(f"**Why undersample.** Random undersampling to a 50/50 set keeps only real transactions, which is what the base paper chose after SMOTE and Tomek links failed on its extremely rare minority class {c('base', 'smote', 'tomek', 'hegarcia')}. "
            f"It has a known cost: undersampling distorts the posterior fraud probability unless it is recalibrated {c('dp15')}. Chapter 8 measures that cost on the 1 % variant, where the undersampled models raise hundreds of false alarms.")]

    # ------------------------------------------------------------------ 6.5
    b += [H2("6.5 Mathematical formulation"),
          H3("6.5.1 The Gaussian-Bernoulli RBM classifier"),
          P("Let v be the vector of n_v = 18 Gaussian visible units, h the vector of n_h binary hidden units and y a one-hot label with two units. "
            f"The model has weight matrices W (visible to hidden) and U (label to hidden) and bias vectors c, b and d for the three layers. Following Appendix A of the paper {c('base')}, extended with the label layer, the energy is"),
          EQ("E(v, h, y) = Σᵢ (vᵢ − cᵢ)² / (2σ²) − Σⱼ bⱼ hⱼ − Σᵢⱼ (vᵢ / σ) Wᵢⱼ hⱼ − Σₖ dₖ yₖ − Σₖⱼ yₖ Uₖⱼ hⱼ"),
          P("and the joint distribution is p(v, h, y) = exp(−E) / Z, where the partition function Z sums over every configuration and is intractable. The code fixes σ = 1 (inputs are z-scored). "
            "The conditional distributions used for sampling are"),
          EQ("p(hⱼ = 1 | v, y) = sigmoid( bⱼ + Σᵢ vᵢ Wᵢⱼ / σ + Σₖ yₖ Uₖⱼ )"),
          EQ("p(v | h) = N( c + σ W h , σ² )          p(y = k | h) = softmaxₖ( dₖ + Σⱼ Uₖⱼ hⱼ )"),
          P("The first is `_visible_to_hidden_prob`, the second `_hidden_to_visible_params` and `_hidden_to_label_prob` in `backend/rbm_classifier.py`."),
          H3("6.5.2 Prediction by free energy"),
          P("To classify a transaction the model compares the two label hypotheses y = 0 and y = 1 through the free energy with the hidden units summed out. As coded in `predict_proba`,"),
          EQ("F(v, y) = − Σᵢ cᵢ vᵢ / σ − Σₖ dₖ yₖ − Σⱼ ln( 1 + exp( bⱼ + Σᵢ vᵢ Wᵢⱼ / σ + Σₖ yₖ Uₖⱼ ) )"),
          EQ("P(fraud | v) = exp(−F(v, 1)) / ( exp(−F(v, 0)) + exp(−F(v, 1)) )"),
          P("The visible term of F is linear in v (the exact Gaussian expression has a quadratic term) and does not depend on y, so it appears identically in F(v, 0) and F(v, 1) and cancels in the ratio; the simplification therefore does not change the prediction. "
            "A transaction is labelled fraud when P(fraud | v) exceeds 0.5. The probability is *not* calibrated: it is the posterior of an approximately trained energy model, which is why the shipped PCD model, whose ROC-AUC is "
            f"{F.f3(F.SAVED['classical']['roc_auc'])}, still flags almost every transaction at the 0.5 threshold (Chapter 8)."),
          H3("6.5.3 Training by persistent contrastive divergence"),
          P(f"The log-likelihood gradient is the difference between a data-dependent (positive) and a model-dependent (negative) expectation {c('hinton06', 'guide')}. For a batch of m examples the code computes, with the positive hidden probabilities p⁺ from the data and the negative statistics (v⁻, y⁻, p⁻) from a sampler,"),
          EQ("ΔW = (vᵀ p⁺ − (v⁻)ᵀ p⁻) / (m σ)          ΔU = (yᵀ p⁺ − (y⁻)ᵀ p⁻) / m"),
          EQ("Δb = mean(p⁺ − p⁻)     Δc = mean(v − v⁻) / σ²     Δd = mean(y − y⁻)"),
          EQ("θ ← θ + η Δθ"),
          P("For classical training the negative statistics come from a *persistent* Gibbs chain: the chain state (v, y, h) is created once per batch size from random values and then advanced by one full Gibbs step (h given v and y; then v, y given h) after every update "
            f"{c('pcd')}. The training loss that is logged is a pseudo reconstruction error, the mean squared difference between a batch and the mean reconstruction from its *thresholded* hidden activations; it is a monitoring value only and does not enter the gradient."),
          H3("6.5.4 Simulated-annealing sampling (SAS)"),
          P("For SAS the Gibbs step is replaced by an annealing loop (`simulated_annealing_grad` in `backend/samplers.py`) with n_s = 10 sweeps and 16 reads. The inverse temperature rises linearly from β₀ = 1 / 2.0 = 0.5 to β₁ = 1 / 0.1 = 10. "
            "Within each sweep, twice over, the hidden field of every read r is computed from the **mean visible vector of the batch**, not from individual rows, and the hidden units are resampled for a random 5 % of the positions:"),
          EQ("fᵣ = b + (v̄ W) / σ + yᵣ U          hᵣ ← Bernoulli( sigmoid( 2 β fᵣ ) ) at the flipped positions"),
          P("The labels are then redrawn for 30 % of the reads from softmax( β ( d + hᵣ Uᵀ ) ). After the last sweep, the visible vector of each read is drawn from p(v | hᵣ), and the 16 reads are **averaged** into a single negative-phase vector that is repeated for every row of the batch. "
            "This is the paper's idea (anneal to approach a Boltzmann sample) in a form cheap enough for a CPU, but it is not the path-integral Monte Carlo simulator the paper used: there is no replica coupling, the field ignores row-to-row variation and the negative phase is a mean, not a set of samples."),
          H3("6.5.5 Quantum-inspired sampling (QS)"),
          P(f"QS (`quantum_sampling_grad`) uses the same machinery but follows the shape of the quantum-annealing Hamiltonian H(s) = A(s) H_D + B(s) H_P {c('base')}. With s running over ten values from 0 to 1 and γ = 0.8,"),
          EQ("A(s) = γ (1 − s)     B(s) = s     β_eff = 0.5 + 2 B(s)     P(tunnel) = 0.3 A(s)"),
          EQ("p(hⱼ = 1) = sigmoid( 2 β_eff B(s) fⱼ )     p̃(y) = (1 − 0.2 A) softmax( B (d + h Uᵀ) ) + 0.2 A / 2"),
          P("In every sweep each hidden bit is, with probability 0.3 A(s), replaced by a fair coin flip regardless of the field (the stand-in for quantum tunnelling), and otherwise sampled from the tempered sigmoid. Early sweeps are therefore noisy and late sweeps are nearly classical, as in an anneal; "
            "the label draw is blended with uniform noise in proportion to A(s) (a depolarising-noise stand-in). Reads are averaged as for SAS. Nothing in this procedure runs on quantum hardware or simulates a quantum state."),
          H3("6.5.6 QUBO form"),
          P(f"The energy of the classifier can be written as a QUBO problem f(x) = xᵀ Q x over the concatenated vector x = (v, y, h) {c('base')}. `GRBMC.get_qubo_matrix` builds the matrix that the Model comparison page shows as a heat map:"),
          EQ("Q = − [ diag(c)  0  ½W ;  0  diag(d)  ½Uᵀ ;  ½Wᵀ  ½U  diag(b) ]"),
          P("It has (n_v + 2 + n_h) rows: 220 for the 200-hidden-unit PCD model and 85 for the 65-hidden-unit SAS and QS models. The matrix is used only for display and inspection; the sampling code never solves it. "
            "A real hardware run would also need a binary expansion of the Gaussian visible units, which the paper identifies as a bottleneck and this project does not implement."),
          H3("6.5.7 Learning-rate schedules and the ensemble"),
          P("`train.py` sets the learning rate at the start of every epoch t (counted from 0). PCD and SAS share an exponential decay and QS follows the smooth decay with a floor that the paper gives as its Eq. (15):"),
          EQ("η_PCD(t) = η_SAS(t) = 0.01 exp(−0.08 t)          η_QS(t) = 0.005 exp(−0.15 t) + 0.0005"),
          P("The ensemble probability of the application is the mean of the three model probabilities, P_ens = (P_PCD + P_SAS + P_QS) / 3, and the decision is fraud when P_ens > 0.5."),
          H3("6.5.8 Evaluation metrics"),
          P(f"With TP, FP, TN and FN the counts of the confusion matrix and fraud as the positive class, the project reports {c('powers')}"),
          EQ("precision = TP / (TP + FP)     recall = TP / (TP + FN)     F1 = 2 · precision · recall / (precision + recall)     accuracy = (TP + TN) / (TP + TN + FP + FN)"),
          P(f"ROC-AUC is the area under the curve of recall against the false-positive rate {c('fawcett')}. On the 1 % variant the precision-recall area (average precision) is added because it is more informative than ROC-AUC when the positive class is rare {c('saito', 'davis')}. "
            "All threshold-based figures use 0.5 unless a threshold is stated.")]

    # ------------------------------------------------------------------ 6.6
    b += [H2("6.6 Model architecture and training"),
          FIG(F.diag("12_grbmc_structure.png"), "Structure of the GRBMC (visible, hidden and label layers) and the three negative-phase samplers.", 5.4),
          P(f"All three models read the {S['train'][1]} selected features as visible units and have two label units. They differ in size, batch and sampler, following the paper's hyper-parameter search results (200 hidden units for PCD and 65 for SAS and QS; large batches for the classical trainer and small ones for the annealed trainers {c('base')})."),
          TAB("Hyper-parameters of the three trainers as coded", ["Setting", "PCD (classical)", "SAS", "QS (quantum-inspired)"],
              [["Visible / hidden / label units", "18 / 200 / 2", "18 / 65 / 2", "18 / 65 / 2"],
               ["Weights (W + U)", "18 x 200 + 2 x 200 = 4,000", "18 x 65 + 2 x 65 = 1,300", "1,300"],
               ["Batch size", "512 (min with training rows)", "32", "32"],
               ["Rows used per epoch", "all 6,400", "3,000 (stratified sample, new each epoch)", "3,000 (as SAS)"],
               ["Negative phase", "persistent Gibbs chain, 1 step", "10 sweeps x 2 updates, 16 reads, mean", "10 sweeps, 16 reads, mean, tunnelling"],
               ["Learning rate", "0.01 exp(-0.08 t)", "0.01 exp(-0.08 t)", "0.005 exp(-0.15 t) + 0.0005"],
               ["Initial weights", "N(0, 0.01), biases 0", "N(0, 0.01), biases 0", "N(0, 0.01), biases 0"],
               ["Epochs (API default; the lab form starts at 10)", "20", "20", "20"],
               ["Random seed", "42", "42", "42"],
               ["Wall-clock (mean of 5 seeds, 20 epochs)", f"{t_pcd:.1f} s", f"{t_sas:.1f} s", f"{t_qs:.1f} s"],
               ["Time reported in the base paper", "2 minutes", "4 hours", "1.8 hours"]],
              widths=[1.9, 1.5, 1.6, 1.6], size=9.5),
          P("The `/api/train` route accepts a list of modes, an epoch count and a hidden-unit count; the retraining lab of the interface limits epochs to 1 to 50. The classical trainer replaces the default 65 hidden units by 200 and the default batch of 32 by 512, mirroring the paper. "
            "The seeding script `seed_models.py` trains for 10 epochs on the 8,000-row sample; the histories shipped in `models/` were written by a 20-epoch run through `/api/train`, so the saved models and their histories agree (re-evaluating the saved models reproduces the last-epoch history values)."),
          P(f"The measured training time is seconds, not hours: the paper's 4 hours for simulated annealing and 1.8 hours for hardware sampling reflect a D-Wave simulator and a cloud queue, while this project's samplers are vectorised NumPy with 10 sweeps and the rows per epoch capped at 3,000. "
            "The *Paper time* column on the Model comparison page shows the paper's reported time beside the measured one and labels the two differently so they are not confused."),
          TAB("What the paper describes and what this project implements", ["Aspect", "Base paper", "This project"],
              [["Data", "145 M real transactions, about 19 thousand fraud, balanced to 39 thousand", f"{ds['rows']:,} synthetic transactions, 50/50"],
               ["Visible units", "55 features after filtering", f"{S['train'][1]} features after filtering"],
               ["Feature selection", "correlation filter and CatBoost importance", "correlation filter and random-forest importance"],
               ["Balancing", "manual undersampling (SMOTE, Tomek failed)", "manual undersampling by default; SMOTE and Tomek available"],
               ["Classical trainer", "PCD with Gibbs sampling (QARBoM.jl)", "PCD with one Gibbs step (NumPy)"],
               ["Annealing trainer", "D-Wave simulated annealing, PIMC-style sweeps", "NumPy annealing with batch-mean field and averaged reads"],
               ["Quantum trainer", "real D-Wave quantum annealer through cloud access", "classical simulation with a tunnelling-flip term; no hardware"],
               ["Epochs", "50 (optimum at epoch 25, 34 and 49)", "20 (the lab allows 1 to 50)"],
               ["Model selection", "highest-F1 epoch on the test set", "final epoch is the primary figure here; best epoch is also stored"],
               ["Interface", "none described", "Flask API with 16 routes and a React application"]],
              widths=[1.3, 2.5, 2.8], size=9.5),
          P("Selecting the epoch with the highest test F1, as the paper's Table 1 does, reads the test set to choose the model and so slightly flatters it. The project stores both numbers but treats the final-epoch figure as primary; "
            f"for the shipped models the two agree for SAS and QS and differ strongly for PCD (best epoch {F.best_epoch('classical')[0]} with F1 {F.pct(F.best_epoch('classical')[1])}, final F1 {F.pct(F.HIST['classical']['f1'][-1])}).")]

    # ------------------------------------------------------------------ 6.7
    b += [H2("6.7 Decision logic"),
          P(f"The application turns the probability of the ensemble into an action with two cut-offs. Above 0.7 the risk level is HIGH and the recommended action is *decline and alert*; between 0.4 and 0.7 it is MEDIUM and the action is *challenge with 3-D Secure*; below 0.4 it is LOW and the transaction is *approved*. "
            f"The headline label (FRAUD or LEGITIMATE) is separate and flips at 0.5, so a MEDIUM transaction can be labelled fraud while the suggested action is only a challenge. The cut-offs are fixed in `app.py` and the interface; they are not tuned. "
            f"Chapter 8 shows the ensemble's precision, recall and F1 across thresholds: at 0.5 the ensemble reaches precision {F.pct(ens['precision'])} and recall {F.pct(ens['recall'])}, and at 0.7 the ensemble flags nothing on the held-out split, so the HIGH band is rarely reached by the averaged score on this data (single models, such as SAS in the Verify screen, can exceed it)."),
          FIG(F.diag("11_flowchart_decision.png"), "Scoring flow of one transaction, including the scaling step that the batch route silently skips.", 5.2)]

    return b


def application_blocks():
    lat = F.LATENCY
    sv = F.SERVING
    b = []

    # ------------------------------------------------------------------ 6.8
    b += [H2("6.8 Application architecture"),
          P(f"SecurePay AI has three tiers. The **browser tier** is a React {19} single-page application built with Vite and served on port {F.WEB_PORT}; it uses react-router for seven pages, Recharts for charts and Framer Motion for transitions. "
            f"Vite proxies every `/api` request to the **application tier**, a Flask 3.1 service on port {F.API_PORT} (`backend/app.py` and the extra blueprint `backend/api_extra.py`). The Flask process owns the **data tier**: "
            "an in-memory dictionary (`store`) that holds the dataset, the fitted pipeline, the three models and their histories, backed by files on disk - `data/creditcard_synthetic.csv`, `models/pipeline.pkl`, `models/grbmc_*.pkl` and `models/history_*.json`. There is no SQL database."),
          FIG(F.diag("01_system_architecture.png"), "System architecture: React interface, Vite proxy, Flask API, in-memory store and files on disk.", 5.5),
          P("At start-up the backend loads the CSV, tries to load `pipeline.pkl` and, if that fails, rebuilds the pipeline from the 8,000-row sample, then loads the saved models and histories. "
            "On the development PC the saved `pipeline.pkl` could not be unpickled by the installed pandas (it had been written by a different pandas version), so the pipeline was rebuilt at every start; because every step is seeded this reproduces the shipped models' behaviour exactly (their metrics matched the saved histories to the last digit). "
            "A request path is `React -> Vite proxy -> Flask route -> store -> response`; the sequence for one scored transaction is shown below."),
          FIG(F.diag("07_sequence_prediction.png"), "Sequence of one transaction check from the browser to the three models and back.", 5.4),
          P("The React application has these pages: a landing page, the **Dashboard** (dataset totals, fraud rate by merchant category and best F1 per model), **Verify transaction** (a form that returns the risk score, the action band and per-model probabilities), "
            "**Bulk verification** (CSV upload with optional metrics and a download), **Analytics** (four tabs: where, when, how much and card signals), **Model comparison** (comparison, training curves, features, QUBO matrix) and the **Model lab** (generate data, preprocess and retrain). "
            "A health badge in the header polls `/api/health` every 30 seconds and an offline screen replaces the data when the API cannot be reached.")]

    # ------------------------------------------------------------------ 6.9
    b += [H2("6.9 API design"),
          P("The API is plain JSON over HTTP with no versioning. Sixteen routes are registered; the first twelve are in `app.py` and the last four are the read-only extras in `api_extra.py` that the React pages need."),
          TAB("API routes", ["Method and path", "Purpose", "Notes"],
              [["GET /", "legacy single-page template", "served from `frontend/templates`"],
               ["GET /api/health", "status, trained models, row count", "polled by the header badge"],
               ["POST /api/generate_dataset", "regenerate the synthetic file", "rows clamped to 500-50,000 per class; overwrites the CSV; clears models in memory"],
               ["GET /api/dataset_info", "row counts, columns, five sample rows, describe()", ""],
               ["POST /api/preprocess", "run the pipeline with `method` and `top_k`", "returns shapes, importances, dropped columns; default `top_k` 22"],
               ["POST /api/train", "train the chosen modes for N epochs", "synchronous, can take a minute; overwrites model files"],
               ["GET /api/train_status", "epochs and best F1 per trained model", ""],
               ["GET /api/comparison", "best-epoch table with the paper's time", "falls back to the paper's Table 1 if no history exists"],
               ["GET /api/qubo?mode=", "QUBO matrix (top-left 40 x 40 and statistics)", "404 if the model is missing"],
               ["POST /api/predict_single", "score one transaction", "ensemble or one model; missing fields default to dataset mean or mode"],
               ["POST /api/predict_batch", "score an uploaded CSV", "adds Predicted_Class, Fraud_Probability, Risk; metrics when `Class` is present"],
               ["GET /api/export_predictions", "download the last batch result", "404 before the first batch"],
               ["GET /api/dataset_stats", "fraud rate by merchant, channel, hour, amount band, card signals", "read-only, computed from the full file"],
               ["GET /api/model_history", "per-epoch metrics of the three models", "read-only"],
               ["GET /api/feature_importance", "ranked importances and the selected columns", "read-only"],
               ["GET /api/sample_batch", "download `sample_batch.csv`", "20 labelled rows"]],
              widths=[1.9, 2.4, 2.3], size=9),
          P("A single-transaction request and its response look like this (the ensemble mode is the default):"),
          CODE('POST /api/predict_single\n{"Amount": 1200, "Merchant_Category": "Online", "Transaction_Type": "Online",\n "Card_Present": 0, "Country_Match": 0, "Time": 54000, "V3": 1.8, "V14": -1.1, "V17": 1.4}\n\n200 {"prediction": 1, "fraud_probability": 0.684, "label": "FRAUD", "risk_level": "MEDIUM",\n     "individual_models": {"classical": 0.509, "sa": 0.947, "qa": 0.595}}'),
          P("The numbers in the response are those captured in the Verify screen of Chapter 8. Errors are returned as `{\"error\": message}` with status 400 (no file uploaded), 404 (unknown or untrained model) or 500 (any exception, after the traceback is printed to the console).")]

    # ------------------------------------------------------------------ 6.10
    b += [H2("6.10 Security and error handling"),
          P("The application is a prototype for a controlled demonstration, and its security posture is correspondingly minimal. The table lists what exists and what does not; none of the gaps was hidden from the documentation, and the first row is a functional defect, not only a security matter."),
          TAB("Error handling and security review", ["Area", "What the code does", "Consequence"],
              [["Feature scaling at serving time", "in `predict_batch`, `scaler.transform` is applied to the selected numeric columns only (the columns are selected before scaling); the scaler was fitted on 24, so scikit-learn raises and a bare `except: pass` swallows the error. `predict_single` scales before selecting and is correct",
                f"for bulk uploads the models receive raw Amount, V values and so on; on a fresh {sv['fresh_rows']:,}-row balanced batch accuracy is {F.pct(sv['as_served_no_scaling']['ensemble']['accuracy'])} as served against {F.pct(sv['with_scaling']['ensemble']['accuracy'])} when scaling is applied, and `sample_batch.csv` is flagged {sv['sample_batch_as_served_flagged']} of {sv['sample_batch_rows']}"],
               ["Authentication and authorisation", "none", "anyone who can reach port 8304 can regenerate the dataset and retrain or overwrite the models"],
               ["CORS", "`CORS(app)` allows every origin", "any web page can call the API from a browser"],
               ["Server mode", "`app.run(host=\"0.0.0.0\", debug=True)` in `__main__`", "the Werkzeug debugger and reloader are on and the port is open on all interfaces; not for production"],
               ["Upload handling", "`pd.read_csv(file)`; no size limit, no type check", "a large or malformed file can exhaust memory or raise a 500"],
               ["Model files", "loaded with `joblib.load` (pickle)", "a tampered pickle can run code on load, so the `models/` folder must be trusted"],
               ["Input validation", "missing fields are replaced by dataset mean or mode; values are not range-checked", "an out-of-range value is scored without complaint"],
               ["Concurrency", "one global `store`, Flask development server", "concurrent training and prediction are not safe"],
               ["Errors", "`try/except` in the main routes returns JSON 500 with the message", "clients see a readable error; internal paths can leak in messages"],
               ["Secrets", "`.env` holds only the two port numbers", "no credentials are used; `.env` is git-ignored"]],
              widths=[1.4, 2.7, 2.5], size=9),
          P("The React client has its own handling: `ApiError` carries the status and the server's message, the Verify, Bulk and Lab pages show a toast on failure, the Bulk page has an explicit error state for a failed upload, and the Dashboard falls back to an *API offline* screen. "
            "The serving defect was found while writing this chapter, by reading the code and then confirming the result with `scripts/run_experiments.py`; it is documented and not fixed, in line with the project's rule that the documentation reports the code as it is. "
            "Chapter 10 lists the fix (scale with the full numeric column list, and fail loudly instead of silently).")]

    # ------------------------------------------------------------------ 6.11
    b += [H2("6.11 Installation and execution"),
          P("The project needs Python 3.11 and Node.js. All Python dependencies are pinned in `requirements.txt`: Flask 3.1.0, Flask-Cors 5.0.0, NumPy 1.26.4, pandas 2.2.2, scikit-learn 1.5.0, SciPy 1.13.0, imbalanced-learn 0.12.4, Matplotlib 3.9.0, seaborn 0.13.2, joblib 1.4.2 and openpyxl 3.1.5. "
            "The measurement scripts also use XGBoost 2.0.3, which is installed on the development PC but is not in `requirements.txt` because the application does not need it."),
          TAB("Run steps", ["Step", "Command", "Result"],
              [["1. Install Python packages", "`pip install -r requirements.txt`", "backend dependencies"],
               ["2. Generate data and models (only if missing)", "`python backend/synthetic_data.py` then `python seed_models.py`", "39,000-row CSV; three models; `pipeline.pkl` (about 45 s)"],
               ["3. Start both servers", "`run.bat` (or `run.ps1`)", f"Flask on {F.API_PORT} and Vite on {F.WEB_PORT}; the browser opens"],
               ["4. Or start them by hand", f"`python backend/app.py` and, in `frontend`, `npm install` then `npm run dev -- --host 127.0.0.1`", "same result"],
               ["5. Check the API", "`python scripts/smoke_test.py http://127.0.0.1:8304`", f"{F.SMOKE_PASSED}/{F.SMOKE_TOTAL} checks pass (read-only)"],
               ["6. Reproduce the numbers", "`python scripts/run_experiments.py` and `python scripts/measure_latency.py`", "`experiments/metrics.json`, `experiments/latency.json`"]],
              widths=[1.9, 2.9, 1.8], size=9.5),
          P(f"Ports come from `.env` (`BACKEND_PORT`, `FRONTEND_PORT`), and `vite.config.js` reads the same file so the proxy and the servers agree. "
            f"Once running, a single check takes a median of {_lat('predict_single_fraud_example'):.0f} ms through the Flask development server on `127.0.0.1` (95th percentile {lat['predict_single_fraud_example']['p95_ms']:.0f} ms) and a 20-row bulk upload {_lat('predict_batch_20_rows'):.0f} ms; "
            "addresses must use `127.0.0.1` rather than `localhost` on the development PC, where the name lookup adds about two seconds per call. The retraining lab is the only step that takes noticeable time, because `/api/train` runs inside one request."),
          FIG(F.fig("f12_latency.png"), "Median and 95th-percentile response time of the API endpoints on the development PC.", 4.9)]
    return b


def _compact(bl):
    """Report-mode variant (F.REPORT): same headings, equations and findings, shorter prose, fewer tables and figures."""
    import os

    S, ds, ens = F.SPLIT, F.DATASET, F.SAVED["ensemble"]
    bp = F.best_epoch("classical")
    SH = {
        "SecurePay AI follows the method of the base paper": (
            f"SecurePay AI follows the base paper {c('base')}: a Gaussian-Bernoulli RBM classifier (GRBMC) is trained on a balanced set of card transactions with three ways of estimating the negative phase - "
            "persistent contrastive divergence (PCD), simulated-annealing sampling (SAS) and quantum sampling (QS). The project adds a re-runnable preprocessing pipeline, an ensemble, a three-band decision rule, a REST API, "
            "a web application and a measured comparison against conventional classifiers, in seven steps:"),
        "Two properties of the method": (
            "The three trainers share one model class and one prediction rule and differ only in how the negative phase is sampled. The SAS and QS samplers are *simplified classical approximations* in NumPy, "
            "not the paper's path-integral simulator and not quantum hardware (Section 6.6), so QS is called *quantum-inspired* throughout."),
        "The base paper's data are 145 million": (
            f"The base paper's data are 145 million real transactions (about 19 thousand fraud), undersampled manually to a 39 thousand-row 50/50 set {c('base')}. That data is not public, so `backend/synthetic_data.py` generates "
            f"a synthetic file of the same size and balance with a seeded generator (seed 42): **{ds['rows']:,} rows and {ds['columns']} columns**, {ds['fraud']:,} fraudulent and {ds['legit']:,} legitimate. No licence restriction applies."),
        "The columns V1 to V22 imitate": (
            "V1 to V22 imitate anonymised principal-component features and carry no meaning beyond the listed shifts; the interface names for V3, V14 and V17 (*history signal*, *location variance*, *spending pattern*) are friendly labels, "
            "not real attributes. Because the classes come from different distributions the problem is easier than real fraud (Chapter 8)."),
        "The file is balanced by construction": (
            f"The base paper found SMOTE and Tomek links poor on a tiny minority class and used manual undersampling {c('base', 'smote', 'tomek')}. To see a realistic imbalance the experiment script also builds a "
            f"{F.IMB['rows']:,}-row variant with 1 % fraud (390 rows), used only for evaluation in Chapter 8."),
        "The preprocessing code is": (
            f"`full_pipeline` in `backend/preprocessing.py` is applied to an 8,000-row random sample (`random_state = 42`) and follows Section III-A of the base paper {c('base')}."),
        "**Z-score.**": "**Z-score.** Gaussian visible units expect zero mean and unit variance, so each numeric column x becomes",
        "where μ and s are": "where μ and s come from the 8,000-row sample. The fitted scaler is stored in `models/pipeline.pkl` for the serving code; Section 6.10 describes a defect in how the batch route uses it.",
        "**Feature ranking.**": (
            f"**Feature ranking.** The base paper ranks features with CatBoost {c('catboost')}; it is not installed here, so `feature_importance_filter` falls back to a random forest {c('breiman')} (this is what ran). "
            "The strongest features are Amount, V3, Card_Present, V17, V7, Country_Match, V10, Transaction_Type_Online, V14 and Transaction_Type_Chip; the weakest of the 18 kept are included only because 18 slots are requested."),
        "**Order of operations.**": (
            "**Order of operations.** Scaling, balancing and feature ranking are fitted on the whole sample *before* the split, so test rows influence the scaler and the ranking. The effect is small on this balanced synthetic file "
            "but it is a leak; the 1 % experiments in Chapter 8 split first and fit on the training rows only."),
        "The choice of model is the base paper's": None,
        "**Why undersample.**": (
            f"**Why undersample.** Undersampling to 50/50 keeps only real transactions, as the base paper chose after SMOTE and Tomek failed {c('base', 'smote', 'tomek', 'hegarcia')}, but it distorts the posterior probability "
            f"unless recalibrated {c('dp15')}; Chapter 8 measures this on the 1 % variant."),
        "Let v be the vector of": (
            "Let v be the n_v = 18 Gaussian visible units, h the n_h binary hidden units and y a one-hot label (two units); W and U join the visible and label units to the hidden layer and c, b, d are the biases. "
            f"Following Appendix A of the paper {c('base')}, extended with the label layer, the energy is"),
        "and the joint distribution is": "with p(v, h, y) = exp(−E) / Z (Z is intractable) and σ = 1 in the code. The sampling conditionals are",
        "The first is `_visible_to_hidden_prob`": None,
        "To classify a transaction the model compares": "Classification compares the two label hypotheses through the free energy with the hidden units summed out (`predict_proba`):",
        "The visible term of F is linear": (
            "The visible term is linear in v (the exact Gaussian term is quadratic) and cancels in the ratio, so the simplification does not change the prediction. A transaction is labelled fraud when P(fraud | v) > 0.5. "
            f"The probability is *not* calibrated, which is why the shipped PCD model (ROC-AUC {F.f3(F.SAVED['classical']['roc_auc'])}) flags almost every transaction at 0.5 (Chapter 8)."),
        "The log-likelihood gradient is": (
            f"The gradient is the difference between a data (positive) and a model (negative) expectation {c('hinton06', 'guide')}; for a batch of m rows, with positive hidden probabilities p⁺ and negative statistics (v⁻, y⁻, p⁻) from a sampler,"),
        "For classical training the negative statistics": (
            f"Classically the negative statistics come from a *persistent* Gibbs chain advanced by one full Gibbs step after every update {c('pcd')}. The logged loss is a pseudo reconstruction error used for monitoring only."),
        "For SAS the Gibbs step is replaced": (
            "SAS (`simulated_annealing_grad`) replaces the Gibbs step by 10 sweeps over 16 reads, with inverse temperature rising linearly from 0.5 to 10. In each sweep (twice) the hidden field of every read is computed from the "
            "**mean visible vector of the batch** and a random 5 % of the hidden units are resampled:"),
        "The labels are then redrawn for 30 %": (
            "Labels are redrawn for 30 % of the reads from softmax(β(d + hᵣUᵀ)); each read's visible vector is drawn from p(v | hᵣ) and the 16 reads are **averaged** into one negative-phase vector repeated for every row. "
            "This keeps the paper's idea of annealing towards a Boltzmann sample but is not its path-integral simulator: there is no replica coupling and the negative phase is a mean, not a set of samples."),
        "QS (`quantum_sampling_grad`) uses the same machinery": (
            f"QS (`quantum_sampling_grad`) follows the shape of H(s) = A(s) H_D + B(s) H_P {c('base')}; over ten values of s from 0 to 1 with γ = 0.8,"),
        "In every sweep each hidden bit is": (
            "In each sweep a hidden bit is replaced by a fair coin flip with probability 0.3 A(s) (the stand-in for tunnelling) and otherwise sampled from the tempered sigmoid; the label draw is blended with uniform noise in proportion to A(s). "
            "Reads are averaged as for SAS. Nothing here runs on, or simulates the state of, quantum hardware."),
        "The energy of the classifier can be written": (
            f"The energy can be written as a QUBO f(x) = xᵀ Q x over x = (v, y, h) {c('base')}; `GRBMC.get_qubo_matrix` builds the matrix that the Model comparison page shows as a heat map:"),
        "It has (n_v + 2 + n_h) rows": "It has 220 rows for the PCD model and 85 for SAS and QS and is used only for display; a hardware run would also need a binary expansion of the Gaussian units, which this project does not implement.",
        "`train.py` sets the learning rate": "`train.py` sets the learning rate at the start of epoch t (from 0): PCD and SAS decay exponentially and QS follows the paper's Eq. (15):",
        "ROC-AUC is the area under": (
            f"ROC-AUC is the area under the recall-against-false-positive-rate curve {c('fawcett')}; on the 1 % variant average precision is added because it is more informative for a rare positive class {c('saito', 'davis')}. "
            "Thresholded figures use 0.5 unless stated."),
        "All three models read the": (
            f"All models read the {S['train'][1]} selected features and have two label units; sizes, batches and samplers follow the paper's search (200 hidden units and a large batch for PCD, 65 and small batches for SAS and QS {c('base')})."),
        "The `/api/train` route accepts": (
            "`/api/train` takes a list of modes, an epoch count and a hidden-unit count (the lab limits epochs to 1-50); PCD widens 65 hidden units to 200 and the batch to 512, as in the paper. "
            "The shipped histories come from a 20-epoch run through the API and agree with the saved models."),
        "The measured training time is seconds": (
            "Training takes seconds here, not the paper's hours (4 h for SAS, 1.8 h for hardware sampling): those reflect a D-Wave simulator and a cloud queue, whereas these samplers are vectorised NumPy with at most 3,000 rows per epoch. "
            "The Model comparison page labels the paper's time and the measured time separately."),
        "Selecting the epoch with the highest test F1": (
            "Choosing the highest-test-F1 epoch, as the paper's Table 1 does, reads the test set and flatters the model. The project stores both numbers and treats the final epoch as primary; "
            f"they agree for SAS and QS and differ strongly for PCD (best epoch {bp[0]} with F1 {F.pct(bp[1])}, final F1 {F.pct(F.HIST['classical']['f1'][-1])})."),
        "The application turns the probability of the ensemble": (
            "Above 0.7 the risk level is HIGH (*decline and alert*), from 0.4 to 0.7 MEDIUM (*challenge with 3-D Secure*) and below 0.4 LOW (*approve*). The FRAUD or LEGITIMATE label flips separately at 0.5, so a MEDIUM transaction can be labelled fraud. "
            f"The cut-offs are fixed, not tuned. At 0.5 the ensemble has precision {F.pct(ens['precision'])} and recall {F.pct(ens['recall'])}; at 0.7 it flags nothing on the held-out split, so the HIGH band is rarely reached by the averaged score on this data."),
        "SecurePay AI has three tiers": (
            f"SecurePay AI has three tiers: a React single-page application built with Vite (port {F.WEB_PORT}), a Flask 3.1 service (port {F.API_PORT}; `backend/app.py` and `backend/api_extra.py`) to which Vite proxies every `/api` request, "
            "and a data tier of one in-memory `store` backed by `data/creditcard_synthetic.csv`, `models/pipeline.pkl`, `models/grbmc_*.pkl` and `models/history_*.json`. There is no SQL database (architecture and sequence diagrams: Chapter 5)."),
        "At start-up the backend loads": (
            "At start-up the backend loads the CSV, tries `pipeline.pkl` and, if that fails, rebuilds the pipeline from the 8,000-row sample, then loads the saved models and histories. On the development PC the saved pipeline could not be unpickled by the installed pandas, "
            "so it was rebuilt at every start; because every step is seeded this reproduces the shipped models' metrics exactly."),
        "The React application has these pages": (
            "The pages are a landing page, **Dashboard**, **Verify transaction** (risk score, action band, per-model probabilities), **Bulk verification** (CSV upload and download), **Analytics** (four tabs), "
            "**Model comparison** (comparison, training curves, features, QUBO matrix) and the **Model lab** (generate, preprocess, retrain). A header badge polls `/api/health` every 30 seconds and an offline screen replaces the data when the API is unreachable."),
        "The API is plain JSON over HTTP": (
            "The API is plain JSON over HTTP with no versioning; sixteen routes are registered (twelve in `app.py`, four read-only extras in `api_extra.py`). Chapter 5 tabulates them. In short: `GET /api/health`, `/api/dataset_info`, `/api/dataset_stats`, "
            "`/api/model_history`, `/api/feature_importance`, `/api/train_status`, `/api/comparison`, `/api/qubo`, `/api/export_predictions` and `/api/sample_batch` read state; `POST /api/generate_dataset`, `/api/preprocess` and `/api/train` change it (training is synchronous and "
            "overwrites the model files); `POST /api/predict_single` scores one transaction and `POST /api/predict_batch` scores an uploaded CSV. A single-transaction exchange looks like this:"),
        "A single-transaction request and its response": None,
        "The numbers in the response are those captured": (
            "The numbers are those captured in the Verify screen of Chapter 8. Errors are returned as `{\"error\": message}` with status 400 (no file), 404 (unknown or untrained model) or 500 (any exception)."),
        "The application is a prototype for a controlled demonstration": (
            "The application is a prototype for a controlled demonstration; the table lists what exists and what does not, and the first row is a functional defect, not only a security matter."),
        "The React client has its own handling": (
            "The React client shows a toast on failure, an explicit error state on the Bulk page and an *API offline* screen on the Dashboard. The scaling defect was found by reading the code and confirmed with `scripts/run_experiments.py`; "
            "it is documented and not fixed, and Chapter 10 lists the fix (scale with the full numeric column list and fail loudly)."),
        "The project needs Python 3.11 and Node.js": (
            "The project needs Python 3.11 and Node.js. Python dependencies are pinned in `requirements.txt` (Flask 3.1.0, Flask-Cors 5.0.0, NumPy 1.26.4, pandas 2.2.2, scikit-learn 1.5.0, SciPy 1.13.0, imbalanced-learn 0.12.4, Matplotlib 3.9.0, "
            "seaborn 0.13.2, joblib 1.4.2, openpyxl 3.1.5); the measurement scripts also use XGBoost 2.0.3, which the application does not need."),
        "Ports come from `.env`": (
            f"Ports come from `.env` and `vite.config.js` reads the same file. A single check takes a median of {_lat('predict_single_fraud_example'):.0f} ms through the Flask development server on `127.0.0.1` "
            f"(95th percentile {F.LATENCY['predict_single_fraud_example']['p95_ms']:.0f} ms) and a 20-row bulk upload {_lat('predict_batch_20_rows'):.0f} ms; use `127.0.0.1` rather than `localhost` on the development PC, where the name lookup adds about two seconds per call. "
            "Only the retraining lab takes noticeable time, because `/api/train` runs inside one request."),
    }
    DROP_FIG = {"10_flowchart_training.png", "11_flowchart_decision.png", "01_system_architecture.png", "07_sequence_prediction.png", "f11_feature_importance.png", "f12_latency.png"}
    DROP_ROWS = {
        "Hyper-parameters of the three trainers as coded": {"Weights (W + U)", "Initial weights", "Random seed", "Epochs (API default; the lab form starts at 10)"},
        "What the paper describes and what this project implements": {"Visible units", "Feature selection", "Epochs", "Interface"},
        "Error handling and security review": {"Server mode", "Upload handling", "Input validation", "Concurrency", "Secrets"},
        "API routes": set(x[0] for x in []),
    }
    out = []
    for b in bl:
        k = b[0]
        if k == "p":
            hit = [key for key in SH if b[1].startswith(key)]
            if hit:
                if SH[hit[0]] is None:
                    continue
                b = ("p", SH[hit[0]])
        elif k == "b" and b[1][0].startswith("**Why a GRBM classifier.**"):
            b = ("b", [
                f"**Why a GRBM classifier.** An RBM is an energy-based network whose energy can be written as a QUBO problem {c('base', 'hinton06', 'fischer')}; a label layer turns it into a classifier {c('larochelle')} and Gaussian visible units read z-scored features {c('liao')}. "
                "It is small (a few thousand weights), trains in seconds on a CPU and gives a probability that can be thresholded.",
                f"**Why three trainers.** Contrastive divergence approximates the negative phase with Gibbs sampling {c('cd', 'pcd', 'guide')}; replacing the chain by an annealing sampler is the idea the paper tests on a D-Wave simulator and hardware {c('adachi', 'ajagekar')}. One code base keeps data, model class and evaluation identical.",
                f"**Why simulate.** Quantum hardware was not available, so the sampler is a classical program with an annealing schedule and a tunnelling term; it keeps the structure of the paper's experiment but cannot test its quantum-advantage claim, and none is made {c('base')}.",
                "**Why an ensemble.** The three models make different errors (Chapter 8); averaging gives a smoother score and lets the interface show per-model scores.",
                f"**Why also run LR, RF and XGBoost.** The batch objectives ask for them {c('shi', 'rfpaper', 'xgb')}; `scripts/run_experiments.py` trains them on the same split so the RBM is judged against standard baselines. They are not part of the shipped application."])
        elif k == "fig":
            if os.path.basename(b[1]) in DROP_FIG:
                continue
            b = ("fig", b[1], b[2], b[3] * 0.85)
        elif k == "tab":
            if b[1] == "API routes":
                continue
            drop = DROP_ROWS.get(b[1], set())
            rows = [r for r in b[3] if r[0] not in drop]
            b = ("tab", b[1], b[2], rows, b[4], b[5], min(b[6], 9))
        elif k == "code" and "predict_single" in b[1]:
            b = ("code", b[1], 8)
        out.append(b)
    return out


def blocks():
    full = [H1("6. METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
    return _compact(full) if F.REPORT else full
