"""Seed do banco: 50 produtos do Figma + reviews sintéticas PT-BR.

Produtos: lidos de `backend/data/products.json` (extraído de
/tmp/qc-unzip/src/App.tsx — nomes, preços, cores e imagens idênticos ao Figma).
Reviews: 3-6 por produto, texto coerente com as estrelas (positivas 4-5,
neutras 3, negativas 1-2). Também grava `backend/data/seed_reviews.csv`
(text, stars, product_id) para reuso no treino.

Uso (com Postgres no ar):
    cd backend && python seed.py
Uso sem Postgres (SQLite local):
    cd backend && USE_SQLITE=1 python seed.py

Cada classe tem uma responsabilidade (SRP): carregar os dados, gerar os
textos, popular produtos, popular reviews, escrever o CSV e orquestrar.
"""

from __future__ import annotations

import csv
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Product  # noqa: E402
from app.repositories import (  # noqa: E402
    PredictionRepository,
    ProductRepository,
    ReviewRepository,
)
from ml.interfaces import SentimentPredictor  # noqa: E402
from ml.labels import label_from_stars  # noqa: E402
from ml.predictors import get_default_predictor  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RANDOM_SEED = 42

AUTHORS = [
    "Marina C.", "Rafael M.", "Camila A.", "João P.", "Beatriz L.",
    "Lucas T.", "Fernanda S.", "Gabriel R.", "Larissa M.", "Thiago A.",
    "Patrícia N.", "Bruno K.", "Aline D.", "Diego F.", "Sofia B.",
]

POSITIVE_TEXTS = [
    "Superou minhas expectativas. O acabamento é impecável e chegou muito bem embalado.",
    "Produto excelente, exatamente como nas fotos. A entrega foi rápida e a experiência de compra muito simples.",
    "Qualidade acima da média e um design realmente bonito. Recomendo sem dúvida.",
    "Adorei! Uso todos os dias, muito confortável e bonito. Vale cada centavo.",
    "Chegou antes do prazo, embalagem perfeita e produto maravilhoso. Compraria de novo.",
    "Lindo demais, material de ótima qualidade. Já virou parte da minha rotina.",
    "Excelente custo-benefício. Funciona perfeitamente e o atendimento foi impecável.",
]
NEUTRAL_TEXTS = [
    "Produto ok, cumpre o básico pelo preço. Nada de especial, mas não decepciona.",
    "É razoável. A qualidade é aceitável, mas esperava um acabamento um pouco melhor.",
    "Chegou no prazo e funciona como esperado. Nem bom nem ruim, mediano.",
    "Atende o que promete, sem encantar. Pelo preço, está dentro do esperado.",
]
NEGATIVE_TEXTS = [
    "Péssimo. O produto veio com defeito e a qualidade é muito abaixo do anunciado.",
    "Decepção total: chegou atrasado, mal embalado e com defeito. Não recomendo.",
    "Muito ruim, o material é frágil e quebrou na primeira semana. Dinheiro jogado fora.",
    "Não vale o preço. O acabamento é horrível e o atendimento não resolveu meu problema.",
]

# Proporção por review gerada (como no varejo real: maioria positiva).
POSITIVE_SHARE = 0.62
NEUTRAL_SHARE_UP_TO = 0.82
MIN_REVIEWS_PER_PRODUCT = 3
MAX_REVIEWS_PER_PRODUCT = 6
MAX_REVIEW_AGE_DAYS = 180


class SeedDataLoader:
    """Lê o catálogo do Figma (`data/products.json`)."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (DATA_DIR / "products.json")

    def load_products(self) -> list[dict]:
        return json.loads(self._path.read_text(encoding="utf-8"))


class ReviewTemplateGenerator:
    """Gera reviews sintéticas por produto, com RNG determinístico."""

    def __init__(self, seed: int = RANDOM_SEED) -> None:
        self._rng = random.Random(seed)

    def generate_for_product(self, product_id: int) -> list[dict]:
        count = self._rng.randint(MIN_REVIEWS_PER_PRODUCT, MAX_REVIEWS_PER_PRODUCT)
        return [self._one_review(product_id) for _ in range(count)]

    def _one_review(self, product_id: int) -> dict:
        roll = self._rng.random()
        if roll < POSITIVE_SHARE:
            text, stars = self._rng.choice(POSITIVE_TEXTS), self._rng.choice([4, 5, 5])
        elif roll < NEUTRAL_SHARE_UP_TO:
            text, stars = self._rng.choice(NEUTRAL_TEXTS), 3
        else:
            text, stars = self._rng.choice(NEGATIVE_TEXTS), self._rng.choice([1, 2])
        age = timedelta(days=self._rng.randint(1, MAX_REVIEW_AGE_DAYS))
        return {
            "product_id": product_id,
            "author": self._rng.choice(AUTHORS),
            "stars": stars,
            "text": text,
            "source": "seed",
            "created_at": datetime.now(timezone.utc) - age,
        }


class ProductSeeder:
    """Limpa e reinsere o catálogo (seed idempotente)."""

    def __init__(
        self,
        products: ProductRepository,
        reviews: ReviewRepository,
        predictions: PredictionRepository,
    ) -> None:
        self._products = products
        self._reviews = reviews
        self._predictions = predictions

    def seed(self, products: list[dict]) -> None:
        self._predictions.clear()
        self._reviews.clear()
        self._products.clear()
        for item in products:
            self._products.add(Product(**item))
        self._products.commit()


class ReviewSeeder:
    """Insere as reviews geradas, já com a predição do modelo salva."""

    def __init__(
        self,
        reviews: ReviewRepository,
        predictions: PredictionRepository,
        predictor: SentimentPredictor,
    ) -> None:
        self._reviews = reviews
        self._predictions = predictions
        self._predictor = predictor

    def seed(self, rows: list[dict]) -> None:
        for row in rows:
            review = self._reviews.create(
                product_id=row["product_id"],
                author=row["author"],
                stars=row["stars"],
                text=row["text"],
                source=row["source"],
                created_at=row["created_at"],
            )
            result = self._predictor.predict(row["text"])
            self._predictions.save(review_id=review.id, result=result)
        self._reviews.commit()


class SeedCsvWriter:
    """Grava as reviews geradas em `data/seed_reviews.csv`."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (DATA_DIR / "seed_reviews.csv")

    def write(self, rows: list[dict]) -> Path:
        with self._path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=["text", "stars", "product_id"]
            )
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {"text": row["text"], "stars": row["stars"],
                     "product_id": row["product_id"]}
                )
        return self._path


class DatabaseSeeder:
    """Orquestra o seed completo: produtos + reviews + CSV."""

    def __init__(
        self,
        loader: SeedDataLoader | None = None,
        generator: ReviewTemplateGenerator | None = None,
        product_seeder: ProductSeeder | None = None,
        review_seeder: ReviewSeeder | None = None,
        csv_writer: SeedCsvWriter | None = None,
    ) -> None:
        self._loader = loader or SeedDataLoader()
        self._generator = generator or ReviewTemplateGenerator()
        self._product_seeder = product_seeder
        self._review_seeder = review_seeder
        self._csv_writer = csv_writer or SeedCsvWriter()

    def run(self) -> tuple[int, list[dict], Path]:
        products = self._loader.load_products()
        if self._product_seeder is None or self._review_seeder is None:
            raise ValueError("DatabaseSeeder precisa dos seeders montados (ver main()).")
        self._product_seeder.seed(products)
        rows: list[dict] = []
        for item in products:
            rows.extend(self._generator.generate_for_product(item["id"]))
        self._review_seeder.seed(rows)
        csv_path = self._csv_writer.write(rows)
        return len(products), rows, csv_path


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        product_repo = ProductRepository(db)
        review_repo = ReviewRepository(db)
        prediction_repo = PredictionRepository(db)
        seeder = DatabaseSeeder(
            product_seeder=ProductSeeder(product_repo, review_repo, prediction_repo),
            review_seeder=ReviewSeeder(
                review_repo, prediction_repo, get_default_predictor()
            ),
        )
        n_products, rows, csv_path = seeder.run()
        counts = {
            label: sum(1 for r in rows if label_from_stars(r["stars"]) == label)
            for label in ("positive", "neutral", "negative")
        }
        print(f"[seed] {n_products} produtos, {len(rows)} reviews "
              f"(pos={counts['positive']} neu={counts['neutral']} "
              f"neg={counts['negative']})")
        print(f"[seed] CSV: {csv_path}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
