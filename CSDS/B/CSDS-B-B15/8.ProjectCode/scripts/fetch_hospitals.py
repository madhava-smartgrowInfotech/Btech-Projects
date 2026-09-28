"""One-time fetch of Hyderabad hospitals from OpenStreetMap (Overpass API).

Writes data/hospitals_osm.csv (committed). Data (c) OpenStreetMap contributors, ODbL.
Specialties, OP limits and emergency quotas are then assigned by scripts/seed_hospitals.py.
"""
import csv
import json
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "hospitals_osm.csv"
# Greater Hyderabad bounding box (south, west, north, east)
BBOX = (17.25, 78.30, 17.60, 78.65)
QUERY = f"""
[out:json][timeout:60];
(
  node["amenity"="hospital"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
  way["amenity"="hospital"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
  relation["amenity"="hospital"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
);
out center tags;
"""
ENDPOINTS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter",
             "https://maps.mail.ru/osm/tools/overpass/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]


def fetch():
    body = urllib.parse.urlencode({"data": QUERY}).encode()
    last = None
    for url in ENDPOINTS:
        try:
            req = urllib.request.Request(url, data=body, headers={"User-Agent": "MediQueue/1.0"})
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read())
        except Exception as e:  # try the mirror
            last = e
    raise RuntimeError(f"Overpass fetch failed: {last}")


def main():
    data = fetch()
    rows, seen = [], set()
    for el in data["elements"]:
        tags = el.get("tags", {})
        name = (tags.get("name:en") or tags.get("name") or "").strip()
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if not name or lat is None or name.lower() in seen:
            continue
        seen.add(name.lower())
        rows.append({
            "osm_id": f"{el['type']}/{el['id']}",
            "name": name,
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "speciality_tag": tags.get("healthcare:speciality", ""),
            "emergency_tag": tags.get("emergency", ""),
            "operator_type": tags.get("operator:type", ""),
            "addr": ", ".join(v for k, v in tags.items() if k in ("addr:street", "addr:suburb", "addr:city") and v),
        })
    rows.sort(key=lambda r: r["name"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"saved {len(rows)} hospitals -> {OUT}")


if __name__ == "__main__":
    main()
