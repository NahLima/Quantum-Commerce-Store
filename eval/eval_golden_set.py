"""Avalia o classificador de sentimento no golden set manual da Quantum.

    O golden set (`eval/golden_set.csv`) são 24 avaliações novas em PT-BR,
    escritas para este teste (não copiadas do seed de demonstração nem do
    Olist), ligadas a produtos reais do Figma, 8 por classe, com rótulos
    aprovados pela Naiara (01/nov/2026 — G20, G21 e G23 mantidos neutros).
    O script roda o preditor principal (TF-IDF + Regressão Logística,
    treinado no Olist) sobre cada item e imprime acurácia geral e por
    classe — sem re-treinar nada.

    Uso (a partir da raiz do repo):

        python eval/eval_golden_set.py
        python eval/eval_golden_set.py --model-dir /caminho/para/artifacts
        python eval/eval_golden_set.py --csv eval/golden_set.csv --errors

    Os artefatos `*.joblib` não são versionados (ver `.gitignore`); o
    `--model-dir` padrão é `backend/ml/artifacts/`. Quando os artefatos
    não existem, o script falha com mensagem clara em vez de avaliar
    com o fallback de léxico — o número do golden set só vale com o
    modelo treinado.

    Resultado registrado (01/nov/2026): 13/24 = 0,542 (positiva 6/8,
    negativa 5/8, neutra 2/8), contra 0,780 de acurácia no teste do
    Olist. A classe neutra é o gargalo.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from ml.interfaces import SentimentPredictor  # noqa: E402
from ml.labels import LABELS, LABEL_PT  # noqa: E402
from ml.predictors import TfidfLogRegPredictor  # noqa: E402

_DEFAULT_CSV = Path(__file__).resolve().parent / "golden_set.csv"
_DEFAULT_MODEL_DIR = (
    Path(__file__).resolve().parent.parent / "backend" / "ml" / "artifacts"
)


@dataclass(frozen=True)
class GoldenSetItem:
    """Um item do golden set: texto e o rótulo esperado (aprovado)."""

    item_id: str
    text: str
    expected: str


@dataclass(frozen=True)
class ItemResult:
    """O que o preditor disse sobre um item do golden set."""

    item: GoldenSetItem
    predicted: str
    confidence: float

    @property
    def correct(self) -> bool:
        return self.predicted == self.item.expected


@dataclass
class EvaluationReport:
    """Resultado da avaliação: acerto geral, por classe e os erros."""

    results: list[ItemResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def correct(self) -> int:
        return sum(1 for r in self.results if r.correct)

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0

    def per_class(self) -> dict[str, tuple[int, int]]:
        """{rótulo: (acertos, total)} — rótulo esperado."""
        counts: dict[str, list[int]] = {label: [0, 0] for label in LABELS}
        for result in self.results:
            counts[result.item.expected][1] += 1
            if result.correct:
                counts[result.item.expected][0] += 1
        return {label: (c[0], c[1]) for label, c in counts.items()}

    @property
    def errors(self) -> list[ItemResult]:
        return [r for r in self.results if not r.correct]


class GoldenSetLoader:
    """Lê o CSV do golden set. Só conhece o formato do arquivo."""

    def __init__(self, csv_path: Path) -> None:
        self._csv_path = csv_path

    def load(self) -> list[GoldenSetItem]:
        with self._csv_path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        items = []
        for row in rows:
            expected = row["rotulo_esperado"].strip()
            if expected not in LABELS:
                raise ValueError(
                    f"Rótulo inválido no golden set ({row['id']}): {expected!r}"
                )
            items.append(
                GoldenSetItem(
                    item_id=row["id"].strip(),
                    text=row["texto"].strip(),
                    expected=expected,
                )
            )
        if not items:
            raise ValueError(f"Golden set vazio: {self._csv_path}")
        return items


class GoldenSetEvaluator:
    """Avalia um preditor no golden set. Depende só da abstração
    `SentimentPredictor` — qualquer modelo pode ser avaliado aqui."""

    def __init__(self, predictor: SentimentPredictor) -> None:
        self._predictor = predictor

    def evaluate(self, items: list[GoldenSetItem]) -> EvaluationReport:
        results = []
        for item in items:
            prediction = self._predictor.predict(item.text)
            results.append(
                ItemResult(
                    item=item,
                    predicted=prediction.label,
                    confidence=prediction.confidence,
                )
            )
        return EvaluationReport(results=results)


class ReportPrinter:
    """Imprime o relatório da avaliação. Só formata texto."""

    def print(self, report: EvaluationReport, *, show_errors: bool) -> None:
        print(f"Golden set: {report.total} itens")
        print(f"Acerto geral: {report.correct}/{report.total} = {report.accuracy:.3f}")
        print()
        print(f"{'classe':<10} {'acerto':>7}")
        for label in LABELS:
            correct, total = report.per_class()[label]
            print(f"{LABEL_PT[label]:<10} {correct}/{total}")
        if show_errors:
            print()
            print(f"Erros ({len(report.errors)}):")
            for result in report.errors:
                item = result.item
                print(
                    f"  {item.item_id} esperado={LABEL_PT[item.expected]}"
                    f" previsto={LABEL_PT[result.predicted]}"
                    f" conf={result.confidence:.3f} :: {item.text}"
                )


def build_predictor(model_dir: Path) -> TfidfLogRegPredictor:
    """Monta o preditor LogReg. Falha com mensagem clara sem artefatos."""
    predictor = TfidfLogRegPredictor(model_dir=model_dir)
    if not predictor.is_available():
        raise SystemExit(
            "Artefatos do modelo não encontrados em "
            f"{model_dir} (vectorizer.joblib / model_logreg.joblib).\n"
            "Gere-os com: cd backend && python -m ml.train --olist\n"
            "ou aponte --model-dir para o diretório com os artefatos."
        )
    return predictor


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Avalia o LogReg treinado no Olist no golden set Quantum."
    )
    parser.add_argument(
        "--csv", type=Path, default=_DEFAULT_CSV,
        help="CSV do golden set (padrão: eval/golden_set.csv)",
    )
    parser.add_argument(
        "--model-dir", type=Path, default=_DEFAULT_MODEL_DIR,
        help="Diretório com os artefatos treinados (padrão: backend/ml/artifacts/)",
    )
    parser.add_argument(
        "--errors", action="store_true",
        help="lista os itens errados com previsto e confiança",
    )
    args = parser.parse_args(argv)

    items = GoldenSetLoader(args.csv).load()
    report = GoldenSetEvaluator(build_predictor(args.model_dir)).evaluate(items)
    ReportPrinter().print(report, show_errors=args.errors)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
