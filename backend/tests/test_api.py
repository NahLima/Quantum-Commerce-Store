"""Testes da API (TestClient, banco SQLite em memória via USE_SQLITE)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["USE_SQLITE"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Product  # noqa: E402
from app.database import SessionLocal  # noqa: E402

Base.metadata.create_all(bind=engine)
db = SessionLocal()
if db.query(Product).count() == 0:
    db.add(Product(id=1, name="Fone Orbit Pro", category="Tecnologia",
                   price_cents=8900, color="Rosa Névoa",
                   image_url="https://example.com/fone.jpg",
                   rating=4.5, reviews_count=18))
    db.commit()
db.close()

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_products():
    r = client.get("/products")
    assert r.status_code == 200
    products = r.json()
    assert len(products) >= 1
    assert products[0]["name"] == "Fone Orbit Pro"


def test_get_product_not_found():
    assert client.get("/products/99999").status_code == 404


def test_predict_fallback_returns_label():
    r = client.post("/predict", json={"text": "Produto excelente, adorei demais!"})
    assert r.status_code == 200
    body = r.json()
    assert body["label"] in ("positive", "neutral", "negative")
    assert body["probabilities"]["positive"] > body["probabilities"]["negative"]


def test_create_review_predicts_and_persists():
    r = client.post("/reviews", json={
        "product_id": 1, "author": "Teste", "stars": 5,
        "text": "Produto maravilhoso, qualidade impecável, recomendo!",
    })
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["label"] == "positive"
    r2 = client.get("/products/1/sentiment")
    assert r2.status_code == 200
    assert r2.json()["total_reviews"] >= 1
    assert r2.json()["counts"]["positive"] >= 1


def test_product_top_terms_use_only_the_product_texts():
    """Os termos do termômetro vêm das avaliações do produto, não do Olist inteiro."""
    from app.models import Review
    from app.services import ProductTopTerms

    reviews = [
        Review(product_id=1, author="A", stars=5,
               text="Adorei o tecido aveludado, macio e confortável."),
        Review(product_id=1, author="B", stars=5,
               text="Qualidade impecável, tecido aveludado, recomendo!"),
        Review(product_id=1, author="C", stars=1,
               text="O zíper emperrou e o tecido rasgou, péssima qualidade."),
    ]
    terms = ProductTopTerms()
    assert "aveludado" in terms.top_positive_terms(reviews)
    assert "tecido" in terms.top_positive_terms(reviews)
    assert "emperrou" in terms.top_negative_terms(reviews)
    assert "parabéns" not in terms.top_positive_terms(reviews)
    assert "parabéns" not in terms.top_negative_terms(reviews)


def test_sentiment_top_terms_come_from_the_product_reviews():
    """O endpoint de sentimento só cita palavras que as reviews do produto contêm,
    e o total do termômetro é igual à quantidade de reviews listadas."""
    r = client.get("/products/1/reviews?limit=100")
    assert r.status_code == 200
    listed = r.json()
    texts = " ".join(item["text"].lower() for item in listed)
    r2 = client.get("/products/1/sentiment")
    assert r2.status_code == 200
    body = r2.json()
    assert body["total_reviews"] == len(listed)
    for term in body["top_positive_terms"] + body["top_negative_terms"]:
        assert term in texts, f"termo {term!r} não aparece em nenhuma avaliação do produto"
    assert "parabéns" not in body["top_positive_terms"]
