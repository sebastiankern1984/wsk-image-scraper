import asyncio
import logging

import httpx

from app.services.image_sources.base import BaseImageSource, ImageResult

logger = logging.getLogger(__name__)

USER_AGENT = "WSK-Image-Scraper/1.0 (contact@wsk-medical.de)"


class OpenFoodFactsSource(BaseImageSource):
    name = "openfoodfacts"

    def is_configured(self) -> bool:
        return True

    async def search(
        self,
        ean: str | None,
        pzn: str | None,
        name: str | None,
        manufacturer: str | None,
    ) -> list[ImageResult]:
        if not ean:
            return []

        url = f"https://world.openfoodfacts.org/api/v2/product/{ean}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers={"User-Agent": USER_AGENT})

                if resp.status_code == 404:
                    return []

                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning(f"OpenFoodFacts HTTP error for EAN {ean}: {e}")
            return []
        except Exception as e:
            logger.warning(f"OpenFoodFacts request failed for EAN {ean}: {e}")
            return []
        finally:
            # Rate limit: 100/min fair use
            await asyncio.sleep(0.6)

        product = data.get("product", {})
        if not product:
            return []

        image_keys = [
            "image_front_url",
            "image_ingredients_url",
            "image_nutrition_url",
            "image_packaging_url",
        ]

        results: list[ImageResult] = []
        for key in image_keys:
            image_url = product.get(key)
            if image_url:
                results.append(
                    ImageResult(
                        source=self.name,
                        image_url=image_url,
                        title=key.replace("image_", "").replace("_url", ""),
                    )
                )

        return results[:4]
