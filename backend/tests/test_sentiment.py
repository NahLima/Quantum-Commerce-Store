"""Testes do módulo de sentimento (TF-IDF + Regressão Logística)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.sentiment import label_from_stars, predict  # noqa: E402
from ml.train import build_vectorizer, generate_synthetic  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402


def test_label_from_stars():
    assert label_from_stars(1) == "negative"
    assert label_from_stars(2) == "negative"
    assert label_from_stars(3) == "neutral"
    assert label_from_stars(4) == "positive"
    assert label_from_stars(5) == "positive"


def test_logreg_trains_and_predicts_clear_cases():
    df = generate_synthetic(n_per_class=60, seed=7)
    vec = build_vectorizer()
    X = vec.fit_transform(df["text"])
    model = LogisticRegression(C=4.0,
                               class_weight="balanced", max_iter=1000,
                               random_state=42)
    model.fit(X, df["label"])
    pos = model.predict(vec.transform(
        ["Produto excelente, adorei, qualidade impecável, recomendo muito!"]))[0]
    neg = model.predict(vec.transform(
        ["Péssimo, produto horrível com defeito, não recomendo, decepção total"]))[0]
    assert pos == "positive", pos
    assert neg == "negative", neg


def test_predict_never_crashes_and_returns_valid_label():
    for text in ["Adorei o produto, excelente qualidade!",
                 "Horrível, veio quebrado e atrasado.",
                 "Ok, nada demais.", ""]:
        result = predict(text)
        assert result["label"] in ("positive", "neutral", "negative")
        assert 0.0 <= result["confidence"] <= 1.0
        assert abs(sum(result["probabilities"].values()) - 1.0) < 0.05
