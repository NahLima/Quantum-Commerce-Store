// Avaliações locais (fallback quando a API FastAPI não está acessível).
//
// O Figma original trazia apenas 3 avaliações fixas e positivas por produto.
// Para que o Termômetro de Sentimento seja significativo, geramos aqui, de
// forma determinística, de 4 a 6 avaliações por produto, com sentimentos
// variados (positiva / neutra / negativa), a partir de modelos de texto em
// PT-BR. São dados sintéticos de demonstração — quando o backend estiver no
// ar, as avaliações reais do Postgres substituem estas (ver src/lib/api.ts).

export type SentimentLabel = 'positiva' | 'neutra' | 'negativa';

export type Review = {
  id: string;
  productId: number;
  author: string;
  date: string;
  rating: number; // 1–5 estrelas
  text: string;
  sentiment: SentimentLabel;
  confidence: number; // 0–1, confiança do classificador (simulada no fallback)
  verified: boolean;
};

export type SentimentStats = {
  total: number;
  positive: number;
  neutral: number;
  negative: number;
  positivePct: number;
  neutralPct: number;
  negativePct: number;
  averageRating: number;
  topPositiveTerms: { term: string; count: number }[];
  topNegativeTerms: { term: string; count: number }[];
};

const AUTHORS = [
  'Marina C.', 'Rafael M.', 'Camila A.', 'Beatriz L.', 'Thiago S.',
  'Larissa P.', 'Gustavo H.', 'Fernanda R.', 'João V.', 'Patrícia D.',
  'Lucas F.', 'Aline T.', 'Bruno K.', 'Sofia N.', 'Diego A.',
  'Helena M.', 'Igor B.', 'Natália G.', 'Caio R.', 'Juliana O.',
];

const DATES = [
  '12 mai 2025', '28 abr 2025', '09 abr 2025', '22 mar 2025', '03 mar 2025',
  '18 fev 2025', '27 jan 2025', '15 jan 2025', '08 dez 2024', '30 nov 2024',
];

const POSITIVE_TEXTS = [
  'O {name} superou minhas expectativas. Acabamento impecável e chegou muito bem embalado.',
  'Produto excelente, exatamente como nas fotos. A entrega foi rápida e a experiência de compra muito simples.',
  'Qualidade acima da média e um design realmente bonito. Recomendo sem dúvida.',
  'Uso todos os dias e funciona perfeitamente. Vale cada centavo, compraria de novo.',
  'Chegou antes do prazo, muito bem embalado. O material é ótimo e o acabamento caprichado.',
  'Adorei! Bonito, prático e com ótima qualidade. Já indiquei para duas amigas.',
];

const NEUTRAL_TEXTS = [
  'Produto bom, cumpre o que promete. Nada de extraordinário, mas atende bem no dia a dia.',
  'Chegou no prazo e funciona como descrito. O material poderia ser um pouco melhor pelo preço.',
  'É um bom produto, mas esperava um acabamento um pouco mais caprichado. No geral, ok.',
  'Funciona bem, mas a cor é um pouco diferente da foto. Nada que atrapalhe o uso.',
];

const NEGATIVE_TEXTS = [
  'Decepcionada. O produto chegou com defeito e o acabamento deixa muito a desejar.',
  'Não vale o preço. O material é frágil e quebrou com menos de um mês de uso.',
  'A entrega atrasou duas semanas e o produto veio com a embalagem danificada.',
  'Qualidade bem abaixo do esperado. Não recomendo, esperava muito mais.',
  'Veio com defeito e a troca foi demorada. O atendimento deixou a desejar.',
];

// Gerador pseudoaleatório determinístico (mesmo produto => mesmas avaliações).
function mulberry32(seed: number) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function pick<T>(rand: () => number, arr: T[]): T {
  return arr[Math.floor(rand() * arr.length)];
}

export function getLocalReviews(productId: number, productName: string): Review[] {
  const rand = mulberry32(productId * 7919 + 13);
  // 4 a 6 avaliações por produto
  const count = 4 + Math.floor(rand() * 3);
  // Produtos "problemáticos" (id múltiplo de 7) concentram mais negativas,
  // para o dashboard de operações ter o que mostrar.
  const negativeHeavy = productId % 7 === 0;
  const reviews: Review[] = [];
  const usedAuthors = new Set<number>();

  for (let i = 0; i < count; i++) {
    const roll = rand();
    let sentiment: SentimentLabel;
    if (negativeHeavy) {
      sentiment = roll < 0.4 ? 'negativa' : roll < 0.6 ? 'neutra' : 'positiva';
    } else {
      sentiment = roll < 0.68 ? 'positiva' : roll < 0.85 ? 'neutra' : 'negativa';
    }

    let authorIdx = Math.floor(rand() * AUTHORS.length);
    while (usedAuthors.has(authorIdx)) authorIdx = (authorIdx + 1) % AUTHORS.length;
    usedAuthors.add(authorIdx);

    let text: string;
    let rating: number;
    let confidence: number;
    if (sentiment === 'positiva') {
      text = pick(rand, POSITIVE_TEXTS);
      rating = rand() < 0.75 ? 5 : 4;
      confidence = 0.88 + rand() * 0.11;
    } else if (sentiment === 'neutra') {
      text = pick(rand, NEUTRAL_TEXTS);
      rating = 3;
      confidence = 0.72 + rand() * 0.2;
    } else {
      text = pick(rand, NEGATIVE_TEXTS);
      rating = rand() < 0.6 ? 1 : 2;
      confidence = 0.85 + rand() * 0.13;
    }

    reviews.push({
      id: `local-${productId}-${i}`,
      productId,
      author: AUTHORS[authorIdx],
      date: DATES[Math.floor(rand() * DATES.length)],
      rating,
      text: text.replaceAll('{name}', productName),
      sentiment,
      confidence: Math.round(confidence * 100) / 100,
      verified: true,
    });
  }
  return reviews;
}

const POSITIVE_TERMS = ['qualidade', 'acabamento', 'entrega rápida', 'design', 'vale a pena', 'recomendo', 'ótimo', 'perfeito'];
const NEGATIVE_TERMS = ['defeito', 'atraso', 'frágil', 'embalagem', 'atendimento', 'preço', 'qualidade', 'danificado'];

function topTerms(reviews: Review[], terms: string[], sentiment: SentimentLabel) {
  const counts = new Map<string, number>();
  for (const review of reviews) {
    if (review.sentiment !== sentiment) continue;
    const lower = review.text.toLowerCase();
    for (const term of terms) {
      if (lower.includes(term)) counts.set(term, (counts.get(term) ?? 0) + 1);
    }
  }
  return [...counts.entries()]
    .map(([term, count]) => ({ term, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);
}

export function computeSentimentStats(reviews: Review[]): SentimentStats {
  const total = reviews.length || 1;
  const positive = reviews.filter((r) => r.sentiment === 'positiva').length;
  const neutral = reviews.filter((r) => r.sentiment === 'neutra').length;
  const negative = reviews.filter((r) => r.sentiment === 'negativa').length;
  const averageRating =
    reviews.length === 0
      ? 0
      : Math.round((reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length) * 10) / 10;
  return {
    total: reviews.length,
    positive,
    neutral,
    negative,
    positivePct: Math.round((positive / total) * 100),
    neutralPct: Math.round((neutral / total) * 100),
    negativePct: Math.round((negative / total) * 100),
    averageRating,
    topPositiveTerms: topTerms(reviews, POSITIVE_TERMS, 'positiva'),
    topNegativeTerms: topTerms(reviews, NEGATIVE_TERMS, 'negativa'),
  };
}

export const SENTIMENT_META: Record<
  SentimentLabel,
  { label: string; className: string }
> = {
  positiva: { label: 'Positiva', className: 'sentiment-positive' },
  neutra: { label: 'Neutra', className: 'sentiment-neutral' },
  negativa: { label: 'Negativa', className: 'sentiment-negative' },
};
