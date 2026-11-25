import type { AccountReview } from "@/lib/reviews";

export function ReviewSummary({ review }: { review: AccountReview }) {
  return <div className="review-summary">
    <p className="review-rating">{review.rating} de 5 estrellas</p>
    <blockquote className="review-own-comment">{review.comment}</blockquote>
    <p className="field-help">Nombre público: <strong>{review.display_name}</strong></p>
    {review.visibility === "WITHDRAWN" && <p className="field-help">Esta reseña está retirada y no aparece en la portada.</p>}
    {review.visibility === "HIDDEN" && <p className="field-help">Esta reseña está oculta por moderación.</p>}
  </div>;
}
