import logging
from datetime import date

import httpx

from app.config import settings
from app.services.image_sources.base import BaseImageSource, ImageResult

logger = logging.getLogger(__name__)

API_URL = "https://customsearch.googleapis.com/customsearch/v1"


class GoogleSearchSource(BaseImageSource):
    name = "google"

    def __init__(self) -> None:
        self._daily_count: int = 0
        self._daily_reset_date: date = date.today()

    def is_configured(self) -> bool:
        return bool(settings.GOOGLE_API_KEY) and bool(settings.GOOGLE_CX)

    def _check_and_reset_daily(self) -> None:
        today = date.today()
        if today != self._daily_reset_date:
            self._daily_count = 0
            self._daily_reset_date = today

    async def search(
        self,
        ean: str | None,
        pzn: str | None,
        name: str | None,
        manufacturer: str | None,
    ) -> list[ImageResult]:
        if not self.is_configured():
            return []

        self._check_and_reset_daily()

        if self._daily_count >= settings.GOOGLE_DAILY_LIMIT:
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

        self._daily_count += 1

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
