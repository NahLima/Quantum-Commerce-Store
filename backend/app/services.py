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

import re
from collections import Counter

from app.models import Prediction, Product, Review
from app.repositories import (
    DEFAULT_REVIEW_LIMIT,
    PredictionRepository,
    ProductRepository,
    ReviewRepository,
)
from app.schemas import PredictOut, ReviewIn, ReviewOut, SentimentSummary
from ml.interfaces import SentimentPredictor
from ml.labels import LABELS, label_from_stars
from ml.stopwords import PT_STOPWORDS

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


def _words(text: str) -> list[str]:
    """Palavras minúsculas com 3+ letras (acentos preservados)."""
    return re.findall(r"[a-zà-ú]{3,}", text.lower())


def _label_of(review: Review) -> str:
    """Rótulo da review: predição salva, ou regra por estrelas (1-2 neg, 3 neu, 4-5 pos)."""
    if review.prediction is not None:
        return review.prediction.label
    return label_from_stars(review.stars)


class ProductTopTerms:
    """Termos mais citados nas avaliações DESTE produto.

    Conta as palavras mais frequentes nos textos das reviews positivas
    (elogios) e negativas (reclamações) do próprio produto, ignorando
    stopwords. Antes, os termos vinham do `top_terms.json` global do
    treino (Olist inteiro): o termômetro mostrava palavras que nenhuma
    avaliação do produto continha.
    """

    def __init__(self, stopwords: set[str] | None = None) -> None:
        self._stopwords = stopwords if stopwords is not None else set(PT_STOPWORDS)

    def top_positive_terms(self, reviews: list[Review]) -> list[str]:
        return self._top_terms(reviews, "positive")

    def top_negative_terms(self, reviews: list[Review]) -> list[str]:
        return self._top_terms(reviews, "negative")

    def _top_terms(self, reviews: list[Review], label: str) -> list[str]:
        counts: Counter = Counter()
        for review in reviews:
            if _label_of(review) != label:
                continue
            for word in _words(review.text):
                if word not in self._stopwords:
                    counts[word] += 1
        # Mais frequentes primeiro; empate desempatado em ordem alfabética
        # (resultado determinístico para o mesmo conjunto de reviews).
        return [
            word
            for word, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[
                :MAX_TOP_TERMS
            ]
        ]


class SentimentService:
    """Agregado de sentimento de um produto (o 'termômetro')."""

    def __init__(
        self,
        products: ProductRepository,
        reviews: ReviewRepository,
        terms: ProductTopTerms | None = None,
    ) -> None:
        self._products = products
        self._reviews = reviews
        self._terms = terms or ProductTopTerms()

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
            top_positive_terms=self._terms.top_positive_terms(reviews),
            top_negative_terms=self._terms.top_negative_terms(reviews),
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
            counts[_label_of(review)] += 1
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
