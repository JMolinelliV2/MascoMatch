"use client";

import { LoadingState } from "../ui/loading-state";
import { ErrorState } from "../ui/error-state";
import { requestError } from "@/lib/request-error";
import { ReportAccessories } from "../ui/report-accessories";
import Link from "next/link";
import { useEffect, useState } from "react";
import { dogTraits, lostDate, lostDogsEndpoint, sexLabel, speciesLabel } from "@/lib/lost-dogs";
import type { LostDogNotice } from "@/lib/lost-dogs";
import { ReportPhotoAlbum } from "../ui/report-photo-album";
import { ReportPublication } from "../report-publication";
import { ReportId } from "../ui/report-id";
import { PublicationAuthor } from "../ui/publication-author";
import { PublicationEditLink } from "../ui/publication-edit-link";
import { Icon } from "../ui/pictogram";
import { usePublicationOwnership } from "../use-publication-ownership";
import { MarkRecovered, RecoverySuccess } from "../ui/owner-recovery";

export function DogDetail({ id }: { id: string }) {
  const [dog, setDog] = useState<LostDogNotice | null>(null);
  const [error, setError] = useState("");
  const [missing, setMissing] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [recovered, setRecovered] = useState<LostDogNotice | null>(null);
  const ownership = usePublicationOwnership(id, "lost_case");
  useEffect(() => {
    const reload = () => setRefresh(value => value + 1);
    window.addEventListener("focus", reload);
    window.addEventListener("mascomatch:cases", reload);
    return () => { window.removeEventListener("focus", reload); window.removeEventListener("mascomatch:cases", reload); };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setError(""); setMissing(false); setDog(null);
    void fetch(`${lostDogsEndpoint}/${encodeURIComponent(id)}`, { signal: controller.signal, cache: "no-store" }).then(async response => {
      if (response.status === 404 || response.status === 422) { if (!controller.signal.aborted) setMissing(true); return; }
      if (!response.ok) throw new Error("No pudimos cargar el aviso. Intentá de nuevo en un momento.");
      const data: LostDogNotice = await response.json();
      if (!controller.signal.aborted) setDog(data);
    }).catch(cause => { if (!controller.signal.aborted) setError(requestError(cause, "Revisá tu conexión y probá de nuevo en unos instantes.")); });
    return () => controller.abort();
  }, [id, refresh]);

  return <main id="main-content" className="page dog-detail-page">
    {recovered?.id === id || (ownership.allowed && ownership.status === "FOUND") ? <RecoverySuccess caseId={id} name={recovered?.id === id ? recovered.name : dog?.name} />
      : missing ? <ErrorState headingLevel={1} title="Este aviso ya no está disponible" description="Puede que la mascota haya sido encontrada o que su dueño haya cerrado el aviso."><Link href="/perdidos" className="button button-secondary">Ver mascotas reportadas</Link></ErrorState>
      : error ? <ErrorState headingLevel={1} title="No pudimos cargar este aviso" description={error} onRetry={() => setRefresh(value => value + 1)} />
      : !dog ? <LoadingState title="Cargando el aviso" description="Estamos reuniendo sus fotos y detalles." />
      : <article className="dog-detail">
        <ReportPhotoAlbum key={dog.id} src={dog.photo_url ? `${lostDogsEndpoint}/${encodeURIComponent(dog.id)}/photo` : null} galleryEndpoint={`${lostDogsEndpoint}/${encodeURIComponent(dog.id)}/photos`} alt={`Foto de ${dog.name}`} />
        <div className="dog-detail-info">
          <div className="dog-detail-status"><span className="lost-status">Sigue perdido</span><ReportId id={dog.id} publicId={dog.public_id} compact copyable /><PublicationEditLink id={dog.id} kind="lost_case" owned={ownership.allowed} /></div>
          <h1>{dog.name}</h1>
          <PublicationAuthor name={dog.publisher_name} />
          <p className="dog-traits">{[speciesLabel(dog.species), ...dogTraits(dog)].join(" · ")}</p>
          <dl className="review-details">
            <div><dt>Sexo</dt><dd>{sexLabel(dog.sex)}</dd></div>
            <div><dt>Zona donde se perdió</dt><dd>{dog.public_location || "No indicada"}</dd></div>
            <div><dt>Perdido desde el</dt><dd><time dateTime={dog.lost_at}>{lostDate(dog.lost_at)}</time></dd></div>
          </dl>
          <h2>Descripción</h2><p className="dog-full-description">{dog.description || "Sin descripción adicional."}</p>
          <ReportAccessories details={dog} />
          <div className="dog-help">{ownership.checking ? <p role="status">Comprobando las opciones de tu aviso…</p>
            : ownership.error ? <ErrorState compact headingLevel={3} title="No pudimos consultar tu cuenta" description="Reintentá para ver las opciones disponibles en este aviso." onRetry={ownership.retry} />
            : ownership.allowed ? <><h2>¿Ya está de nuevo con vos?</h2><p>Este es tu aviso. Podés marcarla como encontrada y cerrar la búsqueda.</p><div className="dog-help-actions"><MarkRecovered caseId={dog.id} onRecovered={() => setRecovered(dog)} /></div></>
            : <><h2>¿Podés ayudar a encontrarla?</h2><p>Contanos si la viste o si está a salvo con vos. Tu reporte quedará vinculado a este aviso.</p><div className="dog-help-actions">
            <Link href={`/avistamiento?aviso=${dog.id}`} className="button button-primary"><Icon name="eye" />La vi</Link>
            <Link href={`/encontre?aviso=${dog.id}`} className="button button-secondary button-found-report"><Icon name="heart" />La tengo conmigo</Link>
          </div></>}</div>
          <ReportPublication id={dog.id}/>
        </div>
      </article>}
  </main>;
}
