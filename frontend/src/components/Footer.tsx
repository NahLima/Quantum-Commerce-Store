import Link from 'next/link';
import { categories } from '../lib/products';

export default function Footer() {
  return (
    <footer>
      <div className="footer-main">
        <div className="footer-brand">
          <div className="brand">
            <span className="brand-mark">Q</span>QUANTUM<span>COMMERCE</span>
          </div>
          <p>
            Uma curadoria de objetos extraordinários
            <br />
            para uma vida em movimento.
          </p>
        </div>
        <div>
          <h4>EXPLORE</h4>
          {categories.map((category) => (
            <Link
              key={category.name}
              href={`/?categoria=${encodeURIComponent(category.name)}#catalogo`}
            >
              {category.label}
            </Link>
          ))}
          <Link href="/ops">Operações — sentimento</Link>
        </div>
        <div>
          <h4>AJUDA</h4>
          <a href="#">Envios e entregas</a>
          <a href="#">Trocas e devoluções</a>
          <a href="#">Fale com a gente</a>
          <a href="#">Perguntas frequentes</a>
        </div>
        <div className="newsletter">
          <h4>FIQUE POR DENTRO</h4>
          <p>Novidades, histórias e escolhas que inspiram.</p>
          <label>
            <input placeholder="Seu melhor e-mail" type="email" />
            <button aria-label="Cadastrar e-mail">→</button>
          </label>
        </div>
      </div>
      <div className="footer-bottom">
        <span>© 2026 QUANTUM COMMERCE</span>
        <span>FEITO PARA OS CURIOSOS.</span>
        <span>PRIVACIDADE · TERMOS</span>
      </div>
    </footer>
  );
}
