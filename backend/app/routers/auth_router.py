from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..auth import create_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..models import User
from ..schemas import LoginIn, PasswordChangeIn, PhoneIn, RegisterIn, TokenOut
from ..services.common import audit

router = APIRouter(prefix="/auth", tags=["auth"])


def _login(db: Session, email: str, password: str, role: str = None) -> TokenOut:
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(401, "Wrong email or password")
    if role and role != user.role:
        raise HTTPException(403, f"This is a {user.role} account. Please choose \"{user.role.capitalize()}\" on the login page.")
    return TokenOut(access_token=create_token(user), role=user.role, name=user.name)


@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(409, "Email already registered")
    user = User(name=body.name.strip(), email=body.email, password_hash=hash_password(body.password), role="citizen", phone=body.phone)
    db.add(user); db.flush()
    audit(db, user.id, "register", "user", user.id)
    db.commit()
    return TokenOut(access_token=create_token(user), role=user.role, name=user.name)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    return _login(db, body.email, body.password, body.role)


@router.post("/token", response_model=TokenOut, include_in_schema=True)
def token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Form login used by the Swagger 'Authorize' button (username = email)."""
    return _login(db, form.username, form.password)


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role,
            "department_id": user.department_id, "department": user.department.name if user.department else None,
            "ward": user.ward, "phone": user.phone, "created_at": user.created_at.isoformat()}


@router.post("/password")
def change_password(body: PasswordChangeIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(400, "Current password is wrong")
    user.password_hash = hash_password(body.new_password)
    audit(db, user.id, "change_password", "user", user.id)
    db.commit()
    return {"ok": True}


@router.put("/phone")
def set_phone(body: PhoneIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Citizens may save (or remove) a mobile number. It is shown to an officer only if the admin shares it for one complaint."""
    if user.role != "citizen":
        raise HTTPException(403, "Only citizens can save a phone number")
    user.phone = body.phone
    audit(db, user.id, "set_phone", "user", user.id)
    db.commit()
    return {"phone": user.phone}
