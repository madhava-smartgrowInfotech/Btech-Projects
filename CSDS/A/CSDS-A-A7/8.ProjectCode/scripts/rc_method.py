"""Chapter 6 content: methodology and software implementation (SHEGUARD).

Every number comes from docs/REPORT_FACTS.md and experiments/study/*.json; code listings are cut from the real source files.
"""
from __future__ import annotations

from doc_common import CHARTS, DIAG, ROOT, STUDY, study

M = study("metrics.json")
A = study("api_metrics.json")
S = study("safephrase.json")


def src(path: str, start: int, end: int) -> str:
    """Real source lines (1-based, inclusive) from the project."""
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[start - 1:end])


def grab(path: str, marker: str, n: int) -> str:
    """`n` real source lines starting at the first line that contains `marker`."""
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    i = next(k for k, line in enumerate(lines) if marker in line)
    return "\n".join(lines[i:i + n])


def count_lines(patterns, folders):
    total = 0
    for folder in folders:
        for pat in patterns:
            for f in (ROOT / folder).rglob(pat):
                if "node_modules" in f.parts or "__pycache__" in f.parts or "venv" in f.parts:
                    continue
                total += len(f.read_text(encoding="utf-8", errors="ignore").splitlines())
    return total


def pct(x, nd=1):
    return f"{x * 100:.{nd}f} %"


def fig(d, path, caption, width=5.0):
    """Insert a figure; skipped (with a console note) when the picture has not been generated yet."""
    if path.exists():
        d.figure(path, caption, width=width)
    else:
        print("MISSING FIGURE", path)


# ---------------------------------------------------------------------------------------------------------------- 6.1
def sec_method_overview(d):
    d.h2("Overall Methodology")
    d.paras(
        "SHEGUARD follows the lifecycle of an unsafe journey: before it, while it happens and after it. Before the journey the user plans a route; "
        "OpenStreetMap-based routing (OSRM) returns driving alternatives and each is scored against a table of district-level risk tiers that was "
        "built from public crime statistics with K-Means clustering. During an emergency a single tap, or a spoken cover phrase recognised in the browser, "
        "starts a session: the position is streamed to guardians over a WebSocket on a link that needs no login, alerts are attempted by Telegram and e-mail, "
        "and the user can add photo or audio evidence. After the emergency the evidence is already stored with a timestamp, a location and a SHA-256 hash, and "
        "an AI assistant (Gemini) is available for advice.",
        "The base paper [1] builds the first stage only: it clusters regions with K-Means and Gaussian mixtures on crime, population, literacy, expenditure, police "
        "and forest data, and proposes a cab-service integration that raises alerts when a ride deviates into an unsafe cluster. SHEGUARD keeps the idea of a "
        "clustering-based risk map feeding route guidance, simplifies it (one feature, one algorithm, three tiers) and adds the hands-free activation, live "
        "guardian tracking, evidence preservation and assistant stages around it.",
        "One difference from the batch abstract must be stated at the outset. The abstract names Flutter, Supabase and Postgres Row Level Security. The "
        "implementation is a **React 19 and TypeScript web application, installable as a progressive web app, on a FastAPI and SQLite back end**. Access control is "
        "enforced in code: every query filters on the user id carried in the JWT, and guardians have no account at all, they hold only an unguessable per-session link. "
        "\"Smart SOS\" is a one-tap button with a three-second hold to cancel; there is no shake, power-button or fall-detection trigger.")
    if not getattr(d, "report", False):
        fig(d, DIAG / "02_high_level_workflow.png", "High-level workflow of SHEGUARD", width=6.2)
    d.table([["Stage", "Method", "Output"],
             ["1 Collect", "Public district-wise crimes-against-women table 2001-2012 (Kaggle, CC0); districts geocoded once with Nominatim", "9,017 rows, 827 districts, 467 with coordinates"],
             ["2 Prepare", "Drop TOTAL rows; sum seven crime columns; average per reporting year; join with coordinates", "One `crime_rate` per district"],
             ["3 Cluster", "StandardScaler and K-Means with k = 3; tiers named by mean crime rate; 0-100 `risk_score` by min-max", "467 district rows (low 278, medium 148, high 41)"],
             ["4 Plan route", "OSRM alternatives; every 8th point mapped to the nearest district (haversine); tier weights 1 / 2.5 / 5, night factor 1.6", "Routes sorted by risk score; first is recommended"],
             ["5 Trigger", "One-tap button, or the Web Speech API plus a word-window matcher against stored phrases", "`POST /api/sos/start` with the trigger name"],
             ["6 Share", "Session row with a 32-hex `share_token`; position pings every 4 s; WebSocket broadcast; Telegram and Gmail attempts", "Public read-only tracking page; delivery report"],
             ["7 Preserve", "Multipart upload, SHA-256 of the bytes, stored file, row with kind, time and position", "Evidence list with 64-hex hashes"],
             ["8 Assist", "Gemini `generateContent` with a safety system prompt and the approximate location", "Short answer (not demonstrated in this run: quota error)"]],
            "Pipeline of SHEGUARD", widths=[0.12, 0.54, 0.34], font=9)


# ---------------------------------------------------------------------------------------------------------------- 6.2
def sec_dataset(d):
    d.h2("Dataset")
    dd = M["data"]
    d.p("The only learned component of the product, the area-risk model, is trained on public statistics; there is no synthetic data and no labelled "
        "ground truth. Two Kaggle datasets were committed to the repository and the district coordinates were produced once from OpenStreetMap.")
    d.table([["Item", "Source and licence", "Size and use"],
             ["District crimes file", "Kaggle \"Crime in India\" (rajanand) [23]; CC0 public domain",
              f"`district_wise_crimes_against_women_2001_2012.csv`: {dd['raw_rows']:,} rows, {dd['rows_after_total_removal']:,} after dropping `TOTAL` roll-ups; {dd['state_ut_count']} states and union territories; years {dd['years'][0]}-{dd['years'][-1]}; {dd['district_state_pairs']} (state, district) pairs; seven crime columns. **Trains the model**"],
             ["State-year file", "Kaggle \"Crimes against women in India 2001-2021\" (balajivaraprasad) [24]; CC0",
              f"`crimes_against_women_2001_2021.csv`: {M['state_year_file']['rows']} rows, {M['state_year_file']['states']} state labels, {M['state_year_file']['years'][0]}-{M['state_year_file']['years'][1]}. Committed, **not used by any feature**"],
             ["District coordinates", "Nominatim over OpenStreetMap (ODbL) [29]; one request per second",
              f"`districts_geocoded.csv`: **{dd['geocoded_pairs']} of {dd['district_state_pairs']} pairs ({dd['geocode_rate'] * 100:.1f} %)**; the rest (railway divisions, sub-district entries) were dropped, not guessed"],
             ["Routes", "OSRM public demo server [17]; place search by Nominatim", "Fetched live per request; nothing stored"]],
            "Data used by SHEGUARD", widths=[0.17, 0.3, 0.53], font=9)
    d.p(f"The seven counted categories are Rape, Kidnapping and Abduction, Dowry Deaths, Assault on women with intent to outrage her modesty, Insult to modesty of Women, Cruelty by Husband or his Relatives and "
        f"Importation of Girls. Their combined shares are Cruelty by husband or relatives {pct(M['crime_mix']['cruelty_by_husband_share_of_all_counted_crimes'])}, assault on modesty {pct(M['crime_mix']['assault_on_modesty_share'])}, "
        f"rape {pct(M['crime_mix']['rape_share'])}, kidnapping {pct(M['crime_mix']['kidnapping_share'])}, insult to modesty {pct(M['crime_mix']['insult_modesty_share'])} and dowry deaths {pct(M['crime_mix']['dowry_deaths_share'])}. "
        "The risk score therefore mostly counts domestic-violence reports, which say little about danger on a street at night; this is a property of the data and is repeated among the limitations.")
    fig(d, CHARTS / "09_crime_mix.png", "Share of each counted crime category in the district file", width=4.4)
    yrs = dd["years_reported_distribution"]
    d.p(f"Districts report between one and twelve years: {yrs['12']} of {dd['district_state_pairs']} report all twelve and {yrs['1']} report a single year; the geocoded districts average "
        f"{dd['geocoded_years_reported_mean']:.2f} reporting years. The feature is an average per reporting year, so a district with five years of data is not penalised for its missing years, "
        "but the average of a few years is noisier. The counts are raw numbers, **not rates per population**: the file contains no population, so a large district ranks above a small one with the same per-person risk.")
    gaps = ", ".join(s.title() for s in M["states_with_no_geocoded_district"])
    d.p(f"Geocoding left {len(M['states_with_no_geocoded_district'])} of {dd['state_ut_count']} states and union territories with no district at all ({gaps}), "
        f"and the geocoded points are otherwise plausible: none lies outside India's bounding box and {M['geocode_sanity']['districts_sharing_identical_coordinates']} districts share a coordinate "
        f"({M['geocode_sanity']['distinct_coordinates']} distinct points). There is **no train and test split**, because the model is unsupervised and there is no ground-truth risk label to hold out.")
    if not getattr(d, "report", False):
        fig(d, CHARTS / "05_state_coverage.png", "Districts per state in the crime file and how many were geocoded and used", width=4.8)
        fig(d, CHARTS / "10_district_map.png", "The 467 geocoded districts coloured by tier", width=4.2)


# ---------------------------------------------------------------------------------------------------------------- 6.3
def sec_preprocessing(d):
    d.h2("Preprocessing")
    d.h3("Building the district feature table")
    d.p("`ml/train_risk_model.py` prepares the data in five steps:")
    d.numbered([
        "**Remove roll-ups.** Rows whose district name contains `TOTAL` (state totals) are dropped, leaving 8,597 of 9,017 rows.",
        "**Sum the categories.** The seven crime columns are added into `total_crimes` for each row (one district-year).",
        "**Average per reporting year.** Rows are grouped by state and district; `crime_rate` is the sum of `total_crimes` divided by the number of distinct years the district reported.",
        "**Attach coordinates.** An inner join with `districts_geocoded.csv` keeps the 467 districts that have a latitude and longitude.",
        "**Scale.** `StandardScaler` converts `crime_rate` to a z-score before clustering; the scaler is saved with the model.",
    ])
    d.p("After clustering, the tier names are assigned by sorting the three clusters on their mean `crime_rate` (lowest is `low`, highest is `high`), so the names do not depend on the arbitrary cluster numbers, and "
        "`risk_score` is a min-max rescaling of `crime_rate` to 0-100 computed within the fitted data. The table is written to `data/district_risk.csv` and loaded into the `district_risk` database table when the back end starts.")
    d.h3("Geocoding")
    d.p("`scripts/geocode_districts.py` asks Nominatim for \"District, State, India\" once per district, at most one request per 1.1 seconds, and saves its progress after every row so an interrupted run resumes. "
        "A district with no result is skipped. The cache is committed, so the step never has to run again.")
    d.h3("Route preprocessing")
    d.p("The OSRM response is requested with `alternatives=true`, `overview=full` and GeoJSON geometry; its [longitude, latitude] pairs are swapped to [latitude, longitude]. "
        "The scorer takes every eighth point of the polyline (`sample_every_n = 8`) so that a long route is judged by a few dozen sample points rather than thousands.")
    d.h3("Voice and input preprocessing")
    d.p("SafePhrase text, both the stored phrases and the speech transcript, is normalised by `normalizeText`: lower-cased, every character outside a-z, 0-9 and space replaced by a space, "
        "runs of spaces collapsed and the ends trimmed. The transcript buffer keeps only the last 200 characters so that old speech cannot trigger a new match. A stored phrase is shown "
        "to the user only as a SHA-256 fingerprint of its normalised text. Request bodies are validated by Pydantic models (e-mail format, password of at least six characters, required "
        "coordinates); the evidence upload checks the `kind` (photo or audio) and rejects an empty file.")


# ---------------------------------------------------------------------------------------------------------------- 6.4
def sec_algorithm_choice(d):
    d.h2("Algorithm Choice and Justification")
    alt = M["alternative_tiering"]
    d.table([["Decision", "Chosen", "Alternatives measured or considered", "Why"],
             ["Risk tiers", "K-Means, k = 3 on the standardised crime rate [9], [10]",
              f"Ward hierarchical [15] ({pct(alt['agglomerative_ward']['agreement_with_kmeans'])} agreement), Gaussian mixture [14] ({pct(alt['gaussian_mixture']['agreement_with_kmeans'])}), equal-count terciles ({pct(alt['equal_count_terciles']['agreement_with_kmeans'])}), fixed 100 / 300 cut-offs ({pct(alt['fixed_100_300_cutoffs']['agreement_with_kmeans'])})",
              "Simple, deterministic given a seed, fits in milliseconds, matches one of the two algorithms of the base paper; the tier boundaries come from the data instead of being invented"],
             ["Number of tiers", "k = 3", "k = 2 to 8 swept (below)", "A UI choice (low, medium, high); not the optimum of the indices"],
             ["Features", "One: average crimes per reporting year", "Base paper: crime, population, literacy, expenditure, police, forest", "Only the crime counts were available in the committed data; no population to normalise by"],
             ["Route score", "Mean of tier weights over sampled points, times a night factor", "Distance-weighted interpolation between districts; learned weights", "Transparent: every score can be explained from three weights; no labelled routes exist to learn from"],
             ["Spatial lookup", "Nearest district by haversine distance over all 467 rows", "Polygon containment; k-d tree", "No district boundaries were available; 467 rows need no index (but there is no distance limit)"],
             ["Routing", "OSRM public server [17] over OpenStreetMap [18]", "Commercial map APIs", "Free, returns alternatives and full geometry, no key"],
             ["Voice trigger", "Web Speech API [25] plus a word-window matcher", "Exact substring only; edit distance; an on-device keyword spotter", "Runs in the browser with no extra service; tolerates one missed word at higher sensitivity; no model to train"],
             ["Live location", "WebSocket broadcast keyed by share token [20]", "Polling the tracking endpoint", f"Guardians receive a position {A['websocket']['one_viewer_post_to_receive']['mean_ms']:.0f} ms on average after the update (measured locally, one viewer); no polling load"],
             ["Evidence integrity", "SHA-256 of the uploaded bytes [22]", "Digital signatures; blockchain anchoring", f"Cheap (about {A['evidence_integrity']['sha256_1MB_ms']:.0f} ms per MB), standard, detects any change to the file if it is recomputed"],
             ["Authentication", "bcrypt [21] and HS256 JWT [19]", "Sessions; OAuth", "Stateless, standard, small code"]],
            "Main decisions of the implementation", widths=[0.13, 0.22, 0.33, 0.32], font=8.5)
    d.h3("Why k = 3, and what the indices say")
    ks = M["k_sweep"]
    row = {r["k"]: r for r in ks}
    d.p(f"Silhouette [11] and Davies-Bouldin [12] scores were computed for k = 2 to 8 on the 467 standardised values. k = 3 gives silhouette {row[3]['silhouette']:.3f} and Davies-Bouldin {row[3]['davies_bouldin']:.3f}. "
        f"k = 2 has the highest silhouette ({row[2]['silhouette']:.3f}) and k = 4 beats k = 3 on both indices (silhouette {row[4]['silhouette']:.3f}, Davies-Bouldin {row[4]['davies_bouldin']:.3f}). "
        "The choice of three clusters is therefore a presentation decision, three colours on the map and three weights in the scorer, not the metric optimum. The base paper [1] also reports 3-4 clusters; its tables "
        "give silhouette 0.416 and Davies-Bouldin 0.970 at k = 3 on its multi-feature data, which are not comparable with a single-feature result.")
    if not getattr(d, "report", False):
        fig(d, CHARTS / "01_k_sweep.png", "Silhouette and Davies-Bouldin scores for k = 2 to 8", width=4.6)
    d.h3("What the clustering actually does")
    e = M["one_feature_equivalence"]
    d.p(f"Because the data have one dimension, K-Means reduces to two cut-offs on the crime rate: districts below {e['threshold_low_medium']:.2f} crimes per year are low, those from there up to "
        f"{e['threshold_medium_high']:.2f} are medium and the rest are high. A threshold rule reproduces the K-Means tiers for {pct(e['threshold_rule_agreement_with_kmeans'], 0)} of districts. "
        "The \"model\" is therefore a data-driven pair of thresholds, and it is described as such in this report. The consequence for stability is measured in section 6.6.")
    fig(d, CHARTS / "02_crime_rate_tiers.png", "Distribution of the crime rate with the two cut-offs found by K-Means", width=4.8)
    if not getattr(d, "report", False):
        fig(d, CHARTS / "03_tiering_agreement.png", "Agreement of four other tiering methods with the shipped K-Means tiers", width=4.4)


# ---------------------------------------------------------------------------------------------------------------- 6.5
def sec_math(d):
    d.h2("Mathematical Formulation")
    d.p("The quantities used by the implementation are written below; the symbols are those of the code.")
    d.h3("Crime rate, scaling and risk score")
    d.code("crime_rate(i)  = ( sum over years y reported by district i of  sum over the 7 categories c of  count(i, y, c) ) / n_years(i)     (1)\n"
           "z(i)           = ( crime_rate(i) - mu ) / sigma            mu, sigma = mean and standard deviation over the 467 districts          (2)\n"
           "risk_score(i)  = 100 x ( crime_rate(i) - min ) / ( max - min )                                                                     (3)")
    d.h3("K-Means and its quality indices")
    d.p("K-Means [9], [10] chooses cluster centres that minimise the within-cluster sum of squares, with k = 3, `random_state` 42 and ten initialisations:")
    d.code("WCSS = sum over clusters j = 1..k of  sum over districts i in C_j of  ( z(i) - c_j )^2                                          (4)\n"
           "silhouette s(i) = ( b(i) - a(i) ) / max( a(i), b(i) ),   a = mean distance to own cluster, b = mean distance to the nearest other   (5)\n"
           "Davies-Bouldin DB = (1/k) sum over j of  max over l != j of  ( s_j + s_l ) / d(c_j, c_l)       lower is better                    (6)")
    d.p(f"The reported values are the mean silhouette {M['reproduction']['silhouette']:.4f}, DB {M['reproduction']['davies_bouldin']:.3f} and the Calinski-Harabasz index [13] {M['reproduction']['calinski_harabasz']:.1f}.")
    d.h3("Route risk score")
    d.p("For a route with coordinates p_1 ... p_n, the sample is every eighth point, P = {p_1, p_9, p_17, ...}. Let tier(p) be the risk tier of the district nearest to p, with the great-circle distance")
    d.code("haversine(p, q) = 2 R asin( sqrt( sin^2(dphi / 2) + cos(phi_p) cos(phi_q) sin^2(dlambda / 2) ) ),   R = 6371 km                  (7)\n"
           "w(low) = 1.0,  w(medium) = 2.5,  w(high) = 5.0                                                                                     (8)\n"
           "night(t) = 1.6 if UTC hour >= 15 (about 20:30-05:30 IST), else 1                                                                   (9)\n"
           "score(route) = night(t) x ( 1 / |P| ) x sum over p in P of  w( tier(p) )                                                          (10)")
    d.p("The route with the smallest score is recommended. Because night(t) multiplies every route by the same constant, it changes the size of the score but cannot change which of two routes is smaller; "
        "this is proved by the unit test `test_night_never_reorders_two_routes` and observed on all 16 test pairs (section 6.6 and Chapter 7). The UI also derives a LOW, MODERATE or HIGH label from the tier shares: "
        "HIGH when at least 20 % of the sampled points are in high-risk districts, MODERATE when any is or at least half are medium, otherwise LOW.")
    d.h3("SafePhrase matching")
    d.p("Let T be the set of words of a normalised stored phrase (m words) and let the spoken transcript be the word sequence u_1 ... u_L. The matcher returns the best window share")
    d.code("share = max over windows i = 1..max(1, L - m + 1) of  | { t in T : t in {u_i ... u_(i+m-1)} } | / m                                     (11)\n"
           "trigger  if  the normalised transcript contains the normalised phrase  or  share >= threshold(sensitivity)                         (12)\n"
           "threshold:  Low 1.00,  Medium 0.85,  High 0.75,  Ultra 0.60                                                                        (13)")
    d.p("Word order inside the window is ignored, and a phrase of three words needs all three at Low and Medium, because two of three is 0.67, below 0.85.")
    d.h3("Evidence integrity, tokens and tracking links")
    d.code("sha256(file bytes) -> 64 hexadecimal characters, stored with the evidence row; the stored file is named by its first 16 characters  (14)\n"
           "JWT claims: sub = user id, exp = issue time + 7 days; signed HS256 with the server secret                                        (15)\n"
           "share_token = random UUID in 32 hexadecimal characters = 128 random bits, one per emergency session                              (16)")


# ---------------------------------------------------------------------------------------------------------------- 6.6
def sec_model_training(d):
    d.h2("Model Training and Evaluation Procedure")
    r = M["reproduction"]
    d.p("`ml/train_risk_model.py` loads the two CSV files, builds the feature table of section 6.3, fits `StandardScaler` and `KMeans(n_clusters=3, random_state=42, n_init=10)`, "
        "names the tiers, and writes four artefacts: `models/risk_model.joblib` (scaler, K-Means model and the cluster-to-tier map; 3,064 bytes), `data/district_risk.csv` (467 rows), "
        "`experiments/metrics.json` and the console summary. On the development machine (Intel Core i5-12500, 15.7 GB, no GPU used) loading the data takes about 0.05 s and the K-Means fit "
        "about 0.12 s, so a retrain is instantaneous. There is **no train, validation or test split**: the method is unsupervised, there is no label for \"how risky a district is\", and "
        "the same 467 points are clustered and described.")
    d.p("`ml/eval.py` reloads the table and recomputes the silhouette and Davies-Bouldin scores of the stored tiers, the per-tier statistics and a sanity check that a route made only of "
        "high-risk-district points scores 5.0 while one made only of low-risk points scores 1.0. A second script, `scripts/run_experiments.py`, written for this report, repeats the "
        "model on the unmodified data and adds the studies below; it does not overwrite any shipped artefact.")
    d.table([["Measure", "Value"],
             ["Districts clustered", str(M["data"]["geocoded_pairs"])],
             ["Silhouette / Davies-Bouldin / Calinski-Harabasz", f"{r['silhouette']:.4f} / {r['davies_bouldin']:.3f} / {r['calinski_harabasz']:.1f}"],
             ["Tier counts (low / medium / high)", f"{r['tier_counts']['low']} / {r['tier_counts']['medium']} / {r['tier_counts']['high']}"],
             ["Mean crimes per year (low / medium / high)", "97.76 / 327.92 / 720.93"],
             ["Tier ranges, crimes per year", "low 0-212.0; medium 215.5-522.0; high 537.67-1191.58"],
             ["Agreement of a fresh fit with the shipped `district_risk.csv`", pct(r["agreement_with_shipped_district_risk_csv"], 0)],
             ["Stability over 30 single-initialisation runs (ARI vs shipped)", f"minimum {M['seed_stability']['min_ari_vs_shipped']:.3f}, mean {M['seed_stability']['mean_ari']:.3f}"]],
            "Evaluation of the area-risk model", widths=[0.55, 0.45], font=9.5, align=["l", "l"])
    d.p(f"The shipped result reproduces exactly: a fresh fit gives the same silhouette, the same tier counts and {pct(r['agreement_with_shipped_district_risk_csv'], 0)} agreement with the committed table. "
        f"With a single random initialisation instead of ten, the adjusted Rand index against the shipped tiers falls to {M['seed_stability']['min_ari_vs_shipped']:.2f} in the worst of 30 runs "
        f"(mean {M['seed_stability']['mean_ari']:.2f}), so districts near the two cut-offs change tier with the initialisation; the shipped model is stable only because it fixes the seed.")
    a = M["alternative_tiering"]
    d.p(f"Other ways of drawing three tiers disagree substantially: Ward clustering agrees on {pct(a['agglomerative_ward']['agreement_with_kmeans'])} of districts (231 / 164 / 72 districts), a Gaussian mixture on "
        f"{pct(a['gaussian_mixture']['agreement_with_kmeans'])} (181 / 214 / 72), equal-count terciles on {pct(a['equal_count_terciles']['agreement_with_kmeans'])} and fixed 100 and 300 cut-offs on {pct(a['fixed_100_300_cutoffs']['agreement_with_kmeans'])}. "
        "The size of the \"high\" tier (41 districts) is thus a consequence of the method and not a fact about India. The highest crime rates are West Godavari (1,191.6 per year), Vijayawada (1,059.0, five reporting years), "
        "Guntur (1,032.5), Jaipur (1,001.4, five years) and Krishna (895.2); 12 of the 41 high-tier districts are in Andhra Pradesh and 11 in Rajasthan.")
    d.h3("Route scoring evaluation")
    rs = M["route_summary"]
    d.p(f"The route scorer has no labelled data either, so it was exercised on {rs['pairs_requested']} real city pairs from the OSRM server (responses cached in `experiments/study/osrm_cache.json`). "
        f"{rs['pairs_with_alternatives']} pairs returned two alternatives and {rs['alternatives_histogram']['1']} returned only one, so for those trips there is nothing to choose between. The recommended route was also the "
        f"OSRM fastest in {rs['recommended_is_fastest']} of {rs['pairs_routed']} pairs, and where alternatives existed the safest pick cost on average {rs['mean_extra_minutes_when_alternatives']} extra minutes. "
        f"The day and night orderings were identical in {rs['ranking_same_day_night']} of {rs['pairs_routed']} pairs; tier weights of 1 / 2 / 3 or 1 / 3 / 9 changed the recommendation in {rs['weights_change_ranking']} of {rs['multi_route_pairs']} pairs "
        f"and sampling every 1, 4, 16 or 32 points instead of 8 changed it in {rs['sample_n_changes_ranking']}. Scoring one route takes about {rs['score_one_route_ms_mean']:.0f} ms of pure-Python distance computation.")
    cc = M["city_coverage"]
    d.p(f"The weakness is coverage. `nearest_district` has no distance limit, and for 40 Indian city centres the nearest geocoded district is a median {cc['median_km']} km away but up to {cc['max_km']} km: Hyderabad is "
        f"{cc['nearest_district_km']['Hyderabad']} km from its nearest district, Lucknow {cc['nearest_district_km']['Lucknow']} km, Kolkata {cc['nearest_district_km']['Kolkata']} km and Kanpur {cc['nearest_district_km']['Kanpur']} km; {cc['over_100km']} of the 40 are more than 100 km away. "
        f"Along the 16 test routes the mean distance from a sample point to the district that scored it was {rs['mean_nearest_district_km_along_routes']} km (maximum {rs['max_nearest_district_km_along_routes']} km). "
        "A route through such a city is scored with the tier of a district hundreds of kilometres away.")
    if not getattr(d, "report", False):
        fig(d, CHARTS / "04_city_coverage.png", "Distance from city centres to the nearest district in the risk table", width=4.8)
        fig(d, CHARTS / "06_route_scores_day_night.png", "Route scores by day and by night for the ten city pairs that returned two routes", width=5.6)
    d.p("**How the figures were produced.** `scripts/run_experiments.py` imports the product's own `backend/app/services/risk.py`; `scripts/measure_api.py`, `scripts/safephrase_eval.mjs` "
        "and `scripts/assistant_eval.py` measure the running API, the SafePhrase matcher and the assistant, and `tests/` holds the automated tests. Results are written to `experiments/study/`.")


# ---------------------------------------------------------------------------------------------------------------- 6.7
def sec_app_arch(d):
    d.h2("Application Architecture")
    if not getattr(d, "report", False):
        fig(d, DIAG / "01_system_architecture.png", "System architecture of SHEGUARD", width=6.2)
    py = count_lines(["*.py"], ["backend/app"])
    ts = count_lines(["*.ts", "*.tsx"], ["frontend/src"])
    d.paras(
        "The back end is a FastAPI application. Routers in `routes/` (auth, guardians, risk, routes_plan, sos, evidence, track, ai, places, ws) validate input and enforce ownership; "
        "`services/` holds the logic that talks to outside systems or does the scoring (osrm, risk, gemini, telegram, email, hashing); SQLAlchemy models in `models.py` map to six SQLite tables; "
        "Pydantic schemas in `schemas.py` define request bodies; `auth.py` has password hashing, JWT creation and the `get_current_user` dependency; `ws_manager.py` keeps guardian WebSocket viewers "
        "grouped by share token. On start-up the application creates the tables and loads `data/district_risk.csv` into `district_risk` if that table is empty. Uploaded evidence is written under "
        "`data/evidence/{session_id}/` and mounted read-only at `/evidence-files`.",
        "The front end is a React 19 single-page application in TypeScript built with Vite. It has nine screens (landing, login, register, dashboard, safe routes, AI Guardian, SafePhrase, emergency, profile and "
        "guardians) and a public tracking page at `/track/{token}`. `lib/api.ts` wraps `fetch`, attaches the bearer token from `localStorage` and signs the user out on a 401; the hooks `useLiveLocation` "
        "(geolocation `watchPosition`, one push every 4 s), `useVoiceTrigger` (Web Speech API in continuous mode, restarted when the browser stops it), and `useBattery` provide device input; Leaflet draws the maps "
        "and the risk circles; Tailwind CSS 4 styles the interface; `vite-plugin-pwa` produces the manifest and service worker. SafePhrase phrases, settings and the recent-activity list are kept in the browser "
        "(`localStorage`) and never sent to the server, which learns only the trigger name (`manual` or `safephrase`) when an emergency starts. The Vite server on port 5107 proxies `/api` and `/ws` to port 8107.")
    d.table([["Layer", "Technology", "Version"],
             ["Language and runtime", "Python; Node.js", "3.11.9; 24.19.0"],
             ["Web framework", "FastAPI with uvicorn", "0.115.6; 0.32.1"],
             ["Database", "SQLAlchemy over SQLite", "2.0.36"],
             ["Machine learning", "scikit-learn; pandas; NumPy; joblib", "1.5.2; 2.2.3; 2.1.3; 1.4.2"],
             ["Security", "PyJWT (HS256); bcrypt", "2.10.1; 4.2.1"],
             ["Services", "httpx client for OSRM, Nominatim, Gemini and Telegram; smtplib for Gmail", "0.28.1; standard library"],
             ["Real-time", "FastAPI WebSocket; websockets", "14.1"],
             ["Front end", "React; Vite; Tailwind CSS; Leaflet; TypeScript", "19.0.1; 6; 4.1; 1.9.4; 5.8"],
             ["Size", "Back end Python (`backend/app`); front end TypeScript (`frontend/src`)", f"{py:,} lines; {ts:,} lines (26 files)"],
             ["Machine used", "Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, Windows 11 Pro", "no GPU used"]],
            "Technology stack of the implementation", widths=[0.24, 0.5, 0.26], font=9.5)
    d.p("The screens follow the lifecycle of an emergency. **Dashboard:** SOS button, guardian count, area risk at the current position, battery, SafePhrase status, recent activity. **Safe routes:** destination "
        "search, route map with the risk heat layer and route cards. **AI Guardian:** chat with the assistant. **SafePhrase:** phrases, test mode and sensitivity. **Emergency:** who was alerted, tracking link, live map, "
        "evidence buttons, hold-to-cancel. **Profile:** guardians (name, phone, e-mail, Telegram chat ID), sign-out and a fake-call screen.")


# ---------------------------------------------------------------------------------------------------------------- 6.8
def sec_walkthrough(d):
    d.h2("Key Code Walkthroughs")
    d.h3("Training the risk tiers")
    d.p("The three tiers are produced by a scaler and K-Means with a fixed seed; the cluster ids are then renamed by sorting the clusters on their mean crime rate.")
    d.code(grab("ml/train_risk_model.py", "X = data[[\"crime_rate\"]].values", 17), "Clustering and tier naming in ml/train_risk_model.py")
    d.h3("Scoring a route")
    d.p("`score_route` samples the polyline, finds the nearest district for each sample, adds the tier weight (multiplied at night) and returns the mean.")
    d.code(grab("backend/app/services/risk.py", "def score_route", 23), "Route score in backend/app/services/risk.py")
    d.h3("Matching a spoken phrase")
    d.p("The matcher first tests whether the normalised transcript contains the phrase; otherwise it slides a window of the phrase's length over the transcript words and keeps the best share of matched words.")
    d.code(grab("frontend/src/lib/safephrase.ts", "const spoken = normalizeText(transcript)", 25), "Phrase matching in frontend/src/lib/safephrase.ts")
    d.h3("Starting an emergency")
    d.p("`start_sos` stores the session and the first ping, builds the tracking link from the browser's origin, then tries every guardian on every configured channel and reports what was delivered.")
    d.code(grab("backend/app/routes/sos.py", "guardians = db.query(models.Guardian)", 11), "Guardian alert fan-out in backend/app/routes/sos.py")
    d.p("Delivery is attempted one guardian and one channel at a time. `send_email` is an ordinary blocking function inside an `async` route, so with real Gmail credentials it would hold the server's event loop for as long as each "
        "SMTP exchange takes (up to the 10 s timeout). The channels were never run with real credentials in this project.")
    if not getattr(d, "report", False):
        d.h3("Streaming a location to guardians")
        d.p("Each position update is stored as a ping and then broadcast to the WebSocket viewers registered under the session's share token.")
        d.code(grab("backend/app/routes/sos.py", "session.last_lat = body.lat", 12), "Location push in backend/app/routes/sos.py")
        d.code(grab("backend/app/ws_manager.py", "async def broadcast", 9), "Broadcast in backend/app/ws_manager.py")
    d.h3("Preserving evidence")
    d.p("The uploaded bytes are hashed before they are written; the stored file is named by the first sixteen characters of the hash and the row records the full digest, the kind, the time and the position.")
    d.code(grab("backend/app/routes/evidence.py", "data = await file.read()", 24), "Evidence hashing and storage in backend/app/routes/evidence.py")
    if not getattr(d, "report", False):
        d.h3("Pushing the live position from the browser")
        d.code(grab("frontend/src/hooks/useLiveLocation.ts", "const watchId", 16), "Throttled position push in frontend/src/hooks/useLiveLocation.ts")


# ---------------------------------------------------------------------------------------------------------------- 6.9
def sec_api(d):
    d.h2("API Design")
    d.p("The API is REST over JSON under `/api`: 19 HTTP endpoints and one WebSocket route, plus one static mount for evidence files. FastAPI serves interactive documentation at `/docs`. Every endpoint except health, registration, login, the public district list, "
        "the guardian tracking page and the evidence mount needs `Authorization: Bearer <token>`; the WebSocket is addressed by the share token alone. Errors have the form `{\"detail\": \"message\"}` with status 400, 401, 404, 422 or 502.")
    d.table([["Method", "Path", "Auth", "Purpose"],
             ["GET", "/api/health", "none", "Liveness"],
             ["POST", "/api/auth/register", "none", "Create an account; returns a JWT and the user"],
             ["POST", "/api/auth/login", "none", "Returns a JWT and the user"],
             ["GET", "/api/auth/me", "JWT", "Current user"],
             ["GET / POST", "/api/guardians", "JWT", "List own guardians; add one (name, phone, e-mail, Telegram chat ID)"],
             ["PUT / DELETE", "/api/guardians/{id}", "JWT, owner", "Edit or remove a guardian; another user's id gives 404"],
             ["GET", "/api/risk/areas", "public", "467 district rows with tier, score, rate and coordinates"],
             ["POST", "/api/routes/plan", "JWT", "OSRM alternatives scored and sorted; first is recommended; 502 if OSRM fails, 404 if no route"],
             ["GET", "/api/places/search?q=", "JWT", "Nominatim search restricted to India, five results"],
             ["POST", "/api/sos/start", "JWT", "New session and share token; guardian alerts; returns the tracking URL and delivery report"],
             ["POST", "/api/sos/{id}/location", "JWT, owner", "Store a ping and broadcast it; 400 once the session is cancelled"],
             ["POST", "/api/sos/{id}/cancel", "JWT, owner", "End the session and broadcast `cancelled`"],
             ["GET", "/api/sos/{id}", "JWT, owner", "Status, trigger, times, last position, evidence count"],
             ["POST / GET", "/api/sos/{id}/evidence", "JWT, owner", "Upload a photo or audio file (multipart, kind, optional lat and lng); list with hashes"],
             ["GET", "/api/track/{share_token}", "token only", "Read-only view for guardians: name, status, path, last position"],
             ["WS", "/ws/track/{share_token}", "token only", "Pushes `location` and `cancelled` messages"],
             ["POST", "/api/ai/ask", "JWT", "Question and optional position to Gemini; 502 on provider error"],
             ["GET", "/evidence-files/...", "none (static)", "Stored evidence files"]],
            "API endpoints", widths=[0.12, 0.3, 0.14, 0.44], font=8.5)
    d.p("**Example: plan a route.** The request carries two coordinate pairs; the response lists each alternative with its geometry, risk score and the tier counts of the sampled points:")
    d.code('POST /api/routes/plan\n{"origin_lat": 28.6139, "origin_lng": 77.2090, "dest_lat": 26.9124, "dest_lng": 75.7873}\n'
           '-> {"routes": [{"index": 0, "distance_m": ..., "duration_s": ..., "coordinates": [[lat, lng], ...],\n'
           '                "risk_score": 3.204, "risk_tiers": {"low": .., "medium": .., "high": ..},\n'
           '                "is_night": false, "recommended": true}, {...}], "safest_index": 0}',
           "Route request and response (shape)")
    d.p("**Example: start an emergency.** `POST /api/sos/start` with `{\"lat\": 17.385, \"lng\": 78.4867, \"trigger\": \"safephrase\"}` returns `session_id`, `share_token`, `tracking_url`, `started_at` and a "
        "`delivery` list with one `{guardian, telegram, email}` entry per guardian. The WebSocket then sends `{\"type\": \"location\", \"lat\", \"lng\", \"ts\"}` messages and a final `{\"type\": \"cancelled\"}`.")


# ---------------------------------------------------------------------------------------------------------------- 6.10
def sec_security(d):
    d.h2("Security and Error Handling")
    d.bullets([
        "**Passwords** are hashed with bcrypt and a random salt; registration requires a valid e-mail address and a password of at least six characters (nothing stronger is required, `aaaaaa` is accepted).",
        "**Tokens.** A signed HS256 JWT [19] with the user id (`sub`) and a seven-day expiry; every protected route decodes it, loads the user and returns 401 for a missing, forged, tampered or expired token. The secret comes from `.env`; the code falls back to a development default only if none is set.",
        "**Ownership instead of row-level security.** Guardians, sessions, pings and evidence carry the owner's id, and every route compares it with the token's user: another user's session, guardian or evidence list returns 404 (confirmed by live probes and tests).",
        "**Guardian access.** Guardians never log in. They reach an emergency only through the 128-bit `share_token` in the link, which opens a read-only endpoint and a read-only WebSocket.",
        "**Evidence.** Only `photo` and `audio` kinds and non-empty files are accepted; the file is hashed with SHA-256 on arrival.",
        "**Provider errors.** OSRM, Nominatim and Gemini failures are caught and returned as 502 with a message; the front end replaces the raw error with a plain \"unavailable\" text.",
    ])
    d.p("**Known gaps, found by testing and code review, stated so that they are not mistaken for features.** Six are recorded as expected-failure tests (Chapter 7): (1) a Gemini read timeout is not caught and becomes HTTP 500 instead of 502; "
        "(2) coordinates are not range-checked (latitude 999 is accepted); (3) the `trigger` field accepts any string; (4) the WebSocket accepts any token, even one that matches no session; (5) there is no upload size limit "
        f"(a 20 MB file was accepted in {A['input_handling']['evidence: 20 MB upload (accepted = no size limit)']['seconds']} s); (6) an `.html` file uploaded as a photo is served back as `text/html` from the API's origin.")
    d.p("Further weaknesses were found by probing or reading the code: stored evidence files can be fetched without a token (the file name needs the 16-hex hash prefix, so it is not guessable from the session id, but anyone with a link has the file); "
        "25 wrong passwords in a row all return 401 with no lock-out; the tracking page keeps the whole location trail after the session is cancelled and never expires; CORS allows every origin; the blocking `send_email` call described in section 6.8; "
        "and `.env`, which holds the keys, is tracked by version control in this repository and must not be committed. The Telegram alert is sent with `parse_mode` HTML while containing the user's name, so a name with an angle bracket could make "
        "Telegram refuse it; this was read from the code and not tested. The hash of an evidence file lives in the same database as its path, and no endpoint recomputes it, so tampering is detectable only if someone does the comparison.")


# ---------------------------------------------------------------------------------------------------------------- 6.11
def sec_install(d):
    d.h2("Installation and Execution")
    d.p("The application needs Python 3.10 or later (3.11.9 was used) and Node.js 18 or later (24.19.0 was used). All commands are run from the project folder `8.ProjectCode`.")
    d.table([["Step", "Command", "What it does"],
             ["1", "setup.bat", "Copies `.env.example` to `.env` if needed, creates `venv`, installs `backend/requirements.txt`, runs `npm install` in `frontend/`"],
             ["2", "Edit `.env`", "Set `JWT_SECRET`, `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`; without the last three no alert is delivered, and without the first the assistant answers with an error"],
             ["3", "venv\\Scripts\\python.exe ml\\train_risk_model.py", "Optional: rebuilds the model, `data/district_risk.csv` and `experiments/metrics.json` (committed copies already exist)"],
             ["4", "run.bat", "Starts the back end on port 8107 (`uvicorn backend.app.main:app`) and the Vite front end on port 5107, and opens the browser"],
             ["5", "venv\\Scripts\\python.exe scripts\\seed_demo.py", "With the back end running, creates the demo account and one sample guardian"],
             ["6", "venv\\Scripts\\python.exe scripts\\smoke_test.py", "Twelve live end-to-end steps against the running API"],
             ["7", "venv\\Scripts\\python.exe -m pytest tests -q", "The 57 automated tests (offline; uses a temporary database)"],
             ["8", "run_experiments.py, measure_api.py, assistant_eval.py; node scripts\\safephrase_eval.mjs", "Regenerate the measurements in `experiments/study/`"]],
            "Installation and execution", widths=[0.07, 0.38, 0.55], font=9)
    d.p("`docs/03_HOW_TO_RUN.md` also describes phone testing through a Cloudflare quick tunnel (`run_phone.bat`); that path was not exercised in this documentation run. "
        "A browser with speech recognition (Chrome or Edge) is needed for SafePhrase, and Chrome asks for location, microphone and camera permission.")
    if not getattr(d, "report", False):
        d.table([["Account", "E-mail", "Password"],
                 ["Demo user", "demo@sheguard.app", "Demo@1234"]],
                "Demo account created by the seed script", widths=[0.2, 0.5, 0.3], font=10)
    else:
        d.p("The demo account created by the seed script is listed in Appendix B.")
    d.p("**Golden path.** Register or log in, add two guardians on the profile page, open Safe routes and search a destination, open SafePhrase to check the phrase and sensitivity, press the SOS button, "
        "add a photo and an audio clip, open the tracking link in a private window, and hold the cancel button for three seconds.")
