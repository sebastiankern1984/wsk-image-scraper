import asyncio
import logging
import time

from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import DuckDuckGoSearchException

from app.services.image_sources.base import BaseImageSource, ImageResult

logger = logging.getLogger(__name__)

# Class-level rate limit tracking
_last_request_time: float = 0.0
_consecutive_failures: int = 0
_cooldown_until: float = 0.0
MIN_DELAY = 4.0  # Minimum seconds between requests
MAX_CONSECUTIVE_FAILURES = 3  # After this many failures, enter cooldown
COOLDOWN_DURATION = 120.0  # 2 minutes cooldown after repeated failures


class DuckDuckGoSource(BaseImageSource):
    name = "duckduckgo"

    def is_configured(self) -> bool:
        global _cooldown_until
        # Not "configured" during cooldown — batch runner will skip us
        if time.time() < _cooldown_until:
            return False
        return True

    async def search(
        self,
        ean: str | None,
        pzn: str | None,
        name: str | None,
        manufacturer: str | None,
    ) -> list[ImageResult]:
        global _last_request_time, _consecutive_failures, _cooldown_until

        # Build query: name + manufacturer only (EAN rarely helps for image search)
        parts = []
        if name:
            parts.append(name)
        if manufacturer:
            parts.append(manufacturer)

        if not parts:
            return []

        query = " ".join(parts)

        # Rate limit: wait at least MIN_DELAY since last request
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < MIN_DELAY:
            await asyncio.sleep(MIN_DELAY - elapsed)

        _last_request_time = time.time()

        try:
            loop = asyncio.get_event_loop()
            images = await loop.run_in_executor(
                None,
                lambda: _ddg_image_search(query),
            )
            # Success — reset failure counter
            _consecutive_failures = 0
        except Exception as e:
            _consecutive_failures += 1
            if _consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                _cooldown_until = time.time() + COOLDOWN_DURATION
                logger.warning(
                    f"DuckDuckGo: {_consecutive_failures} consecutive failures, "
                    f"entering {COOLDOWN_DURATION}s cooldown. Last error: {e}"
                )
            else:
                logger.warning(f"DuckDuckGo search failed for '{query}': {e}")
            return []

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
            max_results=5,
        ))
