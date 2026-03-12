from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)


async def get_products_without_images(
    wskhub_session: AsyncSession,
    own_session: AsyncSession,
    limit: int | None = None,
) -> list[dict]:
    """
    Query WSK Hub products + product_eans.
    Cross-reference with own product_images to find products without accepted images.
    """
    # Get all products from WSK Hub with their primary EAN
    q = text("""
        SELECT p.product_id, p.name, p.manufacturer, p.ean, p.pzn, p.nan,
               pe.ean_value as primary_ean
        FROM products p
        LEFT JOIN product_eans pe ON pe.product_id = p.id
            AND pe.is_primary = true AND pe.valid_to IS NULL
        ORDER BY p.id
    """)
    result = await wskhub_session.execute(q)
    products = result.mappings().all()

    # Get product_ids that already have accepted images in our DB
    accepted = await own_session.execute(
        text("SELECT DISTINCT product_id::text FROM product_images WHERE status = 'accepted'")
    )
    accepted_ids = {str(r[0]) for r in accepted}

    # Filter out products with accepted images
    filtered = [
        {
            "product_id": str(p["product_id"]),
            "name": p["name"],
            "manufacturer": p["manufacturer"],
            "ean": p["primary_ean"] or p["ean"],
            "pzn": p["pzn"],
            "nan": p["nan"],
        }
        for p in products
        if str(p["product_id"]) not in accepted_ids
    ]

    if limit:
        return filtered[:limit]
    return filtered


async def get_product_count(wskhub_session: AsyncSession) -> int:
    """Total products in WSK Hub."""
    result = await wskhub_session.execute(text("SELECT count(*) FROM products"))
    return result.scalar()


async def get_all_products_with_image_status(
    wskhub_session: AsyncSession,
    own_session: AsyncSession,
    offset: int = 0,
    limit: int = 50,
    filter_status: str | None = None,
) -> dict:
    """
    For the gallery page: list products with their image counts.
    filter_status: 'all', 'has_images', 'no_images', 'uncurated', 'accepted', 'rejected'
    Returns: {"items": [...], "total": int}
    """
    # Get products from WSK Hub
    count_result = await wskhub_session.execute(text("SELECT count(*) FROM products"))
    total = count_result.scalar()

    products_result = await wskhub_session.execute(text("""
        SELECT p.product_id, p.name, p.manufacturer, p.ean, p.pzn, p.nan
        FROM products p
        ORDER BY p.name
        LIMIT :limit OFFSET :offset
    """), {"limit": limit, "offset": offset})
    products = products_result.mappings().all()

    # Get image counts per product from own DB
    product_ids = [str(p["product_id"]) for p in products]
    if product_ids:
        image_counts = await own_session.execute(text("""
            SELECT product_id::text,
                   count(*) as total,
                   count(*) FILTER (WHERE status = 'pending') as pending,
                   count(*) FILTER (WHERE status = 'accepted') as accepted,
                   count(*) FILTER (WHERE status = 'rejected') as rejected
            FROM product_images
            WHERE product_id::text = ANY(:ids)
            GROUP BY product_id
        """), {"ids": product_ids})
        counts = {str(r["product_id"]): dict(r) for r in image_counts.mappings()}
    else:
        counts = {}

    items = []
    for p in products:
        pid = str(p["product_id"])
        c = counts.get(pid, {"total": 0, "pending": 0, "accepted": 0, "rejected": 0})
        item = {
            "product_id": pid,
            "name": p["name"],
            "manufacturer": p["manufacturer"],
            "ean": p["ean"],
            "pzn": p["pzn"],
            "nan": p["nan"],
            "image_count": c.get("total", 0),
            "pending_count": c.get("pending", 0),
            "accepted_count": c.get("accepted", 0),
            "rejected_count": c.get("rejected", 0),
        }

        # Apply filter
        if filter_status == "has_images" and item["image_count"] == 0:
            continue
        if filter_status == "no_images" and item["image_count"] > 0:
            continue
        if filter_status == "uncurated" and item["pending_count"] == 0:
            continue
        if filter_status == "accepted" and item["accepted_count"] == 0:
            continue
        if filter_status == "rejected" and item["rejected_count"] == 0:
            continue

        items.append(item)

    return {"items": items, "total": total}
