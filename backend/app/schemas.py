import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clean_phone(v):
    """Indian mobile number: 10 digits starting 6-9 (an optional +91 / 0 prefix and spaces are accepted). Stored as 10 digits."""
    if v is None or not str(v).strip():
        return None
    d = re.sub(r"[\s\-()]", "", str(v))
    d = re.sub(r"^(\+?91|0)", "", d) if len(d) > 10 else d
    if not re.fullmatch(r"[6-9]\d{9}", d):
        raise ValueError("Enter a valid 10-digit mobile number")
    return d


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str
    password: str = Field(min_length=8, max_length=64)
    phone: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def _phone(cls, v):
        return clean_phone(v)

    @field_validator("email")
    @classmethod
    def _email(cls, v):
        v = v.strip().lower()
        if not _EMAIL.match(v):
            raise ValueError("Invalid email address")
        return v


class LoginIn(BaseModel):
    email: str
    password: str
    role: Optional[str] = None          # the role tab chosen on the login page (optional); a mismatch is reported clearly


class PasswordChangeIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=64)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str


class PredictIn(BaseModel):
    text: str = Field(min_length=3, max_length=2000)


class ComplaintIn(BaseModel):
    text: str = Field(min_length=10, max_length=2000)
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lng: Optional[float] = Field(default=None, ge=-180, le=180)
    address: Optional[str] = Field(default=None, max_length=300)
    ward: Optional[str] = Field(default=None, max_length=40)
    near_school: bool = False
    near_hospital: bool = False
    on_main_road: bool = False


    @model_validator(mode="after")
    def _pin(self):
        from .services.geo import in_maharashtra
        if (self.lat is None) != (self.lng is None):
            raise ValueError("Send both latitude and longitude, or neither")
        if self.lat is not None and not in_maharashtra(self.lat, self.lng):
            raise ValueError("The pin is outside Maharashtra. Please move it onto the map of your area")
        return self


class GeoCheckIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    address: Optional[str] = Field(default=None, max_length=300)


class WrongLocationIn(BaseModel):
    note: str = Field(default="", max_length=500)


class FixLocationIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    address: Optional[str] = Field(default=None, max_length=300)
    note: str = Field(default="", max_length=500)


class StatusUpdateIn(BaseModel):
    status: str
    note: str = Field(default="", max_length=1000)


class ConfirmIn(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    feedback: Optional[str] = Field(default=None, max_length=1000)


class ReopenIn(BaseModel):
    note: str = Field(min_length=3, max_length=1000)


class AdminRouteIn(BaseModel):
    category: str
    officer_id: Optional[int] = None
    note: str = Field(default="", max_length=1000)


class CategoryUpdateIn(BaseModel):
    department_id: int


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    old_status: Optional[str]
    new_status: str
    note: str
    proof_image_path: Optional[str]
    created_at: datetime


class PhoneIn(BaseModel):
    phone: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def _phone(cls, v):
        return clean_phone(v)


class HelpRequestIn(BaseModel):
    reason: str = Field(min_length=5, max_length=500)


class HelpReplyIn(BaseModel):
    message: str = Field(default="", max_length=500)
    share_phone: bool = False


class RejectIn(BaseModel):
    reason: str = Field(min_length=5, max_length=500)
