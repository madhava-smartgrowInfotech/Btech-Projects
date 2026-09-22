"""Better-signal suggestions and predicted coverage from the Gaussian Process (pure computation, no database).

Given nearby readings, fit a local GP with the learned hyperparameters, predict a 25 m grid around the
user (only where readings are close enough to support a prediction), and return the nearest point where
the signal is predicted Strong with at least 80% probability.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
from scipy.stats import norm

from .gp import GPParams, aggregate, bearing_deg, fit_predict, haversine_m, local_training_set, project, unproject

COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
MIN_CELLS = 12            # fewer aggregated measurement cells than this -> not enough data to model
SUPPORT_M = 180.0         # only predict grid points within this distance of a measurement


@dataclass
class Suggestion:
    found: bool
    status: str                        # found / already_strong / none_nearby / not_enough_data
    message: str
    target: str
    method: str                        # gaussian-process / nearest-strong-reading
    lat: float | None = None
    lon: float | None = None
    distance_m: float | None = None
    bearing_deg: float | None = None
    direction: str | None = None
    predicted: float | None = None
    predicted_sd: float | None = None
    probability: float | None = None
    here_predicted: float | None = None
    here_probability: float | None = None
    supporting_readings: int = 0
    unit: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def compass(bearing: float) -> str:
    return COMPASS[int((bearing + 22.5) // 45) % 8]


def target_config(gp_bundle: dict, target: str, operator: str | None) -> tuple[GPParams, float, str, dict]:
    t = gp_bundle["targets"][target]
    params = t.get("params_by_operator", {}).get(operator) or t["params"]
    return GPParams.from_dict(params), float(t["strong_threshold"]), t.get("unit", ""), gp_bundle.get("search", {})


def _fmt(target: str, value: float) -> str:
    return f"{value:.0f} dBm" if target == "rsrp" else f"{10 ** value:.1f} Mbps"


def suggest(gp_bundle: dict, target: str, lat: float, lon: float, pts_lat, pts_lon, pts_value,
            operator: str | None = None, search_radius_m: float = 1000.0) -> Suggestion:
    params, threshold, unit, search = target_config(gp_bundle, target, operator)
    cells = aggregate(np.asarray(pts_lat, float), np.asarray(pts_lon, float), np.asarray(pts_value, float), search.get("cell_m", 10.0))
    n_readings = int(np.asarray(pts_value).size)
    if len(cells) == 0:
        return Suggestion(False, "not_enough_data", "No readings near you yet. Collect a few readings while walking and try again.",
                          target, "gaussian-process", supporting_readings=0, unit=unit)

    xy = project(cells.lat, cells.lon, lat, lon)
    local = local_training_set(xy, np.zeros(2), search.get("radius_m", 1500.0), int(search.get("max_points", 1500)))
    if len(local) < MIN_CELLS:
        strong = cells[cells.value >= threshold]
        if len(strong):
            d = haversine_m(lat, lon, strong.lat.to_numpy(), strong.lon.to_numpy())
            j = int(np.argmin(d))
            b = bearing_deg(lat, lon, float(strong.lat.iloc[j]), float(strong.lon.iloc[j]))
            return Suggestion(True, "found", f"Too few readings to model the area; the nearest measured strong spot is {d[j]:.0f} m {compass(b)}.",
                              target, "nearest-strong-reading", float(strong.lat.iloc[j]), float(strong.lon.iloc[j]), round(float(d[j]), 1),
                              round(b, 1), compass(b), round(float(strong.value.iloc[j]), 3), None, None, supporting_readings=n_readings, unit=unit)
        return Suggestion(False, "not_enough_data", "Not enough readings nearby to predict where signal is better.",
                          target, "gaussian-process", supporting_readings=n_readings, unit=unit)

    xy_l, y_l = xy[local], cells.value.to_numpy()[local]
    step = float(search.get("grid_step_m", 25.0))
    g = np.arange(-search_radius_m, search_radius_m + step, step)
    gx, gy = np.meshgrid(g, g)
    grid = np.column_stack([gx.ravel(), gy.ravel()])
    grid = grid[np.hypot(grid[:, 0], grid[:, 1]) <= search_radius_m]
    nearest = np.min(np.hypot(grid[:, None, 0] - xy_l[None, :, 0], grid[:, None, 1] - xy_l[None, :, 1]), axis=1)
    grid = grid[nearest <= SUPPORT_M]
    query = np.vstack([np.zeros((1, 2)), grid])
    mu, sd = fit_predict(xy_l, y_l, query, params)
    prob = 1.0 - norm.cdf((threshold - mu) / np.maximum(sd, 1e-6))
    here_mu, here_p = float(mu[0]), float(prob[0])
    prob_needed = float(search.get("prob_threshold", 0.8))
    base = dict(target=target, method="gaussian-process", supporting_readings=n_readings, unit=unit,
                here_predicted=round(here_mu, 3), here_probability=round(here_p, 3))

    if here_p >= prob_needed:
        return Suggestion(True, "already_strong", f"You are already in a strong area (predicted {_fmt(target, here_mu)}).",
                          lat=lat, lon=lon, distance_m=0.0, predicted=round(here_mu, 3), predicted_sd=round(float(sd[0]), 3),
                          probability=round(here_p, 3), **base)

    ok = prob[1:] >= prob_needed
    if not ok.any():
        return Suggestion(False, "none_nearby", f"No spot within {search_radius_m / 1000:.1f} km is predicted strong with enough confidence.", **base)
    cand = grid[ok]
    dist = np.hypot(cand[:, 0], cand[:, 1])
    j = int(np.argmin(dist))
    c_lat, c_lon = unproject(cand[j:j + 1], lat, lon)
    k = 1 + int(np.flatnonzero(ok)[j])
    b = bearing_deg(lat, lon, float(c_lat[0]), float(c_lon[0]))
    return Suggestion(True, "found", f"Better signal about {dist[j]:.0f} m {compass(b)} (predicted {_fmt(target, float(mu[k]))}, "
                                     f"{prob[k]:.0%} likely Strong).",
                      lat=float(c_lat[0]), lon=float(c_lon[0]), distance_m=round(float(dist[j]), 1), bearing_deg=round(b, 1),
                      direction=compass(b), predicted=round(float(mu[k]), 3), predicted_sd=round(float(sd[k]), 3),
                      probability=round(float(prob[k]), 3), **base)


def predicted_surface(gp_bundle: dict, target: str, center_lat: float, center_lon: float, pts_lat, pts_lon, pts_value,
                      operator: str | None = None, radius_m: float = 1200.0, step_m: float = 40.0) -> list[dict]:
    """Grid of predicted values and Strong probability around a centre, for the map's predicted-coverage layer."""
    params, threshold, _, search = target_config(gp_bundle, target, operator)
    cells = aggregate(np.asarray(pts_lat, float), np.asarray(pts_lon, float), np.asarray(pts_value, float), search.get("cell_m", 10.0))
    if len(cells) < MIN_CELLS:
        return []
    xy = project(cells.lat, cells.lon, center_lat, center_lon)
    local = local_training_set(xy, np.zeros(2), radius_m + 300, int(search.get("max_points", 1500)))
    if len(local) < MIN_CELLS:
        return []
    xy_l, y_l = xy[local], cells.value.to_numpy()[local]
    g = np.arange(-radius_m, radius_m + step_m, step_m)
    gx, gy = np.meshgrid(g, g)
    grid = np.column_stack([gx.ravel(), gy.ravel()])
    nearest = np.min(np.hypot(grid[:, None, 0] - xy_l[None, :, 0], grid[:, None, 1] - xy_l[None, :, 1]), axis=1)
    grid = grid[nearest <= SUPPORT_M]
    if not len(grid):
        return []
    mu, sd = fit_predict(xy_l, y_l, grid, params)
    prob = 1.0 - norm.cdf((threshold - mu) / np.maximum(sd, 1e-6))
    lat, lon = unproject(grid, center_lat, center_lon)
    return [{"lat": round(float(a), 6), "lon": round(float(b), 6), "value": round(float(m), 3), "sd": round(float(s), 3),
             "p_strong": round(float(p), 3)} for a, b, m, s, p in zip(lat, lon, mu, sd, prob)]
