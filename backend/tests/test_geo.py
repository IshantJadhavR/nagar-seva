# -*- coding: utf-8 -*-
"""Location intelligence. The real map services are replaced by a fake, so tests run offline."""
import io
import pytest
from PIL import Image
from backend.app.services import geo
from backend.tests.conftest import login

PIN = (19.9975, 73.7898)            # inside Maharashtra (Nashik)


def _overpass(lat, lng, school_m=None, road_m=None):
    els = []
    if school_m is not None:
        els.append({"type": "node", "lat": lat + school_m / 111320, "lon": lng, "tags": {"amenity": "school", "name": "Test Vidyalaya"}})
    if road_m is not None:
        els.append({"type": "way", "center": {"lat": lat, "lon": lng + road_m / 105000}, "tags": {"highway": "primary", "name": "Main Rd"}})
    return {"elements": els}


@pytest.fixture
def fake_map(monkeypatch):
    state = {"school": 80, "road": None, "forward": None, "down": False, "calls": 0}

    def fake(url, data=None, service="nominatim", timeout=8.0):
        state["calls"] += 1
        if state["down"]:
            raise OSError("offline")
        if "/reverse" in url:
            return {"display_name": "Test Vidyalaya Road, Nashik, Maharashtra, India"}
        if "/search" in url:
            f = state["forward"]
            return [{"lat": str(f[0]), "lon": str(f[1])}] if f else []
        import re, urllib.parse
        q = urllib.parse.unquote_plus((data or b"").decode())
        m = re.search(r"around:\d+,([\d.]+),([\d.]+)", q)           # build the answer around the pin that was asked about
        return _overpass(float(m.group(1)), float(m.group(2)), state["school"], state["road"])
    monkeypatch.setattr(geo, "_http_json", fake)
    return state


def _fresh(lat_shift):
    """Different pin each test so the geo_cache of an earlier test is not reused."""
    return PIN[0] + lat_shift, PIN[1] + lat_shift


def test_bounds_and_distance():
    assert geo.in_maharashtra(19.99, 73.78) and not geo.in_maharashtra(28.6, 77.2)      # Delhi is outside
    assert 105_000 < geo.haversine_m(19, 73, 20, 73) < 117_000


def test_parse_overpass_and_points():
    near = geo.parse_overpass(_overpass(*PIN, school_m=100, road_m=900), *PIN)
    assert near["school"]["distance_m"] < 130 and near["school"]["name"] == "Test Vidyalaya" and near["hospital"] is None
    assert geo.map_points(near) == 20
    assert geo.map_points({"school": {"distance_m": 250}, "hospital": None, "main_road": None}) == 10
    assert geo.map_points({"school": {"distance_m": 900}, "hospital": None, "main_road": {"distance_m": 20}}) == 10
    assert geo.map_points(None) == 0 and geo.map_points({"school": None, "hospital": None, "main_road": None}) == 0
    assert geo.evidence(near) and "from map data" in geo.evidence(near)[0]


def test_geo_check_endpoint(client, citizen, fake_map):
    lat, lng = _fresh(0.001)
    r = client.post("/geo/check", headers=citizen, json={"lat": lat, "lng": lng})
    assert r.status_code == 200, r.text
    b = r.json()
    assert b["inside_area"] and "Nashik" in b["geo_address"] and b["nearby"]["school"] and b["points_from_map"] == 20
    assert client.post("/geo/check", json={"lat": lat, "lng": lng}).status_code == 401


def test_address_mismatch_detected(client, citizen, fake_map):
    fake_map["forward"] = (20.5, 74.5)                          # typed address resolves ~90 km away
    lat, lng = _fresh(0.002)
    b = client.post("/geo/check", headers=citizen, json={"lat": lat, "lng": lng, "address": "Some Chowk, Malegaon"}).json()
    assert b["address_mismatch"] is True and b["address_distance_m"] > 50_000
    fake_map["forward"] = (lat, lng)
    b = client.post("/geo/check", headers=citizen, json={"lat": lat, "lng": lng, "address": "Another place, Nashik"}).json()
    assert b["address_mismatch"] is False


def test_services_down_still_works(client, citizen, fake_map):
    fake_map["down"] = True
    lat, lng = _fresh(0.003)
    b = client.post("/geo/check", headers=citizen, json={"lat": lat, "lng": lng}).json()
    assert b["geo_address"] is None and b["nearby"] is None and b["nearby_checked"] is False and b["points_from_map"] == 0
    r = client.post("/complaints", headers=citizen, json={"text": "Big pothole on the road, please repair", "lat": lat + 0.01, "lng": lng + 0.01})
    assert r.status_code == 201


def test_outside_maharashtra_rejected(client, citizen, fake_map):
    b = client.post("/geo/check", headers=citizen, json={"lat": 28.6, "lng": 77.2}).json()
    assert b["inside_area"] is False and b["nearby"] is None
    r = client.post("/complaints", headers=citizen, json={"text": "Big pothole on the road, please repair", "lat": 28.6, "lng": 77.2})
    assert r.status_code == 422


def test_map_adds_priority_without_text_or_checkbox(client, citizen, fake_map):
    fake_map["school"] = 60
    lat, lng = _fresh(0.004)
    text = "Big pothole in our lane, please repair it soon"
    plain = client.post("/complaints", headers=citizen, json={"text": text}).json()
    mapped = client.post("/complaints", headers=citizen, json={"text": text, "lat": lat, "lng": lng}).json()
    assert mapped["priority_breakdown"]["location_context"] == 20
    assert plain["priority_breakdown"]["location_context"] == 0
    assert mapped["priority_score"] > plain["priority_score"]
    assert mapped["priority_breakdown"]["location_evidence"] and mapped["geo_address"]
    assert mapped["priority_level"] != "critical"                # the map never creates a Critical


def test_officer_wrong_location_and_admin_fix(client, citizen, admin, fake_map):
    fake_map["school"] = None
    lat, lng = _fresh(0.005)
    c = client.post("/complaints", headers=citizen, json={"text": "Garbage has not been collected here for days", "lat": lat, "lng": lng, "ward": "Ward-2"}).json()
    off = login(client, "solid.officer2@example.com", "Officer@123")
    assert c["priority_breakdown"]["location_context"] == 0
    r = client.post(f"/officer/complaints/{c['id']}/wrong-location", headers=off, json={"note": "Nothing here"})
    assert r.status_code == 200 and r.json()["location_flag"] == "wrong"
    assert client.post(f"/officer/complaints/{c['id']}/wrong-location", headers=citizen, json={}).status_code == 403
    assert any(x["id"] == c["id"] for x in client.get("/admin/location-problems", headers=admin).json())
    fake_map["school"] = 50
    new = _fresh(0.006)
    fixed = client.post(f"/admin/complaints/{c['id']}/location", headers=admin, json={"lat": new[0], "lng": new[1], "note": "moved"})
    assert fixed.status_code == 200, fixed.text
    f = fixed.json()
    assert f["location_flag"] is None and f["lat"] == new[0] and f["priority_breakdown"]["location_context"] == 20
    assert client.post(f"/admin/complaints/{c['id']}/location", headers=admin, json={"lat": 28.6, "lng": 77.2}).status_code == 422
    assert not any(x["id"] == c["id"] for x in client.get("/admin/location-problems", headers=admin).json())


def _jpeg_with_gps(lat, lng):
    img = Image.new("RGB", (8, 8), "gray")
    ex = img.getexif()

    def dms(v):
        d = int(v); m = int((v - d) * 60); s = (v - d - m / 60) * 3600
        return (float(d), float(m), float(s))
    ex.get_ifd(0x8825).update({1: "N", 2: dms(lat), 3: "E", 4: dms(lng)})
    buf = io.BytesIO(); img.save(buf, "JPEG", exif=ex)
    return buf.getvalue()


def test_photo_gps_read_and_endpoint(client, citizen, fake_map):
    lat, lng = _fresh(0.007)
    data = _jpeg_with_gps(lat, lng)
    got = geo.photo_gps(io.BytesIO(data))
    assert got and abs(got[0] - lat) < 1e-3 and abs(got[1] - lng) < 1e-3
    r = client.post("/geo/photo-gps", headers=citizen, files={"file": ("p.jpg", io.BytesIO(data), "image/jpeg")}).json()
    assert r["has_gps"] and r["inside_area"] and r["address"]
    plain = io.BytesIO(); Image.new("RGB", (4, 4)).save(plain, "JPEG")
    assert client.post("/geo/photo-gps", headers=citizen, files={"file": ("p.jpg", io.BytesIO(plain.getvalue()), "image/jpeg")}).json() == {"has_gps": False}


def test_photo_far_from_pin_is_flagged(client, citizen, admin, fake_map):
    fake_map["school"] = None
    lat, lng = _fresh(0.008)
    c = client.post("/complaints", headers=citizen, json={"text": "Garbage pile near our gate for days", "lat": lat, "lng": lng}).json()
    far = _jpeg_with_gps(lat + 0.2, lng)                           # ~22 km away
    r = client.post(f"/complaints/{c['id']}/image", headers=citizen, files={"file": ("a.jpg", io.BytesIO(far), "image/jpeg")}).json()
    assert r["photo_distance_m"] > 20_000
    assert client.get(f"/complaints/{c['id']}", headers=citizen).json()["location_flag"] == "photo_far"
    near = client.post("/complaints", headers=citizen, json={"text": "Garbage pile near our gate for days", "lat": lat, "lng": lng}).json()
    ok = _jpeg_with_gps(lat + 0.0001, lng)
    client.post(f"/complaints/{near['id']}/image", headers=citizen, files={"file": ("a.jpg", io.BytesIO(ok), "image/jpeg")})
    assert client.get(f"/complaints/{near['id']}", headers=citizen).json()["location_flag"] is None


# ---------------------------------------------------------------- help request, phone sharing, reject
def _new_citizen(client, phone=None, n=[0]):
    n[0] += 1
    email = f"phone.user{n[0]}@example.com"
    body = {"name": "Phone User", "email": email, "password": "Secret@123"}
    if phone is not None:
        body["phone"] = phone
    assert client.post("/auth/register", json=body).status_code == 201, body
    return login(client, email, "Secret@123")


def _assigned(client, who):
    c = client.post("/complaints", headers=who, json={"text": "Garbage has not been collected in our lane for a week", "ward": "Ward-2"}).json()
    assert c["status"] == "assigned", c
    return c["id"]


def test_phone_validation_and_profile(client):
    r = client.post("/auth/register", json={"name": "Bad Phone", "email": "bad.phone@example.com", "password": "Secret@123", "phone": "12345"})
    assert r.status_code == 422
    h = _new_citizen(client, "+91 98765 43210")
    assert client.get("/auth/me", headers=h).json()["phone"] == "9876543210"
    assert client.put("/auth/phone", headers=h, json={"phone": "98765"}).status_code == 422
    assert client.put("/auth/phone", headers=h, json={"phone": ""}).json()["phone"] is None


def test_help_request_phone_shared_only_when_admin_allows(client, admin):
    citizen = _new_citizen(client, "9123456780")
    cid = _assigned(client, citizen)
    off = login(client, "solid.officer2@example.com", "Officer@123")
    # officer asks for help; cannot see the number yet
    assert client.post(f"/officer/complaints/{cid}/help", headers=off, json={"reason": "x"}).status_code == 422
    r = client.post(f"/officer/complaints/{cid}/help", headers=off, json={"reason": "Cannot find the lane, pin is in a field"})
    assert r.status_code == 200 and r.json()["help_request"]["status"] == "open" and "citizen_phone" not in r.json()
    assert client.post(f"/officer/complaints/{cid}/help", headers=off, json={"reason": "asking again"}).status_code == 409
    # citizen never sees the help request or any phone
    mine = client.get(f"/complaints/{cid}", headers=citizen).json()
    assert "help_request" not in mine and "citizen_phone" not in mine
    # admin sees it in the problem list, with the number
    probs = client.get("/admin/location-problems", headers=admin).json()
    assert any(x["id"] == cid for x in probs)
    assert client.get(f"/complaints/{cid}", headers=admin).json()["citizen_phone"] == "9123456780"
    # admin shares
    ok = client.post(f"/admin/complaints/{cid}/help-reply", headers=admin, json={"message": "Call before going", "share_phone": True})
    assert ok.status_code == 200 and ok.json()["help_request"]["phone_shared"] is True
    seen = client.get(f"/complaints/{cid}", headers=off).json()
    assert seen["citizen_phone"] == "9123456780" and seen["help_request"]["reply"] == "Call before going"
    assert not any(x["id"] == cid for x in client.get("/admin/location-problems", headers=admin).json())
    # another officer never sees it
    other = login(client, "solid.officer1@example.com", "Officer@123")
    assert "citizen_phone" not in client.get(f"/complaints/{cid}", headers=other).json()
    # after the officer resolves, the number is hidden again
    client.patch(f"/officer/complaints/{cid}/status", headers=off, json={"status": "in_progress"})
    client.patch(f"/officer/complaints/{cid}/status", headers=off, json={"status": "resolved", "note": "done"})
    assert "citizen_phone" not in client.get(f"/complaints/{cid}", headers=off).json()


def test_reply_without_sharing_and_missing_phone(client, admin):
    citizen = _new_citizen(client)                       # no phone saved
    cid = _assigned(client, citizen)
    off = login(client, "solid.officer2@example.com", "Officer@123")
    client.post(f"/officer/complaints/{cid}/help", headers=off, json={"reason": "Landmark not clear"})
    bad = client.post(f"/admin/complaints/{cid}/help-reply", headers=admin, json={"share_phone": True})
    assert bad.status_code == 409
    ok = client.post(f"/admin/complaints/{cid}/help-reply", headers=admin, json={"message": "Ask at the temple", "share_phone": False})
    assert ok.status_code == 200
    assert "citizen_phone" not in client.get(f"/complaints/{cid}", headers=off).json()
    assert client.post(f"/admin/complaints/{cid}/help-reply", headers=admin, json={}).status_code == 404     # nothing open now
    assert client.post(f"/admin/complaints/{cid}/help-reply", headers=login(client, "solid.officer2@example.com", "Officer@123"), json={}).status_code == 403


def test_admin_rejects_complaint(client, admin):
    citizen = _new_citizen(client)
    cid = _assigned(client, citizen)
    off = login(client, "solid.officer2@example.com", "Officer@123")
    client.post(f"/officer/complaints/{cid}/wrong-location", headers=off, json={"note": "no such place"})
    assert client.post(f"/admin/complaints/{cid}/reject", headers=admin, json={"reason": "x"}).status_code == 422
    assert client.post(f"/admin/complaints/{cid}/reject", headers=citizen, json={"reason": "not allowed"}).status_code == 403
    r = client.post(f"/admin/complaints/{cid}/reject", headers=admin, json={"reason": "Location does not exist, citizen unreachable"})
    assert r.status_code == 200 and r.json()["status"] == "rejected"
    mine = client.get(f"/complaints/{cid}", headers=citizen).json()           # the citizen can read why
    assert mine["status"] == "rejected" and "Rejected by the admin" in mine["history"][-1]["note"]
    assert not any(x["id"] == cid for x in client.get("/admin/location-problems", headers=admin).json())
    assert not any(x["id"] == cid for x in client.get("/officer/complaints", headers=off).json() if x["status"] in ("assigned", "in_progress"))
    assert client.post(f"/admin/complaints/{cid}/reject", headers=admin, json={"reason": "again please"}).status_code == 409
    assert client.post(f"/complaints/{cid}/reopen", headers=citizen, json={"note": "please look again"}).status_code == 409


def test_login_role_tab_mismatch_is_explained(client):
    r = client.post("/auth/login", json={"email": "citizen@example.com", "password": "Citizen@123", "role": "officer"})
    assert r.status_code == 403 and "citizen account" in r.json()["detail"]
    assert client.post("/auth/login", json={"email": "citizen@example.com", "password": "Citizen@123", "role": "citizen"}).status_code == 200
    assert client.post("/auth/login", json={"email": "citizen@example.com", "password": "bad", "role": "officer"}).status_code == 401   # wrong password is never confused with role
    assert client.post("/auth/login", json={"email": "admin@example.com", "password": "Admin@123"}).status_code == 200                 # role stays optional
