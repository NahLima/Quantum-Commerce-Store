import type { SentimentStats } from '../lib/reviews';
import Stars from './Stars';

/**
 * Termômetro de Sentimento — referência: Mercado Livre.
 * Mostra a nota média, a distribuição positiva/neutra/negativa em barras e
 * os termos mais citados em elogios e reclamações.
 */
export default function SentimentThermometer({
  stats,
  totalLabel,
}: {
  stats: SentimentStats;
  totalLabel?: string;
}) {
  const rows = [
    { label: 'Positivas', pct: stats.positivePct, count: stats.positive, className: 'bar-positive' },
    { label: 'Neutras', pct: stats.neutralPct, count: stats.neutral, className: 'bar-neutral' },
    { label: 'Negativas', pct: stats.negativePct, count: stats.negative, className: 'bar-negative' },
  ];

  return (
    <div className="thermometer">
      <div className="thermometer-score">
        <strong>{stats.averageRating.toFixed(1)}</strong>
        <Stars rating={stats.averageRating} />
        <p>{totalLabel ?? `Baseado em ${stats.total} avaliações verificadas`}</p>
      </div>

      <div className="thermometer-bars">
        {rows.map((row) => (
          <div className="thermo-row" key={row.label}>
            <span>{row.label}</span>
            <div className="thermo-track">
              <div className={`thermo-fill ${row.className}`} style={{ width: `${row.pct}%` }} />
            </div>
            <b>{row.pct}%</b>
            <small>({row.count})</small>
          </div>
        ))}
      </div>

      {(stats.topPositiveTerms.length > 0 || stats.topNegativeTerms.length > 0) && (
        <div className="thermometer-terms">
          {stats.topPositiveTerms.length > 0 && (
            <div>
              <h4>O que gostaram</h4>
              <div className="term-chips">
                {stats.topPositiveTerms.map((t) => (
                  <span key={t.term} className="chip chip-positive">
                    {t.term}
                    {t.count > 0 ? ` · ${t.count}` : ''}
                  </span>
                ))}
              </div>
            </div>
          )}
          {stats.topNegativeTerms.length > 0 && (
            <div>
              <h4>O que reclamaram</h4>
              <div className="term-chips">
                {stats.topNegativeTerms.map((t) => (
                  <span key={t.term} className="chip chip-negative">
                    {t.term}
                    {t.count > 0 ? ` · ${t.count}` : ''}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
