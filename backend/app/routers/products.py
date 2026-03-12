from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, get_wskhub_db
from app.models.product_image import ProductImage
from app.services.product_reader import get_all_products_with_image_status

router = APIRouter(prefix="/products", tags=["products"])


@router.get("")
async def list_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    filter: str = Query("all"),
    db: AsyncSession = Depends(get_db),
    wskhub_db: AsyncSession = Depends(get_wskhub_db),
):
    """List products with image status. Filter: all, has_images, no_images, uncurated, accepted, rejected."""
    offset = (page - 1) * per_page
    result = await get_all_products_with_image_status(
        wskhub_db, db, offset=offset, limit=per_page, filter_status=filter
    )
    return {"items": result["items"], "total": result["total"], "page": page, "per_page": per_page}


@router.get("/{product_id}/images")
async def get_product_images(product_id: str, db: AsyncSession = Depends(get_db)):
    """Get all images for a specific product."""
    result = await db.execute(
        select(ProductImage)
        .where(ProductImage.product_id == product_id)
        .order_by(ProductImage.source, ProductImage.id)
    )
    images = result.scalars().all()
    return [
        {
            "id": img.id,
            "image_id": str(img.id),
            "product_id": img.product_id,
            "ean": img.ean,
            "pzn": img.pzn,
            "search_query": img.search_query,
            "source": img.source,
            "source_url": img.source_url,
            "width": img.width,
            "height": img.height,
            "file_size_kb": img.file_size_kb,
            "status": img.status,
            "thumbnail_url": f"/api/images/{img.id}/thumbnail",
            "file_url": f"/api/images/{img.id}/file",
            "created_at": img.created_at.isoformat() if img.created_at else None,
            "curated_at": img.curated_at.isoformat() if img.curated_at else None,
        }
        for img in images
    ]
