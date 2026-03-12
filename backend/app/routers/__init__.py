from fastapi import APIRouter

from app.routers.batches import router as batches_router
from app.routers.products import router as products_router
from app.routers.images import router as images_router
from app.routers.stats import router as stats_router

api_router = APIRouter(prefix="/api")
api_router.include_router(batches_router)
api_router.include_router(products_router)
api_router.include_router(images_router)
api_router.include_router(stats_router)
