from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.image_batch import ImageBatch
from app.services.batch_runner import start_batch, cancel_batch, get_current_batch_id

router = APIRouter(prefix="/batches", tags=["batches"])


@router.post("/start")
async def start_new_batch():
    """Start a new image scraping batch."""
    try:
        batch_id = await start_batch()
        return {"batch_id": batch_id}
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("")
async def list_batches(db: AsyncSession = Depends(get_db)):
    """List all batch runs, newest first."""
    result = await db.execute(
        select(ImageBatch).order_by(ImageBatch.started_at.desc())
    )
    batches = result.scalars().all()
    return [
        {
            "id": b.id,
            "started_at": b.started_at.isoformat() if b.started_at else None,
            "completed_at": b.completed_at.isoformat() if b.completed_at else None,
            "status": b.status,
            "total_products": b.total_products,
            "processed": b.processed,
            "images_found": b.images_found,
            "error_count": b.error_count,
        }
        for b in batches
    ]


@router.get("/{batch_id}")
async def get_batch(batch_id: int, db: AsyncSession = Depends(get_db)):
    """Get single batch with progress."""
    batch = await db.get(ImageBatch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return {
        "id": batch.id,
        "started_at": batch.started_at.isoformat() if batch.started_at else None,
        "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
        "status": batch.status,
        "total_products": batch.total_products,
        "processed": batch.processed,
        "images_found": batch.images_found,
        "error_count": batch.error_count,
        "is_running": get_current_batch_id() == batch_id,
    }


@router.post("/{batch_id}/cancel")
async def cancel_running_batch(batch_id: int):
    """Cancel a running batch."""
    if get_current_batch_id() != batch_id:
        raise HTTPException(status_code=400, detail="This batch is not currently running")
    await cancel_batch(batch_id)
    return {"ok": True}
