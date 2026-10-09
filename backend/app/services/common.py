from sqlalchemy.orm import Session
from ..models import AuditLog, Complaint, StatusHistory


def audit(db: Session, user_id, action: str, entity: str, entity_id=None, **details):
    db.add(AuditLog(user_id=user_id, action=action, entity=entity, entity_id=entity_id, details=details))


def add_history(db: Session, c: Complaint, old, new, user_id, note="", proof=None):
    db.add(StatusHistory(complaint_id=c.id, old_status=old, new_status=new, changed_by=user_id,
                         note=note, proof_image_path=proof))


OPEN_FOR_PHONE = ("assigned", "in_progress", "reopened", "in_review")


def complaint_out(c: Complaint, with_history=False, viewer=None) -> dict:
    """viewer = the logged-in user. Staff see the help request; the citizen's phone number is shown ONLY to the admin,
    or to the assigned officer after the admin chose to share it (and only while the complaint is still open)."""
    d = {
        "id": c.id, "text": c.text, "language": c.language,
        "category_pred": c.category_pred, "confidence": round(c.confidence, 3),
        "category": c.category_final, "secondary_category": c.secondary_category,
        "department": c.department.name if c.department else None,
        "priority_level": c.priority_level, "priority_score": c.priority_score,
        "priority_breakdown": c.priority_breakdown, "urgent": c.urgent,
        "status": c.status, "route_mode": c.route_mode, "route_reason": c.route_reason,
        "assigned_officer": c.officer.name if c.officer else None,
        "lat": c.lat, "lng": c.lng, "address": c.address, "ward": c.ward,
        "image_path": c.image_path, "geo_address": c.geo_address, "geo_check": c.geo_check,
        "location_flag": c.location_flag, "rating": c.rating, "feedback": c.feedback,
        "created_at": c.created_at.isoformat(), "updated_at": c.updated_at.isoformat(),
    }
    if viewer is not None and viewer.role in ("admin", "officer"):
        hr = c.help_request
        d["help_request"] = hr
        phone = c.citizen.phone if getattr(c, "citizen", None) else None
        if viewer.role == "admin" and hr:
            d["citizen_phone"] = phone
        elif viewer.role == "officer" and hr and hr.get("phone_shared") and c.status in OPEN_FOR_PHONE and c.assigned_officer_id == viewer.id:
            d["citizen_phone"] = phone
    if with_history:
        d["history"] = [{"old_status": h.old_status, "new_status": h.new_status, "note": h.note,
                         "proof_image_path": h.proof_image_path, "created_at": h.created_at.isoformat()}
                        for h in c.history]
    return d
