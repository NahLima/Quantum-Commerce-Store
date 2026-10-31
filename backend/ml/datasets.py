"""Fontes de dados de treino (implementações de `ReviewDataSource`).

    OlistReviewSource: dataset real (Brazilian E-Commerce Public Dataset,
        Kaggle — arquivo original `olist_order_reviews_dataset.csv`,
        99.224 linhas). Colunas reais: `review_comment_message`,
        `review_comment_title` e `review_score`; o texto usado é
        título + mensagem (o título salva 1.737 linhas que só têm
        título). Aceita também um arquivo já renomeado como
        `olist_reviews.csv` com colunas `review_text`/`review_score`.
        Devolve DataFrame vazio se nenhum arquivo existe.
    CsvReviewSource: qualquer CSV com colunas `text` e `stars`.
    SyntheticReviewSource: reviews PT-BR geradas de templates por
        sentimento — default para o trabalho rodar sem download externo.

Uma nova fonte (ex.: outro marketplace) é uma nova classe aqui, sem
mudar o treino (OCP). Todas devolvem o mesmo contrato: DataFrame com
colunas `text`, `stars` e `label`.
"""

from __future__ import annotations

import random
from pathlib import Path

import pandas as pd

from ml.interfaces import ReviewDataSource
from ml.labels import label_from_stars

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
# Nome original do Kaggle primeiro; aceita o nome curto como fallback.
OLIST_FILE = DATA_DIR / "olist_order_reviews_dataset.csv"
OLIST_FILE_SHORT = DATA_DIR / "olist_reviews.csv"

_COLUMNS = ["text", "stars"]


def _with_labels(df: pd.DataFrame) -> pd.DataFrame:
    df = df[["text", "stars"]].reset_index(drop=True)
    df["label"] = df["stars"].apply(label_from_stars)
    return df


class OlistReviewSource(ReviewDataSource):
    """Reviews reais do Olist (Kaggle, Brazilian E-Commerce).

    Esquema real do arquivo: `review_comment_message`,
    `review_comment_title`, `review_score`. O texto é título +
    mensagem (o título sozinho salva 1.737 linhas sem mensagem).
    Das 99.224 linhas, 42.687 têm título ou mensagem (56.537 não
    têm texto nenhum e são descartadas aqui — não dá para classificar
    sentimento de texto vazio).
    """

    def __init__(self, path: Path | None = None) -> None:
        if path is not None:
            self._path = path
        elif OLIST_FILE.exists():
            self._path = OLIST_FILE
        else:
            self._path = OLIST_FILE_SHORT

    @property
    def name(self) -> str:
        return "olist"

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> pd.DataFrame:
        if not self._path.exists():
            return pd.DataFrame(columns=_COLUMNS + ["label"])
        raw = pd.read_csv(self._path)
        if {"review_comment_message", "review_score"}.issubset(raw.columns):
            title = raw.get("review_comment_title", "").fillna("").astype(str)
            message = raw["review_comment_message"].fillna("").astype(str)
            df = pd.DataFrame(
                {
                    "text": (title.str.strip() + " " + message.str.strip()).str.strip(),
                    "stars": raw["review_score"],
                }
            )
        else:  # arquivo já renomeado com colunas review_text/review_score
            df = raw.rename(columns={"review_text": "text", "review_score": "stars"})
            df = df[["text", "stars"]].copy()
            df["text"] = df["text"].fillna("").astype(str).str.strip()
        df = df[df["text"] != ""].dropna(subset=["stars"])
        df["stars"] = df["stars"].astype(int).clip(1, 5)
        return _with_labels(df)


class CsvReviewSource(ReviewDataSource):
    """CSV genérico com colunas `text` e `stars`."""

    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def name(self) -> str:
        return f"csv:{self._path.name}"

    def load(self) -> pd.DataFrame:
        df = pd.read_csv(self._path)
        df = df.dropna(subset=["text", "stars"])
        df["stars"] = df["stars"].astype(int).clip(1, 5)
        return _with_labels(df)


class SyntheticReviewSource(ReviewDataSource):
    """Reviews sintéticas PT-BR, de templates por sentimento.

    Proporção realista de varejo: ~55% positivas, ~25% negativas,
    ~20% neutras. Os templates combinam elogio/crítica + aspecto
    (qualidade, entrega, preço, acabamento, embalagem, atendimento).
    """

    ASPECTS = [
        "a qualidade do produto", "o acabamento", "a entrega", "o preço",
        "a embalagem", "o atendimento", "o material", "o tamanho",
        "a cor", "o caimento", "a durabilidade", "o design",
    ]
    POSITIVE_TEMPLATES = [
        "Adorei! {a} superou minhas expectativas.",
        "Produto excelente, {a} é impecável.",
        "Chegou antes do prazo e {a} é ótima.",
        "Muito bom, recomendo sem dúvida.",
        "Superou o que eu esperava, {a} é perfeita.",
        "Qualidade acima da média, vale cada centavo.",
        "Lindo demais, exatamente como nas fotos.",
        "Perfeito! {a} maravilhosa, comprarei novamente.",
        "O produto é ótimo e o atendimento foi impecável.",
        "Tudo certo, entrega rápida e produto de qualidade.",
        "Estou muito satisfeita, vale muito a pena.",
        "Recomendo para todo mundo, excelente custo-benefício.",
        "Chegou bem embalado, sem nenhum defeito.",
        "Uso todos os dias, muito prático e bonito.",
    ]
    NEGATIVE_TEMPLATES = [
        "Péssimo, {a} é horrível, não recomendo.",
        "Produto com defeito, {a} veio danificada.",
        "Decepção total, {a} não é como nas fotos.",
        "Muito ruim, {a} deixou muito a desejar.",
        "Chegou atrasado e {a} é de péssima qualidade.",
        "Não vale o preço, {a} é frágil e quebrou rápido.",
        "Terrível, vou devolver, {a} é inaceitável.",
        "Produto veio errado e o atendimento não resolveu.",
        "Quebrou na primeira semana, dinheiro jogado fora.",
        "Veio manchado e com cheiro estranho, horrível.",
        "Demorou semanas para chegar e ainda veio danificado.",
        "Não recomendo, qualidade muito abaixo do anunciado.",
        "Fiquei muito insatisfeita, péssima experiência de compra.",
    ]
    NEUTRAL_TEMPLATES = [
        "Produto ok, {a} é razoável pelo preço.",
        "Nada demais, {a} cumpre o básico.",
        "Chegou no prazo, {a} é aceitável.",
        "É um produto mediano, nem bom nem ruim.",
        "Funciona como esperado, sem surpresas.",
        "Ok pelo preço, mas {a} poderia ser melhor.",
        "Não é ruim, mas também não é excelente.",
        "Atende o básico, nada de especial.",
        "Achei comum, esperava um pouco mais.",
        "Produto regular, entrega dentro do prazo.",
        "Cumpre o que promete, sem encantar.",
    ]
    # Multiplicadores da proporção por classe (base: n_per_class).
    CLASS_MULTIPLIERS = {"positive": 1.1, "negative": 0.55, "neutral": 0.4}
    STAR_RANGES = {"positive": (4, 5), "negative": (1, 2), "neutral": (3, 3)}
    EXTRA_SENTENCE_CHANCE = 0.35

    def __init__(self, n_per_class: int = 450, seed: int = 42) -> None:
        self._n_per_class = n_per_class
        self._seed = seed

    @property
    def name(self) -> str:
        return "synthetic"

    def load(self) -> pd.DataFrame:
        rng = random.Random(self._seed)
        pools = {
            "positive": self.POSITIVE_TEMPLATES,
            "negative": self.NEGATIVE_TEMPLATES,
            "neutral": self.NEUTRAL_TEMPLATES,
        }
        rows: list[dict] = []
        for label, multiplier in self.CLASS_MULTIPLIERS.items():
            for _ in range(int(self._n_per_class * multiplier)):
                text = self._render(rng, pools[label])
                if rng.random() < self.EXTRA_SENTENCE_CHANCE:
                    text = f"{text} {self._render(rng, pools[label])}"
                low, high = self.STAR_RANGES[label]
                rows.append(
                    {"text": text, "stars": rng.randint(low, high), "label": label}
                )
        rng.shuffle(rows)
        return pd.DataFrame(rows)

    def _render(self, rng: random.Random, templates: list[str]) -> str:
        template = rng.choice(templates)
        if "{a}" in template:
            return template.format(a=rng.choice(self.ASPECTS))
        return template


def generate_synthetic(n_per_class: int = 450, seed: int = 42) -> pd.DataFrame:
    """Compatibilidade: gera o dataset sintético (ver `SyntheticReviewSource`)."""
    return SyntheticReviewSource(n_per_class=n_per_class, seed=seed).load()
