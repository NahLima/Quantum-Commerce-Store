"""Composição raiz (Dependency Injection manual).

Este é o único lugar que sabe construir os objetos concretos: aqui as
abstrações (`SentimentPredictor`, repositórios) são ligadas às
implementações (`CompositePredictor`, repositórios SQLAlchemy). Rotas e
serviços recebem tudo pronto por `Depends` — nunca instanciam nada (DIP).
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.gemini_client import GeminiClient
from app.repositories import (
    PredictionRepository,
    ProductRepository,
    ReviewRepository,
    SummaryRepository,
)
from app.services import (
    ProductService,
    ReviewService,
    SentimentService,
    SummaryService,
    ProductTopTerms,
)
from ml.interfaces import SentimentPredictor
from ml.predictors import get_default_predictor


def get_predictor() -> SentimentPredictor:
    return get_default_predictor()


def get_product_repository(db: Session = Depends(get_db)) -> ProductRepository:
    return ProductRepository(db)


def get_review_repository(db: Session = Depends(get_db)) -> ReviewRepository:
    return ReviewRepository(db)


def get_prediction_repository(
    db: Session = Depends(get_db),
) -> PredictionRepository:
    return PredictionRepository(db)


def get_product_terms() -> ProductTopTerms:
    return ProductTopTerms()


def get_product_service(
    products: ProductRepository = Depends(get_product_repository),
) -> ProductService:
    return ProductService(products)


def get_sentiment_service(
    products: ProductRepository = Depends(get_product_repository),
    reviews: ReviewRepository = Depends(get_review_repository),
    terms: ProductTopTerms = Depends(get_product_terms),
) -> SentimentService:
    return SentimentService(products, reviews, terms)


def get_review_service(
    products: ProductRepository = Depends(get_product_repository),
    reviews: ReviewRepository = Depends(get_review_repository),
    predictions: PredictionRepository = Depends(get_prediction_repository),
    predictor: SentimentPredictor = Depends(get_predictor),
) -> ReviewService:
    return ReviewService(products, reviews, predictions, predictor)


def get_summary_repository(db: Session = Depends(get_db)) -> SummaryRepository:
    return SummaryRepository(db)


def get_gemini_client() -> GeminiClient:
    return GeminiClient()


def get_summary_service(
    products: ProductRepository = Depends(get_product_repository),
    reviews: ReviewRepository = Depends(get_review_repository),
    summaries: SummaryRepository = Depends(get_summary_repository),
    sentiment: SentimentService = Depends(get_sentiment_service),
    gemini: GeminiClient = Depends(get_gemini_client),
) -> SummaryService:
    return SummaryService(products, reviews, summaries, sentiment, gemini)
