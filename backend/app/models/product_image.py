from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, Index, Integer, String, Text, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base

if TYPE_CHECKING:
    from app.models.image_batch import ImageBatch


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    batch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("image_batches.id"), nullable=True)
    product_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    ean: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    pzn: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    search_query: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # openfoodfacts, google, bing
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    local_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_size_kb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, accepted, rejected
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    curated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    batch: Mapped[Optional["ImageBatch"]] = relationship(back_populates="images")

    __table_args__ = (
        UniqueConstraint("product_id", "source_url", name="uq_product_source_url"),
        Index("ix_product_images_status", "status"),
        Index("ix_product_images_source", "source"),
    )
