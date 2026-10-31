"""Preditores de sentimento (implementações de `SentimentPredictor`).

    TfidfLogRegPredictor: modelo principal treinado (TF-IDF + Regressão
        Logística). Carrega os artefatos de `ml/artifacts/` sob demanda
        e os mantém em cache na instância.
    CompositePredictor: tenta o preditor principal e cai para o fallback
        (léxico) quando os artefatos não existem ou falham — por isso
        `POST /predict` nunca quebra.

Um novo modelo (ex.: outro classificador scikit-learn) é uma nova classe
neste arquivo implementando `SentimentPredictor`; nenhum serviço muda (OCP).
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib

from ml.interfaces import (
    ArtifactUnavailableError,
    PredictionResult,
    SentimentPredictor,
)
from ml.labels import LABEL_PT, LABELS, MODEL_DIR, MODEL_NAME, MODEL_VERSION
from ml.lexicon import LexiconFallbackPredictor

_VECTORIZER_FILE = "vectorizer.joblib"
_MODEL_FILE = "model_logreg.joblib"
_METRICS_FILE = "metrics.json"


class TfidfLogRegPredictor(SentimentPredictor):
    """TF-IDF + Regressão Logística, carregado dos artefatos do treino."""

    def __init__(self, model_dir: Path | None = None) -> None:
        self._model_dir = model_dir or MODEL_DIR
        self._artifacts: tuple | None = None
        self._loaded = False

    @property
    def name(self) -> str:
        return MODEL_NAME

    @property
    def model_dir(self) -> Path:
        return self._model_dir

    def is_available(self) -> bool:
        return (
            self._model_dir / _VECTORIZER_FILE
        ).exists() and (self._model_dir / _MODEL_FILE).exists()

    def predict(self, text: str) -> PredictionResult:
        cleaned = (text or "").strip()
        if not cleaned:
            return LexiconFallbackPredictor().predict("")
        vectorizer, model, model_version = self._load_artifacts()
        probabilities = self._probabilities(vectorizer, model, cleaned)
        label = max(probabilities, key=probabilities.get)
        return PredictionResult(
            label=label,
            label_pt=LABEL_PT[label],
            probabilities={k: round(probabilities[k], 3) for k in LABELS},
            confidence=round(probabilities[label], 3),
            model_name=MODEL_NAME,
            model_version=model_version,
        )

    def _load_artifacts(self) -> tuple:
        if self._loaded:
            if self._artifacts is None:
                raise ArtifactUnavailableError("Artefatos treinados ausentes.")
            return self._artifacts
        self._loaded = True
        try:
            vectorizer = joblib.load(self._model_dir / _VECTORIZER_FILE)
            model = joblib.load(self._model_dir / _MODEL_FILE)
            model_version = self._read_model_version()
        except Exception as exc:
            self._artifacts = None
            raise ArtifactUnavailableError(
                f"Não foi possível carregar os artefatos: {exc}"
            ) from exc
        self._artifacts = (vectorizer, model, model_version)
        return self._artifacts

    def _read_model_version(self) -> str:
        metrics_path = self._model_dir / _METRICS_FILE
        if metrics_path.exists():
            try:
                meta = json.loads(metrics_path.read_text(encoding="utf-8"))
                return str(meta.get("model_version", MODEL_VERSION))
            except (json.JSONDecodeError, OSError):
                pass
        return MODEL_VERSION

    @staticmethod
    def _probabilities(vectorizer, model, text: str) -> dict[str, float]:
        features = vectorizer.transform([text])
        raw = model.predict_proba(features)[0]
        probabilities = {c: float(p) for c, p in zip(model.classes_, raw)}
        for label in LABELS:
            probabilities.setdefault(label, 0.0)
        return probabilities


class CompositePredictor(SentimentPredictor):
    """Principal + fallback: nunca deixa a API sem resposta."""

    def __init__(
        self,
        primary: SentimentPredictor | None = None,
        fallback: SentimentPredictor | None = None,
    ) -> None:
        self._primary = primary or TfidfLogRegPredictor()
        self._fallback = fallback or LexiconFallbackPredictor()

    @property
    def name(self) -> str:
        return self._primary.name

    def is_available(self) -> bool:
        return True  # o fallback sempre está disponível

    def predict(self, text: str) -> PredictionResult:
        if not (text or "").strip():
            return self._fallback.predict(text)
        if not self._primary.is_available():
            return self._fallback.predict(text)
        try:
            return self._primary.predict(text)
        except (ArtifactUnavailableError, Exception):
            return self._fallback.predict(text)


_default_predictor: CompositePredictor | None = None


def get_default_predictor() -> CompositePredictor:
    """Singleton preguiçoso do preditor usado pela API e pelo seed."""
    global _default_predictor
    if _default_predictor is None:
        _default_predictor = CompositePredictor()
    return _default_predictor
