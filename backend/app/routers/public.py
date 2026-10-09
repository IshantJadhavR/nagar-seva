"""Public numbers for the landing page. No personal data, no login."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Complaint

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count(Complaint.id))) or 0
    done = db.scalar(select(func.count(Complaint.id)).where(Complaint.status.in_(("resolved", "closed")))) or 0
    auto = db.scalar(select(func.count(Complaint.id)).where(Complaint.route_mode == "auto")) or 0
    return {"total": total, "resolved": done, "auto_routed": auto}
