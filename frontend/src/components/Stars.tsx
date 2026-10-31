export default function Stars({ rating }: { rating: number }) {
  return (
    <span className="stars" aria-label={`${rating} de 5 estrelas`}>
      ★★★★★ <small>{rating.toFixed(1)}</small>
    </span>
  );
}
