"""Pin and photo checks used by the complaint form BEFORE the citizen submits."""
import io
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from .. import config
from ..auth import require_roles
from ..database import get_db
from ..models import User
from ..schemas import GeoCheckIn
from ..services import geo

router = APIRouter(prefix="/geo", tags=["geo"])


@router.post("/check")
def check(body: GeoCheckIn, user: User = Depends(require_roles("citizen")), db: Session = Depends(get_db)):
    """What is at this pin? Address, nearby school/hospital/main road, and whether the typed address agrees."""
    res = geo.analyse(db, body.lat, body.lng, body.address)
    res["points_from_map"] = geo.map_points(res["nearby"])
    res["evidence"] = geo.evidence(res["nearby"])
    return res


@router.post("/photo-gps")
async def photo_gps(file: UploadFile = File(...), user: User = Depends(require_roles("citizen")), db: Session = Depends(get_db)):
    """Reads the GPS position stored inside a photo (if any) and turns it into an address. Nothing is saved."""
    if file.content_type not in config.ALLOWED_IMAGE_TYPES:
        raise HTTPException(415, "Only JPEG, PNG or WebP images are allowed")
    data = await file.read(config.MAX_UPLOAD_BYTES + 1)
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Image too large (max 5 MB)")
    gps = geo.photo_gps(io.BytesIO(data))
    if not gps:
        return {"has_gps": False}
    return {"has_gps": True, "lat": round(gps[0], 6), "lng": round(gps[1], 6),
            "inside_area": geo.in_maharashtra(*gps), "address": geo.reverse_geocode(db, *gps) if geo.in_maharashtra(*gps) else None}
