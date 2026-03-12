from dataclasses import dataclass


@dataclass
class ImageResult:
    source: str  # "openfoodfacts", "google", "bing"
    image_url: str  # URL to download from
    thumbnail_url: str | None = None
    title: str | None = None
    width: int | None = None
    height: int | None = None


class BaseImageSource:
    name: str = "base"

    async def search(
        self,
        ean: str | None,
        pzn: str | None,
        name: str | None,
        manufacturer: str | None,
    ) -> list[ImageResult]:
        raise NotImplementedError

    def is_configured(self) -> bool:
        return True
