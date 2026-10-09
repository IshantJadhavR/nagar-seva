import io
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from .. import config
from ..auth import get_current_user, require_roles
from ..database import get_db
from ..models import Complaint, User
from ..schemas import ComplaintIn, ConfirmIn, PredictIn, ReopenIn
from ..services import geo
from ..services.classifier import detect_language, get_classifier
from ..services.common import add_history, audit, complaint_out
from ..services.routing import (count_similar_nearby, department_for, load_routing_config, pick_officer, route_decision)
from ..services.severity import priority_score

router = APIRouter(tags=["complaints"])


def classifier_dep():
    try:
        return get_classifier()
    except RuntimeError as e:
        raise HTTPException(503, str(e))


def _breakdown(sev: dict) -> dict:
    """Points per factor (numbers) plus the evidence (words found, days, rule note) under separate keys."""
    return {**sev["breakdown"], "danger_words_found": sev["danger_words"], "duration_days": sev["duration_days"],
            "critical_reason": sev["critical_reason"], "policy_note": sev.get("policy_note"),
            "location_evidence": sev.get("location_evidence", [])}


@router.post("/predict")
def predict(body: PredictIn, clf=Depends(classifier_dep), db: Session = Depends(get_db)):
    """Public demo endpoint: category + confidence + department + priority, nothing is stored."""
    probs = clf.predict(body.text)
    dec = route_decision(probs, load_routing_config())
    sev = priority_score(body.text, dec["category"])
    dept_id = department_for(db, dec["category"])
    from ..models import Department
    dept = db.get(Department, dept_id) if dept_id else None
    top3 = sorted(probs.items(), key=lambda kv: -kv[1])[:3]
    return {"language": detect_language(body.text), "category": dec["category"],
            "confidence": round(dec["confidence"], 3), "top3": [(k, round(v, 3)) for k, v in top3],
            "department": dept.name if dept else None, "would_auto_route": dec["mode"] == "auto" and not sev["critical"],
            "review_reasons": dec["reasons"], "secondary_category": dec["secondary"],
            "priority_level": sev["level"], "priority_score": sev["score"], "priority_breakdown": _breakdown(sev),
            "critical_reason": sev["critical_reason"]}


@router.post("/complaints", status_code=201)
def create_complaint(body: ComplaintIn, user: User = Depends(require_roles("citizen")),
                     clf=Depends(classifier_dep), db: Session = Depends(get_db)):
    text = body.text.strip()
    probs = clf.predict(text)
    dec = route_decision(probs, load_routing_config())
    category = dec["category"]

    similar = count_similar_nearby(db, category, body.lat, body.lng)
    # the server asks the map itself; we never trust the browser's claim about what is near the pin
    place = geo.analyse(db, body.lat, body.lng, body.address)
    sev = priority_score(text, category, body.near_school, body.near_hospital, body.on_main_road,
                         similar_nearby=similar, map_places=place["nearby"])

    mode, reasons = dec["mode"], list(dec["reasons"])
    urgent = sev["critical"]
    if urgent:                       # safety emergencies always go to a human, regardless of confidence
        mode = "review"
        reasons.append(f"CRITICAL: {sev['critical_reason']}")
    dept_id = department_for(db, category)
    officer = None
    if mode == "auto":
        officer = pick_officer(db, dept_id, body.ward)
        if officer is None:
            mode = "review"
            reasons.append("No officer available in this department")

    c = Complaint(
        citizen_id=user.id, text=text, language=detect_language(text),
        category_pred=category, confidence=dec["confidence"], probs=probs, category_final=category,
        department_id=dept_id, secondary_category=dec["secondary"],
        priority_level=sev["level"], priority_score=sev["score"],
        priority_breakdown=_breakdown(sev),
        urgent=urgent, status="assigned" if mode == "auto" else "in_review", route_mode=mode,
        route_reason="; ".join(reasons), assigned_officer_id=officer.id if officer else None,
        lat=body.lat, lng=body.lng, address=body.address, ward=body.ward,
        geo_address=place["geo_address"],
        geo_check={k: place[k] for k in ("nearby", "address_distance_m", "address_mismatch", "nearby_checked")},
        location_flag="check_address" if place["address_mismatch"] else None)
    db.add(c); db.flush()
    add_history(db, c, None, c.status, user.id, "Complaint submitted")
    audit(db, user.id, "create_complaint", "complaint", c.id, mode=mode, category=category,
          confidence=round(dec["confidence"], 3), priority=sev["level"])
    db.commit(); db.refresh(c)
    return complaint_out(c, with_history=True)


@router.get("/complaints/mine")
def my_complaints(user: User = Depends(require_roles("citizen")), db: Session = Depends(get_db)):
    rows = db.scalars(select(Complaint).where(Complaint.citizen_id == user.id).order_by(Complaint.id.desc())).all()
    return [complaint_out(c) for c in rows]


def _can_view(user: User, c: Complaint) -> bool:
    if user.role == "admin":
        return True
    if user.role == "citizen":
        return c.citizen_id == user.id
    return c.assigned_officer_id == user.id or (user.department_id and c.department_id == user.department_id)


@router.get("/complaints/{cid}")
def get_complaint(cid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.get(Complaint, cid)
    if not c or not _can_view(user, c):
        raise HTTPException(404, "Complaint not found")      # same message: do not reveal existence
    return complaint_out(c, with_history=True, viewer=user)


@router.post("/complaints/{cid}/image")
async def upload_image(cid: int, file: UploadFile = File(...), user: User = Depends(require_roles("citizen")),
                       db: Session = Depends(get_db)):
    c = db.get(Complaint, cid)
    if not c or c.citizen_id != user.id:
        raise HTTPException(404, "Complaint not found")
    ext = config.ALLOWED_IMAGE_TYPES.get(file.content_type)
    if not ext:
        raise HTTPException(415, "Only JPEG, PNG or WebP images are allowed")
    data = await file.read(config.MAX_UPLOAD_BYTES + 1)
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Image too large (max 5 MB)")
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"                          # never trust the client's file name
    (config.UPLOAD_DIR / name).write_bytes(data)
    c.image_path = name
    # does the photo's own GPS (EXIF) agree with the pin?  Many photos carry none; then we simply say nothing.
    gps = geo.photo_gps(io.BytesIO(data))
    if gps:
        check = dict(c.geo_check or {})
        check["photo_gps"] = {"lat": round(gps[0], 6), "lng": round(gps[1], 6)}
        if c.lat is not None:
            dist = round(geo.haversine_m(c.lat, c.lng, gps[0], gps[1]))
            check["photo_distance_m"] = dist
            if dist > geo.PHOTO_MISMATCH_M and c.location_flag in (None, "check_address"):
                c.location_flag = "photo_far"
        c.geo_check = check
    audit(db, user.id, "upload_image", "complaint", c.id)
    db.commit()
    return {"image_path": name, "photo_gps": (c.geo_check or {}).get("photo_gps"), "photo_distance_m": (c.geo_check or {}).get("photo_distance_m")}


@router.post("/complaints/{cid}/confirm")
def confirm(cid: int, body: ConfirmIn, user: User = Depends(require_roles("citizen")), db: Session = Depends(get_db)):
    c = db.get(Complaint, cid)
    if not c or c.citizen_id != user.id:
        raise HTTPException(404, "Complaint not found")
    if c.status != "resolved":
        raise HTTPException(409, "Only resolved complaints can be confirmed")
    old, c.status = c.status, "closed"
    c.rating, c.feedback = body.rating, body.feedback
    add_history(db, c, old, "closed", user.id, "Citizen confirmed the resolution")
    audit(db, user.id, "confirm", "complaint", c.id)
    db.commit(); db.refresh(c)
    return complaint_out(c, with_history=True)


@router.post("/complaints/{cid}/reopen")
def reopen(cid: int, body: ReopenIn, user: User = Depends(require_roles("citizen")), db: Session = Depends(get_db)):
    c = db.get(Complaint, cid)
    if not c or c.citizen_id != user.id:
        raise HTTPException(404, "Complaint not found")
    if c.status != "resolved":
        raise HTTPException(409, "Only resolved complaints can be reopened")
    old, c.status = c.status, "reopened"
    add_history(db, c, old, "reopened", user.id, body.note)
    audit(db, user.id, "reopen", "complaint", c.id)
    db.commit(); db.refresh(c)
    return complaint_out(c, with_history=True)
