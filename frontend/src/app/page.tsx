import HomeContent from '../components/HomeContent';
import { categories, type Category } from '../lib/products';

type Filter = Category | 'Todos';

/**
 * Página inicial (server component): lê ?categoria= e ?q= no servidor e
 * entrega o catálogo já renderizado no HTML — nada depende de hidratação
 * para aparecer. A interatividade (filtros, favoritos, carregar mais)
 * vive no HomeContent (client component).
 */
export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ categoria?: string; q?: string }>;
}) {
  const sp = await searchParams;
  const rawCategory = sp.categoria;
  const initialCategory: Filter =
    rawCategory && categories.some((c) => c.name === rawCategory)
      ? (rawCategory as Category)
      : 'Todos';
  return <HomeContent initialCategory={initialCategory} initialQuery={sp.q ?? ''} />;
}
