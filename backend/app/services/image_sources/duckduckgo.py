import asyncio
import logging

from duckduckgo_search import DDGS

from app.services.image_sources.base import BaseImageSource, ImageResult

logger = logging.getLogger(__name__)


class DuckDuckGoSource(BaseImageSource):
    name = "duckduckgo"

    def is_configured(self) -> bool:
        return True  # No API key needed

    async def search(
        self,
        ean: str | None,
        pzn: str | None,
        name: str | None,
        manufacturer: str | None,
    ) -> list[ImageResult]:
        # Build query from available info
        parts = []
        if name:
            parts.append(name)
        if manufacturer:
            parts.append(manufacturer)
        if ean:
            parts.append(ean)
        elif pzn:
            parts.append(f"PZN {pzn}")

        if not parts:
            return []

        query = " ".join(parts) + " Produktbild"

        try:
            # Run sync DDG search in thread pool to not block async loop
            loop = asyncio.get_event_loop()
            images = await loop.run_in_executor(
                None,
                lambda: _ddg_image_search(query),
            )
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed for '{query}': {e}")
            return []

        # Rate limit - be polite
        await asyncio.sleep(1.0)

        results: list[ImageResult] = []
        for img in images[:5]:
            url = img.get("image", "")
            if not url:
                continue
            results.append(
                ImageResult(
                    source=self.name,
                    image_url=url,
                    title=img.get("title"),
                    width=img.get("width"),
                    height=img.get("height"),
                )
            )

        return results


def _ddg_image_search(query: str) -> list[dict]:
    """Sync wrapper for DDG image search (runs in thread pool)."""
    with DDGS() as ddgs:
        return list(ddgs.images(
            keywords=query,
            region="de-de",
            safesearch="moderate",
            size="Large",
            type_image="photo",
            max_results=5,
        ))
