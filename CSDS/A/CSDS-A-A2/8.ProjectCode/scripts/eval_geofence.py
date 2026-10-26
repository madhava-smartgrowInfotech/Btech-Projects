"""
Geo-fence evaluation: haversine accuracy, boundary behaviour and sensitivity to GPS noise.

  A. haversine (sphere) vs. Vincenty inverse (WGS-84 ellipsoid) at campus scale
  B. accept / reject sweep across the boundary (radius + tolerance)
  C. Monte-Carlo simulation of GPS error: P(accept) as a function of true distance for several
     error magnitudes. This is a SIMULATION under an assumed isotropic Gaussian error model; it is
     not a field measurement of phone GPS.

    venv\\Scripts\\python scripts\\eval_geofence.py        ->  docs/evaluation/geofence.json
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from core import geofence  # noqa: E402

OUT = ROOT / "docs" / "evaluation"
OUT.mkdir(parents=True, exist_ok=True)
LAT0, LON0 = 17.3850, 78.4867   # same demo centre as the smoke test and demo pipeline


def vincenty_m(lat1, lon1, lat2, lon2) -> float:
    a, f = 6378137.0, 1 / 298.257223563
    b = (1 - f) * a
    U1, U2 = math.atan((1 - f) * math.tan(math.radians(lat1))), math.atan((1 - f) * math.tan(math.radians(lat2)))
    L = math.radians(lon2 - lon1)
    lam = L
    for _ in range(200):
        sinS = math.hypot(math.cos(U2) * math.sin(lam),
                          math.cos(U1) * math.sin(U2) - math.sin(U1) * math.cos(U2) * math.cos(lam))
        if sinS == 0:
            return 0.0
        cosS = math.sin(U1) * math.sin(U2) + math.cos(U1) * math.cos(U2) * math.cos(lam)
        sig = math.atan2(sinS, cosS)
        sinA = math.cos(U1) * math.cos(U2) * math.sin(lam) / sinS
        cos2A = 1 - sinA ** 2
        cos2Sm = cosS - 2 * math.sin(U1) * math.sin(U2) / cos2A if cos2A else 0.0
        C = f / 16 * cos2A * (4 + f * (4 - 3 * cos2A))
        lam_new = L + (1 - C) * f * sinA * (sig + C * sinS * (cos2Sm + C * cosS * (-1 + 2 * cos2Sm ** 2)))
        if abs(lam_new - lam) < 1e-14:
            lam = lam_new
            break
        lam = lam_new
    u2 = cos2A * (a * a - b * b) / (b * b)
    A = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
    B = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))
    dS = B * sinS * (cos2Sm + B / 4 * (cosS * (-1 + 2 * cos2Sm ** 2) - B / 6 * cos2Sm * (-3 + 4 * sinS ** 2) * (-3 + 4 * cos2Sm ** 2)))
    return b * A * (sig - dS)


def offset(lat, lon, dist_m, bearing_deg):
    """Destination point on the sphere (used only to generate test positions)."""
    R, d, br = geofence.EARTH_RADIUS_M, dist_m / geofence.EARTH_RADIUS_M, math.radians(bearing_deg)
    p1, l1 = math.radians(lat), math.radians(lon)
    p2 = math.asin(math.sin(p1) * math.cos(d) + math.cos(p1) * math.sin(d) * math.cos(br))
    l2 = l1 + math.atan2(math.sin(br) * math.sin(d) * math.cos(p1), math.cos(d) - math.sin(p1) * math.sin(p2))
    return math.degrees(p2), math.degrees(l2)


def main() -> None:
    # ---- A. haversine vs Vincenty ------------------------------------------------ #
    rows = []
    for d in (10, 25, 50, 75, 100, 250, 500, 1000, 5000):
        errs = []
        for br in range(0, 360, 45):
            lat, lon = offset(LAT0, LON0, d, br)
            errs.append(geofence.haversine_m(LAT0, LON0, lat, lon) - vincenty_m(LAT0, LON0, lat, lon))
        rows.append({"nominal_m": d, "max_abs_error_m": float(np.max(np.abs(errs))),
                     "max_rel_error_pct": float(np.max(np.abs(errs)) / d * 100)})
    # ---- B. boundary sweep ---------------------------------------------------------- #
    radius = config.DEFAULT_GEOFENCE_RADIUS_M
    sweep = []
    for d in range(0, 151, 5):
        lat, lon = offset(LAT0, LON0, d, 90)
        r = geofence.check_geofence(lat, lon, LAT0, LON0, radius, 10.0)
        sweep.append({"distance_m": d, "inside": r.inside, "measured_m": round(r.distance_m, 2)})
    acc_rej = geofence.check_geofence(LAT0, LON0 + 0.00001, LAT0, LON0, radius, config.MAX_GPS_ACCURACY_M + 1)
    acc_ok = geofence.check_geofence(LAT0, LON0 + 0.00001, LAT0, LON0, radius, config.MAX_GPS_ACCURACY_M)
    # ---- C. Monte-Carlo GPS noise ----------------------------------------------------- #
    rng = np.random.default_rng(20261015)
    allowed = radius + config.GEOFENCE_TOLERANCE_M
    sigmas = [3, 5, 10, 20, 30]
    dists = list(range(0, 201, 5))
    N = 20000
    curves = {}
    for s in sigmas:
        ps = []
        for d in dists:
            e = rng.normal(0, s, size=(N, 2))
            ps.append(float((np.hypot(d + e[:, 0], e[:, 1]) <= allowed).mean()))
        curves[str(s)] = ps
    key_points = {}
    for s in sigmas:
        key_points[str(s)] = {
            "accept_at_40m": curves[str(s)][dists.index(40)], "accept_at_60m": curves[str(s)][dists.index(60)],
            "accept_at_100m": curves[str(s)][dists.index(100)], "accept_at_150m": curves[str(s)][dists.index(150)],
        }
    result = {
        "centre": [LAT0, LON0], "radius_m": radius, "tolerance_m": config.GEOFENCE_TOLERANCE_M, "allowed_m": allowed,
        "max_gps_accuracy_m": config.MAX_GPS_ACCURACY_M,
        "A_haversine_vs_vincenty": rows,
        "B_boundary_sweep": sweep,
        "B_accuracy_gate": {"at_limit_accepted": acc_ok.inside, "over_limit_rejected": not acc_rej.inside,
                            "over_limit_reason": acc_rej.reason},
        "C_gps_noise_simulation": {"model": "isotropic Gaussian, sigma per axis (m); 20000 trials per point",
                                   "trials": N, "distances_m": dists, "sigmas_m": sigmas, "p_accept": curves,
                                   "key_points": key_points},
    }
    (OUT / "geofence.json").write_text(json.dumps(result, indent=1))
    print(json.dumps({"A": rows, "gate": result["B_accuracy_gate"], "key": key_points}, indent=1))


if __name__ == "__main__":
    main()
