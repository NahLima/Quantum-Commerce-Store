export default function Stars({ rating }: { rating: number }) {
  // Antes, o componente desenhava 5 estrelas cheias qualquer que fosse a
  // nota — só o número ao lado mudava. Por isso uma avaliação de 3
  // estrelas (como a da Amora) exibia ★★★★★ 3.0, e uma de 1 estrela
  // também. Agora as estrelas seguem a nota (arredondada): cheias em azul,
  // vazias em cinza.
  const filled = Math.max(0, Math.min(5, Math.round(rating)));
  return (
    <span className="stars" aria-label={`${rating} de 5 estrelas`}>
      {'★'.repeat(filled)}
      <span className="empty">{'☆'.repeat(5 - filled)}</span>{' '}
      <small>{rating.toFixed(1)}</small>
    </span>
  );
}
