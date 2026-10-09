from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..auth import require_roles
from ..database import get_db
from ..models import now
from ..models import Category, Complaint, Correction, Department, User
from ..schemas import AdminRouteIn, CategoryUpdateIn, FixLocationIn, HelpReplyIn, RejectIn
from ..services import geo
from ..services.common import add_history, audit, complaint_out
from ..services.severity import priority_score
from ..services.routing import pick_officer

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_roles("admin"))])
IST = ZoneInfo("Asia/Kolkata")
PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


@router.get("/review-queue")
def review_queue(db: Session = Depends(get_db)):
    rows = db.scalars(select(Complaint).where(Complaint.status == "in_review")).all()
    rows.sort(key=lambda c: (not c.urgent, PRIORITY_RANK[c.priority_level], c.created_at))
    return [complaint_out(c) for c in rows]


@router.get("/location-problems")
def location_problems(db: Session = Depends(get_db)):
    """Complaints whose location is doubtful: officer said wrong, photo GPS far from the pin, or address vs pin mismatch."""
    rows = db.scalars(select(Complaint).where(Complaint.location_flag.is_not(None))
                      .where(Complaint.status.notin_(("closed", "rejected")))).all()
    rows.sort(key=lambda c: (c.location_flag != "wrong", PRIORITY_RANK[c.priority_level], c.created_at))
    return [complaint_out(c) for c in rows]


@router.post("/complaints/{cid}/location")
def fix_location(cid: int, body: FixLocationIn, admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    """Admin moves the pin. The map check and the priority are recomputed from the new place."""
    c = db.get(Complaint, cid)
    if not c:
        raise HTTPException(404, "Complaint not found")
    if not geo.in_maharashtra(body.lat, body.lng):
        raise HTTPException(422, "The pin is outside Maharashtra")
    place = geo.analyse(db, body.lat, body.lng, body.address)
    old_level = c.priority_level
    c.lat, c.lng = body.lat, body.lng
    c.address = body.address or c.address
    c.geo_address = place["geo_address"]
    c.geo_check = {k: place[k] for k in ("nearby", "address_distance_m", "address_mismatch", "nearby_checked")}
    c.location_flag = None
    if c.help_request and c.help_request.get("status") == "open":
        c.help_request = {**c.help_request, "status": "answered", "reply": "The admin corrected the location on the map."}
    sev = priority_score(c.text, c.category_final, map_places=place["nearby"])
    bd = dict(c.priority_breakdown or {})
    if not c.urgent:                                  # never lower an emergency; recompute the rest
        c.priority_level, c.priority_score = sev["level"], sev["score"]
        bd.update({**sev["breakdown"], "location_evidence": sev.get("location_evidence", [])})
        c.priority_breakdown = bd
    add_history(db, c, c.status, c.status, admin.id,
                f"Location corrected by admin (priority {old_level} to {c.priority_level}). {body.note.strip()}")
    audit(db, admin.id, "fix_location", "complaint", c.id)
    db.commit(); db.refresh(c)
    return complaint_out(c, with_history=True, viewer=admin)


@router.post("/complaints/{cid}/help-reply")
def help_reply(cid: int, body: HelpReplyIn, admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    """Answer the officer's help request. Optionally share the citizen's phone number with that officer for this complaint."""
    c = db.get(Complaint, cid)
    if not c or not c.help_request or c.help_request.get("status") != "open":
        raise HTTPException(404, "No open help request for this complaint")
    if body.share_phone and not (c.citizen and c.citizen.phone):
        raise HTTPException(409, "This citizen has not given a phone number")
    c.help_request = {**c.help_request, "status": "answered", "reply": body.message.strip(), "phone_shared": body.share_phone,
                      "answered_at": now().isoformat()}
    if c.location_flag == "help":
        c.location_flag = None
    note = "Admin answered the officer's help request" + (" and shared the citizen's phone number with the officer." if body.share_phone else ".")
    add_history(db, c, c.status, c.status, admin.id, note)
    audit(db, admin.id, "help_reply", "complaint", c.id, phone_shared=body.share_phone)      # who saw a phone number is always recorded
    db.commit(); db.refresh(c)
    return complaint_out(c, with_history=True, viewer=admin)


@router.post("/complaints/{cid}/reject")
def reject(cid: int, body: RejectIn, admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    """'Delete' a complaint that is fake, a duplicate or impossible to locate. The row is kept (status 'rejected', with the
    reason shown to the citizen) so there is a record of what happened; it leaves every work queue."""
    c = db.get(Complaint, cid)
    if not c:
        raise HTTPException(404, "Complaint not found")
    if c.status in ("closed", "rejected"):
        raise HTTPException(409, f"A {c.status} complaint cannot be rejected")
    old, c.status = c.status, "rejected"
    c.location_flag = None
    if c.help_request and c.help_request.get("status") == "open":
        c.help_request = {**c.help_request, "status": "answered", "reply": "Complaint rejected by the admin."}
    add_history(db, c, old, "rejected", admin.id, "Rejected by the admin: " + body.reason.strip())
    audit(db, admin.id, "reject", "complaint", c.id, reason=body.reason.strip())
    db.commit(); db.refresh(c)
    return complaint_out(c, with_history=True, viewer=admin)


@router.post("/complaints/{cid}/route")
def route(cid: int, body: AdminRouteIn, admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    c = db.get(Complaint, cid)
    if not c:
        raise HTTPException(404, "Complaint not found")
    if c.status != "in_review":
        raise HTTPException(409, "Only complaints in the review queue can be routed")
    cat = db.scalar(select(Category).where(Category.name == body.category))
    if not cat:
        raise HTTPException(422, f"Unknown category '{body.category}'")
    if body.officer_id is not None:
        officer = db.get(User, body.officer_id)
        if not officer or officer.role != "officer" or officer.department_id != cat.department_id:
            raise HTTPException(422, "Officer must belong to the selected category's department")
    else:
        officer = pick_officer(db, cat.department_id, c.ward)
    if officer is None:
        raise HTTPException(409, "No officer available in that department; add one first")

    # every admin decision is stored; rows where corrected != predicted are new training data
    db.add(Correction(complaint_id=c.id, text=c.text, predicted_category=c.category_pred,
                      corrected_category=cat.name, corrected_by=admin.id))
    c.category_final, c.department_id, c.assigned_officer_id = cat.name, cat.department_id, officer.id
    c.route_mode, old, c.status = "manual", c.status, "assigned"
    add_history(db, c, old, "assigned", admin.id, body.note or f"Routed by admin to {cat.department.name}")
    audit(db, admin.id, "admin_route", "complaint", c.id, predicted=c.category_pred, corrected=cat.name)
    db.commit(); db.refresh(c)
    return complaint_out(c, with_history=True)


@router.get("/departments")
def departments(db: Session = Depends(get_db)):
    return [{"id": d.id, "name": d.name} for d in db.scalars(select(Department).order_by(Department.id))]


@router.get("/categories")
def categories(db: Session = Depends(get_db)):
    return [{"id": c.id, "name": c.name, "department_id": c.department_id, "department": c.department.name}
            for c in db.scalars(select(Category).order_by(Category.id))]


@router.patch("/categories/{cat_id}")
def update_category(cat_id: int, body: CategoryUpdateIn, admin: User = Depends(require_roles("admin")),
                    db: Session = Depends(get_db)):
    cat = db.get(Category, cat_id)
    if not cat or not db.get(Department, body.department_id):
        raise HTTPException(404, "Category or department not found")
    old = cat.department_id
    cat.department_id = body.department_id
    audit(db, admin.id, "update_category_mapping", "category", cat.id, old_department=old, new_department=body.department_id)
    db.commit(); db.refresh(cat)
    return {"id": cat.id, "name": cat.name, "department_id": cat.department_id, "department": cat.department.name}


@router.get("/officers")
def officers(db: Session = Depends(get_db)):
    return [{"id": o.id, "name": o.name, "email": o.email, "department_id": o.department_id, "ward": o.ward}
            for o in db.scalars(select(User).where(User.role == "officer").order_by(User.id))]


@router.get("/analytics")
def analytics(db: Session = Depends(get_db)):
    rows = db.scalars(select(Complaint)).all()
    n = len(rows)

    def count(key):
        out = {}
        for c in rows:
            out[key(c)] = out.get(key(c), 0) + 1
        return out
    auto = sum(1 for c in rows if c.route_mode == "auto")
    corrections = db.scalars(select(Correction)).all()
    changed = sum(1 for k in corrections if k.predicted_category != k.corrected_category)
    hot = {}
    for c in rows:
        if c.lat is not None and c.lng is not None:
            k = (round(c.lat, 3), round(c.lng, 3))
            hot[k] = hot.get(k, 0) + 1
    # complaints per day for the last 14 days, counted on the INDIAN calendar day
    today = datetime.now(IST).date()
    days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    per_day = {d: 0 for d in days}
    for c in rows:
        d = c.created_at.astimezone(IST).date()
        if d in per_day:
            per_day[d] += 1
    # average time from submission to the moment an officer marked it resolved
    hours = []
    for c in rows:
        done = next((h for h in c.history if h.new_status == "resolved"), None)
        if done:
            hours.append((done.created_at - c.created_at).total_seconds() / 3600)
    closed_like = sum(1 for c in rows if c.status in ("resolved", "closed"))
    rejected = sum(1 for c in rows if c.status == "rejected")
    rated = [c.rating for c in rows if c.rating]
    return {
        "open": n - closed_like - rejected, "resolved_total": closed_like,
        "resolution_rate": round(closed_like / n, 3) if n else 0.0,
        "avg_resolution_hours": round(sum(hours) / len(hours), 1) if hours else None,
        "avg_rating": round(sum(rated) / len(rated), 2) if rated else None,
        "per_day": [{"date": d.isoformat(), "count": per_day[d]} for d in days],
        "total": n, "by_status": count(lambda c: c.status), "by_category": count(lambda c: c.category_final),
        "by_priority": count(lambda c: c.priority_level),
        "by_department": count(lambda c: c.department.name if c.department else "none"),
        "auto_routed": auto, "sent_to_review": n - auto,
        "auto_route_rate": round(auto / n, 3) if n else 0.0,
        "avg_confidence": round(sum(c.confidence for c in rows) / n, 3) if n else 0.0,
        "urgent_open": sum(1 for c in rows if c.urgent and c.status not in ("closed", "rejected")),
        "admin_decisions": len(corrections), "admin_changed_prediction": changed,
        "hotspots": [{"lat": k[0], "lng": k[1], "count": v} for k, v in sorted(hot.items(), key=lambda kv: -kv[1])[:50]],
    }
