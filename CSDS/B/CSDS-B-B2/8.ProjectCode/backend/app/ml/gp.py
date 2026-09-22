"""Gaussian Process utilities for spatial signal prediction (training evaluation and live suggestions).

Readings are projected to local metres, grid-averaged to remove duplicates, and a GP is fitted
locally around the point of interest with hyperparameters learned offline (optimizer off at request
time, so a fit takes milliseconds). The kernel has two scales:

    C_short * Matern(~30 m) + C_long * Matern(~300-1200 m) + White

The short component follows street-level variation; the long one carries the area trend into gaps
between measured streets. With a single scale the GP learns only the short range and falls back to
the mean inside gaps, which lost to inverse-distance weighting on held-out blocks.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

EARTH_R = 6_371_008.8


def project(lat, lon, lat0: float, lon0: float) -> np.ndarray:
    """Equirectangular projection to metres around (lat0, lon0) - accurate to <0.1% within a few km."""
    lat = np.asarray(lat, float)
    lon = np.asarray(lon, float)
    x = np.radians(lon - lon0) * EARTH_R * np.cos(np.radians(lat0))
    y = np.radians(lat - lat0) * EARTH_R
    return np.column_stack([x, y])


def unproject(xy: np.ndarray, lat0: float, lon0: float) -> tuple[np.ndarray, np.ndarray]:
    xy = np.atleast_2d(xy)
    lat = lat0 + np.degrees(xy[:, 1] / EARTH_R)
    lon = lon0 + np.degrees(xy[:, 0] / (EARTH_R * np.cos(np.radians(lat0))))
    return lat, lon


def haversine_m(lat1, lon1, lat2, lon2) -> np.ndarray:
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi, dlmb = p2 - p1, np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlmb / 2) ** 2
    return 2 * EARTH_R * np.arcsin(np.sqrt(a))


def bearing_deg(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dl = np.radians(lon2 - lon1)
    x = np.sin(dl) * np.cos(p2)
    y = np.cos(p1) * np.sin(p2) - np.sin(p1) * np.cos(p2) * np.cos(dl)
    return float((np.degrees(np.arctan2(x, y)) + 360) % 360)


def aggregate(lat, lon, values, cell_m: float = 10.0) -> pd.DataFrame:
    """Average readings that fall in the same cell_m x cell_m square (removes 1 Hz repeats)."""
    df = pd.DataFrame({"lat": lat, "lon": lon, "v": values}).dropna()
    if df.empty:
        return pd.DataFrame(columns=["lat", "lon", "value", "n"])
    lat0, lon0 = float(df.lat.mean()), float(df.lon.mean())
    xy = project(df.lat, df.lon, lat0, lon0)
    df["gx"] = np.floor(xy[:, 0] / cell_m).astype(np.int64)
    df["gy"] = np.floor(xy[:, 1] / cell_m).astype(np.int64)
    g = df.groupby(["gx", "gy"]).agg(lat=("lat", "mean"), lon=("lon", "mean"), value=("v", "mean"), n=("v", "size"))
    return g.reset_index(drop=True)


@dataclass
class GPParams:
    amp_short: float      # variance of the street-level component (target units squared)
    ls_short: float       # metres
    amp_long: float       # variance of the area-trend component
    ls_long: float        # metres
    noise: float          # observation noise variance
    nu: float = 1.5

    @classmethod
    def initial(cls, y: np.ndarray) -> "GPParams":
        v = float(np.var(y)) or 1.0
        return cls(amp_short=0.4 * v, ls_short=60.0, amp_long=0.4 * v, ls_long=600.0, noise=0.2 * v)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "GPParams":
        return cls(**{k: float(v) for k, v in d.items()})


SHORT_BOUNDS, LONG_BOUNDS = (10.0, 300.0), (300.0, 10000.0)


def make_kernel(p: GPParams, fixed: bool = True):
    from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel

    def b(bounds):
        return "fixed" if fixed else bounds

    return (ConstantKernel(p.amp_short, b((1e-3, 1e4))) * Matern(p.ls_short, b(SHORT_BOUNDS), nu=p.nu)
            + ConstantKernel(p.amp_long, b((1e-3, 1e4))) * Matern(p.ls_long, b(LONG_BOUNDS), nu=p.nu)
            + WhiteKernel(p.noise, b((1e-4, 1e3))))


def learn_params(xy: np.ndarray, y: np.ndarray, init: GPParams | None = None, restarts: int = 2, seed: int = 42) -> GPParams:
    """Maximise the marginal likelihood on (a subsample of) readings."""
    from sklearn.gaussian_process import GaussianProcessRegressor

    init = init or GPParams.initial(y)
    gpr = GaussianProcessRegressor(kernel=make_kernel(init, fixed=False), normalize_y=False,
                                   n_restarts_optimizer=restarts, random_state=seed)
    gpr.fit(xy, y - y.mean())
    k = gpr.kernel_   # ((C*M) + (C*M)) + White
    short, long_ = k.k1.k1, k.k1.k2
    return GPParams(amp_short=float(short.k1.constant_value), ls_short=float(short.k2.length_scale),
                    amp_long=float(long_.k1.constant_value), ls_long=float(long_.k2.length_scale),
                    noise=float(k.k2.noise_level), nu=init.nu)


def fit_predict(xy_train: np.ndarray, y_train: np.ndarray, xy_query: np.ndarray, p: GPParams,
                prior_mean: float | None = None, latent: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """Fit with frozen hyperparameters and return predictive mean and std.

    latent=True returns the uncertainty of the underlying signal field (what a spot "really" offers);
    latent=False adds the observation noise, i.e. the spread expected for a single new reading.
    """
    from sklearn.gaussian_process import GaussianProcessRegressor

    mean = float(np.mean(y_train)) if prior_mean is None else prior_mean
    gpr = GaussianProcessRegressor(kernel=make_kernel(p, fixed=True), optimizer=None, normalize_y=False)
    gpr.fit(xy_train, y_train - mean)
    mu, sd = gpr.predict(xy_query, return_std=True)   # includes the WhiteKernel noise
    if latent:
        sd = np.sqrt(np.maximum(sd ** 2 - p.noise, 1e-9))
    return mu + mean, sd


def local_training_set(xy_train: np.ndarray, center: np.ndarray, radius_m: float, max_points: int) -> np.ndarray:
    """Indices of training points within radius_m of center, keeping the max_points nearest."""
    d = np.hypot(xy_train[:, 0] - center[0], xy_train[:, 1] - center[1])
    idx = np.flatnonzero(d <= radius_m)
    if len(idx) > max_points:
        idx = idx[np.argsort(d[idx])[:max_points]]
    return idx
