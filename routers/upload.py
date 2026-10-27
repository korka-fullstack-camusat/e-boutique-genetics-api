import os
import uuid
from pathlib import Path

import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import List

from routers.admin_users import require_admin

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

# Stockage local (servi par Nginx sous /uploads/) quand Cloudinary n'est pas configuré.
# Par défaut dans le dossier uploads/ du dépôt, pour pouvoir le sauvegarder sur GitHub.
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", Path(__file__).resolve().parent.parent / "uploads"))
UPLOAD_URL_PREFIX = os.getenv("UPLOAD_URL_PREFIX", "/uploads/")
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 Mo
ALLOWED_TYPES = {
    "image/jpeg": ".jpeg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

router = APIRouter()


def _cloudinary_configured() -> bool:
    return all([
        os.getenv("CLOUDINARY_CLOUD_NAME"),
        os.getenv("CLOUDINARY_API_KEY"),
        os.getenv("CLOUDINARY_API_SECRET"),
    ])


@router.post("/", dependencies=[Depends(require_admin)])
async def upload_images(files: List[UploadFile] = File(...)):
    """Upload images to Cloudinary (si configuré) ou sur le disque du serveur, et retourne leurs URLs"""
    use_cloudinary = _cloudinary_configured()
    if not use_cloudinary:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    urls = []
    for file in files:
        ext = ALLOWED_TYPES.get(file.content_type or "")
        if not ext:
            raise HTTPException(status_code=400, detail=f"Format d'image non supporté : {file.filename}")
        content = await file.read()
        if len(content) > MAX_IMAGE_SIZE:
            raise HTTPException(status_code=400, detail=f"Image trop volumineuse (max 10 Mo) : {file.filename}")

        if use_cloudinary:
            result = cloudinary.uploader.upload(
                content,
                folder="genetics/products",
                resource_type="image",
            )
            urls.append(result["secure_url"])
        else:
            filename = f"{uuid.uuid4().hex}{ext}"
            (UPLOAD_DIR / filename).write_bytes(content)
            urls.append(UPLOAD_URL_PREFIX + filename)
    return {"images": urls}
