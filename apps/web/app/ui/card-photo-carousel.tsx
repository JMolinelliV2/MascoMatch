"use client";
import Link from "next/link";
import { useRef, useState } from "react";
import { lostDogsEndpoint } from "@/lib/lost-dogs";
import type { LostDogNotice } from "@/lib/lost-dogs";
import { Icon } from "./pictogram";
import { PhotoViewer } from "./photo-viewer";

export function CardPhotoCarousel({ animal }: { animal: LostDogNotice }) {
  const [index, setIndex] = useState(0);
  const [failed, setFailed] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const touch = useRef<number | null>(null);
  const photos = animal.photo_ids || [];
  const count = photos.length || (animal.photo_url ? 1 : 0);
  const current = Math.min(index, Math.max(0, count - 1));
  const base = `${lostDogsEndpoint}/${animal.id}`;
  const src = photos[current] ? `${base}/photos/${photos[current]}` : animal.photo_url ? `${base}/photo` : null;
  const move = (delta: number) => setIndex((current + delta + count) % count);
  return <div className="dog-photo card-photo-carousel" role="group" aria-label={`Fotos de ${animal.name}`} onKeyDown={event => {
    if (count > 1 && (event.key === "ArrowLeft" || event.key === "ArrowRight")) { event.preventDefault(); move(event.key === "ArrowLeft" ? -1 : 1); }
  }} onTouchStart={event => { touch.current = event.touches[0]?.clientX ?? null; }} onTouchEnd={event => {
    const end = event.changedTouches[0]?.clientX;
    if (count > 1 && touch.current !== null && end !== undefined && Math.abs(end - touch.current) > 45) move(end < touch.current ? 1 : -1);
    touch.current = null;
  }}>
    <Link href={`/perdidos/${animal.id}`} className="report-photo-primary" aria-label={`Ver aviso de ${animal.name}`}>
      {src && failed !== src ? <img src={src} alt={`${animal.name}, foto ${current + 1}`} loading="lazy" onError={() => setFailed(src)} /> : <div className="dog-photo-placeholder"><Icon name="paw" /><span>{src ? "Foto no disponible" : "Sin fotos"}</span></div>}
    </Link>
    {count > 1 && <>
      <button type="button" className="card-photo-arrow card-photo-prev" onClick={() => move(-1)} aria-label={`Foto anterior de ${animal.name}`}><Icon name="arrow" /></button>
      <button type="button" className="card-photo-arrow card-photo-next" onClick={() => move(1)} aria-label={`Foto siguiente de ${animal.name}`}><Icon name="arrow" /></button>
      <div className="card-photo-dots" aria-label="Elegir foto">{photos.map((id, number) => <button type="button" key={id} aria-label={`Foto ${number + 1} de ${animal.name}`} aria-pressed={number === current} onClick={() => setIndex(number)}><span /></button>)}</div>
      <span className="card-photo-count" aria-live="polite">{current + 1} / {count}</span>
    </>}
    {src && failed !== src && <button type="button" className="report-photo-zoom" aria-label={`Ampliar fotos de ${animal.name}`} aria-haspopup="dialog" onClick={() => setExpanded(true)}><Icon name="expand" /></button>}
    {expanded && <PhotoViewer photos={photos.length ? photos.map((id, number) => ({ id, src: `${base}/photos/${id}`, alt: `${animal.name}, foto ${number + 1}` })) : undefined} galleryEndpoint={photos.length ? undefined : `${base}/photos`} initialIndex={current} title={animal.name} onClose={() => setExpanded(false)} />}
  </div>;
}
