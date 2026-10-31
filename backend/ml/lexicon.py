"""Preditor de fallback por léxico (PT-BR).

Usado quando os artefatos treinados não existem (ex.: antes do primeiro
treino). Regra simples e explicável: conta palavras positivas/negativas,
com tratamento de negação ("não gostei" inverte o sentido).

Implementa `SentimentPredictor`, por isso é substituível por qualquer
outro preditor sem tocar nos serviços (LSP).
"""

from __future__ import annotations

import re

from ml.interfaces import PredictionResult, SentimentPredictor
from ml.labels import LABEL_PT, LABELS

_POSITIVE_WORDS = {
    "excelente", "ótimo", "otimo", "perfeito", "maravilhoso", "incrível",
    "incrivel", "adorei", "amei", "recomendo", "impecável", "impecavel",
    "qualidade", "lindo", "linda", "bonito", "bonita", "confortável",
    "confortavel", "prático", "pratico", "rápido", "rapido", "ótima",
    "otima", "superou", "expectativas", "satisfeito", "satisfeita",
    "vale", "pena", "top", "show", "maravilha", "fantástico", "fantastico",
    "resistente", "durável", "duravel", "elegante", "sofisticado",
    "funciona", "perfeita", "ótimos", "otimos", "adoro", "gostei",
}

_NEGATIVE_WORDS = {
    "péssimo", "pessimo", "horrível", "horrivel", "ruim", "decepcionante",
    "decepção", "decepcao", "frágil", "fragil", "quebrou", "defeito",
    "problema", "atraso", "atrasou", "demorou", "nunca", "lixo",
    "terrível", "terrivel", "insatisfeito", "insatisfeita", "reclamo",
    "devolver", "devolvi", "trocar", "troquei", "danificado", "danificada",
    "manchado", "rasgado", "falha", "errado", "pior", "desgaste",
    "desbotou", "soltou", "frouxo", "aperto", "desconfortável",
    "desconfortavel",
}

# "não"/"nunca" sozinhos são negação, não sentimento: só contam quando
# acompanham outra palavra; por isso a negação é tratada à parte.
_NEGATIONS = {"não", "nao", "nunca", "jamais", "nem"}

_WORD_RE = re.compile(r"[a-zà-ú]+")

_NEUTRAL_PROBABILITIES = {"negative": 0.2, "neutral": 0.6, "positive": 0.2}


class LexiconFallbackPredictor(SentimentPredictor):
    """Classificador por contagem de palavras do léxico."""

    MODEL_NAME = "lexicon-fallback"
    MODEL_VERSION = "0.1.0"

    @property
    def name(self) -> str:
        return self.MODEL_NAME

    def is_available(self) -> bool:
        return True  # o léxico não depende de arquivo nenhum

    def predict(self, text: str) -> PredictionResult:
        words = _WORD_RE.findall((text or "").lower())
        positive_count, negative_count = self._count_with_negation(words)
        label, probabilities = self._to_result(positive_count, negative_count)
        return PredictionResult(
            label=label,
            label_pt=LABEL_PT[label],
            probabilities=probabilities,
            confidence=probabilities[label],
            model_name=self.MODEL_NAME,
            model_version=self.MODEL_VERSION,
        )

    @staticmethod
    def _count_with_negation(words: list[str]) -> tuple[int, int]:
        positive_count = negative_count = 0
        for index, word in enumerate(words):
            negated = index > 0 and words[index - 1] in _NEGATIONS
            if word in _POSITIVE_WORDS:
                if negated:
                    negative_count += 1
                else:
                    positive_count += 1
            elif word in _NEGATIVE_WORDS:
                if negated:
                    positive_count += 1
                else:
                    negative_count += 1
        return positive_count, negative_count

    @staticmethod
    def _to_result(
        positive_count: int, negative_count: int
    ) -> tuple[str, dict[str, float]]:
        total = positive_count + negative_count
        if total == 0:
            return "neutral", dict(_NEUTRAL_PROBABILITIES)
        positive_share = positive_count / total
        negative_share = negative_count / total
        probabilities = {
            "positive": round(0.1 + 0.8 * positive_share, 3),
            "negative": round(0.1 + 0.8 * negative_share, 3),
            "neutral": round(0.1 * (1 - abs(positive_share - negative_share)), 3),
        }
        total_prob = sum(probabilities.values())
        probabilities = {k: round(v / total_prob, 3) for k, v in probabilities.items()}
        if positive_count > negative_count:
            label = "positive"
        elif negative_count > positive_count:
            label = "negative"
        else:
            label = "neutral"
        return label, {k: probabilities[k] for k in LABELS}
