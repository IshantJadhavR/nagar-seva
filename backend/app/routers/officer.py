from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..auth import require_roles
from ..database import get_db
from ..models import Complaint, User
from ..schemas import HelpRequestIn, StatusUpdateIn, WrongLocationIn
from ..models import now
from ..services.common import add_history, audit, complaint_out

router = APIRouter(prefix="/officer", tags=["officer"])
ALLOWED = {"assigned": {"in_progress"}, "reopened": {"in_progress"}, "in_progress": {"resolved"}}
PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


@router.get("/complaints")
def my_assigned(status: str | None = None, user: User = Depends(require_roles("officer")), db: Session = Depends(get_db)):
    q = select(Complaint).where(Complaint.assigned_officer_id == user.id)
    if status:
        q = q.where(Complaint.status == status)
    rows = db.scalars(q).all()
    rows.sort(key=lambda c: (PRIORITY_RANK[c.priority_level], c.created_at))
    return [complaint_out(c) for c in rows]


@router.patch("/complaints/{cid}/status")
def update_status(cid: int, body: StatusUpdateIn, user: User = Depends(require_roles("officer")),
                  db: Session = Depends(get_db)):
    c = db.get(Complaint, cid)
    if not c or c.assigned_officer_id != user.id:
        raise HTTPException(404, "Complaint not found")
    if body.status not in ALLOWED.get(c.status, set()):
        raise HTTPException(409, f"Cannot move from '{c.status}' to '{body.status}'")
    if body.status == "resolved" and not body.note.strip():
        raise HTTPException(422, "Please add a note describing what was done")
    old, c.status = c.status, body.status
    add_history(db, c, old, c.status, user.id, body.note)
    audit(db, user.id, "status_update", "complaint", c.id, old=old, new=c.status)
    db.commit(); db.refresh(c)
    return complaint_out(c, with_history=True, viewer=user)


@router.post("/complaints/{cid}/wrong-location")
def wrong_location(cid: int, body: WrongLocationIn, user: User = Depends(require_roles("officer")),
                   db: Session = Depends(get_db)):
    """The officer went there and the problem is not at the pin. The admin sees it and corrects the location."""
    c = db.get(Complaint, cid)
    if not c or c.assigned_officer_id != user.id:
        raise HTTPException(404, "Complaint not found")
    c.location_flag = "wrong"
    add_history(db, c, c.status, c.status, user.id, "Location reported as wrong by the officer. " + body.note.strip())
    audit(db, user.id, "wrong_location", "complaint", c.id)
    db.commit(); db.refresh(c)
    return complaint_out(c, with_history=True, viewer=user)


@router.post("/complaints/{cid}/help")
def ask_for_help(cid: int, body: HelpRequestIn, user: User = Depends(require_roles("officer")), db: Session = Depends(get_db)):
    """The officer cannot find the place (or the pin is wrong) and asks the admin for help, for example for the
    citizen's phone number. The officer never sees the number unless the admin chooses to share it."""
    c = db.get(Complaint, cid)
    if not c or c.assigned_officer_id != user.id:
        raise HTTPException(404, "Complaint not found")
    if c.status not in ("assigned", "in_progress", "reopened"):
        raise HTTPException(409, "Help can only be requested for an open complaint")
    if c.help_request and c.help_request.get("status") == "open":
        raise HTTPException(409, "A help request is already waiting for the admin")
    c.help_request = {"status": "open", "reason": body.reason.strip(), "by": user.name, "at": now().isoformat(),
                      "reply": "", "phone_shared": False}
    if c.location_flag in (None, "check_address", "photo_far"):
        c.location_flag = "help"
    add_history(db, c, c.status, c.status, user.id, "Officer asked the admin for help finding the location. " + body.reason.strip())
    audit(db, user.id, "ask_help", "complaint", c.id)
    db.commit(); db.refresh(c)
    return complaint_out(c, with_history=True, viewer=user)
