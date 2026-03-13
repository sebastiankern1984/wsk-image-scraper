import asyncio
import logging
from datetime import datetime

from sqlalchemy import select

from app.database import async_session, wskhub_async_session
from app.models.image_batch import ImageBatch
from app.models.product_image import ProductImage
from app.services.product_reader import get_products_without_images
from app.services.image_sources.openfoodfacts import OpenFoodFactsSource
from app.services.image_sources.duckduckgo import DuckDuckGoSource
from app.services.image_sources.google_search import GoogleSearchSource
from app.services.image_sources.bing_search import BingSearchSource
from app.services.image_downloader import download_and_store_image

logger = logging.getLogger(__name__)

# In-memory state
_current_batch_id: int | None = None
_cancel_requested: bool = False


def get_current_batch_id() -> int | None:
    return _current_batch_id


async def start_batch() -> int:
    global _current_batch_id, _cancel_requested
    if _current_batch_id is not None:
        raise RuntimeError("A batch is already running")
    _cancel_requested = False

    async with async_session() as db:
        batch = ImageBatch(status="running")
        db.add(batch)
        await db.commit()
        await db.refresh(batch)
        batch_id = batch.id

    _current_batch_id = batch_id
    asyncio.create_task(_run_batch(batch_id))
    return batch_id


async def cancel_batch(batch_id: int):
    global _cancel_requested
    _cancel_requested = True


async def _run_batch(batch_id: int):
    global _current_batch_id, _cancel_requested
    sources = [OpenFoodFactsSource(), DuckDuckGoSource(), GoogleSearchSource(), BingSearchSource()]

    try:
        # Get products to process
        async with wskhub_async_session() as hub_db, async_session() as own_db:
            products = await get_products_without_images(hub_db, own_db)

        # Update batch total
        async with async_session() as db:
            batch = await db.get(ImageBatch, batch_id)
            batch.total_products = len(products)
            await db.commit()

        for product in products:
            if _cancel_requested:
                break

            images_for_product = 0

            for source in sources:
                if not source.is_configured():
                    continue
                try:
                    results = await source.search(
                        ean=product["ean"],
                        pzn=product["pzn"],
                        name=product["name"],
                        manufacturer=product["manufacturer"],
                    )
                    for i, img_result in enumerate(results):
                        downloaded = await download_and_store_image(
                            product_id=product["product_id"],
                            image_url=img_result.image_url,
                            source=img_result.source,
                            index=i,
                        )
                        if downloaded:
                            async with async_session() as db:
                                pi = ProductImage(
                                    batch_id=batch_id,
                                    product_id=product["product_id"],
                                    ean=product["ean"],
                                    pzn=product["pzn"],
                                    search_query=img_result.title,
                                    source=img_result.source,
                                    source_url=img_result.image_url,
                                    **downloaded,
                                )
                                db.add(pi)
                                await db.commit()
                                images_for_product += 1
                except Exception as e:
                    logger.warning(f"Source {source.name} failed for {product['product_id']}: {e}")

            # Update progress
            async with async_session() as db:
                batch = await db.get(ImageBatch, batch_id)
                batch.processed += 1
                batch.images_found += images_for_product
                if images_for_product == 0:
                    batch.error_count += 1
                await db.commit()

            await asyncio.sleep(0.5)

        # Mark complete
        status = "cancelled" if _cancel_requested else "completed"
        async with async_session() as db:
            batch = await db.get(ImageBatch, batch_id)
            batch.status = status
            batch.completed_at = datetime.utcnow()
            await db.commit()

    except Exception as e:
        logger.error(f"Batch {batch_id} failed: {e}")
        async with async_session() as db:
            batch = await db.get(ImageBatch, batch_id)
            batch.status = "failed"
            batch.completed_at = datetime.utcnow()
            await db.commit()
    finally:
        _current_batch_id = None
        _cancel_requested = False
