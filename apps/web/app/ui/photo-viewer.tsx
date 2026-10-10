"use client";

import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Icon } from "./pictogram";

export type ViewerPhoto = { id: string; src: string; alt: string; thumbnailSrc?: string };
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function ViewerImage({ photo }: { photo: ViewerPhoto }) {
  const [status, setStatus] = useState<"loading" | "ready" | "failed">("loading");
  const [retry, setRetry] = useState(0);
  return <div className="photo-viewer-image">
    {status === "loading" && <p className="photo-viewer-message" role="status">Cargando foto…</p>}
    {status === "failed" ? <div className="photo-viewer-message"><p role="alert">No pudimos cargar esta foto. Puede que ya no esté disponible.</p><button type="button" className="button button-secondary" onClick={() => { setStatus("loading"); setRetry(value => value + 1); }}>Reintentar</button></div>
      : <img key={retry} src={retry ? `${photo.src}${photo.src.includes("?") ? "&" : "?"}reintento=${retry}` : photo.src} alt={photo.alt} onLoad={() => setStatus("ready")} onError={() => setStatus("failed")} />}
  </div>;
}

export function PhotoViewer({ photos, galleryEndpoint, title, initialIndex = 0, onClose }: {
  photos?: ViewerPhoto[]; galleryEndpoint?: string; title: string; initialIndex?: number; onClose: () => void;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const backdropPressed = useRef(false);
  const [remotePhotos, setRemotePhotos] = useState<ViewerPhoto[]>([]);
  const [loading, setLoading] = useState(Boolean(galleryEndpoint));
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [index, setIndex] = useState(initialIndex);
  const items = photos ?? remotePhotos;
  const currentIndex = Math.min(Math.max(index, 0), Math.max(items.length - 1, 0));

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    if (!dialog.open) dialog.showModal();
    return () => { document.body.style.overflow = previousOverflow; };
  }, []);

  useEffect(() => {
    if (!galleryEndpoint) return;
    const controller = new AbortController();
    setLoading(true); setError(""); setRemotePhotos([]); setIndex(0);
    void fetch(galleryEndpoint, { cache: "no-store", signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15000)]) }).then(async response => {
      if (response.status === 404) throw new Error("Este reporte ya no está disponible.");
      if (!response.ok) throw new Error("No pudimos consultar las fotos.");
      const data: { items: { id: string }[] } = await response.json();
      if (!data || !Array.isArray(data.items) || data.items.some(item => !item || typeof item.id !== "string" || !uuid.test(item.id))) throw new Error("No pudimos consultar las fotos.");
      if (!controller.signal.aborted) setRemotePhotos(data.items.map(item => ({ id: item.id, src: `${galleryEndpoint}/${encodeURIComponent(item.id)}`, alt: title })));
    }).catch(cause => { if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : "No pudimos consultar las fotos."); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [galleryEndpoint, retry, title]);

  return createPortal(<dialog ref={dialogRef} className="photo-viewer" aria-labelledby={titleId} onClose={onClose}
    onKeyDown={event => {
      // Keep Escape and arrows within the viewer, including when opened from a map popup.
      event.stopPropagation();
      if (event.key === "ArrowLeft" && items.length > 1) { event.preventDefault(); setIndex(Math.max(0, currentIndex - 1)); }
      if (event.key === "ArrowRight" && items.length > 1) { event.preventDefault(); setIndex(Math.min(items.length - 1, currentIndex + 1)); }
    }}
    onPointerDown={event => {
      const bounds = event.currentTarget.getBoundingClientRect();
      backdropPressed.current = event.target === event.currentTarget &&
        (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom);
    }}
    onClick={event => {
      event.stopPropagation();
      if (backdropPressed.current && event.target === event.currentTarget) event.currentTarget.close();
      backdropPressed.current = false;
    }}>
    <header className="photo-viewer-header"><h2 id={titleId}>{title}</h2><button type="button" className="photo-viewer-close" aria-label="Cerrar fotos" autoFocus onClick={() => dialogRef.current?.close()}><Icon name="close" /></button></header>
    <div className="photo-viewer-canvas">
      {loading ? <p className="photo-viewer-message" role="status">Buscando las fotos del reporte…</p>
        : error ? <div className="photo-viewer-message"><p role="alert">{error}</p><button type="button" className="button button-secondary" onClick={() => setRetry(value => value + 1)}>Reintentar</button></div>
          : !items.length ? <p className="photo-viewer-message" role="status">Este reporte no tiene fotos disponibles.</p>
            : <ViewerImage key={items[currentIndex].id} photo={items[currentIndex]} />}
    </div>
    <footer className="photo-viewer-footer">
      {items.length > 1 && <button type="button" className="photo-viewer-navigation" aria-label="Foto anterior" disabled={currentIndex === 0} onClick={() => setIndex(currentIndex - 1)}><Icon name="chevron" className="photo-viewer-previous" /></button>}
      <p aria-live="polite" aria-atomic="true">{items.length ? `Foto ${currentIndex + 1} de ${items.length}` : "Fotos del reporte"}</p>
      {items.length > 1 && <button type="button" className="photo-viewer-navigation" aria-label="Foto siguiente" disabled={currentIndex === items.length - 1} onClick={() => setIndex(currentIndex + 1)}><Icon name="chevron" /></button>}
    </footer>
  </dialog>, document.body);
}

function GalleryThumbnail({ photo, onOpen }: { photo: ViewerPhoto; onOpen: () => void }) {
  const [failed, setFailed] = useState(false);
  return <button type="button" className="notification-photo-button" aria-label={`Ampliar ${photo.alt}`} aria-haspopup="dialog" onClick={onOpen}>
    {failed ? <span className="dog-photo-placeholder"><Icon name="camera" /><span>Foto no disponible</span></span> : <img src={photo.thumbnailSrc || photo.src} alt={photo.alt} loading="lazy" onError={() => setFailed(true)} />}
    <span className="photo-enlarge-mark" aria-hidden="true"><Icon name="expand" /></span>
  </button>;
}

export function PhotoGallery({ photos, title }: { photos: ViewerPhoto[]; title: string }) {
  const [selected, setSelected] = useState<number | null>(null);
  return <><div className="notification-photos">{photos.map((photo, index) => <GalleryThumbnail key={photo.id} photo={photo} onOpen={() => setSelected(index)} />)}</div>
    {selected !== null && <PhotoViewer photos={photos} title={title} initialIndex={selected} onClose={() => setSelected(null)} />}
  </>;
}
