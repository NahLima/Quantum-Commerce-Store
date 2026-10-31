"""Modelos SQLAlchemy — espelham o catálogo do Figma + reviews com sentimento."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    image_url: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rating: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reviews_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    reviews: Mapped[list["Review"]] = relationship(
        "Review", back_populates="product", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(120), nullable=False, default="Cliente")
    stars: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..5
    text: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="seed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    product: Mapped["Product"] = relationship("Product", back_populates="reviews")
    prediction: Mapped["Prediction | None"] = relationship(
        "Prediction", back_populates="review", uselist=False,
        cascade="all, delete-orphan")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("reviews.id"), nullable=True, index=True)
    label: Mapped[str] = mapped_column(String(20), nullable=False)  # pos/neu/neg
    prob_pos: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    prob_neu: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    prob_neg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    model_name: Mapped[str] = mapped_column(String(60), nullable=False, default="")
    model_version: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    review: Mapped["Review | None"] = relationship("Review", back_populates="prediction")
