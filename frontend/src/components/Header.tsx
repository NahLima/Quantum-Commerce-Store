'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState, type FormEvent } from 'react';
import { categories } from '../lib/products';
import { useCart } from './CartContext';

function Icon({ name, size = 20 }: { name: string; size?: number }) {
  const paths: Record<string, React.ReactNode> = {
    search: (
      <>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-4-4" />
      </>
    ),
    user: (
      <>
        <circle cx="12" cy="8" r="4" />
        <path d="M4.5 21a7.5 7.5 0 0 1 15 0" />
      </>
    ),
    bag: (
      <>
        <path d="M5 8h14l-1 13H6L5 8Z" />
        <path d="M9 9V6a3 3 0 0 1 6 0v3" />
      </>
    ),
    menu: (
      <>
        <path d="M4 7h16M4 12h16M4 17h16" />
      </>
    ),
    close: (
      <>
        <path d="m6 6 12 12M18 6 6 18" />
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

export default function Header() {
  const { count } = useCart();
  const router = useRouter();
  const [mobileMenu, setMobileMenu] = useState(false);
  const [query, setQuery] = useState('');

  function onSearch(event: FormEvent) {
    event.preventDefault();
    setMobileMenu(false);
    const q = query.trim();
    router.push(q ? `/?q=${encodeURIComponent(q)}#catalogo` : '/#catalogo');
  }

  return (
    <>
      <div className="announcement">
        FRETE GRÁTIS EM COMPRAS ACIMA DE R$ 299 <span>•</span> TROCA FÁCIL EM ATÉ 30 DIAS
      </div>
      <header>
        <button
          className="mobile-menu"
          onClick={() => setMobileMenu(!mobileMenu)}
          aria-label="Abrir menu"
        >
          <Icon name={mobileMenu ? 'close' : 'menu'} />
        </button>
        <Link href="/" className="brand" onClick={() => setMobileMenu(false)}>
          <span className="brand-mark">Q</span>QUANTUM<span>COMMERCE</span>
        </Link>
        <nav className={mobileMenu ? 'open' : ''}>
          <Link href="/#catalogo" onClick={() => setMobileMenu(false)}>
            Novidades
          </Link>
          {categories.map((category) => (
            <Link
              key={category.name}
              href={`/?categoria=${encodeURIComponent(category.name)}#catalogo`}
              onClick={() => setMobileMenu(false)}
            >
              {category.label}
            </Link>
          ))}
          <Link href="/ops" onClick={() => setMobileMenu(false)}>
            Operações
          </Link>
        </nav>
        <div className="header-actions">
          <form className="search" onSubmit={onSearch} role="search">
            <Icon name="search" size={18} />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar"
              aria-label="Buscar produtos"
            />
          </form>
          <button aria-label="Minha conta">
            <Icon name="user" />
          </button>
          <button className="cart-button" aria-label="Sacola">
            <Icon name="bag" />
            <b>{count}</b>
          </button>
        </div>
      </header>
    </>
  );
}
