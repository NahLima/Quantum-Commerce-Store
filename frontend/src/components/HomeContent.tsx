'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import {
  categories,
  formatPrice,
  products as localProducts,
  type Category,
  type Product,
} from '../lib/products';
import { categoryImages } from '../lib/products';
import { fetchProducts } from '../lib/api';
import Stars from '../components/Stars';

type Filter = Category | 'Todos';

function Icon({ name, size = 20 }: { name: string; size?: number }) {
  const paths: Record<string, React.ReactNode> = {
    heart: (
      <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8l1.1 1.1L12 21l7.8-7.5 1.1-1.1a5.5 5.5 0 0 0-.1-7.8Z" />
    ),
    arrow: (
      <>
        <path d="M5 12h14" />
        <path d="m14 7 5 5-5 5" />
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

export default function HomeContent({
  initialCategory,
  initialQuery,
}: {
  initialCategory: Filter;
  initialQuery: string;
}) {
  const router = useRouter();
  const [favorites, setFavorites] = useState<number[]>([]);
  const [visible, setVisible] = useState(12);
  // Catálogo: começa com o arquivo local (renderiza na hora, mesmo sem
  // backend) e troca pelo catálogo da API (GET /products) quando ela responde.
  const [products, setProducts] = useState<Product[]>(localProducts);

  useEffect(() => {
    let cancelled = false;
    fetchProducts().then((catalog) => {
      if (!cancelled && catalog) setProducts(catalog);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const activeCategory: Filter = initialCategory;
  const search = initialQuery;

  const filtered = useMemo(
    () =>
      products.filter(
        (product) =>
          (activeCategory === 'Todos' || product.category === activeCategory) &&
          product.name.toLowerCase().includes(search.toLowerCase()),
      ),
    [activeCategory, search, products],
  );

  function chooseCategory(category: Filter) {
    setVisible(12);
    const params = new URLSearchParams();
    if (category !== 'Todos') params.set('categoria', category);
    if (search) params.set('q', search);
    const qs = params.toString();
    router.push(qs ? `/?${qs}#catalogo` : '/#catalogo');
  }

  function toggleFavorite(id: number) {
    setFavorites((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id],
    );
  }

  const heroProduct: Product = products[3] ?? localProducts[3]; // Headphone Eclipse, como no Figma

  return (
    <main>
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">CURADORIA QUANTUM — EDIÇÃO 01</p>
          <h1>
            Escolhas que
            <br />
            movem o seu <em>mundo.</em>
          </h1>
          <p className="hero-description">
            Objetos extraordinários para uma vida em constante movimento. Design, função e
            propósito, reunidos em um só lugar.
          </p>
          <button className="primary-button" onClick={() => chooseCategory('Todos')}>
            EXPLORAR COLEÇÃO <Icon name="arrow" size={18} />
          </button>
          <div className="hero-stats">
            <span>
              <b>{products.length}</b> produtos selecionados
            </span>
            <span>
              <b>5</b> universos para descobrir
            </span>
          </div>
        </div>
        <div className="hero-visual">
          <Image
            src={categoryImages.Tecnologia[3]}
            alt="Headphone preto da coleção Quantum"
            fill
            sizes="53vw"
            priority
          />
          <div className="floating-card">
            <span>DESTAQUE</span>
            <b>{heroProduct.name}</b>
            <small>Som imersivo. Silêncio absoluto.</small>
          </div>
          <span className="vertical-copy">DESIGNED FOR THE CURIOUS</span>
        </div>
      </section>

      <section className="category-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">EXPLORE POR UNIVERSO</p>
            <h2>
              Encontre o que
              <br />
              combina com você.
            </h2>
          </div>
          <button onClick={() => chooseCategory('Todos')}>
            VER TODAS AS CATEGORIAS <Icon name="arrow" size={17} />
          </button>
        </div>
        <div className="category-grid">
          {categories.map((category, index) => (
            <button
              className="category-card"
              key={category.name}
              onClick={() => chooseCategory(category.name)}
            >
              <Image
                src={categoryImages[category.name][index % categoryImages[category.name].length]}
                alt={category.label}
                fill
                sizes="20vw"
              />
              <span className="category-number">0{index + 1}</span>
              <span className="category-info">
                <small>{category.description}</small>
                <b>{category.label}</b>
                <i>
                  <Icon name="arrow" size={18} />
                </i>
              </span>
            </button>
          ))}
        </div>
      </section>

      <section className="catalog" id="catalogo">
        <div className="catalog-top">
          <div>
            <p className="eyebrow">SELEÇÃO QUANTUM</p>
            <h2>{activeCategory === 'Todos' ? 'Mais desejados.' : activeCategory}</h2>
            {search && (
              <p style={{ color: '#777', fontSize: 12, marginTop: 8 }}>
                Resultados para “{search}” — {filtered.length} produto(s).
              </p>
            )}
          </div>
          <div className="filter-tabs">
            {(['Todos', ...categories.map((c) => c.name)] as const).map((category) => (
              <button
                className={activeCategory === category ? 'active' : ''}
                onClick={() => chooseCategory(category)}
                key={category}
              >
                {category}
              </button>
            ))}
          </div>
        </div>
        {filtered.length ? (
          <div className="product-grid">
            {filtered.slice(0, visible).map((product) => (
              <article className="product-card" key={product.id}>
                <Link className="product-image" href={`/produto/${product.id}`}>
                  <Image
                    src={product.image}
                    alt={product.name}
                    fill
                    sizes="(max-width: 720px) 50vw, 25vw"
                    loading="lazy"
                  />
                  {product.badge && <span className="badge">{product.badge}</span>}
                </Link>
                <button
                  className={`favorite ${favorites.includes(product.id) ? 'selected' : ''}`}
                  onClick={() => toggleFavorite(product.id)}
                  aria-label="Favoritar"
                >
                  <Icon name="heart" size={19} />
                </button>
                <div className="product-info" onClick={() => router.push(`/produto/${product.id}`)}>
                  <span>{product.category}</span>
                  <h3>{product.name}</h3>
                  <div>
                    <b>{formatPrice(product.price)}</b>
                    <Stars rating={product.rating} />
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty">
            <h3>Nenhum produto encontrado.</h3>
            <p>Tente buscar outro termo ou explorar nossas categorias.</p>
          </div>
        )}
        {visible < filtered.length && (
          <button className="load-more" onClick={() => setVisible(visible + 12)}>
            CARREGAR MAIS{' '}
            <span>
              {visible} / {filtered.length}
            </span>
          </button>
        )}
      </section>

      <section className="manifesto">
        <p className="eyebrow">NOSSO COMPROMISSO</p>
        <blockquote>
          “Menos ruído.
          <br />
          Mais <em>significado.</em>”
        </blockquote>
        <p>
          Acreditamos em produtos que permanecem — na sua rotina, na memória e no mundo. Cada
          escolha passa por uma curadoria rigorosa de design, qualidade e impacto.
        </p>
        <p style={{ marginTop: 30 }}>
          <Link
            href="/ops"
            style={{ color: '#fff', fontSize: 11, letterSpacing: '.12em', fontWeight: 700 }}
          >
            VER PAINEL DE OPERAÇÕES — TERMÔMETRO DE SENTIMENTO POR CATEGORIA →
          </Link>
        </p>
      </section>
    </main>
  );
}

