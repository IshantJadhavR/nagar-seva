import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # project root
try:                                                # optional: read settings from a .env file in the project root
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass
MODEL_DIR = Path(os.getenv("MODEL_DIR", ROOT / "ml" / "models"))
# Default = SQLite file (zero setup). For PostgreSQL set e.g.
#   DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/complaints
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'backend' / 'complaints.db'}")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")   # set a real one in .env for deployment
TOKEN_MINUTES = int(os.getenv("TOKEN_MINUTES", "480"))
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", ROOT / "backend" / "uploads"))
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
