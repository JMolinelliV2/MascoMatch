"use client";
import { LoadingState } from "./ui/loading-state";
import { ObservationEditLink } from "./ui/observation-edit-link";

import { ReportTraitFields } from "./ui/report-trait-fields";
import { readPetDetails, petDetailsError } from "@/lib/pet-details";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import type { Place } from "@/lib/places";
import {analyticsGeo} from "@/lib/places";
import { lostDogsEndpoint, speciesLabel } from "@/lib/lost-dogs";
import type { LostDogNotice } from "@/lib/lost-dogs";
import { localDateTime, sightingMessage, foundReportMessage } from "@/lib/linked-sightings";
import type { SightingResult } from "@/lib/linked-sightings";
import { LocationPicker } from "./location-picker";
import { DogPhoto } from "./perdidos/dog-photo";
import { PhotoUploader } from "./ui/photo-uploader";
import {usePhotoSelection} from "./use-photo-selection";
import {MAX_REPORT_PHOTOS,photoSelectionError} from "@/lib/report-photos";
import { ReportId } from "./ui/report-id";
import { ReportPurpose } from "./ui/report-purpose";
import { usePublicationOwnership } from "./use-publication-ownership";
import { MarkRecovered, OwnerRecoveryLogin, RecoverySuccess } from "./ui/owner-recovery";
import { PhoneField } from "./ui/phone-field";
import { phoneError } from "@/lib/phone-numbers";
import { ErrorState } from "./ui/error-state";
import { requestError } from "@/lib/request-error";

export function LinkedSightingForm({ caseId, kind = "sighting" }: { caseId: string; kind?: "sighting" | "found" }) {
  const found = kind === "found";
  const ownership = usePublicationOwnership(caseId, "lost_case", found);
  const [recoveredCase, setRecoveredCase] = useState<string | null>(null);
  const [target, setTarget] = useState<LostDogNotice | null>(null);
  const [missing, setMissing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [targetRetry, setTargetRetry] = useState(0);
  const [error, setError] = useState("");
  const [locationError, setLocationError] = useState("");
  const [location, setLocation] = useState<Place | null>(null);
  const {photos,primaryIndex,changePhotos,setPrimaryIndex} = usePhotoSelection();
  const [recent, setRecent] = useState(true);
  const [when, setWhen] = useState(() => localDateTime());
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<SightingResult | null>(null);
  const [refresh, setRefresh] = useState(0);
  const [statusError, setStatusError] = useState("");
  const [paused, setPaused] = useState(false);
  const submission = useRef<{ id: string; date: string } | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const resultId = result?.id;

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setMissing(false); setError("");
    void fetch(`${lostDogsEndpoint}/${encodeURIComponent(caseId)}`, { cache: "no-store", signal: controller.signal }).then(async response => {
      if (response.status === 404 || response.status === 422) { setMissing(true); return; }
      if (!response.ok) throw new Error("No pudimos cargar el aviso. Intentá de nuevo.");
      const data: LostDogNotice = await response.json();
      if (!controller.signal.aborted) setTarget(data);
    }).catch(cause => { if (!controller.signal.aborted) setError(requestError(cause, "Revisá tu conexión y probá de nuevo en unos instantes.")); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [caseId, targetRetry]);


  useEffect(() => {
    if (!resultId) return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    const deadline = Date.now() + 5 * 60000;
    setPaused(false); setStatusError("");
    async function update() {
      try {
        const response = await fetch(`/api/sightings/${caseId}?id=${resultId}`, { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("No pudimos consultar la revisión. Tu reporte sigue guardado.");
        const next: SightingResult = await response.json();
        if (controller.signal.aborted) return;
        setResult(next);
        if (next.status === "PENDING" && Date.now() < deadline) timer = setTimeout(update, 5000);
        else if (next.status === "PENDING") setPaused(true);
      } catch (cause) { if (!controller.signal.aborted) setStatusError(cause instanceof Error ? cause.message : "No pudimos consultar la revisión."); }
    }
    void update();
    return () => { controller.abort(); if (timer) clearTimeout(timer); };
  }, [resultId, caseId, refresh]);

  function changed() { submission.current = null; setError(""); }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || !target || (found && (ownership.checking || ownership.error || ownership.allowed))) return;
    setError(""); setLocationError("");
    if (!found && !location) { setLocationError("Elegí un lugar de la lista o usá tu ubicación actual."); return; }
    const fields = new FormData(event.currentTarget);
    const details = readPetDetails(fields);
    if (petDetailsError(details)) { setError(petDetailsError(details)); return; }
    const photoError = photoSelectionError(photos);
    if (photoError) { setError(photoError); return; }
    if (found && !photos.length) { setError("Adjuntá al menos una foto de la mascota que tenés con vos."); return; }
    const description = String(fields.get("description") || "").trim();
    const finderName = String(fields.get("finder_name") || "").trim();
    const finderPhone = String(fields.get("finder_phone") || "").trim();
    if (found && (description.length < 10 || finderName.length < 2)) { setError("Completá la descripción de la mascota y tu nombre."); return; }
    if (found && phoneError(finderPhone, true)) { setError(phoneError(finderPhone, true)); return; }
    const date = found || recent ? new Date() : new Date(when);
    if (!Number.isFinite(date.getTime()) || date.getTime() > Date.now() + 60000) { setError("Indicá una fecha y hora válidas, que no estén en el futuro."); return; }
    if (!submission.current) submission.current = { id: crypto.randomUUID(), date: date.toISOString() };
    const form = new FormData();
    form.set("details", JSON.stringify(details));
    form.set("source_type", found ? "FOUND_ANIMAL" : "USER_SIGHTING");
    form.set("request_id", submission.current.id);
    if (found) {
      form.set("description", description); form.set("finder_name", finderName); form.set("finder_phone", finderPhone);
      form.set("sex", String(fields.get("sex") || "unknown")); form.set("size", String(fields.get("size") || "unknown"));
    } else if (location) {
      form.set("observed_at", submission.current.date);
      form.set("latitude", String(location.latitude)); form.set("longitude", String(location.longitude));
      if (location.accuracyMeters !== undefined) form.set("location_accuracy_meters", String(Math.min(location.accuracyMeters, 100000)));
      if (location.locality) form.set("public_location", location.locality);
      form.set("analytics_geo",JSON.stringify(analyticsGeo(location)));
    }
    for (const photo of photos) form.append("photos", photo);
    if (photos.length) form.set("primary_index",String(primaryIndex ?? 0));
    setBusy(true);
    try {
      const response = await fetch(`/api/sightings/${caseId}`, { method: "POST", body: form });
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "No pudimos guardar el reporte. Intentá de nuevo.");
      setResult(data);
      window.dispatchEvent(new Event("mascomatch:notifications"));
      requestAnimationFrame(() => heading.current?.focus());
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No pudimos guardar el reporte. Intentá de nuevo."); }
    finally { setBusy(false); }
  }

  return <main id="main-content" className="page linked-sighting-page">
    {recoveredCase === caseId || (found && ownership.allowed && ownership.status === "FOUND") ? <RecoverySuccess caseId={caseId} name={target?.name} />
      : loading || (found && ownership.checking) ? <LoadingState title="Cargando el aviso" description="Estamos preparando las opciones para esta mascota." />
      : found && ownership.error ? <ErrorState headingLevel={1} title="No pudimos consultar tu cuenta" description="No pudimos comprobar si este aviso pertenece a tu cuenta. Reintentá para continuar." onRetry={ownership.retry} />
      : found && ownership.allowed && ownership.status === "ACTIVE" ? <>
        <h1>{target ? `¿${target.name} ya está con vos?` : "¿Tu mascota ya está con vos?"}</h1>
        <p className="page-intro">Este es tu aviso. Para cerrar la búsqueda solo tenés que indicar que ya la recuperaste.</p>
        <MarkRecovered key={caseId} caseId={caseId} onRecovered={() => setRecoveredCase(caseId)} />
      </>
      : found && ownership.allowed ? <><h1>Tu búsqueda ya está cerrada</h1><p className="page-intro">Podés consultar el estado de este aviso desde Mis avisos.</p><Link href="/mis-avisos" className="button button-secondary">Gestionar mis avisos</Link></>
      : missing ? <ErrorState headingLevel={1} title="Este aviso ya no está disponible" description="La búsqueda puede haber terminado o el aviso puede haber sido retirado. Podés compartir lo que viste en un reporte general."><Link href={found ? "/encontre" : "/avistamiento"} className="button button-secondary">{found ? "Reportar una mascota encontrada" : "Publicar un avistamiento"}</Link></ErrorState>
      : !target ? <ErrorState headingLevel={1} title="No pudimos abrir el aviso" description={error} onRetry={() => setTargetRetry(value => value + 1)} />
      : result ? <>
        <h1 ref={heading} tabIndex={-1}>{found ? "Reporte de mascota encontrada guardado" : "Avistamiento guardado"}</h1>
        <p className="page-intro">Gracias por ayudar a encontrar a {target.name}.</p>
        <ReportId id={result.id} publicId={result.public_id} label="ID del reporte" copyable />
        <p role="status" className="notice notice-success sighting-result">{found ? foundReportMessage(result, photos.length > 0) : sightingMessage(result, photos.length > 0)}</p>
        {statusError && <p className="notice notice-warning" role="alert">{statusError}</p>}
        {(paused || statusError) && <button type="button" className="text-button" onClick={() => setRefresh(value => value + 1)}>Actualizar revisión</button>}
        <ObservationEditLink id={result.id} found={found} />
        <div className="success-actions"><Link href="/perdidos" className="button button-secondary">Ver mascotas reportadas</Link></div>
      </> : <>
        <h1>{found ? `¿Tenés a ${target.name} con vos?` : `¿Viste a ${target.name}?`}</h1>
        <p className="page-intro">{found ? "Mostrale al dueño la mascota que tenés con vos. Si confirma que es la suya, le compartiremos tu nombre y teléfono para que puedan coordinar la entrega." : "Indicá el lugar y adjuntá fotos si tenés. Tu avistamiento quedará vinculado a este aviso."}</p>
        <ReportPurpose kind={kind} caseId={caseId} />
        <div className="sighting-target"><DogPhoto dog={target} /><div><div className="report-card-meta"><strong>{target.name}</strong><ReportId id={target.id} publicId={target.public_id} /></div><p>{speciesLabel(target.species)} · Aviso de mascota perdida</p></div></div>
        <form onChange={changed} onSubmit={submit} className="linked-sighting-form" aria-busy={busy}>
          <fieldset disabled={busy} className="form-controls section-fields">
            {!found && <div><h2>¿Dónde la viste?</h2><LocationPicker value={location} required onChange={place => { changed(); setLocation(place); setLocationError(""); }} />{locationError && <p role="alert" className="notice notice-error">{locationError}</p>}</div>}
            <div>
              {found && <><h2>La mascota que tenés con vos</h2><p className="field-help">Subí al menos una foto clara. Podés agregar hasta cinco: de la cara, de cuerpo entero y de sus marcas o accesorios.</p></>}
              <PhotoUploader name="photos" label={found ? "Fotos de la mascota" : "Fotos"} required={found} maxFiles={MAX_REPORT_PHOTOS} inputRef={fileInput} files={photos} primaryIndex={primaryIndex} onPrimaryChange={index=>{changed();setPrimaryIndex(index);}} onFilesChange={next => { changed(); changePhotos(next); }} />
              {found && <label className="field-label">Descripción de la mascota<textarea name="description" className="form-input" required minLength={10} maxLength={4000} rows={4} placeholder="Ej.: es rojiza, tiene una mancha blanca en el pecho y lleva un collar azul. Describí lo que ves, sin copiar el aviso." /></label>}
              <details className="optional-traits"><summary>Agregar características que reconociste (opcional)</summary><p className="field-help">Completá solo lo que pudiste observar. No necesitás repetir los datos del aviso.</p><div className="form-grid">
                {found && <><label className="field-label">Sexo<select name="sex" className="form-input"><option value="unknown">No lo sé</option><option value="male">Macho</option><option value="female">Hembra</option></select></label><label className="field-label">Tamaño<select name="size" className="form-input"><option value="unknown">No lo sé</option><option value="tiny">Muy pequeño</option><option value="small">Pequeño</option><option value="medium">Mediano</option><option value="large">Grande</option></select></label></>}
                <ReportTraitFields species={target.species} />
              </div></details>
              {!found && <p className="field-help">Las fotos de la mascota pueden verse en el mapa público, junto a una zona aproximada.</p>}
            </div>
            {found ? <section className="found-reporter-fields"><h2>Tu contacto para el reencuentro</h2><p className="field-help">El dueño verá primero las fotos y la descripción. Tu nombre y teléfono se compartirán con él únicamente si confirma que es su mascota.</p><div className="form-grid"><label className="field-label">Tu nombre<input name="finder_name" autoComplete="name" className="form-input" required minLength={2} maxLength={100} placeholder="¿Cómo te llamás?" /></label><PhoneField name="finder_phone" label="Teléfono de contacto" required /></div></section> : <>
              <label className="sighting-recent"><input type="checkbox" checked={recent} onChange={event => { changed(); setRecent(event.target.checked); }} />La vi recién</label>
              {!recent && <label className="field-label">¿Cuándo la viste?<input type="datetime-local" value={when} required className="form-input" onChange={event => { changed(); setWhen(event.target.value); }} /><span className="field-help">La fecha y la hora pueden ser aproximadas.</span></label>}
            </>}
            {error && <p role="alert" className="notice notice-error">{error}</p>}
            <div className="form-footer"><button type="submit" className="button button-primary">{busy ? "Enviando…" : found ? "Informar que la tengo conmigo" : "Enviar avistamiento"}</button>
              {found && !ownership.signedIn && <OwnerRecoveryLogin caseId={caseId} />}
              <p className="form-privacy">{found ? "Podés enviarlo sin crear una cuenta. Al enviar, autorizás a compartir tu nombre y teléfono con el dueño únicamente después de que confirme la identidad de la mascota. Tus datos de contacto no se publican." : "Podés enviarlo sin crear una cuenta. La ubicación exacta se compartirá de forma privada con el dueño si el reporte resulta relevante. La identidad de la mascota siempre está por confirmar."}</p></div>
            <p className="form-privacy form-legal">Consultá los <Link href="/terminos" target="_blank" rel="noopener noreferrer" aria-label="Términos y condiciones, se abre en otra pestaña">Términos y condiciones</Link> antes de enviar tu reporte.</p>
          </fieldset>
        </form>
      </>}
  </main>;
}
