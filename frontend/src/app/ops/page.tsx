import Link from 'next/link';
import { categories, formatPrice, products as localProducts } from '../../lib/products';
import { computeSentimentStats, getLocalReviews } from '../../lib/reviews';
import { fetchProducts } from '../../lib/api';
import Stars from '../../components/Stars';

export const metadata = {
  title: 'Operações — Termômetro de Sentimento | Quantum Comerce',
  description:
    'Painel de operações da Quantum Commerce: sentimento das avaliações por categoria e produtos com maior share de avaliações negativas.',
};

// Sempre renderiza por requisição: o catálogo vem da API (GET /products) a
// cada acesso; sem a API no ar, usa o arquivo local. Sem isso o `next build`
// congelaria o catálogo local no HTML estático.
export const dynamic = 'force-dynamic';

/**
 * Painel de operações — catálogo da API, agregados calculados a partir das
 * avaliações locais de demonstração (não existe endpoint de agregados no
 * backend; a regra de alerta é a mesma: negativo > 25%).
 */
export default async function OpsPage() {
  const products = (await fetchProducts()) ?? localProducts;
  const byCategory = categories.map((category) => {
    const items = products.filter((p) => p.category === category.name);
    const reviews = items.flatMap((p) => getLocalReviews(p.id, p.name));
    return { category, products: items.length, ...computeSentimentStats(reviews) };
  });

  const byProduct = products
    .map((p) => {
      const reviews = getLocalReviews(p.id, p.name);
      return { product: p, ...computeSentimentStats(reviews) };
    })
    .sort((a, b) => b.negativePct - a.negativePct || b.negative - a.negative);

  const totalReviews = byCategory.reduce((s, c) => s + c.total, 0);
  const totalNegative = byCategory.reduce((s, c) => s + c.negative, 0);
  const overallNegativePct = totalReviews ? Math.round((totalNegative / totalReviews) * 100) : 0;
  const alerts = byProduct.filter((p) => p.negativePct > 25).length;
  const overallAvg =
    byCategory.reduce((s, c) => s + c.averageRating * c.total, 0) / (totalReviews || 1);

  return (
    <main className="ops-page">
      <div className="breadcrumbs">
        <Link href="/">Início</Link>
        <span>/</span>
        <b>Operações</b>
      </div>

      <p className="eyebrow">QUANTUM COMERCE — OPERAÇÕES</p>
      <h1>
        Termômetro de sentimento<span style={{ color: '#3156ff' }}>.</span>
      </h1>
      <p className="lede">
        O que os clientes estão dizendo sobre cada universo da loja, agregado pelo modelo de
        análise de sentimento. O painel prioriza onde agir primeiro: qualidade do produto,
        fornecedor, descrição do anúncio ou atendimento.
      </p>

      <div className="ops-cards">
        <div className="ops-card">
          <b>{totalReviews}</b>
          <span>avaliações analisadas</span>
        </div>
        <div className="ops-card">
          <b>{overallNegativePct}%</b>
          <span>negativas no geral · média {overallAvg.toFixed(1)} ★</span>
        </div>
        <div className="ops-card">
          <b>{alerts}</b>
          <span>produtos em alerta (&gt; 25% negativas)</span>
        </div>
      </div>

      <h2
        style={{
          fontFamily: 'var(--font-manrope)',
          fontSize: 26,
          letterSpacing: '-0.03em',
          margin: '0 0 18px',
        }}
      >
        Sentimento por categoria
      </h2>
      <div className="ops-table-wrap">
        <table className="ops-table">
          <thead>
            <tr>
              <th>Categoria</th>
              <th>Produtos</th>
              <th>Avaliações</th>
              <th>Nota média</th>
              <th>Positivas</th>
              <th>Neutras</th>
              <th>Negativas</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {byCategory.map((row) => (
              <tr key={row.category.name}>
                <td>
                  <b>{row.category.name}</b>
                  <br />
                  <small style={{ color: '#888' }}>{row.category.description}</small>
                </td>
                <td>{row.products}</td>
                <td>{row.total}</td>
                <td>
                  <Stars rating={row.averageRating} />
                </td>
                <td>{row.positivePct}%</td>
                <td>{row.neutralPct}%</td>
                <td>
                  <b style={{ color: row.negativePct > 25 ? '#a02c2c' : 'inherit' }}>
                    {row.negativePct}%
                  </b>
                </td>
                <td>
                  {row.negativePct > 25 ? (
                    <span className="alert-badge">Alerta</span>
                  ) : (
                    <span className="ok-badge">Saudável</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2
        style={{
          fontFamily: 'var(--font-manrope)',
          fontSize: 26,
          letterSpacing: '-0.03em',
          margin: '48px 0 18px',
        }}
      >
        Produtos com maior share de avaliações negativas
      </h2>
      <div className="ops-table-wrap">
        <table className="ops-table">
          <thead>
            <tr>
              <th>Produto</th>
              <th>Categoria</th>
              <th>Preço</th>
              <th>Avaliações</th>
              <th>Nota média</th>
              <th>Negativas</th>
              <th>O que reclamaram</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {byProduct.slice(0, 10).map((row) => (
              <tr key={row.product.id}>
                <td>
                  <Link href={`/produto/${row.product.id}`} style={{ color: '#17191c' }}>
                    <b>{row.product.name}</b>
                  </Link>
                </td>
                <td>{row.product.category}</td>
                <td>{formatPrice(row.product.price)}</td>
                <td>{row.total}</td>
                <td>
                  <Stars rating={row.averageRating} />
                </td>
                <td>
                  <b style={{ color: row.negativePct > 25 ? '#a02c2c' : 'inherit' }}>
                    {row.negativePct}% ({row.negative})
                  </b>
                </td>
                <td>
                  {row.topNegativeTerms.length
                    ? row.topNegativeTerms.map((t) => t.term).join(', ')
                    : '—'}
                </td>
                <td>
                  {row.negativePct > 25 ? (
                    <span className="alert-badge">Revisar</span>
                  ) : (
                    <span className="ok-badge">Ok</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="ops-note">
        <h3>Como a operação usa este painel</h3>
        <p>
          <b style={{ color: '#fff' }}>1. Priorizar qualidade e fornecedor.</b> Produtos com mais
          de 25% de avaliações negativas entram na fila de revisão: conferir lote, material e
          fotos do anúncio antes de qualquer campanha de mídia.
        </p>
        <p>
          <b style={{ color: '#fff' }}>2. Responder com contexto.</b> Os termos mais citados em
          reclamações (“defeito”, “atraso”, “embalagem”) alimentam respostas-padrão do suporte e
          sinalizam se o problema é do produto, da logística ou da expectativa criada pelo
          anúncio.
        </p>
        <p>
          <b style={{ color: '#fff' }}>3. Medir o efeito das ações.</b> Depois de uma correção
          (troca de fornecedor, ajuste de descrição, melhoria de embalagem), o termômetro do
          produto mostra se o share de negativas cai nas semanas seguintes.
        </p>
        <p style={{ color: '#888b8c', fontSize: 11 }}>
          Catálogo da API (GET /products), com o arquivo local como reserva. Os agregados são
          calculados das avaliações locais de demonstração (src/lib/reviews.ts) — a regra de
          alerta e o layout são os mesmos.
        </p>
      </div>
    </main>
  );
}
