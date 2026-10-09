"""Routing logic: category -> department -> officer, with confidence-aware human fallback."""
import json
from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .. import config
from ..models import Category, Complaint, User

OPEN_STATUSES = ("assigned", "in_progress", "reopened")


@dataclass
class RoutingConfig:
    threshold: float = 0.64
    margin: float = 0.10
    secondary_min: float = 0.25


def load_routing_config() -> RoutingConfig:
    p = config.MODEL_DIR / "routing_config.json"
    if p.exists():
        d = json.loads(p.read_text())
        return RoutingConfig(d.get("threshold", 0.64), d.get("margin", 0.10), d.get("secondary_min", 0.25))
    return RoutingConfig()


def route_decision(probs: dict, cfg: RoutingConfig) -> dict:
    """Pure function: decides auto-route vs human review from class probabilities."""
    ordered = sorted(probs.items(), key=lambda kv: -kv[1])
    (c1, p1), (c2, p2) = ordered[0], ordered[1]
    reasons = []
    if c1 == "Other":
        reasons.append("Predicted 'Other' needs human triage")
    if p1 < cfg.threshold:
        reasons.append(f"Confidence {p1:.2f} is below the threshold {cfg.threshold:.2f}")
    if p1 - p2 < cfg.margin:
        reasons.append(f"Top two categories are too close ({c1} {p1:.2f} vs {c2} {p2:.2f})")
    secondary = c2 if (p2 >= cfg.secondary_min and c2 != "Other") else None
    return {"category": c1, "confidence": p1, "mode": "review" if reasons else "auto",
            "reasons": reasons, "secondary": secondary}


def department_for(db: Session, category_name: str):
    cat = db.scalar(select(Category).where(Category.name == category_name))
    return cat.department_id if cat else None


def pick_officer(db: Session, department_id, ward=None):
    """Officer of that department (preferring the same ward) with the fewest open complaints."""
    if department_id is None:
        return None
    officers = db.scalars(select(User).where(User.role == "officer", User.department_id == department_id)).all()
    if not officers:
        return None
    if ward:
        same = [o for o in officers if o.ward == ward]
        officers = same or officers
    load = dict(db.execute(
        select(Complaint.assigned_officer_id, func.count()).where(
            Complaint.assigned_officer_id.in_([o.id for o in officers]),
            Complaint.status.in_(OPEN_STATUSES)).group_by(Complaint.assigned_officer_id)).all())
    return min(officers, key=lambda o: (load.get(o.id, 0), o.id))


def haversine_m(lat1, lng1, lat2, lng2) -> float:
    a = sin(radians(lat2 - lat1) / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(radians(lng2 - lng1) / 2) ** 2
    return 2 * 6371000 * asin(sqrt(a))


def count_similar_nearby(db: Session, category: str, lat, lng, radius_m=300) -> int:
    """Open complaints of the same category within radius_m (cheap repeat-report signal)."""
    if lat is None or lng is None:
        return 0
    rows = db.execute(select(Complaint.lat, Complaint.lng).where(
        Complaint.category_final == category, Complaint.lat.is_not(None),
        Complaint.status.notin_(("closed",)))).all()
    return sum(1 for la, ln in rows if haversine_m(lat, lng, la, ln) <= radius_m)
