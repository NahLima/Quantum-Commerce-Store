"""Testes do resumo de avaliações (TestClient, banco SQLite via USE_SQLITE).

O cliente do Gemini é trocado por um fake (override de `get_gemini_client`):
a cadeia real — rota, serviço, repositórios, cache — é exercida, só a
chamada de rede é simulada. Sem override, o endpoint devolve o resumo
determinístico (é o comportamento sem chave).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["USE_SQLITE"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.dependencies import get_gemini_client  # noqa: E402
from app.gemini_client import GeminiClient  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Product, Review  # noqa: E402
from app.schemas import SentimentSummary  # noqa: E402
from app.services import deterministic_summary  # noqa: E402
from app.summary_prompt import build_summary_prompt  # noqa: E402

Base.metadata.create_all(bind=engine)

TEST_PRODUCT_ID = 900
FAKE_SUMMARY = (
    "O fone apresenta um som limpo e um acabamento bonito, elogiado por "
    "quem comprou. Contudo, há críticas ao atraso na entrega."
)


def _seed_product_900() -> None:
    db = SessionLocal()
    try:
        if db.get(Product, TEST_PRODUCT_ID) is None:
            db.add(
                Product(
                    id=TEST_PRODUCT_ID,
                    name="Fone Teste Resumo",
                    category="Tecnologia",
                    price_cents=1000,
                    color="Preto",
                    image_url="https://example.com/fone.jpg",
                    rating=4.0,
                    reviews_count=3,
                )
            )
        db.query(Review).filter(Review.product_id == TEST_PRODUCT_ID).delete()
        db.query(Review).filter(Review.product_id == 901).delete()
        for stars, text in [
            (5, "Som limpo, acabamento bonito, adorei demais."),
            (5, "Chegou rápido, som ótimo, muito confortável."),
            (2, "Chegou atrasado e a embalagem veio amassada."),
        ]:
            db.add(
                Review(
                    product_id=TEST_PRODUCT_ID,
                    author="Teste",
                    stars=stars,
                    text=text,
                    source="test",
                )
            )
        if db.get(Product, 901) is None:
            db.add(
                Product(
                    id=901,
                    name="Fone Poucas Avaliações",
                    category="Tecnologia",
                    price_cents=1000,
                    color="Preto",
                    image_url="https://example.com/fone.jpg",
                    rating=5.0,
                    reviews_count=1,
                )
            )
        db.query(Review).filter(Review.product_id == 901).delete()
        db.add(
            Review(
                product_id=901,
                author="Teste",
                stars=5,
                text="Produto ótimo, gostei muito.",
                source="test",
            )
        )
        db.commit()
    finally:
        db.close()


_seed_product_900()


class FakeGemini:
    """Cliente fake: responde sempre o mesmo parágrafo, sem rede."""

    available = True
    model = "fake-gemini"

    def generate(self, prompt: str) -> str:
        assert "Fone Teste Resumo" in prompt
        return FAKE_SUMMARY


class FailingGemini:
    available = True
    model = "fake-gemini"

    def generate(self, prompt: str):
        return None


client = TestClient(app)


def test_prompt_contains_reviews_and_grounding_rules():
    prompt = build_summary_prompt(
        "Fone Teste",
        [(5, "Som limpo, adorei."), (2, "Chegou atrasado.")],
    )
    assert "Fone Teste" in prompt
    assert "Som limpo, adorei." in prompt
    assert "Chegou atrasado." in prompt
    assert "não invente" in prompt.lower()
    assert "Contudo" in prompt


def test_deterministic_summary_matches_frontend_rules():
    stats = SentimentSummary(
        product_id=TEST_PRODUCT_ID,
        total_reviews=3,
        avg_stars=4.0,
        counts={"positive": 2, "neutral": 0, "negative": 1},
        percentages={"positive": 66.7, "neutral": 0.0, "negative": 33.3},
        top_positive_terms=["som", "bonito"],
        top_negative_terms=["atrasado"],
    )
    text = deterministic_summary(stats)
    assert text.startswith("De 3 avaliações, 2 positivas, 0 neutras e 1 negativa.")
    assert "O que mais elogiam: som, bonito." in text
    assert "O que mais reclamam: atrasado." in text


def test_deterministic_summary_without_reviews():
    stats = SentimentSummary(
        product_id=TEST_PRODUCT_ID,
        total_reviews=0,
        avg_stars=None,
        counts={"positive": 0, "neutral": 0, "negative": 0},
        percentages={"positive": 0.0, "neutral": 0.0, "negative": 0.0},
    )
    assert deterministic_summary(stats) == "Ainda não há avaliações para este produto."


def test_gemini_client_unavailable_without_key():
    assert GeminiClient(api_key="").available is False
    assert GeminiClient(api_key="").generate("oi") is None


def test_gemini_client_parses_generate_content_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-goog-api-key"] == "fake-key"
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": "Resumo fake."}]}}
                ]
            },
        )

    client_gemini = GeminiClient(
        api_key="fake-key", transport=httpx.MockTransport(handler)
    )
    assert client_gemini.generate("prompt") == "Resumo fake."


def test_gemini_client_returns_none_on_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": {"message": "boom"}})

    client_gemini = GeminiClient(
        api_key="fake-key", transport=httpx.MockTransport(handler)
    )
    assert client_gemini.generate("prompt") is None


def test_summary_endpoint_without_key_returns_deterministic():
    r = client.get(f"/products/{TEST_PRODUCT_ID}/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["product_id"] == TEST_PRODUCT_ID
    assert body["source"] == "deterministic"
    assert body["review_count"] == 3
    assert body["cached"] is False
    assert body["summary"].startswith("De 3 avaliações")


def test_summary_endpoint_caches_fake_gemini_summary():
    app.dependency_overrides[get_gemini_client] = lambda: FakeGemini()
    try:
        # Primeira visita: sem cache, devolve o determinístico.
        r = client.get(f"/products/{TEST_PRODUCT_ID}/summary")
        assert r.status_code == 200
        assert r.json()["source"] == "deterministic"

        # Geração via endpoint: segunda visita já vê o resumo em cache,
        # gerado pela tarefa em 2º plano da primeira visita.
        r2 = client.get(f"/products/{TEST_PRODUCT_ID}/summary")
        assert r2.status_code == 200
        body = r2.json()
        assert body["source"] == "gemini"
        assert body["cached"] is True
        assert body["summary"] == FAKE_SUMMARY
        assert body["model"] == "fake-gemini"
    finally:
        app.dependency_overrides.pop(get_gemini_client, None)


def test_summary_endpoint_stale_cache_after_new_review():
    app.dependency_overrides[get_gemini_client] = lambda: FakeGemini()
    try:
        # Garante o cache cheio.
        client.get(f"/products/{TEST_PRODUCT_ID}/summary")
        client.get(f"/products/{TEST_PRODUCT_ID}/summary")
        assert client.get(f"/products/{TEST_PRODUCT_ID}/summary").json()["cached"] is True

        # Avaliação nova invalida o cache: volta o determinístico.
        r = client.post(
            "/reviews",
            json={
                "product_id": TEST_PRODUCT_ID,
                "author": "Teste",
                "stars": 5,
                "text": "Som perfeito, entrega rápida, recomendo demais.",
            },
        )
        assert r.status_code == 201
        body = client.get(f"/products/{TEST_PRODUCT_ID}/summary").json()
        assert body["source"] == "deterministic"
        assert body["cached"] is False
        assert body["review_count"] == 4
    finally:
        app.dependency_overrides.pop(get_gemini_client, None)
        _seed_product_900()


def test_summary_endpoint_failing_gemini_stays_deterministic():
    app.dependency_overrides[get_gemini_client] = lambda: FailingGemini()
    try:
        r = client.get(f"/products/{TEST_PRODUCT_ID}/summary")
        assert r.status_code == 200
        assert r.json()["source"] == "deterministic"
    finally:
        app.dependency_overrides.pop(get_gemini_client, None)


def test_summary_endpoint_few_reviews_never_uses_gemini():
    app.dependency_overrides[get_gemini_client] = lambda: FakeGemini()
    try:
        r = client.get("/products/901/summary")
        assert r.status_code == 200
        body = r.json()
        assert body["source"] == "deterministic"
        assert body["review_count"] == 1
        assert body["summary"].startswith("De 1 avaliação")
    finally:
        app.dependency_overrides.pop(get_gemini_client, None)


def test_summary_endpoint_product_not_found():
    assert client.get("/products/99999/summary").status_code == 404
