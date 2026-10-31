"""Schemas Pydantic da API (contrato público — não mudar sem versionar).

Separados das rotas (`app/main.py`) e dos modelos SQLAlchemy
(`app/models.py`): a API fala em schemas; o banco fala em modelos.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

MAX_REVIEW_TEXT_LENGTH = 2000
MAX_STARS = 5
MIN_STARS = 1


class ProductOut(BaseModel):
    id: int
    name: str
    category: str
    price_cents: int
    color: str
    image_url: str
    rating: float
    reviews_count: int

    model_config = {"from_attributes": True}


class ReviewIn(BaseModel):
    product_id: int
    author: str = "Cliente"
    stars: int = Field(..., ge=MIN_STARS, le=MAX_STARS)
    text: str = Field(..., min_length=1, max_length=MAX_REVIEW_TEXT_LENGTH)


class ReviewOut(BaseModel):
    id: int
    product_id: int
    author: str
    stars: int
    text: str
    source: str
    label: str | None = None
    confidence: float | None = None

    model_config = {"from_attributes": True}


class PredictIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_REVIEW_TEXT_LENGTH)


class PredictOut(BaseModel):
    label: str
    label_pt: str
    probabilities: dict[str, float]
    confidence: float
    model_name: str
    model_version: str


class SentimentSummary(BaseModel):
    product_id: int
    total_reviews: int
    avg_stars: float | None
    counts: dict[str, int]
    percentages: dict[str, float]
    top_positive_terms: list[str] = []
    top_negative_terms: list[str] = []
