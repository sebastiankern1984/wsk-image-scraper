import logging
from pathlib import Path

import httpx
from PIL import Image

from app.config import settings

logger = logging.getLogger(__name__)


async def download_and_store_image(
    product_id: str,
    image_url: str,
    source: str,
    index: int,
) -> dict | None:
    """
    Downloads image, validates, creates thumbnail.
    Returns dict with local_path, thumbnail_path, width, height, file_size_kb.
    Returns None on failure.
    """
    base = Path(settings.IMAGE_STORAGE_PATH) / product_id
    orig_dir = base / "original"
    thumb_dir = base / "thumbnails"
    orig_dir.mkdir(parents=True, exist_ok=True)
    thumb_dir.mkdir(parents=True, exist_ok=True)

    # Download image
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(
                image_url, headers={"User-Agent": "WSK-Image-Scraper/1.0"}
            )
            resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to download {image_url}: {e}")
        return None

    # Detect extension from content-type
    ct = resp.headers.get("content-type", "")
    ext = "jpg"
    if "png" in ct:
        ext = "png"
    elif "webp" in ct:
        ext = "webp"
    elif "gif" in ct:
        ext = "gif"

    orig_path = orig_dir / f"{source}_{index}.{ext}"
    orig_path.write_bytes(resp.content)

    # Validate with Pillow + get dimensions
    try:
        img = Image.open(orig_path)
        img.verify()  # Verify it's a valid image
        img = Image.open(orig_path)  # Re-open after verify
        width, height = img.size
    except Exception as e:
        logger.warning(f"Invalid image from {image_url}: {e}")
        orig_path.unlink(missing_ok=True)
        return None

    # Skip tiny images (likely icons/placeholders)
    if width < 50 or height < 50:
        logger.info(f"Skipping tiny image {width}x{height} from {image_url}")
        orig_path.unlink(missing_ok=True)
        return None

    # Generate thumbnail (200px wide, maintain aspect ratio)
    thumb_path = thumb_dir / f"{source}_{index}_thumb.{ext}"
    try:
        thumb = img.copy()
        thumb.thumbnail((200, 200), Image.LANCZOS)
        thumb.save(thumb_path)
    except Exception as e:
        logger.warning(f"Failed to create thumbnail: {e}")
        # Still return the original even if thumbnail fails
        thumb_path = None

    file_size_kb = len(resp.content) // 1024

    return {
        "local_path": str(orig_path),
        "thumbnail_path": str(thumb_path) if thumb_path else None,
        "width": width,
        "height": height,
        "file_size_kb": file_size_kb,
    }
