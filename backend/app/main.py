"""API FastAPI — Quantum Commerce: catálogo + sentimento de reviews.

Rotas finas: cada endpoint só recebe o serviço já montado por
`app/dependencies.py` e delega. Nada de SQL, agregação ou regra de
negócio aqui — isso vive em `app/services.py` e `app/repositories.py`.

Endpoints (contrato público, inalterado pela refatoração):
    GET  /health
    GET  /products[?category=][?search=]
    GET  /products/{id}
    GET  /products/{id}/sentiment   (agregado: % pos/neu/neg, média de estrelas,
                                     termos mais positivos/negativos)
    GET  /products/{id}/summary     (resumo em prosa: Gemini em cache, ou
                                     determinístico; gera em 2º plano se preciso)
    GET  /products/{id}/reviews
    POST /reviews                   (salva + prevê sentimento)
    POST /predict                   (classifica um texto avulso)
"""

from __future__ import annotations

from fastapi import BackgroundTasks, Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import Base, engine
from app.dependencies import (
    get_product_service,
    get_review_service,
    get_sentiment_service,
    get_summary_service,
)
from app.schemas import (
    PredictIn,
    PredictOut,
    ProductOut,
    ProductSummaryOut,
    ReviewIn,
    ReviewOut,
    SentimentSummary,
)
from app.services import (
    MIN_REVIEWS_FOR_AI_SUMMARY,
    ProductNotFoundError,
    ProductService,
    ReviewService,
    SentimentService,
    SummaryService,
)
from ml.labels import MODEL_DIR
from ml.predictors import TfidfLogRegPredictor

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Quantum Commerce — API de Sentimento",
    description="Catálogo + análise de sentimento em reviews (PT-BR). "
                "Trabalho final de ML — FIAP MBA 4AIER.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ProductNotFoundError)
def product_not_found_handler(
    request: Request, exc: ProductNotFoundError
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_dir": str(MODEL_DIR),
        "artifacts": TfidfLogRegPredictor().is_available(),
    }


@app.get("/products", response_model=list[ProductOut])
def list_products(
    category: str | None = None,
    search: str | None = None,
    service: ProductService = Depends(get_product_service),
):
    return service.list_products(category=category, search=search)


@app.get("/products/{product_id}", response_model=ProductOut)
def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
):
    return service.get_product(product_id)


@app.get("/products/{product_id}/reviews", response_model=list[ReviewOut])
def list_reviews(
    product_id: int,
    limit: int = 50,
    service: ReviewService = Depends(get_review_service),
):
    return service.list_reviews(product_id, limit=limit)


@app.get("/products/{product_id}/sentiment", response_model=SentimentSummary)
def product_sentiment(
    product_id: int,
    service: SentimentService = Depends(get_sentiment_service),
):
    return service.summarize(product_id)


@app.get("/products/{product_id}/summary", response_model=ProductSummaryOut)
def product_summary(
    product_id: int,
    background_tasks: BackgroundTasks,
    service: SummaryService = Depends(get_summary_service),
):
    """Resumo em prosa das avaliações do produto.

    Devolve o resumo em cache quando ele corresponde às avaliações atuais;
    caso contrário devolve a versão determinística na hora e agenda a
    geração com o Gemini em segundo plano (a próxima visita já vê o resumo
    com IA). Sem chave do Gemini, sempre devolve o determinístico.
    """
    out = service.get_summary(product_id)
    if (
        out.source == "deterministic"
        and out.review_count >= MIN_REVIEWS_FOR_AI_SUMMARY
        and service.gemini_available
    ):
        background_tasks.add_task(service.refresh_summary, product_id)
    return out


@app.post("/predict", response_model=PredictOut)
def predict_text(
    payload: PredictIn,
    service: ReviewService = Depends(get_review_service),
):
    return service.predict_text(payload.text)


@app.post("/reviews", response_model=ReviewOut, status_code=201)
def create_review(
    payload: ReviewIn,
    service: ReviewService = Depends(get_review_service),
):
    return service.create_review(payload)
