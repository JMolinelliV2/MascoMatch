"use client";
import { useEffect, useState } from "react";
import { Icon } from "./ui/pictogram";

type PublicReview = { id: string; display_name: string; rating: number; comment: string; created_at: string };

export function HomeReviews() {
  const [items, setItems] = useState<PublicReview[]>([]);
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    const reload = () => setRefresh(value => value + 1);
    window.addEventListener("focus", reload); window.addEventListener("mascomatch:reviews", reload);
    void fetch("/api/reviews", { cache: "no-store", signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error("Reviews unavailable");
      const data = await response.json();
      if (!controller.signal.aborted) setItems(data.items);
    }).catch(() => { if (!controller.signal.aborted) setItems([]); });
    return () => { controller.abort(); window.removeEventListener("focus", reload); window.removeEventListener("mascomatch:reviews", reload); };
  }, [refresh]);
  if (!items.length) return null;
  return <section className="home-reviews" aria-labelledby="home-reviews-title">
    <div className="section-heading"><div><p className="eyebrow">Experiencias de la comunidad</p><h2 id="home-reviews-title">Quienes buscaron a su mascota nos cuentan</h2><p className="home-reviews-intro">Reseñas de personas que publicaron un aviso en MascoMatch.</p></div><span className="feature-icon"><Icon name="heart" /></span></div>
    <div className="home-reviews-grid">{items.map(item => <article className="home-review-card" key={item.id}>
      <p className="review-stars" role="img" aria-label={`${item.rating} de 5 estrellas`}><span aria-hidden="true">{"★".repeat(item.rating)}<span className="review-stars-empty">{"☆".repeat(5 - item.rating)}</span></span></p>
      <blockquote><p>{item.comment}</p></blockquote>
      <footer><strong>{item.display_name}</strong><time dateTime={item.created_at}>{new Intl.DateTimeFormat("es-UY", { month: "long", year: "numeric", timeZone: "America/Montevideo" }).format(new Date(item.created_at))}</time></footer>
    </article>)}</div>
  </section>;
}
