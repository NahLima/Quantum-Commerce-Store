"""Aquece o cache de resumos com IA de todos os produtos.

Gera (uma vez) o resumo do Gemini para cada produto com pelo menos
`MIN_REVIEWS_FOR_AI_SUMMARY` avaliações e grava em `summaries`. Depois
disso, a página do produto serve o resumo do cache — sem esperar o LLM
na hora da visita.

Uso (da raiz do repo; o script fala com o banco direto):
    python backend/scripts/generate_summaries.py [--product 2] [--force]

A chave do Gemini vem do ambiente (`GEMINI_API_KEY`, mesmo valor do
`backend/.env`). Sem chave, o script avisa e sai sem fazer nada: o
endpoint continua devolvendo o resumo determinístico.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))  # backend/

# Pausa entre produtos: o free tier do Gemini limita requisições por
# minuto — sem ela, 50 chamadas em sequência esbarram no HTTP 429 e o
# aquecimento gera zero resumos. 7 s entre chamadas (~6/min) fica abaixo
# do limite; 50 produtos levam uns 8–10 minutos no total.
DELAY_BETWEEN_PRODUCTS_S = 7.0

from app.database import SessionLocal
from app.gemini_client import GeminiClient
from app.repositories import (
    ProductRepository,
    ReviewRepository,
    SummaryRepository,
)
from app.services import (
    MIN_REVIEWS_FOR_AI_SUMMARY,
    SentimentService,
    SummaryService,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product", type=int, help="Gerar só este produto.")
    parser.add_argument(
        "--force", action="store_true", help="Regerar mesmo com resumo em cache."
    )
    args = parser.parse_args()

    client = GeminiClient()
    if not client.available:
        print("GEMINI_API_KEY não definida — nada a gerar.")
        print("Defina a chave no ambiente (ou no backend/.env) e rode de novo.")
        return 1

    db = SessionLocal()
    try:
        products = ProductRepository(db)
        service = SummaryService(
            products,
            ReviewRepository(db),
            SummaryRepository(db),
            SentimentService(products, ReviewRepository(db)),
            client,
        )
        ids = [args.product] if args.product else [p.id for p in products.list()]
        generated = skipped = failed = 0
        for index, product_id in enumerate(ids):
            current = service.get_summary(product_id)
            if current.source == "gemini" and not args.force:
                skipped += 1
                continue
            if current.review_count < MIN_REVIEWS_FOR_AI_SUMMARY:
                failed += 1
                print(
                    f"produto {product_id}: poucas avaliações "
                    f"({current.review_count}, mínimo {MIN_REVIEWS_FOR_AI_SUMMARY})."
                )
            elif service.refresh_summary(product_id):
                generated += 1
                print(f"produto {product_id}: resumo gerado ({client.model}).")
            else:
                failed += 1
                print(
                    f"produto {product_id}: erro do Gemini "
                    f"({client.last_error or 'sem resposta'})."
                )
            if index < len(ids) - 1:
                time.sleep(DELAY_BETWEEN_PRODUCTS_S)
        print(f"gerados={generated} em cache={skipped} falhados={failed}")
        return 0 if failed == 0 else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
