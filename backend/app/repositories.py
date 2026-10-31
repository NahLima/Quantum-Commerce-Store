"""Repositórios — a única camada que fala SQLAlchemy.

Cada repositório recebe uma `Session` e só faz acesso a dados: nenhuma
regra de negócio, nenhuma chamada de modelo, nenhuma serialização aqui
(SRP). Serviços dependem dos repositórios, nunca da `Session` direto.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Prediction, Product, Review
from ml.interfaces import PredictionResult

DEFAULT_REVIEW_LIMIT = 50


class ProductRepository:
    """Acesso a `products` (catálogo do Figma)."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, product_id: int) -> Product | None:
        return self._db.get(Product, product_id)

    def exists(self, product_id: int) -> bool:
        return self.get(product_id) is not None

    def list(
        self, category: str | None = None, search: str | None = None
    ) -> list[Product]:
        query = self._db.query(Product)
        if category:
            query = query.filter(Product.category == category)
        if search:
            query = query.filter(Product.name.ilike(f"%{search}%"))
        return query.order_by(Product.id).all()

    def add(self, product: Product) -> Product:
        self._db.add(product)
        return product

    def clear(self) -> None:
        self._db.query(Product).delete()

    def commit(self) -> None:
        self._db.commit()


class ReviewRepository:
    """Acesso a `reviews`."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_product(
        self, product_id: int, limit: int = DEFAULT_REVIEW_LIMIT
    ) -> list[Review]:
        return (
            self._db.query(Review)
            .filter(Review.product_id == product_id)
            .order_by(Review.created_at.desc())
            .limit(limit)
            .all()
        )

    def create(
        self,
        product_id: int,
        author: str,
        stars: int,
        text: str,
        source: str,
        created_at=None,
    ) -> Review:
        fields: dict = {
            "product_id": product_id,
            "author": author,
            "stars": stars,
            "text": text,
            "source": source,
        }
        if created_at is not None:
            fields["created_at"] = created_at
        review = Review(**fields)
        self._db.add(review)
        self._db.flush()  # gera o id antes de salvar a predição
        return review

    def clear(self) -> None:
        self._db.query(Review).delete()

    def commit(self) -> None:
        self._db.commit()

    def refresh(self, review: Review) -> None:
        self._db.refresh(review)


class PredictionRepository:
    """Acesso a `predictions` (resultado do modelo por review)."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def save(
        self, review_id: int | None, result: PredictionResult
    ) -> Prediction:
        prediction = Prediction(
            review_id=review_id,
            label=result.label,
            prob_pos=result.probabilities.get("positive", 0.0),
            prob_neu=result.probabilities.get("neutral", 0.0),
            prob_neg=result.probabilities.get("negative", 0.0),
            model_name=result.model_name,
            model_version=result.model_version,
        )
        self._db.add(prediction)
        return prediction

    def clear(self) -> None:
        self._db.query(Prediction).delete()

    def commit(self) -> None:
        self._db.commit()
