"""Fachada de inferência — compatibilidade com o código anterior.

O comportamento público é o mesmo de antes:
    predict(text) -> dict com label, label_pt, probabilities, confidence,
                     model_name e model_version (nunca levanta exceção
                     por falta de modelo).

A implementação agora vive em `ml/predictors.py` (classes
`TfidfLogRegPredictor` / `CompositePredictor`) e as constantes em
`ml/labels.py`. Este módulo só delega, para que testes e código antigo
(`from ml.sentiment import predict, label_from_stars`) continuem válidos.
"""

from __future__ import annotations

from ml.labels import (
    LABEL_PT,
    LABELS,
    MODEL_DIR,
    MODEL_NAME,
    MODEL_VERSION,
    label_from_stars,
)
from ml.predictors import get_default_predictor

__all__ = [
    "LABEL_PT",
    "LABELS",
    "MODEL_DIR",
    "MODEL_NAME",
    "MODEL_VERSION",
    "label_from_stars",
    "predict",
]


def predict(text: str) -> dict:
    """Classifica um texto de review. Nunca quebra por falta de modelo."""
    return get_default_predictor().predict(text).to_dict()
