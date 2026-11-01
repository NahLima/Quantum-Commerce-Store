// Helpers tipados para falar com a API FastAPI (backend Python).
// Todas as funções são tolerantes a falha: se a API estiver fora do ar,
// devolvem null/false e o front cai para os dados locais (src/lib/products.ts
// e src/lib/reviews.ts). O site NUNCA quebra por causa da API.
//
// Contrato real do backend (verificado contra backend/app/main.py + schemas.py):
//   POST /predict   { "text": "..." } -> { "label": "positive"|"neutral"|"negative",
//     "label_pt": "positiva"|"neutra"|"negativa", "probabilities": {...},
//     "confidence": 0.93, "model_name": "...", "model_version": "1.0.0" }
//   GET  /products/{id}/sentiment -> { "product_id": 1, "total_reviews": 6,
//     "avg_stars": 4.33, "counts": {"positive": 5, "neutral": 1, "negative": 0},
//     "percentages": {"positive": 83.3, ...},
//     "top_positive_terms": [...], "top_negative_terms": [...] }
//   GET  /products/{id}/reviews -> [{ "id": 1, "product_id": 1, "author": "...",
//     "stars": 5, "text": "...", "source": "seed", "label": "positive",
//     "confidence": 0.95 }]
//   POST /reviews    { "product_id": 1, "author": "...", "stars": 5, "text": "..." } -> 201
// As respostas são lidas de forma flexível (aceita label/sentimento/sentiment,
// confidence/confianca/probability...), porque o backend está em construção
// em paralelo.

import type { Review, SentimentLabel, SentimentStats } from './reviews';

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'http://localhost:8000';

export type Prediction = {
  label: SentimentLabel;
  confidence: number;
  model?: string;
};

export type ProductSentiment = {
  stats: SentimentStats;
  reviews?: Review[];
};

function normalizeLabel(raw: unknown): SentimentLabel | null {
  if (typeof raw !== 'string') return null;
  const v = raw.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  if (v.includes('pos')) return 'positiva';
  if (v.includes('neg')) return 'negativa';
  if (v.includes('neu')) return 'neutra';
  return null;
}

function normalizeConfidence(raw: unknown): number {
  const n = typeof raw === 'number' ? raw : Number(raw);
  if (!Number.isFinite(n)) return 0;
  // Aceita 0–1 ou 0–100.
  return n > 1 ? Math.min(100, n) / 100 : Math.max(0, Math.min(1, n));
}

async function fetchJson(input: string, init?: RequestInit, timeoutMs = 8000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(input, { ...init, signal: controller.signal });
    if (!res.ok) return null;
    return (await res.json()) as unknown;
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

/** Classifica um texto em tempo real (usado no formulário "Escreva sua avaliação"). */
export async function predictSentiment(text: string): Promise<Prediction | null> {
  const paths = ['/predict', '/api/predict'];
  for (const path of paths) {
    const data = await fetchJson(`${API_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    if (!data || typeof data !== 'object') continue;
    const d = data as Record<string, unknown>;
    const label = normalizeLabel(d.label ?? d.sentimento ?? d.sentiment ?? d.prediction ?? d.predicao);
    if (!label) continue;
    return {
      label,
      confidence: normalizeConfidence(
        d.confidence ?? d.confianca ?? d.probability ?? d.probabilidade ?? d.score,
      ),
      model: typeof d.model === 'string' ? d.model : undefined,
    };
  }
  return null;
}

function toReview(raw: unknown, productId: number, index: number): Review | null {
  if (!raw || typeof raw !== 'object') return null;
  const r = raw as Record<string, unknown>;
  const sentiment = normalizeLabel(r.sentiment ?? r.sentimento ?? r.label);
  if (!sentiment) return null;
  return {
    id: typeof r.id === 'string' || typeof r.id === 'number' ? String(r.id) : `api-${productId}-${index}`,
    productId,
    author: typeof r.author === 'string' ? r.author : typeof r.autor === 'string' ? r.autor : 'Cliente',
    date:
      typeof r.date === 'string'
        ? r.date
        : typeof r.data === 'string'
          ? r.data
          : typeof r.created_at === 'string'
            ? r.created_at.slice(0, 10)
            : '',
    // Backend usa `stars` (1-5); `rating`/`estrelas` ficam como fallback legado.
    rating:
      typeof r.stars === 'number'
        ? r.stars
        : typeof r.rating === 'number'
          ? r.rating
          : typeof r.estrelas === 'number'
            ? r.estrelas
            : 5,
    text: typeof r.text === 'string' ? r.text : typeof r.texto === 'string' ? r.texto : '',
    sentiment,
    confidence: normalizeConfidence(r.confidence ?? r.confianca ?? 0.9),
    verified: r.verified !== false,
  };
}

function toStats(raw: Record<string, unknown>, reviews: Review[]): SentimentStats {
  // Backend real: { total_reviews, counts: {positive, neutral, negative},
  //   percentages: {positive, neutral, negative}, avg_stars }.
  const counts =
    raw.counts && typeof raw.counts === 'object'
      ? (raw.counts as Record<string, unknown>)
      : {};
  const percentages =
    raw.percentages && typeof raw.percentages === 'object'
      ? (raw.percentages as Record<string, unknown>)
      : {};
  const countOf = (key: string, legacy: string): number => {
    if (typeof counts[key] === 'number') return counts[key] as number;
    if (typeof raw[key] === 'number') return raw[key] as number;
    if (typeof raw[legacy] === 'number') return raw[legacy] as number;
    return reviews.filter((r) =>
      key === 'positive'
        ? r.sentiment === 'positiva'
        : key === 'neutral'
          ? r.sentiment === 'neutra'
          : r.sentiment === 'negativa',
    ).length;
  };
  const total =
    typeof raw.total_reviews === 'number'
      ? raw.total_reviews
      : typeof raw.total === 'number'
        ? raw.total
        : reviews.length;
  const positive = countOf('positive', 'positivas');
  const neutral = countOf('neutral', 'neutras');
  const negative = countOf('negative', 'negativas');
  const denom = total || 1;
  const pctOf = (key: string, count: number): number =>
    typeof percentages[key] === 'number'
      ? Math.round(percentages[key] as number)
      : Math.round((count / denom) * 100);
  const terms = (v: unknown): { term: string; count: number }[] =>
    Array.isArray(v)
      ? v
          .map((t) =>
            typeof t === 'string'
              ? { term: t, count: 0 }
              : t && typeof t === 'object'
                ? {
                    term: String((t as Record<string, unknown>).term ?? (t as Record<string, unknown>).termo ?? ''),
                    count: Number((t as Record<string, unknown>).count ?? 0) || 0,
                  }
                : null,
          )
          .filter((t): t is { term: string; count: number } => t !== null && t.term !== '')
      : [];
  const averageRating =
    typeof raw.avg_stars === 'number'
      ? raw.avg_stars
      : typeof raw.average_rating === 'number'
        ? raw.average_rating
        : typeof raw.media_estrelas === 'number'
          ? raw.media_estrelas
          : reviews.length
            ? Math.round((reviews.reduce((s, r) => s + r.rating, 0) / reviews.length) * 10) / 10
            : 0;
  return {
    total,
    positive,
    neutral,
    negative,
    positivePct: pctOf('positive', positive),
    neutralPct: pctOf('neutral', neutral),
    negativePct: pctOf('negative', negative),
    averageRating,
    topPositiveTerms: terms(raw.top_positive_terms ?? raw.termos_positivos),
    topNegativeTerms: terms(raw.top_negative_terms ?? raw.termos_negativos),
  };
}

/** Termômetro de sentimento de um produto a partir da API; null => usar fallback local. */
export async function fetchProductSentiment(productId: number): Promise<ProductSentiment | null> {
  const paths = [`/products/${productId}/sentiment`, `/sentiment?product_id=${productId}`];
  for (const path of paths) {
    const data = await fetchJson(`${API_URL}${path}`);
    if (!data || typeof data !== 'object') continue;
    const d = data as Record<string, unknown>;
    const rawReviews = Array.isArray(d.reviews) ? d.reviews : [];
    const reviews = rawReviews
      .map((r, i) => toReview(r, productId, i))
      .filter((r): r is Review => r !== null);
    return { stats: toStats(d, reviews), reviews: reviews.length ? reviews : undefined };
  }
  return null;
}

/** Envia uma avaliação para o backend. Devolve true se foi persistida. */
export async function submitReview(
  productId: number,
  review: { author: string; rating: number; text: string; sentiment?: SentimentLabel; confidence?: number },
): Promise<boolean> {
  // Backend espera `stars` (1-5); o sentimento é previsto no servidor.
  const body = JSON.stringify({
    product_id: productId,
    author: review.author,
    stars: review.rating,
    text: review.text,
  });
  for (const path of ['/reviews', '/api/reviews']) {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 8000);
      const res = await fetch(`${API_URL}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body,
        signal: controller.signal,
      });
      clearTimeout(timer);
      if (res.ok || res.status === 201) return true;
    } catch {
      // tenta o próximo caminho / desiste silenciosamente
    }
  }
  return false;
}

/** Checagem rápida de saúde da API (usada para indicar "modo offline" na UI). */
export async function checkApiHealth(): Promise<boolean> {
  const data = await fetchJson(`${API_URL}/health`, undefined, 3000);
  if (data !== null) return true;
  const root = await fetchJson(`${API_URL}/`, undefined, 3000);
  return root !== null;
}
