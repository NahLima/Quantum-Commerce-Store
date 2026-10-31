import type { Review } from '../lib/reviews';
import { SENTIMENT_META } from '../lib/reviews';
import Stars from './Stars';

export default function ReviewCard({ review }: { review: Review }) {
  const meta = SENTIMENT_META[review.sentiment];
  return (
    <article className="review-card">
      <div className="review-card-head">
        <span className="avatar">{review.author.charAt(0)}</span>
        <p>
          <b>{review.author}</b>
          {review.verified && <small>Compra verificada</small>}
        </p>
        <Stars rating={review.rating} />
      </div>
      <p className="review-card-text">{review.text}</p>
      <div className="review-card-foot">
        <span className={`sentiment-badge ${meta.className}`}>
          {meta.label} · {Math.round(review.confidence * 100)}%
        </span>
        {review.date && <time>{review.date}</time>}
      </div>
    </article>
  );
}
