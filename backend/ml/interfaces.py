"""Interfaces (abstrações) do domínio de ML.

Princípio aplicado (DIP / ISP): serviços e treino dependem destas
interfaces pequenas, nunca de implementações concretas. Trocar o modelo
ou a fonte de dados é criar uma nova classe que implementa a interface —
sem editar quem a consome (OCP).

    SentimentPredictor: qualquer classificador de texto (TF-IDF+LogReg,
        léxico, ou um futuro modelo) que devolva um PredictionResult.
    ReviewDataSource: qualquer fonte de reviews de treino (Olist, CSV,
        sintético) que devolva um DataFrame com colunas `text` e `stars`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class PredictionResult:
    """Resultado imutável de uma classificação de sentimento."""

    label: str
    label_pt: str
    probabilities: dict[str, float]
    confidence: float
    model_name: str
    model_version: str

    def to_dict(self) -> dict:
        """Serialização idêntica ao schema `PredictOut` da API."""
        return {
            "label": self.label,
            "label_pt": self.label_pt,
            "probabilities": dict(self.probabilities),
            "confidence": self.confidence,
            "model_name": self.model_name,
            "model_version": self.model_version,
        }


class ArtifactUnavailableError(Exception):
    """Artefatos treinados ausentes ou ilegíveis (usa-se o fallback)."""


class SentimentPredictor(ABC):
    """Contrato mínimo de um preditor de sentimento."""

    @abstractmethod
    def predict(self, text: str) -> PredictionResult:
        """Classifica `text` e nunca levanta exceção por falta de modelo."""

    @abstractmethod
    def is_available(self) -> bool:
        """True quando o preditor está pronto para uso."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome do modelo (ex.: "tfidf-logreg", "lexicon-fallback")."""


class ReviewDataSource(ABC):
    """Contrato mínimo de uma fonte de reviews de treino."""

    @abstractmethod
    def load(self) -> pd.DataFrame:
        """Devolve um DataFrame com colunas `text` (str) e `stars` (1-5).

        Pode devolver um DataFrame vazio quando a fonte não existe
        (ex.: CSV do Olist ainda não baixado) — quem escolhe o fallback
        é quem monta o treino, não a fonte.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome da fonte (ex.: "olist", "synthetic")."""
