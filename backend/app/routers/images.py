from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product_image import ProductImage

router = APIRouter(prefix="/images", tags=["images"])


@router.put("/{image_id}/accept")
async def accept_image(image_id: int, db: AsyncSession = Depends(get_db)):
    img = await db.get(ProductImage, image_id)
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    img.status = "accepted"
    img.curated_at = datetime.utcnow()
    await db.commit()
    return {"ok": True, "status": "accepted"}


@router.put("/{image_id}/reject")
async def reject_image(image_id: int, db: AsyncSession = Depends(get_db)):
    img = await db.get(ProductImage, image_id)
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    img.status = "rejected"
    img.curated_at = datetime.utcnow()
    await db.commit()
    return {"ok": True, "status": "rejected"}


@router.delete("/{image_id}")
async def delete_image(image_id: int, db: AsyncSession = Depends(get_db)):
    img = await db.get(ProductImage, image_id)
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    # Delete files from disk
    if img.local_path:
        Path(img.local_path).unlink(missing_ok=True)
    if img.thumbnail_path:
        Path(img.thumbnail_path).unlink(missing_ok=True)
    await db.delete(img)
    await db.commit()
    return {"ok": True}


@router.get("/{image_id}/file")
async def serve_image(image_id: int, db: AsyncSession = Depends(get_db)):
    img = await db.get(ProductImage, image_id)
    if not img or not img.local_path:
        raise HTTPException(status_code=404, detail="Image not found")
    path = Path(img.local_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image file not found on disk")
    return FileResponse(str(path))


@router.get("/{image_id}/thumbnail")
async def serve_thumbnail(image_id: int, db: AsyncSession = Depends(get_db)):
    img = await db.get(ProductImage, image_id)
    if not img or not img.thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    path = Path(img.thumbnail_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail file not found on disk")
    return FileResponse(str(path))
