from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_VERSION: str = "1.0.0"
    APP_NAME: str = "WSK Image Scraper"

    # Own database (read/write)
    DATABASE_URL: str = "postgresql+asyncpg://imgscraper:imgscraper@db:5432/imgscraper"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://imgscraper:imgscraper@db:5432/imgscraper"

    # WSK Hub database (read-only)
    WSKHUB_DATABASE_URL: str = "postgresql+asyncpg://wskhub:wskhub@host.docker.internal:5436/wskhub"

    # API Keys
    GOOGLE_API_KEY: str = ""
    GOOGLE_CX: str = ""
    BING_API_KEY: str = ""

    # Limits
    GOOGLE_DAILY_LIMIT: int = 100
    BING_MONTHLY_LIMIT: int = 1000

    # Storage
    IMAGE_STORAGE_PATH: str = "/data/images"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3098", "http://localhost:5173"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
