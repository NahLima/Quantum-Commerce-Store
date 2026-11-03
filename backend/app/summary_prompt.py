"""Prompt do resumo de avaliações (geração com LLM).

O resumo estilo Mercado Livre ("As capas de almofada apresentam um visual
atraente... Contudo, há críticas quanto à fragilidade...") é um parágrafo
escrito a partir das avaliações do produto — só um modelo generativo
escreve assim. Este módulo é a única fonte do prompt, para o endpoint
(`GET /products/{id}/summary`) e para o caderno de destilação
(`notebooks/resumo-avaliacoes-mt5-colab.ipynb`) usarem exatamente as
mesmas regras.

Regra de ouro do projeto, herdada do RAG futuro: a geração só usa os
dados retornados (as avaliações do produto) e nunca inventa atributo,
preço, prazo ou defeito.
"""

from __future__ import annotations

MAX_REVIEWS_IN_PROMPT = 12


def build_summary_prompt(product_name: str, reviews: list[tuple[int, str]]) -> str:
    """Monta o prompt com as avaliações do produto.

    `reviews`: lista de (estrelas 1-5, texto), na ordem mais recente
    primeiro. Passa no máximo `MAX_REVIEWS_IN_PROMPT` avaliações.
    """
    shown = reviews[:MAX_REVIEWS_IN_PROMPT]
    lines = "\n".join(
        f"{i}. [{stars} estrelas] {text}" for i, (stars, text) in enumerate(shown, start=1)
    )
    return f"""Você resume avaliações de clientes de uma loja online, em português brasileiro.

PRODUTO: {product_name}

AVALIAÇÕES (nota de 1 a 5 + texto):
{lines}

REGRAS (obrigatórias):
- Escreva um parágrafo de 2 a 4 frases, em português brasileiro.
- Afirme SOMENTE o que está escrito nas avaliações acima. Não invente atributos, materiais, preços, prazos, defeitos ou elogios que não apareçam nelas.
- Comece pelos pontos positivos e, se houver críticas, apresente-as depois com "Contudo," ou "Por outro lado,".
- Se não houver críticas nas avaliações, não invente nenhuma.
- Se as avaliações se contradizem, diga isso (por exemplo: "as opiniões divergem sobre...").
- Não cite nomes de clientes nem copie frases inteiras: resuma com suas palavras.
- Não mencione quantidades de avaliações nem notas.

Escreva apenas o parágrafo do resumo, sem título e sem explicações:"""
