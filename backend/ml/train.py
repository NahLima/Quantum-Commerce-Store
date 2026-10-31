"""CLI fina de treino — só monta as dependências (DI manual) e treina.

Toda a lógica vive em `ml/training.py` (`ModelTrainer`) e `ml/datasets.py`
(fontes). Este módulo preserva a interface anterior:

    cd backend && python -m ml.train            # sintético
    cd backend && python -m ml.train --csv data/reviews_train.csv
    cd backend && python -m ml.train --olist     # usa Olist, se presente
                                                 # (data/olist_order_reviews_dataset.csv,
                                                 #  original do Kaggle, na pasta archive do Drive)

Funções mantidas por compatibilidade (testes e scripts antigos):
`build_vectorizer`, `generate_synthetic`, `load_olist`, `load_dataset`,
`train`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.datasets import (  # noqa: E402
    CsvReviewSource,
    OlistReviewSource,
    SyntheticReviewSource,
    generate_synthetic,
)
from ml.interfaces import ReviewDataSource  # noqa: E402
from ml.training import ModelTrainer, build_vectorizer  # noqa: E402

__all__ = [
    "build_vectorizer",
    "generate_synthetic",
    "load_olist",
    "load_dataset",
    "train",
]


def load_olist(path: Path | None = None) -> pd.DataFrame:
    """Compatibilidade: carrega o Olist (vazio se o CSV não existe)."""
    return OlistReviewSource(path).load()


def load_dataset(csv_path: Path | None, use_olist: bool) -> pd.DataFrame:
    """Compatibilidade: escolhe a fonte e devolve o DataFrame rotulado."""
    source = choose_source(csv_path, use_olist)
    df = source.load()
    if df.empty and use_olist:
        print("[dados] Olist não encontrado em data/olist_order_reviews_dataset.csv — usando sintético.")
        df = SyntheticReviewSource().load()
    print(f"[dados] {len(df)} linhas de {source.name}")
    return df


def choose_source(
    csv_path: Path | None, use_olist: bool
) -> ReviewDataSource:
    """Ordem de prioridade: CSV explícito > Olist (--olist) > sintético."""
    if csv_path is not None and csv_path.exists():
        return CsvReviewSource(csv_path)
    if use_olist:
        return OlistReviewSource()
    return SyntheticReviewSource()


def train(csv_path: Path | None = None, use_olist: bool = False) -> dict:
    """Treina baseline, LogReg e MLP; devolve o relatório de métricas."""
    source = choose_source(csv_path, use_olist)
    if use_olist and source.load().empty:
        print("[dados] Olist não encontrado em data/olist_order_reviews_dataset.csv — usando sintético.")
        source = SyntheticReviewSource()
    return ModelTrainer(source=source).train()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Treina o classificador de sentimento.")
    parser.add_argument("--csv", type=Path, default=None,
                        help="CSV com colunas text, stars")
    parser.add_argument("--olist", action="store_true",
                        help="usa data/olist_order_reviews_dataset.csv se existir")
    args = parser.parse_args()
    train(csv_path=args.csv, use_olist=args.olist)
