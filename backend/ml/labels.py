"""Constantes e regra de rotulagem do classificador de sentimento.

Este módulo é a única fonte de verdade para rótulos, nomes de modelo e
versão. Treino (`ml/training.py`), inferência (`ml/predictors.py`) e API
(`app/services.py`) importam daqui — nunca duplicam esses valores.

Rótulos (derivados das estrelas, regra do trabalho):
    estrelas 1-2 -> "negative" | 3 -> "neutral" | 4-5 -> "positive"
"""

from __future__ import annotations

import os
from pathlib import Path

LABELS: list[str] = ["negative", "neutral", "positive"]

LABEL_PT: dict[str, str] = {
    "negative": "negativo",
    "neutral": "neutro",
    "positive": "positivo",
}

MODEL_NAME = "tfidf-logreg"
MODEL_VERSION = "1.0.0"

MODEL_DIR = Path(os.getenv("MODEL_DIR", Path(__file__).parent / "artifacts"))

# Limites da regra de rotulagem por estrelas.
NEGATIVE_MAX_STARS = 2
NEUTRAL_STARS = 3


def label_from_stars(stars: int) -> str:
    """Converte estrelas (1-5) no rótulo de sentimento do trabalho."""
    if stars <= NEGATIVE_MAX_STARS:
        return "negative"
    if stars == NEUTRAL_STARS:
        return "neutral"
    return "positive"


def label_pt(label: str) -> str:
    """Rótulo em PT-BR (para exibição na UI)."""
    return LABEL_PT[label]
