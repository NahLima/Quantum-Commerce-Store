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

import hashlib
import re
from collections import Counter

from app.database import SessionLocal
from app.gemini_client import GeminiClient
from app.models import Prediction, Product, Review, Summary
from app.repositories import (
    DEFAULT_REVIEW_LIMIT,
    PredictionRepository,
    ProductRepository,
    ReviewRepository,
    SummaryRepository,
)
from app.schemas import (
    PredictOut,
    ProductSummaryOut,
    ReviewIn,
    ReviewOut,
    SentimentSummary,
)
from app.summary_prompt import build_summary_prompt
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
        return self.summarize_reviews(product_id, reviews)

    def summarize_reviews(
        self, product_id: int, reviews: list[Review]
    ) -> SentimentSummary:
        """Agregado a partir de reviews já carregadas (evita ler o banco 2x)."""
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


# Resumos com IA -----------------------------------------------------------

MIN_REVIEWS_FOR_AI_SUMMARY = 3


def deterministic_summary(stats: SentimentSummary) -> str:
    """Resumo em prosa sem LLM — mesmas regras do `buildReviewSummary` do front.

    Só repete o que os agregados já dizem (distribuição de sentimento +
    termos mais citados). É o fallback quando não há chave do Gemini, quando
    o produto tem poucas avaliações ou quando o resumo em cache está
    desatualizado (avaliação nova chegou).
    """
    total = stats.total_reviews
    if total == 0:
        return "Ainda não há avaliações para este produto."
    counts = stats.counts
    positive = counts.get("positive", 0)
    neutral = counts.get("neutral", 0)
    negative = counts.get("negative", 0)
    parts = [
        f"De {total} {'avaliação' if total == 1 else 'avaliações'}, "
        f"{positive} {'positiva' if positive == 1 else 'positivas'}, "
        f"{neutral} {'neutra' if neutral == 1 else 'neutras'} e "
        f"{negative} {'negativa' if negative == 1 else 'negativas'}."
    ]
    if stats.top_positive_terms:
        terms = ", ".join(stats.top_positive_terms[:3])
        parts.append(f"O que mais elogiam: {terms}.")
    if stats.top_negative_terms:
        terms = ", ".join(stats.top_negative_terms[:3])
        parts.append(f"O que mais reclamam: {terms}.")
    return " ".join(parts)


def _reviews_hash(reviews: list[Review]) -> str:
    """Hash estável do conjunto atual de avaliações (id + texto)."""
    payload = "\n".join(
        f"{review.id}:{review.text}" for review in sorted(reviews, key=lambda r: r.id)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class SummaryService:
    """Resumo de avaliações com LLM + cache por produto.

    Leitura (`get_summary`) nunca espera o LLM: devolve o resumo em cache
    quando ele corresponde às avaliações atuais e a versão determinística
    nos demais casos. A geração (`refresh_summary`) roda em segundo plano
    (ou pelo script de aquecimento) e grava o cache. Sem chave do Gemini,
    a API continua funcionando com o resumo determinístico.
    """

    def __init__(
        self,
        products: ProductRepository,
        reviews: ReviewRepository,
        summaries: SummaryRepository,
        sentiment: SentimentService,
        gemini: GeminiClient | None = None,
    ) -> None:
        self._products = products
        self._reviews = reviews
        self._summaries = summaries
        self._sentiment = sentiment
        self._gemini = gemini or GeminiClient()

    @property
    def gemini_available(self) -> bool:
        return self._gemini.available

    def get_summary(self, product_id: int) -> ProductSummaryOut:
        product = self._products.get(product_id)
        if product is None:
            raise ProductNotFoundError(product_id)
        reviews = self._reviews.list_by_product(product_id, limit=10_000)
        stats = self._sentiment.summarize_reviews(product_id, reviews)
        if len(reviews) < MIN_REVIEWS_FOR_AI_SUMMARY:
            return ProductSummaryOut(
                product_id=product_id,
                summary=deterministic_summary(stats),
                source="deterministic",
                model=None,
                review_count=len(reviews),
                cached=False,
            )
        cached = self._summaries.get(product_id)
        if cached is not None and cached.reviews_hash == _reviews_hash(reviews):
            return ProductSummaryOut(
                product_id=product_id,
                summary=cached.text,
                source="gemini",
                model=cached.model,
                review_count=cached.review_count,
                cached=True,
            )
        return ProductSummaryOut(
            product_id=product_id,
            summary=deterministic_summary(stats),
            source="deterministic",
            model=None,
            review_count=len(reviews),
            cached=False,
        )

    def refresh_summary(self, product_id: int) -> bool:
        """Gera o resumo com o LLM e grava o cache. Devolve True se salvou.

        Abre a própria sessão: roda em segundo plano, depois que a sessão
        da requisição já foi fechada.
        """
        db = SessionLocal()
        try:
            products = ProductRepository(db)
            reviews_repo = ReviewRepository(db)
            summaries = SummaryRepository(db)
            product = products.get(product_id)
            if product is None or not self._gemini.available:
                return False
            reviews = reviews_repo.list_by_product(product_id, limit=10_000)
            if len(reviews) < MIN_REVIEWS_FOR_AI_SUMMARY:
                return False
            prompt = build_summary_prompt(
                product.name, [(review.stars, review.text) for review in reviews]
            )
            text = self._gemini.generate(prompt)
            if not text:
                return False
            summaries.save(
                Summary(
                    product_id=product_id,
                    text=text,
                    model=self._gemini.model,
                    review_count=len(reviews),
                    reviews_hash=_reviews_hash(reviews),
                )
            )
            return True
        finally:
            db.close()
