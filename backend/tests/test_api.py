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
