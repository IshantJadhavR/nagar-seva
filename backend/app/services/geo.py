"""Location intelligence. Free OpenStreetMap services only (no API keys):

  * Nominatim  - reverse geocoding (pin -> address) and forward geocoding (typed address -> pin)
  * Overpass   - "what is within N metres of this pin?" (schools, hospitals, main roads)
  * EXIF       - GPS position stored inside a phone photo

Everything here FAILS SOFT: if a service is slow, down or rate-limited we return None / empty and the complaint
still works (the form checkboxes and the text keep driving priority). Results are cached in the database.
"""
import json
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from math import asin, cos, radians, sin, sqrt
from typing import Optional

from sqlalchemy.orm import Session

from ..models import GeoCache

# Rough bounding box of Maharashtra (south, north, west, east). A box, not the real border: it also covers
# slivers of neighbouring states. Good enough to reject pins in the sea or in another part of the country.
MH_LAT = (15.60, 22.10)
MH_LNG = (72.60, 80.95)
USER_AGENT = "NagarSeva-final-year-project/1.0 (student project)"     # OSM policy: identify your app
NOMINATIM = "https://nominatim.openstreetmap.org"
OVERPASS = "https://overpass-api.de/api/interpreter"

SCHOOL_NEAR_M, SCHOOL_FAR_M, MAIN_ROAD_M = 150, 300, 30         # thresholds used by the priority engine
ADDRESS_MISMATCH_M = 500                                          # typed address vs pin
PHOTO_MISMATCH_M = 300                                            # photo GPS vs pin
CACHE_DAYS = 30

_lock = threading.Lock()
_last_call = {"nominatim": 0.0, "overpass": 0.0}
_MIN_GAP = {"nominatim": 1.1, "overpass": 0.3}                   # Nominatim allows at most 1 request per second


def in_maharashtra(lat: float, lng: float) -> bool:
    return MH_LAT[0] <= lat <= MH_LAT[1] and MH_LNG[0] <= lng <= MH_LNG[1]


def haversine_m(lat1, lng1, lat2, lng2) -> float:
    """Great-circle distance in metres."""
    p1, p2 = radians(lat1), radians(lat2)
    a = sin((p2 - p1) / 2) ** 2 + cos(p1) * cos(p2) * sin(radians(lng2 - lng1) / 2) ** 2
    return 2 * 6371000 * asin(sqrt(a))


def _http_json(url: str, data: Optional[bytes] = None, service: str = "nominatim", timeout: float = 8.0):
    """One polite HTTP call. Tests replace this function with a fake."""
    with _lock:
        wait = _MIN_GAP[service] - (time.monotonic() - _last_call[service])
        if wait > 0:
            time.sleep(wait)
        _last_call[service] = time.monotonic()
    req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:      # nosec - fixed https hosts only
        return json.loads(r.read().decode("utf-8"))


# ------------------------------------------------------------------ cache
def _cache_get(db: Session, key: str):
    row = db.get(GeoCache, key)
    if row is None:
        return None
    created = row.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) - created > timedelta(days=CACHE_DAYS):
        return None
    return {"v": row.payload}


def _cache_put(db: Session, key: str, kind: str, payload):
    row = db.get(GeoCache, key)
    if row is None:
        db.add(GeoCache(key=key, kind=kind, payload=payload))
    else:
        row.payload, row.created_at = payload, datetime.now(timezone.utc)
    db.commit()


def _key(kind: str, lat: float, lng: float) -> str:
    return f"{kind}:{lat:.4f},{lng:.4f}"            # 4 decimals = about 11 m


# ------------------------------------------------------------------ reverse / forward geocoding
def reverse_geocode(db: Session, lat: float, lng: float) -> Optional[str]:
    key = _key("rev", lat, lng)
    hit = _cache_get(db, key)
    if hit:
        return hit["v"]
    try:
        q = urllib.parse.urlencode({"format": "jsonv2", "lat": lat, "lon": lng, "zoom": 18, "accept-language": "en"})
        data = _http_json(f"{NOMINATIM}/reverse?{q}")
        name = (data.get("display_name") or "")[:300] or None
    except Exception:
        return None
    if name:
        _cache_put(db, key, "reverse", name)
    return name


def forward_geocode(db: Session, text: str) -> Optional[tuple]:
    text = " ".join(text.split())[:200]
    key = f"fwd:{text.lower()}"
    hit = _cache_get(db, key)
    if hit:
        v = hit["v"]
        return tuple(v) if v else None
    try:
        q = urllib.parse.urlencode({"format": "jsonv2", "q": text, "limit": 1, "countrycodes": "in",
                                    "viewbox": f"{MH_LNG[0]},{MH_LAT[1]},{MH_LNG[1]},{MH_LAT[0]}", "bounded": 1})
        data = _http_json(f"{NOMINATIM}/search?{q}")
    except Exception:
        return None
    res = (float(data[0]["lat"]), float(data[0]["lon"])) if data else None
    _cache_put(db, key, "forward", list(res) if res else None)
    return res


# ------------------------------------------------------------------ nearby important places
_QUERY = """[out:json][timeout:10];
(
  nwr(around:{r},{lat},{lng})["amenity"~"^(school|college|kindergarten|university)$"];
  nwr(around:{r},{lat},{lng})["amenity"~"^(hospital|clinic)$"];
  way(around:{rd},{lat},{lng})["highway"~"^(trunk|primary|secondary)$"];
);
out center tags 60;"""


def _classify(tags: dict) -> Optional[str]:
    a, h = tags.get("amenity"), tags.get("highway")
    if a in ("school", "college", "kindergarten", "university"):
        return "school"
    if a in ("hospital", "clinic"):
        return "hospital"
    if h in ("trunk", "primary", "secondary"):
        return "main_road"
    return None


def parse_overpass(data: dict, lat: float, lng: float) -> dict:
    """Overpass JSON -> the nearest school, hospital and main road, each {name, distance_m} or None."""
    best = {"school": None, "hospital": None, "main_road": None}
    for el in data.get("elements", []):
        kind = _classify(el.get("tags", {}))
        if not kind:
            continue
        c = el.get("center") or {"lat": el.get("lat"), "lon": el.get("lon")}
        if c.get("lat") is None:
            continue
        d = round(haversine_m(lat, lng, c["lat"], c["lon"]))
        if best[kind] is None or d < best[kind]["distance_m"]:
            tags = el.get("tags", {})
            best[kind] = {"name": tags.get("name") or tags.get("name:en") or tags.get("ref"), "distance_m": d}
    return best


def nearby_places(db: Session, lat: float, lng: float) -> Optional[dict]:
    """None means 'could not find out' (service down), which is different from 'nothing nearby'."""
    key = _key("near", lat, lng)
    hit = _cache_get(db, key)
    if hit:
        return hit["v"]
    try:
        q = _QUERY.format(r=SCHOOL_FAR_M, rd=MAIN_ROAD_M + 20, lat=lat, lng=lng)
        data = _http_json(OVERPASS, data=urllib.parse.urlencode({"data": q}).encode(), service="overpass", timeout=12)
        found = parse_overpass(data, lat, lng)
    except Exception:
        return None
    _cache_put(db, key, "nearby", found)
    return found


# ------------------------------------------------------------------ photo GPS (EXIF)
def photo_gps(fileobj) -> Optional[tuple]:
    """GPS (lat, lng) stored in a photo, or None. Many apps (WhatsApp, some phone settings) strip it."""
    try:
        from PIL import Image
        img = Image.open(fileobj)
        gps = img.getexif().get_ifd(0x8825)
        if not gps or 2 not in gps or 4 not in gps:
            return None

        def deg(v, ref):
            d = float(v[0]) + float(v[1]) / 60 + float(v[2]) / 3600
            return -d if ref in ("S", "W") else d
        return deg(gps[2], gps.get(1, "N")), deg(gps[4], gps.get(3, "E"))
    except Exception:
        return None


# ------------------------------------------------------------------ one call for the whole check
def analyse(db: Session, lat: Optional[float], lng: Optional[float], typed_address: Optional[str] = None) -> dict:
    """Everything we can learn about a pin. Never raises."""
    out = {"inside_area": None, "geo_address": None, "nearby": None, "address_distance_m": None,
           "address_mismatch": False, "nearby_checked": False}
    if lat is None or lng is None:
        return out
    out["inside_area"] = in_maharashtra(lat, lng)
    if not out["inside_area"]:
        return out
    out["geo_address"] = reverse_geocode(db, lat, lng)
    out["nearby"] = nearby_places(db, lat, lng)
    out["nearby_checked"] = out["nearby"] is not None
    if typed_address and len(typed_address.strip()) >= 6:
        pt = forward_geocode(db, typed_address)
        if pt:
            d = round(haversine_m(lat, lng, pt[0], pt[1]))
            out["address_distance_m"] = d
            out["address_mismatch"] = d > ADDRESS_MISMATCH_M
    return out


def map_points(nearby: Optional[dict]) -> int:
    """Location points the map can justify (same scale as the checkbox: +20 school/hospital, +10 main road)."""
    if not nearby:
        return 0
    pts = 0
    for k in ("school", "hospital"):
        p = nearby.get(k)
        if p:
            pts = max(pts, 20 if p["distance_m"] <= SCHOOL_NEAR_M else 10 if p["distance_m"] <= SCHOOL_FAR_M else 0)
    p = nearby.get("main_road")
    if p and p["distance_m"] <= MAIN_ROAD_M:
        pts = max(pts, 10)
    return pts


def evidence(nearby: Optional[dict]) -> list:
    if not nearby:
        return []
    labels = {"school": "School or college", "hospital": "Hospital or clinic", "main_road": "Main road"}
    out = []
    for k in ("school", "hospital", "main_road"):
        p = nearby.get(k)
        if p and ((k == "main_road" and p["distance_m"] <= MAIN_ROAD_M) or (k != "main_road" and p["distance_m"] <= SCHOOL_FAR_M)):
            out.append(f"{labels[k]}{': ' + p['name'] if p.get('name') else ''} ({p['distance_m']} m, from map data)")
    return out
