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
    # Get all products from WSK Hub with their primary EAN (DISTINCT ON to avoid duplicates)
    q = text("""
        SELECT DISTINCT ON (p.product_id)
               p.product_id, p.name, p.manufacturer, p.ean, p.pzn, p.nan,
               pe.ean_value as primary_ean
        FROM products p
        LEFT JOIN product_eans pe ON pe.product_id = p.id
            AND pe.is_primary = true AND pe.valid_to IS NULL
        ORDER BY p.product_id, pe.ean_value
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

    Strategy: For image-based filters, query our own DB FIRST to get matching product_ids,
    then fetch those products from WSK Hub. This avoids the post-pagination filter bug.
    """
    needs_image_filter = filter_status in ("has_images", "uncurated", "accepted", "rejected")

    if needs_image_filter:
        # --- FILTER-FIRST: Query our DB for matching product_ids, then fetch from WSK Hub ---
        status_conditions = {
            "has_images": "",  # any image
            "uncurated": "HAVING count(*) FILTER (WHERE status = 'pending') > 0",
            "accepted": "HAVING count(*) FILTER (WHERE status = 'accepted') > 0",
            "rejected": "HAVING count(*) FILTER (WHERE status = 'rejected') > 0",
        }
        having_clause = status_conditions[filter_status]

        # Get all matching product_ids with counts from our DB
        count_q = f"""
            SELECT product_id::text as pid,
                   count(*) as total,
                   count(*) FILTER (WHERE status = 'pending') as pending,
                   count(*) FILTER (WHERE status = 'accepted') as accepted,
                   count(*) FILTER (WHERE status = 'rejected') as rejected
            FROM product_images
            GROUP BY product_id
            {having_clause}
        """
        count_result = await own_session.execute(text(count_q))
        all_image_counts = {r["pid"]: dict(r) for r in count_result.mappings()}
        matching_pids = list(all_image_counts.keys())
        total = len(matching_pids)

        if not matching_pids:
            return {"items": [], "total": 0}

        # Fetch product details from WSK Hub for the matching IDs
        # We need to paginate within the matching set
        products_result = await wskhub_session.execute(text("""
            SELECT p.product_id, p.name, p.manufacturer, p.ean, p.pzn, p.nan
            FROM products p
            WHERE p.product_id::text = ANY(:ids)
            ORDER BY p.name
            LIMIT :limit OFFSET :offset
        """), {"ids": matching_pids, "limit": limit, "offset": offset})
        products = products_result.mappings().all()

        # Get thumbnails for these products
        page_pids = [str(p["product_id"]) for p in products]
        if page_pids:
            thumb_result = await own_session.execute(text("""
                SELECT DISTINCT ON (product_id) product_id::text, id
                FROM product_images
                WHERE product_id::text = ANY(:ids)
                ORDER BY product_id, status ASC, id ASC
            """), {"ids": page_pids})
            thumbnails = {str(r["product_id"]): r["id"] for r in thumb_result.mappings()}
        else:
            thumbnails = {}

        items = []
        for p in products:
            pid = str(p["product_id"])
            c = all_image_counts.get(pid, {"total": 0, "pending": 0, "accepted": 0, "rejected": 0})
            thumb_id = thumbnails.get(pid)
            items.append({
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
                "thumbnail_url": f"/api/images/{thumb_id}/thumbnail" if thumb_id else None,
            })

        return {"items": items, "total": total}

    else:
        # --- ALL or NO_IMAGES: Paginate from WSK Hub, then enrich with image counts ---
        if filter_status == "no_images":
            # Get product_ids that DO have images
            has_img = await own_session.execute(text(
                "SELECT DISTINCT product_id::text as pid FROM product_images"
            ))
            exclude_pids = [r["pid"] for r in has_img.mappings()]

            if exclude_pids:
                count_result = await wskhub_session.execute(text("""
                    SELECT count(*) FROM products WHERE product_id::text != ALL(:ids)
                """), {"ids": exclude_pids})
                total = count_result.scalar()

                products_result = await wskhub_session.execute(text("""
                    SELECT p.product_id, p.name, p.manufacturer, p.ean, p.pzn, p.nan
                    FROM products p
                    WHERE p.product_id::text != ALL(:ids)
                    ORDER BY p.name
                    LIMIT :limit OFFSET :offset
                """), {"ids": exclude_pids, "limit": limit, "offset": offset})
            else:
                count_result = await wskhub_session.execute(text("SELECT count(*) FROM products"))
                total = count_result.scalar()
                products_result = await wskhub_session.execute(text("""
                    SELECT p.product_id, p.name, p.manufacturer, p.ean, p.pzn, p.nan
                    FROM products p ORDER BY p.name LIMIT :limit OFFSET :offset
                """), {"limit": limit, "offset": offset})

            products = products_result.mappings().all()
            # No images for these products by definition
            items = [{
                "product_id": str(p["product_id"]),
                "name": p["name"],
                "manufacturer": p["manufacturer"],
                "ean": p["ean"],
                "pzn": p["pzn"],
                "nan": p["nan"],
                "image_count": 0,
                "pending_count": 0,
                "accepted_count": 0,
                "rejected_count": 0,
                "thumbnail_url": None,
            } for p in products]

            return {"items": items, "total": total}

        else:
            # filter_status == "all" (default)
            count_result = await wskhub_session.execute(text("SELECT count(*) FROM products"))
            total = count_result.scalar()

            products_result = await wskhub_session.execute(text("""
                SELECT p.product_id, p.name, p.manufacturer, p.ean, p.pzn, p.nan
                FROM products p
                ORDER BY p.name
                LIMIT :limit OFFSET :offset
            """), {"limit": limit, "offset": offset})
            products = products_result.mappings().all()

            # Enrich with image counts
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

                thumb_result = await own_session.execute(text("""
                    SELECT DISTINCT ON (product_id) product_id::text, id
                    FROM product_images
                    WHERE product_id::text = ANY(:ids)
                    ORDER BY product_id, status ASC, id ASC
                """), {"ids": product_ids})
                thumbnails = {str(r["product_id"]): r["id"] for r in thumb_result.mappings()}
            else:
                counts = {}
                thumbnails = {}

            items = []
            for p in products:
                pid = str(p["product_id"])
                c = counts.get(pid, {"total": 0, "pending": 0, "accepted": 0, "rejected": 0})
                thumb_id = thumbnails.get(pid)
                items.append({
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
                    "thumbnail_url": f"/api/images/{thumb_id}/thumbnail" if thumb_id else None,
                })

            return {"items": items, "total": total}
