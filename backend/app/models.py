from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base, UTCDateTime


def now():
    return datetime.now(timezone.utc)


class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)


class Category(Base):
    """Category -> department mapping. Editable by admin (no model retraining needed)."""
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    department: Mapped[Department] = relationship()


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20))            # citizen | officer | admin
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"), nullable=True)
    ward: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)   # citizens only, optional
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)
    department: Mapped[Optional[Department]] = relationship()


class Complaint(Base):
    __tablename__ = "complaints"
    id: Mapped[int] = mapped_column(primary_key=True)
    citizen_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(20))
    category_pred: Mapped[str] = mapped_column(String(60))
    confidence: Mapped[float] = mapped_column(Float)
    probs: Mapped[dict] = mapped_column(JSON)
    category_final: Mapped[str] = mapped_column(String(60))
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"), nullable=True)
    secondary_category: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    priority_level: Mapped[str] = mapped_column(String(20))
    priority_score: Mapped[int] = mapped_column(Integer)
    priority_breakdown: Mapped[dict] = mapped_column(JSON)
    urgent: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), index=True)   # in_review|assigned|in_progress|resolved|reopened|closed|rejected
    route_mode: Mapped[str] = mapped_column(String(20))           # auto | review | manual
    route_reason: Mapped[str] = mapped_column(Text, default="")
    assigned_officer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lng: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    ward: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    image_path: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    geo_address: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)    # address looked up from the pin
    geo_check: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)           # what the map and photo told us
    location_flag: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # check_address | photo_far | wrong | help
    help_request: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)        # officer asks admin for help (see routers/officer.py)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now, onupdate=now)
    department: Mapped[Optional[Department]] = relationship()
    citizen: Mapped[Optional[User]] = relationship(foreign_keys=[citizen_id])
    officer: Mapped[Optional[User]] = relationship(foreign_keys=[assigned_officer_id])
    history: Mapped[list["StatusHistory"]] = relationship(back_populates="complaint", order_by="StatusHistory.id")


class StatusHistory(Base):
    __tablename__ = "status_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), index=True)
    old_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str] = mapped_column(String(20))
    changed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")
    proof_image_path: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)
    complaint: Mapped[Complaint] = relationship(back_populates="history")


class GeoCache(Base):
    """Cached answers from the free OpenStreetMap services, so we call them as little as possible."""
    __tablename__ = "geo_cache"
    key: Mapped[str] = mapped_column(String(300), primary_key=True)
    kind: Mapped[str] = mapped_column(String(20))
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)


class Correction(Base):
    """Every admin routing decision. Rows where corrected != predicted are new training data."""
    __tablename__ = "corrections"
    id: Mapped[int] = mapped_column(primary_key=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    predicted_category: Mapped[str] = mapped_column(String(60))
    corrected_category: Mapped[str] = mapped_column(String(60))
    corrected_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(60))
    entity: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=now)
