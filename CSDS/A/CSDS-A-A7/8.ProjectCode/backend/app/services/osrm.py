import httpx

OSRM_BASE = "https://router.project-osrm.org"


async def get_route_alternatives(origin_lat, origin_lng, dest_lat, dest_lng):
    """Fetch route alternatives from the free public OSRM demo server."""
    url = (
        f"{OSRM_BASE}/route/v1/driving/"
        f"{origin_lng},{origin_lat};{dest_lng},{dest_lat}"
    )
    params = {
        "alternatives": "true",
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    if data.get("code") != "Ok":
        raise RuntimeError(f"OSRM error: {data.get('message', data.get('code'))}")

    routes = []
    for r in data["routes"]:
        coords = r["geometry"]["coordinates"]  # [lng, lat] pairs
        routes.append({
            "distance_m": r["distance"],
            "duration_s": r["duration"],
            "coordinates": [[c[1], c[0]] for c in coords],  # -> [lat, lng]
        })
    return routes
