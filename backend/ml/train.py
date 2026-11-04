"""CLI fina de treino — só monta as dependências (DI manual) e treina.

Toda a lógica vive em `ml/training.py` (`ModelTrainer`) e `ml/datasets.py`
(fontes). Este módulo preserva a interface anterior:

    cd backend && python -m ml.train            # sintético
    cd backend && python -m ml.train --csv data/reviews_train.csv
    cd backend && python -m ml.train --olist     # usa Olist, se presente
                                                 # (data/olist_order_reviews_dataset.csv,
                                                 #  original do Kaggle, na pasta archive do Drive)
    cd backend && python -m ml.train --olist --b2w   # TREINO OFICIAL
                                                 # Olist + B2W (data/b2w_reviews.csv,
                                                 #  pasta archive-v2 do Drive)

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
    B2WReviewSource,
    CombinedReviewSource,
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
    "load_b2w",
    "load_olist",
    "load_dataset",
    "train",
]


def load_olist(path: Path | None = None) -> pd.DataFrame:
    """Compatibilidade: carrega o Olist (vazio se o CSV não existe)."""
    return OlistReviewSource(path).load()


def load_b2w(path: Path | None = None) -> pd.DataFrame:
    """Carrega o B2W-Reviews01 (vazio se o CSV não existe)."""
    return B2WReviewSource(path).load()


def load_dataset(
    csv_path: Path | None, use_olist: bool, use_b2w: bool = False
) -> pd.DataFrame:
    """Compatibilidade: escolhe a fonte e devolve o DataFrame rotulado."""
    source = choose_source(csv_path, use_olist, use_b2w)
    df = source.load()
    if df.empty and (use_olist or use_b2w):
        print("[dados] Arquivo(s) de treino não encontrado(s) em data/ — usando sintético.")
        df = SyntheticReviewSource().load()
    print(f"[dados] {len(df)} linhas de {source.name}")
    return df


def choose_source(
    csv_path: Path | None, use_olist: bool, use_b2w: bool = False
) -> ReviewDataSource:
    """Ordem de prioridade: CSV explícito > Olist+B2W > Olist > B2W > sintético."""
    if csv_path is not None and csv_path.exists():
        return CsvReviewSource(csv_path)
    if use_olist and use_b2w:
        return CombinedReviewSource([OlistReviewSource(), B2WReviewSource()])
    if use_olist:
        return OlistReviewSource()
    if use_b2w:
        return B2WReviewSource()
    return SyntheticReviewSource()


def train(
    csv_path: Path | None = None, use_olist: bool = False, use_b2w: bool = False
) -> dict:
    """Treina baseline, LogReg e MLP; devolve o relatório de métricas."""
    source = choose_source(csv_path, use_olist, use_b2w)
    if (use_olist or use_b2w) and source.load().empty:
        print("[dados] Arquivo(s) de treino não encontrado(s) em data/ — usando sintético.")
        source = SyntheticReviewSource()
    return ModelTrainer(source=source).train()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Treina o classificador de sentimento.")
    parser.add_argument("--csv", type=Path, default=None,
                        help="CSV com colunas text, stars")
    parser.add_argument("--olist", action="store_true",
                        help="usa data/olist_order_reviews_dataset.csv se existir")
    parser.add_argument("--b2w", action="store_true",
                        help="usa data/b2w_reviews.csv se existir (com --olist, treina Olist+B2W)")
    args = parser.parse_args()
    train(csv_path=args.csv, use_olist=args.olist, use_b2w=args.b2w)
