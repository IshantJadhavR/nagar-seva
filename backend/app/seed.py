"""Creates departments, the category->department table, and DEMO users (demo passwords only!).
Idempotent. Run:  python -m backend.app.seed"""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .auth import hash_password
from .database import Base, SessionLocal, engine, ensure_columns
from .models import Category, Department, User

CATEGORY_DEPARTMENT = {
    "Roads": "Public Works Department", "Garbage": "Solid Waste Management",
    "Water Supply": "Water Supply Department", "Drainage": "Drainage and Sewerage",
    "Streetlight": "Electrical Department", "Public Health": "Health Department",
    "Encroachment": "Building Permission and Encroachment", "Other": "Admin Review",
}
DEMO_PASSWORDS = {"admin": "Admin@123", "officer": "Officer@123", "citizen": "Citizen@123"}


def _get_or_create(db, model, key_col, key, **fields):
    """Return the row whose key_col == key, creating it if missing. Makes seeding safe to repeat and safe if a
    previous start-up was interrupted half way (PostgreSQL keeps what was committed)."""
    row = db.scalar(select(model).where(getattr(model, key_col) == key))
    created = row is None
    if created:
        row = model(**{key_col: key}, **fields)
        db.add(row); db.flush()
    return row, created


def seed(db=None):
    """Creates tables, departments, categories and demo users. Idempotent: every row is checked individually."""
    own = db is None
    db = db or SessionLocal()
    try:
        Base.metadata.create_all(engine)
        ensure_columns()
        added = False
        depts = {}
        for name in dict.fromkeys(CATEGORY_DEPARTMENT.values()):
            depts[name], c = _get_or_create(db, Department, "name", name); added |= c
        for cat, dep in CATEGORY_DEPARTMENT.items():
            _, c = _get_or_create(db, Category, "name", cat, department_id=depts[dep].id); added |= c
        _, c = _get_or_create(db, User, "email", "admin@example.com", name="Admin", role="admin",
                              password_hash=hash_password(DEMO_PASSWORDS["admin"])); added |= c
        _, c = _get_or_create(db, User, "email", "citizen@example.com", name="Demo Citizen", role="citizen",
                              password_hash=hash_password(DEMO_PASSWORDS["citizen"])); added |= c
        for dep, d in depts.items():
            if dep == "Admin Review":
                continue
            slug = dep.split()[0].lower()
            for i, ward in enumerate(("Ward-1", "Ward-2"), start=1):
                _, c = _get_or_create(db, User, "email", f"{slug}.officer{i}@example.com", name=f"{dep} Officer {i}", role="officer",
                                      department_id=d.id, ward=ward, password_hash=hash_password(DEMO_PASSWORDS["officer"]))
                added |= c
        db.commit()
        return added
    except IntegrityError:
        db.rollback()                 # another process seeded at the same moment; that is fine
        return False
    finally:
        if own:
            db.close()


if __name__ == "__main__":
    print("Seeded." if seed() else "Already seeded.")
