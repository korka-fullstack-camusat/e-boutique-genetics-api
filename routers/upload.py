import os
import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

router = APIRouter()


@router.post("/")
async def upload_images(files: List[UploadFile] = File(...)):
    """Upload images to Cloudinary and return secure URLs"""
    if not all([
        os.getenv("CLOUDINARY_CLOUD_NAME"),
        os.getenv("CLOUDINARY_API_KEY"),
        os.getenv("CLOUDINARY_API_SECRET"),
    ]):
        raise HTTPException(status_code=500, detail="Cloudinary non configuré")

    urls = []
    for file in files:
        content = await file.read()
        result = cloudinary.uploader.upload(
            content,
            folder="genetics/products",
            resource_type="image",
        )
        urls.append(result["secure_url"])
    return {"images": urls}
