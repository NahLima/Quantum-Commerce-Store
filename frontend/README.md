# Quantum Commerce — Frontend

Frontend do trabalho final de Machine Learning (análise de sentimento em reviews,
com referência ao Mercado Livre), migrado do export do Figma Make (React + Vite)
para **Next.js 15 (App Router) + TypeScript + Tailwind v4**.

## Stack

- Next.js 15, React 19, TypeScript
- Tailwind v4 (`@tailwindcss/postcss`)
- Fontes DM Sans + Manrope (Google Fonts, via `next/font`)
- Imagens do catálogo: Unsplash (URLs originais do Figma)

## Rodar

```bash
cd frontend
npm install
npm run dev      # http://localhost:3000
```

Build de produção:

```bash
npm run build
npm start
```

## Backend (API de sentimento)

O front fala com a API FastAPI em `NEXT_PUBLIC_API_URL` (padrão
`http://localhost:8000`, ver `.env.example`). Contrato real, verificado
contra o backend em 31/out/2026:

- `POST /predict` `{ "text": "..." }` → `{ "label": "positive"|"neutral"|"negative", "label_pt": "positiva"|"neutra"|"negativa", "probabilities": {...}, "confidence": 0.93, "model_name": "tfidf-logreg", "model_version": "1.0.0" }`
- `GET /products/{id}/sentiment` → `{ "product_id": 1, "total_reviews": 6, "avg_stars": 4.33, "counts": {"positive": 5, "neutral": 1, "negative": 0}, "percentages": {"positive": 83.3, ...}, "top_positive_terms": [...], "top_negative_terms": [...] }`
- `GET /products/{id}/reviews` → `[{ "id": 1, "product_id": 1, "author": "...", "stars": 5, "text": "...", "source": "seed", "label": "positive", "confidence": 0.95 }]`
- `POST /reviews` `{ "product_id": 1, "author": "...", "stars": 5, "text": "..." }` → 201 (o sentimento é previsto no servidor)

O mapeamento fica todo em `src/lib/api.ts`, que aceita tanto o contrato
real quanto variações legadas, para o site não quebrar se um campo mudar
de nome.

## Organização do código (clean code)

- `src/lib/api.ts` é o único lugar que fala HTTP; páginas e componentes
  nunca fazem `fetch` direto.
- Cada componente faz uma coisa: `SentimentThermometer` só desenha o
  termômetro, `ReviewCard` só uma avaliação, `Stars` só as estrelas,
  `Header`/`Footer` só o chrome da página.
- Dados do Figma vivem em `src/lib/products.ts`; dados de demonstração
  em `src/lib/reviews.ts`; nada de dado espalhado nas páginas.
- O mesmo padrão do backend vale aqui: responsabilidade única por
  arquivo, nomes explícitos, sem duplicação. O detalhamento do SOLID
  do projeto está no [README da raiz](../README.md).

**Sem o backend, nada quebra:** o site usa o catálogo local
(`src/lib/products.ts`, dados exatos do Figma) e avaliações sintéticas de
demonstração (`src/lib/reviews.ts`), e mostra um aviso de “modo offline” na
página do produto. Com a API no ar, o termômetro e a classificação ao vivo
passam a usar os dados reais do Postgres.

## Páginas

- `/` — hero, 5 categorias, catálogo com filtros por categoria + busca + carregar mais
- `/produto/[id]` — detalhe do produto + **Termômetro de Sentimento** (estilo
  Mercado Livre: nota média, % positiva/neutra/negativa, “O que gostaram / O que
  reclamaram”) + lista de avaliações com selo de sentimento e confiança +
  formulário “Escreva sua avaliação” com classificação ao vivo via `POST /predict`
- `/ops` — painel de operações: sentimento por categoria, top produtos por share
  de negativas (alerta quando &gt; 25%) e como a operação usa o painel

## Estrutura

```
src/
  app/
    layout.tsx          header + anúncio + footer, fontes, CartProvider
    globals.css         tokens e classes do Figma (portados) + sentimento/ops
    page.tsx            home
    produto/[id]/page.tsx
    ops/page.tsx
  lib/
    products.ts         catálogo — 50 produtos exatos do Figma
    reviews.ts          avaliações locais + estatísticas de sentimento
    api.ts              fetch tipado da FastAPI, com fallback gracioso
  components/
    Stars.tsx  SentimentThermometer.tsx  ReviewCard.tsx
    CartContext.tsx  Header.tsx  Footer.tsx
```
