'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import { categoryImages, formatPrice, getProduct, products } from '../../../lib/products';
import {
  computeSentimentStats,
  getLocalReviews,
  type Review,
  type SentimentLabel,
  type SentimentStats,
} from '../../../lib/reviews';
import { fetchProductSentiment, predictSentiment, submitReview, type Prediction } from '../../../lib/api';
import { useCart } from '../../../components/CartContext';
import Stars from '../../../components/Stars';
import SentimentThermometer from '../../../components/SentimentThermometer';
import ReviewCard from '../../../components/ReviewCard';

function Icon({ name, size = 20 }: { name: string; size?: number }) {
  const paths: Record<string, React.ReactNode> = {
    bag: (
      <>
        <path d="M5 8h14l-1 13H6L5 8Z" />
        <path d="M9 9V6a3 3 0 0 1 6 0v3" />
      </>
    ),
    heart: (
      <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8l1.1 1.1L12 21l7.8-7.5 1.1-1.1a5.5 5.5 0 0 0-.1-7.8Z" />
    ),
    truck: (
      <>
        <path d="M3 6h11v11H3zM14 10h4l3 3v4h-7z" />
        <circle cx="7" cy="19" r="2" />
        <circle cx="18" cy="19" r="2" />
      </>
    ),
    shield: <path d="M12 3 4.5 6v5.5c0 4.6 3.2 8 7.5 9.5 4.3-1.5 7.5-4.9 7.5-9.5V6L12 3Z" />,
    rotate: (
      <>
        <path d="M4 7v5h5" />
        <path d="M5.5 16a8 8 0 1 0 .2-8.3L4 12" />
      </>
    ),
  };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}

const SENTIMENT_LABEL: Record<SentimentLabel, string> = {
  positiva: 'Positiva',
  neutra: 'Neutra',
  negativa: 'Negativa',
};

export default function ProductPage() {
  const params = useParams();
  const id = Number(params.id);
  const product = getProduct(id);
  const { addToCart } = useCart();

  const [activeImage, setActiveImage] = useState(0);
  const [favorite, setFavorite] = useState(false);
  // Estado inicial = dados locais de demonstração (renderiza no servidor).
  // O useEffect abaixo troca pelos dados reais da API quando ela responde.
  const [reviews, setReviews] = useState<Review[]>(() =>
    product ? getLocalReviews(product.id, product.name) : [],
  );
  const [stats, setStats] = useState<SentimentStats | null>(() =>
    product ? computeSentimentStats(getLocalReviews(product.id, product.name)) : null,
  );
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  // Formulário de avaliação
  const [author, setAuthor] = useState('');
  const [rating, setRating] = useState(5);
  const [text, setText] = useState('');
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [predicting, setPredicting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formStatus, setFormStatus] = useState<{ ok: boolean; message: string } | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const gallery = useMemo(
    () => (product ? categoryImages[product.category].slice(0, 4) : []),
    [product],
  );

  // Carrega o sentimento: API primeiro, fallback local se a API estiver fora.
  useEffect(() => {
    if (!product) return;
    let cancelled = false;
    fetchProductSentiment(product.id).then((data) => {
      if (cancelled) return;
      if (data) {
        setApiOnline(true);
        setStats(data.stats);
        if (data.reviews) setReviews(data.reviews);
      } else {
        setApiOnline(false);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [product]);

  // Classificação ao vivo enquanto a pessoa digita a avaliação.
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (text.trim().length < 10) {
      setPrediction(null);
      setPredicting(false);
      return;
    }
    setPredicting(true);
    debounceRef.current = setTimeout(async () => {
      const result = await predictSentiment(text.trim());
      setPrediction(result);
      setPredicting(false);
    }, 700);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [text]);

  if (!product) {
    return (
      <main className="detail-page" style={{ paddingTop: 60, paddingBottom: 100 }}>
        <p className="eyebrow">QUANTUM COMERCE</p>
        <h1 style={{ fontFamily: 'var(--font-manrope)', fontSize: 36 }}>Produto não encontrado.</h1>
        <p style={{ color: '#777' }}>
          <Link href="/">Voltar ao catálogo</Link>
        </p>
      </main>
    );
  }

  const related = products
    .filter((item) => item.category === product.category && item.id !== product.id)
    .slice(0, 4);

  async function onSubmitReview(event: FormEvent) {
    event.preventDefault();
    if (text.trim().length < 10 || !author.trim()) {
      setFormStatus({
        ok: false,
        message: 'Escreva seu nome e uma avaliação com pelo menos 10 caracteres.',
      });
      return;
    }
    setSubmitting(true);
    const label = prediction?.label ?? (rating >= 4 ? 'positiva' : rating === 3 ? 'neutra' : 'negativa');
    const confidence = prediction?.confidence ?? 0.9;
    const saved = await submitReview(product!.id, {
      author: author.trim(),
      rating,
      text: text.trim(),
      sentiment: label,
      confidence,
    });
    const newReview: Review = {
      id: `mine-${Date.now()}`,
      productId: product!.id,
      author: author.trim(),
      date: 'agora mesmo',
      rating,
      text: text.trim(),
      sentiment: label,
      confidence,
      verified: true,
    };
    setReviews((current) => {
      const next = [newReview, ...current];
      setStats(computeSentimentStats(next));
      return next;
    });
    setFormStatus({
      ok: true,
      message: saved
        ? 'Avaliação enviada e salva no banco de dados. Obrigada!'
        : 'Avaliação registrada nesta sessão. A API estava fora do ar, então ela não foi salva no banco — tente novamente quando o backend estiver rodando.',
    });
    setAuthor('');
    setRating(5);
    setText('');
    setPrediction(null);
    setSubmitting(false);
  }

  return (
    <main className="detail-page">
      <div className="breadcrumbs">
        <Link href="/">Início</Link>
        <span>/</span>
        <Link href={`/?categoria=${encodeURIComponent(product.category)}#catalogo`}>
          {product.category}
        </Link>
        <span>/</span>
        <b>{product.name}</b>
      </div>

      <section className="product-detail">
        <div className="gallery">
          <div className="thumbnails">
            {gallery.map((image, index) => (
              <button
                className={activeImage === index ? 'active' : ''}
                key={image}
                onClick={() => setActiveImage(index)}
              >
                <Image src={image} alt={`${product.name} vista ${index + 1}`} width={78} height={90} />
              </button>
            ))}
          </div>
          <div className="main-image">
            <Image src={gallery[activeImage]} alt={product.name} fill sizes="55vw" priority />
            <span>
              0{activeImage + 1} / 0{gallery.length}
            </span>
          </div>
        </div>
        <div className="detail-copy">
          <p className="eyebrow">{product.category} — QUANTUM SELECT</p>
          <h1>{product.name}</h1>
          <div className="rating-line">
            <Stars rating={product.rating} />
            <button
              onClick={() =>
                document.querySelector('#avaliacoes')?.scrollIntoView({ behavior: 'smooth' })
              }
            >
              {product.reviews} avaliações
            </button>
          </div>
          <div className="detail-price">
            {formatPrice(product.price)}{' '}
            <small>ou 6x de {formatPrice(product.price / 6)} sem juros</small>
          </div>
          <p className="description">
            Uma peça criada para acompanhar o ritmo dos seus dias. Materiais selecionados, design
            essencial e desempenho consistente em uma experiência que une forma e função.
          </p>
          <div className="color-selector">
            <label>
              COR <b>{product.color}</b>
            </label>
            <div>
              <button
                className="swatch active"
                style={{ background: product.category === 'Beleza' ? '#d5a58f' : '#1f2428' }}
                aria-label={product.color}
              />
              <button className="swatch" style={{ background: '#d7d2c8' }} aria-label="Areia" />
              <button className="swatch" style={{ background: '#66706a' }} aria-label="Verde" />
            </div>
          </div>
          <div className="buy-row">
            <button className="add-button" onClick={addToCart}>
              ADICIONAR À SACOLA <Icon name="bag" size={19} />
            </button>
            <button
              className={`detail-heart ${favorite ? 'selected' : ''}`}
              onClick={() => setFavorite(!favorite)}
              aria-label="Favoritar"
            >
              <Icon name="heart" />
            </button>
          </div>
          <div className="benefits">
            <span>
              <Icon name="truck" />
              <b>Frete grátis</b>
              <small>acima de R$ 299</small>
            </span>
            <span>
              <Icon name="rotate" />
              <b>Troca fácil</b>
              <small>em até 30 dias</small>
            </span>
            <span>
              <Icon name="shield" />
              <b>Compra segura</b>
              <small>pagamento protegido</small>
            </span>
          </div>
        </div>
      </section>

      {stats && (
        <section className="thermo-section" aria-label="Termômetro de sentimento">
          <p className="eyebrow">TERMÔMETRO DE SENTIMENTO</p>
          <SentimentThermometer stats={stats} />
        </section>
      )}

      <section className="reviews" id="avaliacoes">
        <div className="reviews-summary">
          <p className="eyebrow">QUEM COMPROU, CONTA</p>
          <h2>Avaliações.</h2>
          {stats && (
            <>
              <strong>{stats.averageRating.toFixed(1)}</strong>
              <Stars rating={stats.averageRating} />
              <p>Baseado em {stats.total} avaliações verificadas</p>
              {apiOnline === true && (
                <span className="api-note">● Dados ao vivo da API (Postgres + modelo de ML)</span>
              )}
              {apiOnline === false && (
                <span className="api-note offline">
                  ○ API fora do ar — mostrando avaliações de demonstração locais. Suba o backend
                  para ver os dados reais.
                </span>
              )}
            </>
          )}
        </div>
        <div className="review-list">
          {reviews.map((review) => (
            <ReviewCard key={review.id} review={review} />
          ))}
          {reviews.length === 0 && <p style={{ color: '#888' }}>Carregando avaliações…</p>}
        </div>
      </section>

      <section className="review-form">
        <p className="eyebrow">SUA OPINIÃO CONTA</p>
        <h3>Escreva sua avaliação</h3>
        <p>
          Enquanto você digita, nosso modelo de análise de sentimento classifica seu texto em
          tempo real — igual ao termômetro acima.
        </p>
        <form onSubmit={onSubmitReview}>
          <label htmlFor="review-author">SEU NOME</label>
          <input
            id="review-author"
            type="text"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            placeholder="Ex.: Marina C."
          />
          <label>SUA NOTA</label>
          <div className="stars-input" role="radiogroup" aria-label="Nota de 1 a 5 estrelas">
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                type="button"
                className={rating >= n ? 'on' : ''}
                onClick={() => setRating(n)}
                aria-label={`${n} estrela${n > 1 ? 's' : ''}`}
              >
                ★
              </button>
            ))}
          </div>
          <label htmlFor="review-text">SUA AVALIAÇÃO</label>
          <textarea
            id="review-text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Conte como foi sua experiência com o produto…"
          />
          {text.trim().length >= 10 && (
            <div className="predict-box">
              {predicting && 'Analisando seu texto…'}
              {!predicting && prediction && (
                <>
                  <b>Sentimento detectado: {SENTIMENT_LABEL[prediction.label]}</b> (
                  {Math.round(prediction.confidence * 100)}% de confiança
                  {prediction.model ? ` · modelo ${prediction.model}` : ''}). Sua avaliação vai
                  aparecer acima com esse selo.
                </>
              )}
              {!predicting && !prediction && apiOnline === false && (
                <span className="offline-note">
                  A API de classificação está fora do ar — o sentimento será estimado pela sua
                  nota nesta sessão.
                </span>
              )}
            </div>
          )}
          <div style={{ marginTop: 24 }}>
            <button className="primary-button" type="submit" disabled={submitting}>
              {submitting ? 'ENVIANDO…' : 'ENVIAR AVALIAÇÃO'}
            </button>
          </div>
          {formStatus && (
            <p className={`form-status ${formStatus.ok ? '' : 'error'}`}>{formStatus.message}</p>
          )}
        </form>
      </section>

      <section className="related">
        <p className="eyebrow">VOCÊ TAMBÉM PODE GOSTAR</p>
        <h2>Continue explorando.</h2>
        <div className="related-grid">
          {related.map((item) => (
            <Link key={item.id} href={`/produto/${item.id}`}>
              <Image src={item.image} alt={item.name} width={400} height={270} />
              <span>{item.category}</span>
              <b>{item.name}</b>
              <small>{formatPrice(item.price)}</small>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
