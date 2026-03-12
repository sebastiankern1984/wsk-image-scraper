import logging
from datetime import date

import httpx

from app.config import settings
from app.services.image_sources.base import BaseImageSource, ImageResult

logger = logging.getLogger(__name__)

API_URL = "https://customsearch.googleapis.com/customsearch/v1"


class GoogleSearchSource(BaseImageSource):
    name = "google"

    # Class-level counters so they persist across instances
    _daily_count: int = 0
    _daily_limit: int = settings.GOOGLE_DAILY_LIMIT
    _daily_reset_date: date = date.today()

    def is_configured(self) -> bool:
        return bool(settings.GOOGLE_API_KEY) and bool(settings.GOOGLE_CX)

    @classmethod
    def _check_and_reset_daily(cls) -> None:
        today = date.today()
        if today != cls._daily_reset_date:
            cls._daily_count = 0
            cls._daily_reset_date = today

    async def search(
        self,
        ean: str | None,
        pzn: str | None,
        name: str | None,
        manufacturer: str | None,
    ) -> list[ImageResult]:
        if not self.is_configured():
            return []

        GoogleSearchSource._check_and_reset_daily()

        if GoogleSearchSource._daily_count >= settings.GOOGLE_DAILY_LIMIT:
            logger.info(
                f"Google daily limit reached ({settings.GOOGLE_DAILY_LIMIT}). "
                f"Skipping search."
            )
            return []

        # Build query: prefer EAN, fall back to name + manufacturer
        if ean:
            query = ean
        else:
            parts = [p for p in (name, manufacturer) if p]
            if not parts:
                return []
            query = " ".join(parts)

        params = {
            "key": settings.GOOGLE_API_KEY,
            "cx": settings.GOOGLE_CX,
            "searchType": "image",
            "num": 5,
            "imgSize": "large",
            "q": query,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(API_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            logger.warning(f"Google image search failed for '{query}': {e}")
            return []

        GoogleSearchSource._daily_count += 1

        items = data.get("items", [])
        results: list[ImageResult] = []

        for item in items[:5]:
            image_info = item.get("image", {})
            results.append(
                ImageResult(
                    source=self.name,
                    image_url=item.get("link", ""),
                    title=item.get("title"),
                    width=image_info.get("width"),
                    height=image_info.get("height"),
                )
            )

        return results
