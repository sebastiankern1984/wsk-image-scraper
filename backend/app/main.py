from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, dispose_engines


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await dispose_engines()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Will include api_router later when routers are created


@app.get("/api/health")
async def health():
    return {"ok": True, "version": settings.APP_VERSION, "name": settings.APP_NAME}
