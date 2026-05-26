import base64
from fastapi import APIRouter, UploadFile, File
from typing import List

router = APIRouter()


@router.post("/")
async def upload_images(files: List[UploadFile] = File(...)):
    """Upload images and return base64 encoded strings"""
    results = []
    for file in files:
        content = await file.read()
        b64 = base64.b64encode(content).decode("utf-8")
        mime = file.content_type or "image/jpeg"
        results.append(f"data:{mime};base64,{b64}")
    return {"images": results}
