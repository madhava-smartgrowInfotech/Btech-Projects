"""Documentation-run experiments for SHEGUARD (area-risk model + route scoring).

Everything here re-uses the product's own data and code (data/*.csv, backend/app/services/risk.py) and
writes experiments/study/metrics.json. It does not touch the shipped model, data/district_risk.csv or
experiments/metrics.json.

    venv\\Scripts\\python.exe scripts\\run_experiments.py

The only network use is the public OSRM demo server (the same one the product calls); responses are cached in
experiments/study/osrm_cache.json so a re-run is offline and repeatable.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import httpx
import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.services import risk as risk_service  # noqa: E402

OUT = ROOT / "experiments" / "study"
OUT.mkdir(parents=True, exist_ok=True)
CACHE = OUT / "osrm_cache.json"

CRIME_COLS = [
    "Rape", "Kidnapping and Abduction", "Dowry Deaths",
    "Assault on women with intent to outrage her modesty",
    "Insult to modesty of Women", "Cruelty by Husband or his Relatives", "Importation of Girls",
]
TIERS = ["low", "medium", "high"]

CITIES = {
    "Hyderabad": (17.3850, 78.4867), "Secunderabad": (17.4399, 78.4983), "Vijayawada": (16.5062, 80.6480),
    "Warangal": (17.9689, 79.5941), "Visakhapatnam": (17.6868, 83.2185), "Delhi": (28.6139, 77.2090),
    "Jaipur": (26.9124, 75.7873), "Agra": (27.1767, 78.0081), "Mumbai": (19.0760, 72.8777),
    "Pune": (18.5204, 73.8567), "Chennai": (13.0827, 80.2707), "Bengaluru": (12.9716, 77.5946),
    "Kolkata": (22.5726, 88.3639), "Patna": (25.5941, 85.1376), "Lucknow": (26.8467, 80.9462),
    "Kanpur": (26.4499, 80.3319), "Ahmedabad": (23.0225, 72.5714), "Surat": (21.1702, 72.8311),
    "Bhopal": (23.2599, 77.4126), "Indore": (22.7196, 75.8577), "Nagpur": (21.1458, 79.0882),
    "Raipur": (21.2514, 81.6296), "Guwahati": (26.1445, 91.7362), "Bhubaneswar": (20.2961, 85.8245),
    "Kochi": (9.9312, 76.2673), "Thiruvananthapuram": (8.5241, 76.9366), "Chandigarh": (30.7333, 76.7794),
    "Ranchi": (23.3441, 85.3096), "Dehradun": (30.3165, 78.0322), "Srinagar": (34.0837, 74.7973),
    "Panaji": (15.4909, 73.8278), "Shimla": (31.1048, 77.1734), "Gandhinagar": (23.2156, 72.6369),
    "Coimbatore": (11.0168, 76.9558), "Madurai": (9.9252, 78.1198), "Varanasi": (25.3176, 82.9739),
    "Amritsar": (31.6340, 74.8723), "Jodhpur": (26.2389, 73.0243), "Mysuru": (12.2958, 76.6394),
    "Imphal": (24.8170, 93.9368),
}
PAIRS = [
    ("Hyderabad", "Vijayawada"), ("Hyderabad", "Warangal"), ("Visakhapatnam", "Vijayawada"), ("Delhi", "Jaipur"),
    ("Delhi", "Agra"), ("Mumbai", "Pune"), ("Chennai", "Bengaluru"), ("Kolkata", "Patna"), ("Lucknow", "Kanpur"),
    ("Ahmedabad", "Surat"), ("Bhopal", "Indore"), ("Nagpur", "Raipur"), ("Bengaluru", "Mysuru"),
    ("Kochi", "Thiruvananthapuram"), ("Chandigarh", "Delhi"), ("Hyderabad", "Secunderabad"),
]


def rnd(x, n=4):
    return round(float(x), n)


# ------------------------------------------------------------------ data + model reproduction
def load_features():
    df = pd.read_csv(ROOT / "data" / "raw" / "district_wise_crimes_against_women_2001_2012.csv")
    raw_rows = len(df)
    df = df[~df["DISTRICT"].str.contains("TOTAL", case=False, na=False)].copy()
    df["total_crimes"] = df[CRIME_COLS].sum(axis=1)
    agg = df.groupby(["STATE/UT", "DISTRICT"]).agg(total_crimes=("total_crimes", "sum"),
                                                    years_reported=("Year", "nunique")).reset_index()
    agg["crime_rate"] = agg["total_crimes"] / agg["years_reported"]
    agg = agg.rename(columns={"STATE/UT": "state", "DISTRICT": "district"})
    geo = pd.read_csv(ROOT / "data" / "districts_geocoded.csv")
    merged = agg.merge(geo, on=["state", "district"], how="inner")
    return raw_rows, df, agg, merged


def tier_labels(crime, labels):
    means = pd.Series(crime).groupby(labels).mean().sort_values()
    m = {c: TIERS[i] for i, c in enumerate(means.index)}
    return np.array([m[l] for l in labels])


def exp_data_and_model(res):
    raw_rows, df, agg, data = load_features()
    res["data"] = {
        "raw_rows": raw_rows,
        "rows_after_total_removal": len(df),
        "years": sorted(int(y) for y in df["Year"].unique()),
        "state_ut_count": int(df["STATE/UT"].nunique()),
        "district_state_pairs": len(agg),
        "geocoded_pairs": int(len(data)),
        "geocode_rate": rnd(len(data) / len(agg)),
        "years_reported_distribution": {str(k): int(v) for k, v in agg["years_reported"].value_counts().sort_index().items()},
        "geocoded_years_reported_mean": rnd(data["years_reported"].mean(), 2),
        "crime_rate_describe": {k: rnd(v, 2) for k, v in data["crime_rate"].describe().items()},
    }
    # coverage by state: geocoded vs all
    cov = (agg.assign(geo=agg.set_index(["state", "district"]).index.isin(data.set_index(["state", "district"]).index))
           .groupby("state").agg(total=("district", "count"), geocoded=("geo", "sum")).reset_index())
    cov["rate"] = (cov["geocoded"] / cov["total"]).round(3)
    res["coverage_by_state"] = cov.sort_values("total", ascending=False).to_dict(orient="records")
    res["states_with_no_geocoded_district"] = cov[cov["geocoded"] == 0]["state"].tolist()

    # geocode sanity: inside India bounding box, duplicate coordinates
    in_box = data["lat"].between(6.5, 37.5) & data["lng"].between(68.0, 97.5)
    dup = data.duplicated(["lat", "lng"], keep=False)
    res["geocode_sanity"] = {
        "outside_india_bbox": int((~in_box).sum()),
        "districts_sharing_identical_coordinates": int(dup.sum()),
        "distinct_coordinates": int(data[["lat", "lng"]].drop_duplicates().shape[0]),
    }

    X = StandardScaler().fit_transform(data[["crime_rate"]].values)
    km = KMeans(n_clusters=3, random_state=42, n_init=10).fit(X)
    lab = km.labels_
    tiers = tier_labels(data["crime_rate"].values, lab)
    data = data.assign(tier=tiers)

    shipped = pd.read_csv(ROOT / "data" / "district_risk.csv")
    same = (shipped.merge(data[["state", "district", "tier"]], on=["state", "district"])
            .eval("risk_tier == tier").mean())
    res["reproduction"] = {
        "silhouette": rnd(silhouette_score(X, lab)),
        "davies_bouldin": rnd(davies_bouldin_score(X, lab)),
        "calinski_harabasz": rnd(calinski_harabasz_score(X, lab), 1),
        "tier_counts": {t: int((tiers == t).sum()) for t in TIERS},
        "agreement_with_shipped_district_risk_csv": rnd(same),
        "shipped_model_loads": bool(joblib.load(ROOT / "models" / "risk_model.joblib")["kmeans"].n_clusters == 3),
    }
    # K-Means on one feature = thresholds: boundaries between tiers
    crime = data["crime_rate"].values
    bounds = {t: [rnd(crime[tiers == t].min(), 2), rnd(crime[tiers == t].max(), 2)] for t in TIERS}
    thr_low_med = (crime[tiers == "low"].max() + crime[tiers == "medium"].min()) / 2
    thr_med_high = (crime[tiers == "medium"].max() + crime[tiers == "high"].min()) / 2
    rule = np.where(crime < thr_low_med, "low", np.where(crime < thr_med_high, "medium", "high"))
    res["one_feature_equivalence"] = {
        "tier_ranges_crimes_per_year": bounds,
        "threshold_low_medium": rnd(thr_low_med, 2),
        "threshold_medium_high": rnd(thr_med_high, 2),
        "threshold_rule_agreement_with_kmeans": rnd((rule == tiers).mean()),
    }

    # k sweep
    sweep = []
    for k in range(2, 9):
        m = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X)
        sweep.append({"k": k, "silhouette": rnd(silhouette_score(X, m.labels_)),
                      "davies_bouldin": rnd(davies_bouldin_score(X, m.labels_)),
                      "inertia": rnd(m.inertia_, 2)})
    res["k_sweep"] = sweep

    # stability: 30 random inits, n_init=1
    aris, sils = [], []
    for s in range(30):
        m = KMeans(n_clusters=3, random_state=s, n_init=1).fit(X)
        aris.append(adjusted_rand_score(lab, m.labels_))
        sils.append(silhouette_score(X, m.labels_))
    res["seed_stability"] = {"runs": 30, "min_ari_vs_shipped": rnd(min(aris)), "mean_ari": rnd(np.mean(aris)),
                             "silhouette_min": rnd(min(sils)), "silhouette_max": rnd(max(sils))}

    # alternative tiering methods
    alts = {}
    gm = GaussianMixture(n_components=3, random_state=42, n_init=5).fit(X)
    alts["gaussian_mixture"] = tier_labels(crime, gm.predict(X))
    alts["agglomerative_ward"] = tier_labels(crime, AgglomerativeClustering(n_clusters=3).fit_predict(X))
    q = pd.qcut(crime, 3, labels=TIERS).astype(str)
    alts["equal_count_terciles"] = np.array(q)
    alts["fixed_100_300_cutoffs"] = np.where(crime < 100, "low", np.where(crime < 300, "medium", "high"))
    out = {}
    for name, a in alts.items():
        out[name] = {"agreement_with_kmeans": rnd((a == tiers).mean()),
                     "ari_vs_kmeans": rnd(adjusted_rand_score(tiers, a)),
                     "tier_counts": {t: int((a == t).sum()) for t in TIERS}}
    res["alternative_tiering"] = out

    # who is "high risk"
    top = data.sort_values("crime_rate", ascending=False).head(12)[["state", "district", "crime_rate", "years_reported"]]
    res["top_high_risk_districts"] = [{**r, "crime_rate": rnd(r["crime_rate"], 1)} for r in top.to_dict(orient="records")]
    res["high_tier_by_state"] = {k: int(v) for k, v in data[data.tier == "high"].groupby("state").size().sort_values(ascending=False).head(8).items()}
    # crime composition of tiers (share of 'Cruelty by Husband or Relatives', which is domestic)
    comp = df.groupby(["STATE/UT", "DISTRICT"])[CRIME_COLS].sum().reset_index().rename(columns={"STATE/UT": "state", "DISTRICT": "district"})
    comp = comp.merge(data[["state", "district", "tier"]], on=["state", "district"])
    tot = comp[CRIME_COLS].sum(axis=1)
    res["crime_mix"] = {
        "cruelty_by_husband_share_of_all_counted_crimes": rnd(comp["Cruelty by Husband or his Relatives"].sum() / tot.sum()),
        "rape_share": rnd(comp["Rape"].sum() / tot.sum()),
        "kidnapping_share": rnd(comp["Kidnapping and Abduction"].sum() / tot.sum()),
        "assault_on_modesty_share": rnd(comp["Assault on women with intent to outrage her modesty"].sum() / tot.sum()),
        "insult_modesty_share": rnd(comp["Insult to modesty of Women"].sum() / tot.sum()),
        "dowry_deaths_share": rnd(comp["Dowry Deaths"].sum() / tot.sum()),
    }
    # year-state trend file
    st = pd.read_csv(ROOT / "data" / "raw" / "crimes_against_women_2001_2021.csv")
    res["state_year_file"] = {"rows": len(st), "years": [int(st["Year"].min()), int(st["Year"].max())],
                              "states": int(st["State"].nunique())}
    return data


# ------------------------------------------------------------------ route scoring
def osrm(a, b, cache):
    key = f"{a}|{b}"
    if key in cache:
        return cache[key]
    (la, lo), (lb, lb2) = CITIES[a], CITIES[b]
    url = f"https://router.project-osrm.org/route/v1/driving/{lo},{la};{lb2},{lb}"
    for attempt in range(3):
        try:
            r = httpx.get(url, params={"alternatives": "true", "overview": "full", "geometries": "geojson", "steps": "false"}, timeout=30)
            r.raise_for_status()
            data = r.json()
            routes = [{"distance_m": x["distance"], "duration_s": x["duration"],
                       "coordinates": [[c[1], c[0]] for c in x["geometry"]["coordinates"]]} for x in data["routes"]]
            cache[key] = routes
            time.sleep(1.2)
            return routes
        except Exception as e:  # noqa: BLE001
            print("OSRM retry", key, e)
            time.sleep(3)
    cache[key] = None
    return None


def exp_routes(res, data):
    districts = [SimpleNamespace(lat=r.lat, lng=r.lng, risk_tier=r.tier) for r in data.itertuples()]
    dlat = data["lat"].values
    dlng = data["lng"].values

    def nearest_km(lat, lng):
        return min(risk_service._haversine_km(lat, lng, a, b) for a, b in zip(dlat, dlng))

    # coverage of the 467-point district grid around 39 major cities
    near = {c: rnd(nearest_km(*xy), 1) for c, xy in CITIES.items()}
    arr = np.array(list(near.values()))
    res["city_coverage"] = {"cities": len(near), "nearest_district_km": near,
                            "median_km": rnd(np.median(arr), 1), "max_km": rnd(arr.max(), 1),
                            "within_25km": int((arr <= 25).sum()), "within_50km": int((arr <= 50).sum()),
                            "over_100km": int((arr > 100).sum())}

    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    day = pd.Timestamp("2026-10-26 07:00", tz="UTC").to_pydatetime()      # 12:30 IST
    night = pd.Timestamp("2026-10-26 18:00", tz="UTC").to_pydatetime()    # 23:30 IST
    rows, rank_checks = [], {"night_changes_ranking": 0, "sample_n_changes_ranking": 0, "weights_change_ranking": 0, "multi_route_pairs": 0}
    weights_alt = [{"low": 1.0, "medium": 2.0, "high": 3.0}, {"low": 1.0, "medium": 3.0, "high": 9.0}]
    orig_w = dict(risk_service.TIER_WEIGHT)
    t_score = []
    for a, b in PAIRS:
        routes = osrm(a, b, cache)
        CACHE.write_text(json.dumps(cache))
        if not routes:
            rows.append({"pair": f"{a} - {b}", "error": "OSRM unavailable"})
            continue
        s_day = [risk_service.score_route(r, districts, now=day) for r in routes]
        s_night = [risk_service.score_route(r, districts, now=night) for r in routes]
        t0 = time.perf_counter()
        risk_service.score_route(routes[0], districts, now=day)
        t_score.append(time.perf_counter() - t0)
        order = lambda sc: [i for i, _ in sorted(enumerate(sc), key=lambda x: x[1]["score"])]  # noqa: E731
        o_day, o_night = order(s_day), order(s_night)
        fastest = int(np.argmin([r["duration_s"] for r in routes]))
        shortest = int(np.argmin([r["distance_m"] for r in routes]))
        rec = o_day[0]
        row = {"pair": f"{a} - {b}", "alternatives": len(routes),
               "distance_km": [rnd(r["distance_m"] / 1000, 1) for r in routes],
               "duration_min": [rnd(r["duration_s"] / 60, 1) for r in routes],
               "points": len(routes[0]["coordinates"]), "samples_used": len(routes[0]["coordinates"][::8]),
               "score_day": [x["score"] for x in s_day], "score_night": [x["score"] for x in s_night],
               "tier_samples_route0": s_day[0]["tiers"],
               "recommended": rec, "fastest": fastest,
               "recommended_is_fastest": rec == fastest,
               "extra_minutes_vs_fastest": rnd((routes[rec]["duration_s"] - routes[fastest]["duration_s"]) / 60, 1),
               "ranking_same_day_night": o_day == o_night}
        if len(routes) > 1:
            rank_checks["multi_route_pairs"] += 1
            if o_day != o_night:
                rank_checks["night_changes_ranking"] += 1
            for n in (1, 4, 16, 32):
                sc = [risk_service.score_route(r, districts, sample_every_n=n, now=day) for r in routes]
                if order(sc)[0] != rec:
                    rank_checks["sample_n_changes_ranking"] += 1
                    break
            changed = False
            for w in weights_alt:
                risk_service.TIER_WEIGHT.clear(); risk_service.TIER_WEIGHT.update(w)
                sc = [risk_service.score_route(r, districts, now=day) for r in routes]
                if order(sc)[0] != rec:
                    changed = True
            risk_service.TIER_WEIGHT.clear(); risk_service.TIER_WEIGHT.update(orig_w)
            if changed:
                rank_checks["weights_change_ranking"] += 1
        # nearest-district distance along route (every 8th point)
        dists = [nearest_km(la, ln) for la, ln in routes[0]["coordinates"][::8]]
        row["nearest_district_km_mean"] = rnd(np.mean(dists), 1)
        row["nearest_district_km_max"] = rnd(max(dists), 1)
        rows.append(row)
    res["routes"] = rows
    ok = [r for r in rows if "error" not in r]
    res["route_summary"] = {
        "pairs_requested": len(PAIRS), "pairs_routed": len(ok),
        "pairs_with_alternatives": sum(1 for r in ok if r["alternatives"] > 1),
        "alternatives_histogram": {str(k): sum(1 for r in ok if r["alternatives"] == k) for k in sorted({r["alternatives"] for r in ok})},
        "recommended_is_fastest": sum(1 for r in ok if r["recommended_is_fastest"]),
        "ranking_same_day_night": sum(1 for r in ok if r["ranking_same_day_night"]),
        "mean_extra_minutes_when_alternatives": rnd(np.mean([r["extra_minutes_vs_fastest"] for r in ok if r["alternatives"] > 1] or [0]), 1),
        "mean_nearest_district_km_along_routes": rnd(np.mean([r["nearest_district_km_mean"] for r in ok]), 1),
        "max_nearest_district_km_along_routes": rnd(max(r["nearest_district_km_max"] for r in ok), 1),
        "score_one_route_ms_mean": rnd(np.mean(t_score) * 1000, 1),
        **rank_checks,
    }
    # arithmetic proof that the night multiplier cannot reorder routes
    ex = {"coordinates": [[17.0, 78.0]] * 20}
    s1 = risk_service.score_route(ex, districts, now=day)["score"]
    s2 = risk_service.score_route(ex, districts, now=night)["score"]
    res["night_multiplier"] = {"day_score": s1, "night_score": s2, "ratio": rnd(s2 / s1, 3),
                               "constant": risk_service.NIGHT_MULTIPLIER}

    # sanity pair used by ml/eval.py, plus a mixed route
    hi = next(d for d in districts if d.risk_tier == "high")
    lo = next(d for d in districts if d.risk_tier == "low")
    me = next(d for d in districts if d.risk_tier == "medium")
    sc = lambda d: risk_service.score_route({"coordinates": [[d.lat, d.lng]] * 10}, districts, sample_every_n=1, now=day)["score"]  # noqa: E731
    res["tier_scores_day"] = {"low": sc(lo), "medium": sc(me), "high": sc(hi)}


def main():
    res = {}
    data = exp_data_and_model(res)
    exp_routes(res, data)
    (OUT / "metrics.json").write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("reproduction", "one_feature_equivalence", "seed_stability", "route_summary", "night_multiplier", "city_coverage")}, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main()
