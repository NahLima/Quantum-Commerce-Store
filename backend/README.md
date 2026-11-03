# Quantum Commerce — Backend + ML

Trabalho final de Machine Learning (FIAP MBA, turma 4AIER) — **análise de
sentimento em reviews (PT-BR)**, com referência ao Mercado Livre.

Stack: Python 3.12, FastAPI, SQLAlchemy, Postgres 16 (Docker), scikit-learn.

## Arquitetura em camadas

```
docker-compose.yml      # postgres:16 + api (FastAPI :8000)
backend/
  app/
    main.py             # ROTAS finas: só recebem o serviço e delegam
    dependencies.py     # COMPOSIÇÃO RAIZ: monta repos/serviços/preditor (DI manual)
    schemas.py          # contratos Pydantic (ProductOut, ReviewIn/Out, Predict*, SentimentSummary)
    services.py         # REGRAS: ProductService, SentimentService, ReviewService, ProductTopTerms
    repositories.py     # DADOS: ProductRepository, ReviewRepository, PredictionRepository
    models.py           # Product, Review, Prediction (SQLAlchemy)
    database.py         # engine/sessão; Postgres por padrão, SQLite com USE_SQLITE=1
  ml/
    interfaces.py       # SentimentPredictor, ReviewDataSource, PredictionResult
    labels.py           # rótulos, MODEL_NAME/VERSION, label_from_stars (fonte única)
    predictors.py       # TfidfLogRegPredictor, CompositePredictor, get_default_predictor
    lexicon.py          # LexiconFallbackPredictor (fallback por léxico PT-BR)
    datasets.py         # OlistReviewSource, CsvReviewSource, SyntheticReviewSource
    training.py         # ModelTrainer, MetricsReporter, build_vectorizer
    train.py            # CLI fina de treino (monta a DI e chama o trainer)
    sentiment.py        # fachada predict() — compatibilidade com código antigo
    stopwords.py        # stopwords PT-BR inline
    artifacts/          # model_logreg.joblib, model_mlp.joblib, vectorizer.joblib,
                        # metrics.json, top_terms.json (gerados pelo treino)
  data/
    products.json       # 50 produtos extraídos do Figma (App.tsx)
    seed_reviews.csv    # gerado pelo seed (text, stars, product_id)
    olist_order_reviews_dataset.csv   # OPCIONAL: CSV do Olist (não versionado, ver "Treino com Olist")
  seed.py               # ProductSeeder + ReviewSeeder + DatabaseSeeder
  tests/                # pytest (8 testes)
```

Dependência entre camadas (só para baixo, nunca ao contrário):

```
main.py (rotas) → dependencies.py → services.py → repositories.py → models.py / database.py
services.py → ml/interfaces.py (abstrações) ← ml/predictors.py, ml/lexicon.py
training.py → ml/interfaces.py (ReviewDataSource) ← ml/datasets.py
```

## Como rodar (Mac)

```bash
# 1. subir Postgres + API (na RAIZ do repo)
cp .env.example .env                    # .env da raiz: o compose lê este
cp backend/.env.example backend/.env   # backend/.env: seed.py / uvicorn local
# ajuste POSTGRES_PASSWORD com a MESMA senha nos dois arquivos
docker compose up --build

# 2. popular o banco (em outro terminal)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python seed.py                          # 50 produtos + 234 reviews

# 3. treinar o modelo (gera ml/artifacts/)
python -m ml.train                     # sintético (~922 reviews)
python -m ml.train --olist             # com o Olist (ver abaixo)

# 4. rodar a API fora do Docker (opcional; o compose já sobe a API)
uvicorn app.main:app --reload --port 8000
```

Frontend (Next.js) roda separadamente: `cd frontend && npm run dev`
(consome `http://localhost:8000`).

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | status + presença dos artefatos |
| GET | `/products?category=&search=` | lista produtos (50 do Figma) |
| GET | `/products/{id}` | detalhe (404 se inexistente) |
| GET | `/products/{id}/sentiment` | % pos/neu/neg, média de estrelas, termos top |
| GET | `/products/{id}/summary` | resumo em prosa das avaliações (Gemini em cache, ou determinístico) |
| GET | `/products/{id}/reviews?limit=50` | reviews com predição (`label`, `confidence`) |
| POST | `/reviews` | salva review + prevê sentimento (201) |
| POST | `/predict` | `{text}` → `{label, label_pt, probabilities, confidence, model_name, model_version}` |

## Resumo de avaliações com IA

`GET /products/{id}/summary` devolve um parágrafo em prosa estilo
Mercado Livre (`{product_id, summary, source, model, review_count, cached}`).
`source` é `"gemini"` (resumo em cache) ou `"deterministic"` (fallback).

- **Geração:** `SummaryService` monta o prompt (`app/summary_prompt.py` —
  avaliações do produto + regras de fidelidade: só afirmar o que está nas
  avaliações, sem inventar atributo, preço ou defeito) e chama o Gemini
  (`app/gemini_client.py`, modelo `gemini-3.8-flash`, `temperature` 0.2).
  A chave vem de `GEMINI_API_KEY` no ambiente (ver `.env.example`); sem
  ela, o endpoint sempre devolve o determinístico — nunca quebra.
- **Cache:** o resumo é salvo na tabela `summaries` com o hash das
  avaliações atuais. Avaliação nova invalida o cache (o hash muda) e o
  endpoint devolve o determinístico na hora, agendando a regeneração em
  segundo plano (a próxima visita já vê o resumo com IA). Mínimo de 3
  avaliações para gerar com IA; abaixo disso, só o determinístico.
- **Aquecimento:** `python backend/scripts/generate_summaries.py`
  (da raiz do repo) gera o resumo de todos os produtos de uma vez, para a
  página nunca esperar o LLM. `--product N` gera só um; `--force` regera
  mesmo com cache.
- **Determinístico:** `deterministic_summary()` (em `app/services.py`)
  segue as mesmas regras do `buildReviewSummary` do front — contagens +
  termos mais citados. É o fallback em todos os casos (sem chave, LLM
  fora do ar, poucas avaliações, cache desatualizado).

## Modelo

- **Principal:** TF-IDF (1–2 gramas, max_features 8000, min_df 2,
  sublinear_tf, stopwords PT-BR) + Regressão Logística multinomial
  (C=4, class_weight=balanced).
- **Baseline:** classificador maioria.
- **Comparação:** MLPClassifier (128 neurônios, 1 camada oculta).
- **Rótulos:** estrelas 1–2 = negativo, 3 = neutro, 4–5 = positivo
  (regra única em `ml/labels.py::label_from_stars`).
- **Fallback:** se não houver artefato treinado, `/predict` usa o léxico
  PT-BR (`ml/lexicon.py`, com negação) — a API nunca quebra.

### Treino com Olist

```bash
# 1. baixe olist_order_reviews_dataset.csv do Kaggle
#    (Brazilian E-Commerce Public Dataset — o arquivo também está
#    na pasta `archive` do Drive da Quantum)
# 2. salve como backend/data/olist_order_reviews_dataset.csv
#    (o arquivo NÃO é versionado: está no .gitignore)
# 3. treine:
python -m ml.train --olist
```

O `OlistReviewSource` lê as colunas reais `review_comment_message`,
`review_comment_title` e `review_score` (texto = título + mensagem;
o título salva 1.737 linhas sem mensagem). Das 99.224 linhas, 42.687
têm texto. Sem o arquivo, `--olist` avisa e usa o sintético.

### Métricas

Último treino registrado: ver `ml/artifacts/metrics.json` — treino
real no Olist, 31/out/2026 (34.149 treino / 8.538 teste):

| modelo | accuracy | F1-macro |
|---|---|---|
| baseline maioria | 0,657 | 0,264 |
| **LogReg (principal)** | **0,780** | **0,635** |
| MLP (comparação) | 0,787 | 0,600 |

F1 por classe (LogReg): positiva 0,886, negativa 0,761, neutra 0,259
— a classe neutra (só 8,5% do treino) é o gargalo. A MLP ganha em
acurácia e perde em F1-macro; ela treina numa subamostra estratificada
de 12.000 linhas porque densifica o TF-IDF (`mlp_n_train` no
`metrics.json`), e o teste é o mesmo para os três modelos.

### Golden set Quantum (transferência para a loja)

Avaliação manual na loja, 01/nov/2026 — 24 avaliações novas em PT-BR
(8 por classe, produtos reais do Figma), rótulos aprovados pela
Naiara (G20, G21 e G23 mantidos neutros, por decisão dela). LogReg
treinado no Olist, sem re-treino (`eval/golden_set.csv`,
`eval/eval_golden_set.py`): **13/24 = 0,542** (positiva 6/8,
negativa 5/8, neutra 2/8), contra 0,780 de acurácia no teste do
Olist. A neutra é o gargalo — 5 dos 6 erros de neutra viraram
positiva (G19 → 0,904; G24 → 0,861). Os artefatos `*.joblib` não
são versionados; o script falha com mensagem clara sem eles
(`--model-dir` aponta os artefatos).

> **Aviso honesto:** o treino sintético de demonstração (922 linhas)
> dá F1 = 1,0 nos dois modelos — artefato dos templates que se
> sobrepõem, não resultado real. Não apresentar 1,0 como desempenho
> do modelo.

## Testes

```bash
cd backend && .venv/bin/python -m pytest tests/ -v
```

22 testes, todos com o banco SQLite em memória/fallback (`USE_SQLITE=1` é
setado em `tests/test_api.py` antes dos imports):

- `test_api.py`: health, listagem de produtos, 404, `/predict` (fallback),
  criar review + persistência da predição.
- `test_sentiment.py`: regra de rótulo por estrelas, LogReg treina e acerta
  casos claros, `predict()` nunca quebra (inclui texto vazio).
- `test_summary.py` (12): prompt do resumo (contém as avaliações e as
  regras de fidelidade), resumo determinístico, `GeminiClient` (sem chave
  → indisponível; resposta HTTP simulada), endpoint do resumo (cache,
  invalidação por avaliação nova, falha do LLM, poucas avaliações, 404).
  O cliente do Gemini é trocado por um fake (override de
  `get_gemini_client`); a cadeia real é exercida, só a rede é simulada.

## OOP, SOLID e Clean Code

O backend foi refatorado de um desenho procedural (schemas, SQL e agregação
misturados em `main.py`; funções soltas em `train.py` / `sentiment.py`)
para camadas com classes e interfaces, **sem mudar o contrato da API**
(mesmos endpoints e campos de resposta) e sem quebrar os 8 testes.

| Princípio | Onde |
|---|---|
| **S — Responsabilidade única** | `ProductRepository` só acessa dados; `ReviewService` só orquestra review+predição; `ModelTrainer` só treina; `MetricsReporter` só persiste/imprime métricas; `ProductTopTerms` só extrai termos das reviews do produto; cada seeder (`ProductSeeder`, `ReviewSeeder`) só popula uma tabela |
| **O — Aberto/fechado** | Novo modelo = nova classe implementando `SentimentPredictor` (`ml/interfaces.py`); nova fonte = nova classe implementando `ReviewDataSource`. Serviços e treino não mudam |
| **L — Substituição de Liskov** | `LexiconFallbackPredictor` e `TfidfLogRegPredictor` são intercambiáveis onde se espera `SentimentPredictor` (o `CompositePredictor` explora isso); `OlistReviewSource` / `CsvReviewSource` / `SyntheticReviewSource` são intercambiáveis onde se espera `ReviewDataSource` |
| **I — Segregação de interfaces** | `SentimentPredictor`: só `predict` / `is_available` / `name`. `ReviewDataSource`: só `load` / `name`. Nenhuma classe implementa o que não usa |
| **D — Inversão de dependência** | `ReviewService` recebe um `SentimentPredictor` (abstração), não o LogReg; `ModelTrainer` recebe um `ReviewDataSource`. Os concretos são montados num só lugar: `app/dependencies.py` (API) e a CLI de `ml/train.py` (treino) |

Clean code: nomes em inglês no código, métodos curtos, sem duplicação (a
regra de rótulo vive só em `ml/labels.py`; o cálculo de confiança da
predição, só em `app/services.py::prediction_confidence`), constantes
nomeadas em vez de números mágicos (`LOGREG_C`, `TFIDF_MAX_FEATURES`,
`MIN_REVIEWS_PER_PRODUCT`) e type hints em todo o código novo.

## Como estender

### Adicionar um novo preditor (ex.: outro classificador)

1. Crie a classe em `ml/predictors.py` (ou novo arquivo em `ml/`)
   implementando `SentimentPredictor` (`predict`, `is_available`, `name`).
2. Passe-a como `primary` do `CompositePredictor` em
   `ml/predictors.py::get_default_predictor` (ou injete outra instância em
   `app/dependencies.py::get_predictor`).
3. Nenhum serviço, rota ou teste muda — o contrato é o `PredictionResult`.

### Adicionar uma nova fonte de dados (ex.: outro marketplace)

1. Crie a classe em `ml/datasets.py` implementando `ReviewDataSource`
   (`load()` devolve DataFrame com `text`, `stars`, `label`).
2. Ensine `ml/train.py::choose_source` a escolhê-la (ex.: nova flag
   `--fonte`).
3. O `ModelTrainer` não muda.

### Adicionar um endpoint

1. Schema em `app/schemas.py` (se precisar de um novo contrato).
2. Regra em `app/services.py` (use repositórios, nunca SQL direto).
3. Rota fina em `app/main.py` delegando para o serviço via
   `app/dependencies.py` (adicione o `Depends` lá, se for um serviço novo).

## Limitações

- **Docker / Postgres não testados nesta VM** (não há Docker aqui). A
  validação real precisa acontecer no Mac (`docker compose up` + seed).
  Testes, treino e smoke test rodaram com SQLite (`USE_SQLITE=1`).
- **Olist não incluído no repo** (dataset externo do Kaggle). Sem ele, o
  treino usa o sintético e as métricas não são generalizáveis.
- **Não versionar:** `.venv/`, `app.db`, `*.joblib`, `.env`
  (ver `.gitignore`). Versionáveis: `metrics.json` e `top_terms.json`.
