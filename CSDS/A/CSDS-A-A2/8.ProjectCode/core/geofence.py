"""Geo-fence verification using the haversine great-circle distance."""
from __future__ import annotations

import math
from dataclasses import dataclass

import config

EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance in metres between two WGS-84 coordinates."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


@dataclass
class GeoResult:
    inside: bool
    distance_m: float
    allowed_m: float
    reason: str


def check_geofence(
    student_lat: float,
    student_lon: float,
    center_lat: float,
    center_lon: float,
    radius_m: float,
    accuracy_m: float | None = None,
) -> GeoResult:
    """
    Verify a student's GPS position against the session boundary.

    The allowed distance is radius + a small fixed tolerance for GPS noise.
    Readings with very poor accuracy are rejected outright.
    """
    if accuracy_m is not None and accuracy_m > config.MAX_GPS_ACCURACY_M:
        return GeoResult(
            False,
            haversine_m(student_lat, student_lon, center_lat, center_lon),
            radius_m,
            f"GPS accuracy too low (±{accuracy_m:.0f} m). Move to an open area and retry.",
        )

    distance = haversine_m(student_lat, student_lon, center_lat, center_lon)
    allowed = radius_m + config.GEOFENCE_TOLERANCE_M
    if distance <= allowed:
        return GeoResult(True, distance, allowed, f"Inside geo-fence ({distance:.1f} m from centre).")
    return GeoResult(
        False,
        distance,
        allowed,
        f"Outside geo-fence: you are {distance:.0f} m away, limit is {allowed:.0f} m.",
    )
