from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from . import config
from .routers import admin, auth_router, complaints, geo_router, officer, public
from .seed import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed()          # creates tables and demo data on first run (idempotent)
    yield


config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app = FastAPI(title="Multilingual Civic Complaint Triage", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router.router)
app.include_router(complaints.router)
app.include_router(officer.router)
app.include_router(admin.router)
app.include_router(public.router)
app.include_router(geo_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")


# Photos are served by their random (uuid) file name. Fine for a demo;
# for production use an authenticated endpoint or signed URLs.
app.mount("/uploads", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")
