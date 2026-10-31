"""Serviços — regras de negócio da API.

Cada serviço tem uma única responsabilidade (SRP) e depende de
abstrações, nunca de SQL direto:
    ProductService: catálogo (lista / detalhe).
    SentimentService: agregado de sentimento por produto (% pos/neu/neg,
        média de estrelas, termos mais relevantes).
    ReviewService: criar review + prever sentimento, e prever texto avulso.

Os serviços recebem repositórios e um `SentimentPredictor` (DIP): trocar
o modelo ou o banco não muda nenhuma regra aqui.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from app.models import Prediction, Product, Review
from app.repositories import (
    DEFAULT_REVIEW_LIMIT,
    PredictionRepository,
    ProductRepository,
    ReviewRepository,
)
from app.schemas import PredictOut, ReviewIn, ReviewOut, SentimentSummary
from ml.interfaces import SentimentPredictor
from ml.labels import LABELS, MODEL_DIR, label_from_stars

MAX_TOP_TERMS = 10
PRODUCT_NOT_FOUND = "Produto não encontrado"


class ProductNotFoundError(Exception):
    """Produto inexistente — a rota traduz para HTTP 404."""

    def __init__(self, product_id: int) -> None:
        super().__init__(PRODUCT_NOT_FOUND)
        self.product_id = product_id


def prediction_confidence(prediction: Prediction | None) -> float | None:
    """Maior probabilidade da predição salva (ou None, sem predição)."""
    if prediction is None:
        return None
    return max(prediction.prob_pos, prediction.prob_neu, prediction.prob_neg)


def review_to_out(review: Review) -> ReviewOut:
    """Serializa uma review com o rótulo/confiança da predição salva."""
    out = ReviewOut.model_validate(review)
    if review.prediction is not None:
        out.label = review.prediction.label
        out.confidence = prediction_confidence(review.prediction)
    return out


class ProductService:
    """Catálogo: listar e buscar produtos."""

    def __init__(self, products: ProductRepository) -> None:
        self._products = products

    def list_products(
        self, category: str | None = None, search: str | None = None
    ) -> list[Product]:
        return self._products.list(category=category, search=search)

    def get_product(self, product_id: int) -> Product:
        product = self._products.get(product_id)
        if product is None:
            raise ProductNotFoundError(product_id)
        return product


class TopTermsProvider:
    """Lê os termos mais relevantes do LogReg (`top_terms.json`).

    Extração (mesma do comportamento anterior): termos de maior
    coeficiente positivo da classe "positive" (o que mais indica
    elogio) e da classe "negative" (o que mais indica crítica).
    Arquivo ausente ou inválido -> listas vazias, sem quebrar a API.
    """

    def __init__(self, model_dir: Path | None = None) -> None:
        self._model_dir = model_dir or MODEL_DIR

    def load(self) -> dict:
        terms_path = self._model_dir / "top_terms.json"
        if not terms_path.exists():
            return {}
        try:
            return json.loads(terms_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def top_positive_terms(self) -> list[str]:
        terms = self.load()
        return terms.get("positive", {}).get("positive", [])[:MAX_TOP_TERMS]

    def top_negative_terms(self) -> list[str]:
        terms = self.load()
        return terms.get("negative", {}).get("positive", [])[:MAX_TOP_TERMS]


class SentimentService:
    """Agregado de sentimento de um produto (o 'termômetro')."""

    def __init__(
        self,
        products: ProductRepository,
        reviews: ReviewRepository,
        terms: TopTermsProvider | None = None,
    ) -> None:
        self._products = products
        self._reviews = reviews
        self._terms = terms or TopTermsProvider()

    def summarize(self, product_id: int) -> SentimentSummary:
        product = self._products.get(product_id)
        if product is None:
            raise ProductNotFoundError(product_id)
        reviews = self._reviews.list_by_product(product_id, limit=10_000)
        return SentimentSummary(
            product_id=product_id,
            total_reviews=len(reviews),
            avg_stars=self._average_stars(reviews),
            counts=dict(self._count_labels(reviews)),
            percentages=self._percentages(reviews),
            top_positive_terms=self._terms.top_positive_terms(),
            top_negative_terms=self._terms.top_negative_terms(),
        )

    @staticmethod
    def _average_stars(reviews: list[Review]) -> float | None:
        if not reviews:
            return None
        return round(sum(r.stars for r in reviews) / len(reviews), 2)

    @staticmethod
    def _count_labels(reviews: list[Review]) -> Counter:
        counts: Counter = Counter({label: 0 for label in LABELS})
        for review in reviews:
            if review.prediction is not None:
                counts[review.prediction.label] += 1
            else:  # sem predição salva: deriva das estrelas (regra do trabalho)
                counts[label_from_stars(review.stars)] += 1
        return counts

    def _percentages(self, reviews: list[Review]) -> dict[str, float]:
        counts = self._count_labels(reviews)
        total = len(reviews)
        return {
            label: round(counts[label] / total * 100, 1) if total else 0.0
            for label in LABELS
        }


class ReviewService:
    """Criar reviews (com predição) e classificar texto avulso."""

    def __init__(
        self,
        products: ProductRepository,
        reviews: ReviewRepository,
        predictions: PredictionRepository,
        predictor: SentimentPredictor,
    ) -> None:
        self._products = products
        self._reviews = reviews
        self._predictions = predictions
        self._predictor = predictor

    def list_reviews(
        self, product_id: int, limit: int = DEFAULT_REVIEW_LIMIT
    ) -> list[ReviewOut]:
        if not self._products.exists(product_id):
            raise ProductNotFoundError(product_id)
        reviews = self._reviews.list_by_product(product_id, limit=limit)
        return [review_to_out(review) for review in reviews]

    def predict_text(self, text: str) -> PredictOut:
        """Classifica um texto avulso e persiste a predição (sem review)."""
        result = self._predictor.predict(text)
        self._predictions.save(review_id=None, result=result)
        self._predictions.commit()
        return PredictOut(**result.to_dict())

    def create_review(self, payload: ReviewIn) -> ReviewOut:
        """Salva a review, prevê o sentimento e devolve a review anotada."""
        if not self._products.exists(payload.product_id):
            raise ProductNotFoundError(payload.product_id)
        review = self._reviews.create(
            product_id=payload.product_id,
            author=payload.author,
            stars=payload.stars,
            text=payload.text,
            source="api",
        )
        result = self._predictor.predict(payload.text)
        self._predictions.save(review_id=review.id, result=result)
        self._reviews.commit()
        self._reviews.refresh(review)
        return review_to_out(review)
