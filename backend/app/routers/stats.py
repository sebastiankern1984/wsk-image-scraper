from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, get_wskhub_db
from app.models.image_batch import ImageBatch
from app.models.product_image import ProductImage
from app.services.product_reader import get_product_count
from app.services.image_sources.google_search import GoogleSearchSource
from app.services.image_sources.bing_search import BingSearchSource

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    wskhub_db: AsyncSession = Depends(get_wskhub_db),
):
    total_products = await get_product_count(wskhub_db)

    # Image counts by status
    img_counts = await db.execute(
        select(
            func.count(ProductImage.id).label("total"),
            func.count(ProductImage.id).filter(ProductImage.status == "pending").label("pending"),
            func.count(ProductImage.id).filter(ProductImage.status == "accepted").label("accepted"),
            func.count(ProductImage.id).filter(ProductImage.status == "rejected").label("rejected"),
        )
    )
    row = img_counts.one()

    # Products with at least 1 accepted image
    products_with = await db.execute(
        select(func.count(func.distinct(ProductImage.product_id)))
        .where(ProductImage.status == "accepted")
    )
    products_with_images = products_with.scalar() or 0

    # Last batch
    last_batch_result = await db.execute(
        select(ImageBatch).order_by(ImageBatch.started_at.desc()).limit(1)
    )
    last_batch = last_batch_result.scalar_one_or_none()

    return {
        "total_products": total_products,
        "products_with_images": products_with_images,
        "products_without_images": total_products - products_with_images,
        "total_images": row.total,
        "pending_images": row.pending,
        "accepted_images": row.accepted,
        "rejected_images": row.rejected,
        "last_batch": {
            "id": last_batch.id,
            "status": last_batch.status,
            "started_at": last_batch.started_at.isoformat() if last_batch.started_at else None,
            "processed": last_batch.processed,
            "total_products": last_batch.total_products,
            "images_found": last_batch.images_found,
        } if last_batch else None,
        "google_usage": {"used": GoogleSearchSource._daily_count, "limit": GoogleSearchSource._daily_limit},
        "bing_usage": {"used": BingSearchSource._monthly_count, "limit": BingSearchSource._monthly_limit},
    }
