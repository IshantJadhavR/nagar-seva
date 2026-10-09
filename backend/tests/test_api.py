# -*- coding: utf-8 -*-
import io
from backend.tests.conftest import login


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_auth_rules(client):
    assert client.post("/auth/login", json={"email": "citizen@example.com", "password": "wrong"}).status_code == 401
    assert client.get("/complaints/mine").status_code == 401
    r = client.post("/auth/register", json={"name": "Asha", "email": "asha.patil@example.com", "password": "Secret@123"})
    assert r.status_code == 201 and r.json()["role"] == "citizen"
    assert client.post("/auth/register", json={"name": "Asha", "email": "asha.patil@example.com", "password": "Secret@123"}).status_code == 409
    assert client.post("/auth/register", json={"name": "A", "email": "bad", "password": "short"}).status_code == 422


def test_confident_complaint_is_auto_routed(client, citizen):
    r = client.post("/complaints", headers=citizen, json={
        "text": "Big pothole on the road near the school, children may fall. 3 days now.",
        "lat": 19.9, "lng": 74.4, "ward": "Ward-1", "near_school": True})
    assert r.status_code == 201, r.text
    c = r.json()
    assert c["route_mode"] == "auto" and c["status"] == "assigned"
    assert c["department"] == "Public Works Department" and c["assigned_officer"]
    assert c["priority_level"] in ("medium", "high") and c["priority_breakdown"]["location_context"] == 20
    assert c["history"][0]["new_status"] == "assigned"


def test_hindi_complaint_language_detected(client, citizen):
    r = client.post("/complaints", headers=citizen, json={"text": "सड़क पर बड़ा गड्ढा हो गया है, कृपया ठीक करें"})
    assert r.status_code == 201 and r.json()["language"] == "Hindi"


def test_ambiguous_goes_to_review_then_admin_routes_and_correction_saved(client, citizen, admin):
    r = client.post("/complaints", headers=citizen, json={"text": "Water is overflowing near the pipe, please check"})
    c = r.json()
    assert c["route_mode"] == "review" and c["status"] == "in_review" and c["assigned_officer"] is None
    queue = client.get("/admin/review-queue", headers=admin).json()
    assert any(x["id"] == c["id"] for x in queue)
    # citizen cannot use admin endpoints
    assert client.get("/admin/review-queue", headers=citizen).status_code == 403
    # admin corrects the category -> assigned + correction recorded
    r = client.post(f"/admin/complaints/{c['id']}/route", headers=admin, json={"category": "Drainage"})
    assert r.status_code == 200
    out = r.json()
    assert out["status"] == "assigned" and out["department"] == "Drainage and Sewerage" and out["route_mode"] == "manual"
    stats = client.get("/admin/analytics", headers=admin).json()
    assert stats["admin_decisions"] >= 1 and stats["admin_changed_prediction"] >= 1


def test_critical_goes_to_human_queue_even_when_confident(client, citizen, admin):
    r = client.post("/complaints", headers=citizen, json={"text": "There is an open manhole without a cover on the road"})
    c = r.json()
    assert c["priority_level"] == "critical" and c["urgent"] and c["route_mode"] == "review"
    queue = client.get("/admin/review-queue", headers=admin).json()
    assert queue[0]["urgent"] is True          # urgent cases sorted first


def test_officer_workflow_and_citizen_confirmation(client, citizen):
    cid = client.post("/complaints", headers=citizen, json={
        "text": "Garbage has not been collected in our lane for a week", "ward": "Ward-2"}).json()
    assert cid["route_mode"] == "auto"
    officer = {"Authorization": "Bearer " + client.post("/auth/login", json={
        "email": "solid.officer2@example.com", "password": "Officer@123"}).json()["access_token"]}
    cid = cid["id"]
    assert any(x["id"] == cid for x in client.get("/officer/complaints", headers=officer).json())
    # cannot skip steps
    assert client.patch(f"/officer/complaints/{cid}/status", headers=officer, json={"status": "resolved", "note": "x"}).status_code == 409
    assert client.patch(f"/officer/complaints/{cid}/status", headers=officer, json={"status": "in_progress"}).status_code == 200
    assert client.patch(f"/officer/complaints/{cid}/status", headers=officer, json={"status": "resolved"}).status_code == 422   # note required
    ok = client.patch(f"/officer/complaints/{cid}/status", headers=officer, json={"status": "resolved", "note": "Cleared the heap"})
    assert ok.status_code == 200 and ok.json()["status"] == "resolved"
    done = client.post(f"/complaints/{cid}/confirm", headers=citizen, json={"rating": 5, "feedback": "Thanks"})
    assert done.status_code == 200 and done.json()["status"] == "closed"
    assert client.post(f"/complaints/{cid}/confirm", headers=citizen, json={}).status_code == 409


def test_reopen(client, citizen):
    cid = client.post("/complaints", headers=citizen, json={"text": "Garbage heap near the market, not collected", "ward": "Ward-1"}).json()["id"]
    off = login(client, "solid.officer1@example.com", "Officer@123")
    client.patch(f"/officer/complaints/{cid}/status", headers=off, json={"status": "in_progress"})
    client.patch(f"/officer/complaints/{cid}/status", headers=off, json={"status": "resolved", "note": "done"})
    r = client.post(f"/complaints/{cid}/reopen", headers=citizen, json={"note": "Garbage is back"})
    assert r.status_code == 200 and r.json()["status"] == "reopened"


def test_privacy_other_citizens_cannot_read(client, citizen):
    cid = client.post("/complaints", headers=citizen, json={"text": "Garbage pile near our gate for days"}).json()["id"]
    other = login(client, "asha.patil@example.com", "Secret@123")
    assert client.get(f"/complaints/{cid}", headers=other).status_code == 404
    assert client.get(f"/complaints/{cid}", headers=citizen).status_code == 200


def test_validation_and_image_upload(client, citizen):
    assert client.post("/complaints", headers=citizen, json={"text": "short"}).status_code == 422
    cid = client.post("/complaints", headers=citizen, json={"text": "Garbage pile near the temple gate"}).json()["id"]
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 50
    ok = client.post(f"/complaints/{cid}/image", headers=citizen, files={"file": ("x.png", io.BytesIO(png), "image/png")})
    assert ok.status_code == 200 and ok.json()["image_path"].endswith(".png")
    bad = client.post(f"/complaints/{cid}/image", headers=citizen, files={"file": ("x.exe", io.BytesIO(b"MZ"), "application/octet-stream")})
    assert bad.status_code == 415


def test_admin_can_change_category_department_mapping(client, admin):
    cats = {c["name"]: c for c in client.get("/admin/categories", headers=admin).json()}
    depts = {d["name"]: d["id"] for d in client.get("/admin/departments", headers=admin).json()}
    r = client.patch(f"/admin/categories/{cats['Garbage']['id']}", headers=admin, json={"department_id": depts["Health Department"]})
    assert r.json()["department"] == "Health Department"
    client.patch(f"/admin/categories/{cats['Garbage']['id']}", headers=admin, json={"department_id": depts["Solid Waste Management"]})


def test_register_new_citizen_and_login(client):
    r = client.post("/auth/register", json={"name": "Asha Patil", "email": "meera.joshi@example.com", "password": "Strong#Pass1"})
    assert r.status_code == 201 and r.json()["role"] == "citizen"
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.post("/auth/login", json={"email": "MEERA.JOSHI@example.com", "password": "Strong#Pass1"}).status_code == 200
    # two citizens never see each other's complaints
    c = client.post("/complaints", json={"text": "Big pothole on our road for three days"}, headers=h).json()
    assert client.get("/complaints/mine", headers=h).json()[0]["id"] == c["id"]


def test_timestamps_are_timezone_aware_utc(client, citizen):
    c = client.post("/complaints", json={"text": "Garbage is piling up in our lane"}, headers=citizen).json()
    assert c["created_at"].endswith("+00:00")          # the browser converts this to IST


def test_change_password(client):
    r = client.post("/auth/register", json={"name": "Ravi K", "email": "ravi@example.com", "password": "OldPass#123"})
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.post("/auth/password", json={"current_password": "wrong", "new_password": "NewPass#123"}, headers=h).status_code == 400
    assert client.post("/auth/password", json={"current_password": "OldPass#123", "new_password": "NewPass#123"}, headers=h).status_code == 200
    assert client.post("/auth/login", json={"email": "ravi@example.com", "password": "NewPass#123"}).status_code == 200


def test_public_stats_and_analytics_fields(client, admin):
    s = client.get("/public/stats").json()
    assert set(s) == {"total", "resolved", "auto_routed"} and s["total"] >= 1
    a = client.get("/admin/analytics", headers=admin).json()
    assert len(a["per_day"]) == 14 and "resolution_rate" in a and "avg_resolution_hours" in a
