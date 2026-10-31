"""Treino do classificador de sentimento (PT-BR).

Modelos comparados (todos sobre o mesmo TF-IDF):
    1. Baseline maioria — prevê sempre a classe majoritária.
    2. Regressão Logística multinomial (MODELO PRINCIPAL).
    3. MLPClassifier (128 neurônios) — rede neural simples, para comparação.

`ModelTrainer` recebe um `ReviewDataSource` e treina a partir dele: a
fonte (Olist, CSV ou sintético) é intercambiável sem mudar o treino (DIP).
`MetricsReporter` é a única responsável por persistir e imprimir os
resultados — o trainer não escreve arquivo nem imprime relatório.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier

from ml.datasets import SyntheticReviewSource
from ml.interfaces import ReviewDataSource
from ml.labels import LABELS, MODEL_VERSION
from ml.stopwords import PT_STOPWORDS

RANDOM_STATE = 42
TEST_SIZE = 0.2

TFIDF_MAX_FEATURES = 8000
TFIDF_MIN_DF = 2

LOGREG_C = 4.0
LOGREG_MAX_ITER = 1000

MLP_HIDDEN_LAYERS = (128,)
MLP_MAX_ITER = 300
# A MLP do scikit-learn não trabalha com matriz esparsa: ela densifica
# o TF-IDF. Com o Olist (~34 mil linhas de treino x 8.000 features),
# densificar tudo passaria de 2 GB. A MLP treina então numa subamostra
# estratificada (o teste continua sendo o mesmo para os três modelos,
# então a comparação segue válida). Registrado em `mlp_n_train`.
MLP_MAX_TRAIN_ROWS = 12_000

TOP_TERMS_PER_CLASS = 15

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
VECTORIZER_FILE = "vectorizer.joblib"
LOGREG_FILE = "model_logreg.joblib"
MLP_FILE = "model_mlp.joblib"
METRICS_FILE = "metrics.json"
TOP_TERMS_FILE = "top_terms.json"


def build_vectorizer() -> TfidfVectorizer:
    """TF-IDF usado pelo treino e pela inferência (mesma configuração)."""
    return TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=TFIDF_MAX_FEATURES,
        min_df=TFIDF_MIN_DF,
        sublinear_tf=True,
        stop_words=PT_STOPWORDS,
        lowercase=True,
    )


class ModelTrainer:
    """Treina baseline, LogReg e MLP a partir de uma fonte de reviews."""

    def __init__(
        self,
        source: ReviewDataSource | None = None,
        artifacts_dir: Path | None = None,
        random_state: int = RANDOM_STATE,
    ) -> None:
        self._source = source or SyntheticReviewSource()
        self._artifacts_dir = artifacts_dir or ARTIFACTS_DIR
        self._random_state = random_state
        self._mlp_model = None

    @property
    def source_name(self) -> str:
        return self._source.name

    def train(self) -> dict:
        """Treina os três modelos e devolve o relatório de métricas."""
        df = self._source.load()
        train_texts, test_texts, train_labels, test_labels = train_test_split(
            df["text"],
            df["label"],
            test_size=TEST_SIZE,
            random_state=self._random_state,
            stratify=df["label"],
        )
        vectorizer = build_vectorizer()
        train_features = vectorizer.fit_transform(train_texts)
        test_features = vectorizer.transform(test_texts)

        results: dict = {
            "model_version": MODEL_VERSION,
            "n_train": len(train_texts),
            "n_test": len(test_texts),
            "labels": LABELS,
            "class_distribution": df["label"].value_counts().to_dict(),
            "source": self._source.name,
        }
        results["baseline_majority"] = self._train_baseline(
            train_features, train_labels, test_features, test_labels
        )
        logreg = self._train_logreg(
            train_features, train_labels, test_features, test_labels, results
        )
        self._train_mlp(
            train_features, train_labels, test_features, test_labels, results
        )
        terms = self._top_terms(vectorizer, logreg)
        MetricsReporter(self._artifacts_dir).write(
            results, terms, vectorizer, logreg, self._mlp_model
        )
        return results

    def _train_baseline(self, train_features, train_labels, test_features, test_labels):
        dummy = DummyClassifier(strategy="most_frequent").fit(
            train_features, train_labels
        )
        predictions = dummy.predict(test_features)
        return self._scores(test_labels, predictions)

    def _train_logreg(self, train_features, train_labels, test_features, test_labels, results):
        logreg = LogisticRegression(
            C=LOGREG_C,
            class_weight="balanced",
            max_iter=LOGREG_MAX_ITER,
            random_state=self._random_state,
        )
        logreg.fit(train_features, train_labels)
        results["logreg"] = self._detailed_scores(test_labels, logreg.predict(test_features))
        return logreg

    def _train_mlp(self, train_features, train_labels, test_features, test_labels, results):
        self._mlp_model = MLPClassifier(
            hidden_layer_sizes=MLP_HIDDEN_LAYERS,
            max_iter=MLP_MAX_ITER,
            random_state=self._random_state,
        )
        mlp_train_features, mlp_train_labels = train_features, train_labels
        if train_features.shape[0] > MLP_MAX_TRAIN_ROWS:
            from sklearn.model_selection import train_test_split as _split

            mlp_train_features, _, mlp_train_labels, _ = _split(
                train_features,
                train_labels,
                train_size=MLP_MAX_TRAIN_ROWS,
                random_state=self._random_state,
                stratify=train_labels,
            )
        results["mlp_n_train"] = int(mlp_train_features.shape[0])
        self._mlp_model.fit(mlp_train_features, mlp_train_labels)
        results["mlp"] = self._detailed_scores(
            test_labels, self._mlp_model.predict(test_features)
        )

    @staticmethod
    def _scores(test_labels, predictions) -> dict:
        return {
            "accuracy": round(accuracy_score(test_labels, predictions), 4),
            "f1_macro": round(f1_score(test_labels, predictions, average="macro"), 4),
        }

    @staticmethod
    def _detailed_scores(test_labels, predictions) -> dict:
        scores = ModelTrainer._scores(test_labels, predictions)
        scores["per_class"] = classification_report(
            test_labels, predictions, output_dict=True, zero_division=0
        )
        scores["confusion_matrix"] = confusion_matrix(
            test_labels, predictions, labels=LABELS
        ).tolist()
        return scores

    @staticmethod
    def _top_terms(vectorizer, model, n: int = TOP_TERMS_PER_CLASS) -> dict:
        features = vectorizer.get_feature_names_out()
        terms: dict[str, dict[str, list[str]]] = {}
        for index, label in enumerate(model.classes_):
            coefficients = model.coef_[index]
            order = coefficients.argsort()
            terms[label] = {
                "positive": [features[j] for j in order[-n:][::-1]],
                "negative": [features[j] for j in order[:n]],
            }
        return terms


class MetricsReporter:
    """Persiste artefatos/métricas e imprime o resumo do treino."""

    def __init__(self, artifacts_dir: Path | None = None) -> None:
        self._artifacts_dir = artifacts_dir or ARTIFACTS_DIR

    def write(self, results, terms, vectorizer, logreg, mlp) -> None:
        self._artifacts_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(vectorizer, self._artifacts_dir / VECTORIZER_FILE)
        joblib.dump(logreg, self._artifacts_dir / LOGREG_FILE)
        joblib.dump(mlp, self._artifacts_dir / MLP_FILE)
        self._write_json(METRICS_FILE, results)
        self._write_json(TOP_TERMS_FILE, terms)
        self._print_summary(results)

    def _write_json(self, filename: str, payload: dict) -> None:
        (self._artifacts_dir / filename).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @staticmethod
    def _print_summary(results: dict) -> None:
        print(f"\n[treino] n_train={results['n_train']} n_test={results['n_test']}")
        for key in ("baseline_majority", "logreg", "mlp"):
            metrics = results[key]
            print(f"  {key:20s} acc={metrics['accuracy']:.4f}  "
                  f"f1_macro={metrics['f1_macro']:.4f}")
        print(f"[artefatos] {ARTIFACTS_DIR}")
