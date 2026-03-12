import logging
from datetime import date

import httpx

from app.config import settings
from app.services.image_sources.base import BaseImageSource, ImageResult

logger = logging.getLogger(__name__)

API_URL = "https://api.bing.microsoft.com/v7.0/images/search"


class BingSearchSource(BaseImageSource):
    name = "bing"

    # Class-level counters so they persist across instances
    _monthly_count: int = 0
    _monthly_limit: int = settings.BING_MONTHLY_LIMIT
    _monthly_reset_date: date = date.today().replace(day=1)

    def is_configured(self) -> bool:
        return bool(settings.BING_API_KEY)

    @classmethod
    def _check_and_reset_monthly(cls) -> None:
        today = date.today()
        first_of_month = today.replace(day=1)
        if first_of_month != cls._monthly_reset_date:
            cls._monthly_count = 0
            cls._monthly_reset_date = first_of_month

    async def search(
        self,
        ean: str | None,
        pzn: str | None,
        name: str | None,
        manufacturer: str | None,
    ) -> list[ImageResult]:
        if not self.is_configured():
            return []

        BingSearchSource._check_and_reset_monthly()

        if BingSearchSource._monthly_count >= settings.BING_MONTHLY_LIMIT:
            logger.info(
                f"Bing monthly limit reached ({settings.BING_MONTHLY_LIMIT}). "
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

        headers = {
            "Ocp-Apim-Subscription-Key": settings.BING_API_KEY,
        }
        params = {
            "q": query,
            "count": 5,
            "size": "Large",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(API_URL, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            logger.warning(f"Bing image search failed for '{query}': {e}")
            return []

        BingSearchSource._monthly_count += 1

        values = data.get("value", [])
        results: list[ImageResult] = []

        for item in values[:5]:
            results.append(
                ImageResult(
                    source=self.name,
                    image_url=item.get("contentUrl", ""),
                    title=item.get("name"),
                    width=item.get("width"),
                    height=item.get("height"),
                )
            )

        return results
