import os
import tempfile
from pathlib import Path

# Must be set BEFORE the app is imported
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmp) / 'test.db'}"
os.environ["UPLOAD_DIR"] = str(Path(_tmp) / "uploads")

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.routers.complaints import classifier_dep


class StubClassifier:
    """Keyword-based fake model so API tests do not need the trained model."""
    def predict(self, text):
        t = text.lower()
        p = {k: 0.01 for k in ["Roads", "Garbage", "Water Supply", "Drainage", "Streetlight", "Public Health", "Encroachment", "Other"]}
        if "pothole" in t or "road" in t:
            p["Roads"] = 0.90
        elif "garbage" in t:
            p["Garbage"] = 0.90
        elif "pipe" in t or "water" in t:
            p["Water Supply"] = 0.50; p["Drainage"] = 0.45          # ambiguous -> review
        else:
            p["Other"] = 0.90
        s = sum(p.values())
        return {k: v / s for k, v in p.items()}


@pytest.fixture(scope="session")
def client():
    app.dependency_overrides[classifier_dep] = lambda: StubClassifier()
    with TestClient(app) as c:          # runs lifespan -> seeds demo data
        yield c


def login(client, email, password):
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def citizen(client):
    return login(client, "citizen@example.com", "Citizen@123")


@pytest.fixture(scope="session")
def admin(client):
    return login(client, "admin@example.com", "Admin@123")
