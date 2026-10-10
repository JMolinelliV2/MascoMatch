"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { LocationMap } from "../location-map";
import { MatchFeedback } from "../match-feedback";
import type { FeedbackSaved } from "../match-feedback";

import { VerifyEmailNotice } from "../verify-email-notice";
import { useSessionRefresh } from "../use-session-refresh";
import { ReviewRequest } from "../review-request";
import { SightingComparison } from "../ui/sighting-comparison";
import { PhotoGallery } from "../ui/photo-viewer";
type User = { email_verified?: boolean; email_verification_required?: boolean; id: string; name: string; email: string; notification_preferences: { email?: boolean } };
type Notice = { id: string; kind: string; title: string; body: string; read_at: string | null; created_at: string; lost_case_id: string; pet_name: string; observed_at: string; public_location: string | null; latitude: number | null; longitude: number | null; reasons: string[]; photo_ids: string[]; email_status: string; match_id: string | null; match_status: string | null; reporter_contact:string|null; linked_to_notice?:boolean; matching_status?:string|null };
type Inbox = { items: Notice[]; unread_count: number; total: number };

function date(value: string) { return new Intl.DateTimeFormat("es-UY", { dateStyle: "medium", timeStyle: "short", timeZone:"America/Montevideo" }).format(new Date(value)); }

export function NotificationsInbox({ selectedId }: { selectedId?: string }) {
  const sessionVersion = useSessionRefresh();
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [inbox, setInbox] = useState<Inbox | null>(null);
  const [refresh, setRefresh] = useState(0);
  const [offset, setOffset] = useState(0);
  const [map, setMap] = useState<string | null>(null);
  const [marking, setMarking] = useState<string | null>(null);
  const [feedbackMessage, setFeedbackMessage] = useState("");
  const [selectedReviewed, setSelectedReviewed] = useState(false);
  const [reviewCaseId, setReviewCaseId] = useState<string | null>(null);

  useEffect(() => { setSelectedReviewed(false); setFeedbackMessage(""); setReviewCaseId(null); }, [selectedId, user?.id]);

  useEffect(() => {
    const controller = new AbortController();
    void fetch("/api/session", { cache: "no-store", signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error("No pudimos consultar tu sesión.");
      const session = await response.json();
      if (!controller.signal.aborted) setUser(session.user);
    }).catch(cause => { if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : "No pudimos consultar tu sesión."); })
      .finally(() => { if (!controller.signal.aborted) setChecking(false); });
    return () => controller.abort();
  }, [sessionVersion]);

  useEffect(() => {
    if (!user || selectedReviewed) return;
    let disposed = false;
    let controller: AbortController | undefined;
    async function load() {
      controller?.abort(); controller = new AbortController();
      const signal = controller.signal;
      try {
        const response = await fetch(selectedId ? `/api/notifications/${encodeURIComponent(selectedId)}` : `/api/notifications?limit=20&offset=${offset}`, { cache: "no-store", signal });
        if (response.status === 401) { setUser(null); throw new Error("Tu sesión venció. Volvé a ingresar para ver tus avisos."); }
        if (response.status === 404) throw new Error("El aviso de esta alerta ya no está disponible. Podés consultar tus otras notificaciones.");
        if (!response.ok) throw new Error("No pudimos cargar las notificaciones. Intentá de nuevo.");
        const payload = await response.json();
        const data: Inbox = selectedId ? { items: [payload], total: 1, unread_count: payload.read_at ? 0 : 1 } : payload;
        if (!disposed && !signal.aborted) { setInbox(data); setError(""); }
      } catch (cause) { if (!disposed && !signal.aborted) setError(cause instanceof Error ? cause.message : "No pudimos cargar las notificaciones."); }
    }
    setInbox(null); void load();
    const timer = setInterval(load, 20000);
    window.addEventListener("focus", load);
    return () => { disposed = true; controller?.abort(); clearInterval(timer); window.removeEventListener("focus", load); };
  }, [user?.id, refresh, offset, selectedId, selectedReviewed]);

  function feedbackSaved(noticeId: string, result: FeedbackSaved) {
    if (result.recovered) setReviewCaseId(result.caseId);
    setFeedbackMessage(result.recovered ? "Tu mascota quedó marcada como encontrada. La búsqueda está cerrada y el aviso ya no aparece entre los animales perdidos."
      : result.status === "RESOLVED" ? "Confirmaste el avistamiento. La búsqueda sigue activa hasta que recuperes a tu mascota."
      : result.status === "FALSE_MATCH" ? "Descartaste este avistamiento. Tu búsqueda sigue activa." : "Guardaste el avistamiento como posible coincidencia. Tu búsqueda sigue activa.");
    setInbox(current => {
      if (!current) return current;
      const removed = current.items.filter(item => result.recovered ? item.lost_case_id === result.caseId : result.status === "FALSE_MATCH" && item.id === noticeId);
      const confirmed = result.status === "RESOLVED" && !result.recovered ? current.items.find(item => item.id === noticeId) : undefined;
      return { ...current, total: Math.max(0, current.total - removed.length),
        unread_count: Math.max(0, current.unread_count - removed.filter(item => !item.read_at).length - (confirmed && !confirmed.read_at ? 1 : 0)),
        items: current.items.filter(item => !removed.includes(item)).map(item => item.id === noticeId ? { ...item, match_status: result.status,
          read_at: confirmed ? item.read_at || new Date().toISOString() : item.read_at,
          email_status: confirmed && item.email_status === "PENDING" ? "CANCELLED" : item.email_status,
        } : item),
      };
    });
    if (selectedId && (result.recovered || result.status === "FALSE_MATCH")) setSelectedReviewed(true);
    else setRefresh(value => value + 1);
  }

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError("");
    const formElement = event.currentTarget;
    const fields = new FormData(formElement);
    try {
      const response = await fetch("/api/session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ mode: "login", email: fields.get("email"), password: fields.get("password") }) });
      const data = await response.json();
      if (!response.ok) throw new Error(response.status === 401 ? "El correo o la contraseña no son correctos." : "No pudimos iniciar sesión. Intentá de nuevo.");
      formElement.reset(); setUser(data.user); setOffset(0);
      window.dispatchEvent(new Event("mascomatch:session"));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No pudimos iniciar sesión."); }
    finally { setBusy(false); }
  }

  async function logout() {
    const response = await fetch("/api/session", { method: "DELETE" });
    if (!response.ok) { setError("No pudimos cerrar la sesión. Intentá de nuevo."); return; }
    setUser(null); setInbox(null); window.dispatchEvent(new Event("mascomatch:session"));
  }

  async function read(id: string) {
    setMarking(id);
    try {
      const response = await fetch(`/api/notifications/${id}/read`, { method: "PATCH" });
      if (!response.ok) throw new Error("No pudimos marcar la notificación como leída.");
      const notice = await response.json();
      setInbox(current => current ? { ...current, unread_count: Math.max(0, current.unread_count - 1), items: current.items.map(item => item.id === id ? notice : item) } : current);
      window.dispatchEvent(new Event("mascomatch:notifications"));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No pudimos actualizar la notificación."); }
    finally { setMarking(null); }
  }

  return <main id="main-content" className="page notifications-page">
    <Link href="/" className="back-link"><span aria-hidden="true">←</span> Volver al inicio</Link>
    <h1>Notificaciones</h1><p className="page-intro">Avistamientos que podrían ayudar a encontrar a tus animales.</p>
    {checking ? <p role="status" className="page-intro">Consultando tu sesión…</p> : !user ? <form onSubmit={login} className="notification-login">
      <h2>Ingresá con la cuenta de tu aviso</h2><p className="field-help">Así podrás ver los lugares y las fotos que compartieron.</p>
      <fieldset disabled={busy} className="form-controls section-fields">
        <label className="field-label">Correo electrónico<input name="email" type="email" required maxLength={320} autoComplete="email" className="form-input" /></label>
        <label className="field-label">Contraseña<input name="password" type="password" required maxLength={128} autoComplete="current-password" className="form-input" /></label>
        <button type="submit" className="button button-primary">{busy ? "Ingresando…" : "Ingresar"}</button>
      </fieldset>
      <p>¿Todavía no tenés cuenta? <Link className="text-button" href="/crear-cuenta">Crear cuenta</Link></p>
      <Link className="text-button" href="/recuperar">Olvidé mi contraseña</Link>
    </form> : <>
      {user.email_verification_required && !user.email_verified && <VerifyEmailNotice email={user.email} />}
      <div className="notifications-account"><span>{user.name}</span><button type="button" className="text-button" onClick={() => void logout()}>Cerrar sesión</button></div>
      <p><Link href="/mi-cuenta#notificaciones" className="text-button">Configurar notificaciones en Mi cuenta</Link></p>
      {selectedId && <Link href="/notificaciones" className="text-button">Ver todas las notificaciones</Link>}
      <div className="notifications-toolbar"><span aria-live="polite">{selectedId ? "Avistamiento de la alerta" : inbox ? `${inbox.unread_count} sin leer` : "Cargando avisos…"}</span><button type="button" className="text-button" onClick={() => setRefresh(value => value + 1)}>Actualizar</button></div>
      {feedbackMessage && <div className="notice" role="status"><p>{feedbackMessage}</p><Link className="text-button" href="/mis-avisos">Ver el estado en Mis avisos</Link></div>}
      {reviewCaseId && <ReviewRequest key={reviewCaseId} caseId={reviewCaseId} recovered />}
      {inbox?.total === 0 && !selectedReviewed && <div className="lost-dogs-empty"><h2>Sin avistamientos pendientes</h2><p>Acá aparecerán los avistamientos enviados desde tus avisos y las posibles coincidencias de otros reportes.</p></div>}
      {inbox && <div className="notifications-list">{inbox.items.map(notice => <article key={notice.id} className={`notification-card ${notice.read_at ? "" : "notification-unread"}`}>
        {notice.linked_to_notice ? <SightingComparison status={notice.matching_status} reviewStatus={notice.match_status} /> : <span className="lost-status">{notice.match_status === "RESOLVED" ? "Avistamiento confirmado · búsqueda activa" : notice.kind === "POSSIBLE_MATCH" ? "Posible coincidencia" : notice.photo_ids.length ? "Con fotos · por confirmar" : "Sin foto · por confirmar"}</span>}
        <h2>{notice.title}</h2><p>{notice.body}</p>
        <dl className="review-details"><div><dt>Cuándo lo vieron</dt><dd>{date(notice.observed_at)}</dd></div><div><dt>Zona del avistamiento</dt><dd>{notice.public_location || "Lugar indicado en el mapa"}</dd></div></dl>
        {notice.reasons.length > 0 && <ul className="notification-reasons">{notice.reasons.map(reason => <li key={reason}>{reason}</li>)}</ul>}
        {notice.reporter_contact&&<p>La persona autorizó compartir su contacto: <a href={`mailto:${encodeURIComponent(notice.reporter_contact)}`}>{notice.reporter_contact}</a></p>}
        {notice.photo_ids.length > 0 && <PhotoGallery title={`Fotos del avistamiento para ${notice.pet_name}`} photos={notice.photo_ids.map((photoId, index) => ({ id: photoId, thumbnailSrc: `/api/notifications/${encodeURIComponent(notice.id)}/photos/${encodeURIComponent(photoId)}`, src: `/api/notifications/${encodeURIComponent(notice.id)}/photos/${encodeURIComponent(photoId)}/large`, alt: `foto ${index + 1} del avistamiento para ${notice.pet_name}` }))} />}
        <div className="location-actions"><Link href={`/perdidos/${notice.lost_case_id}`} className="text-button">Ver mi aviso</Link>
          {notice.latitude !== null && notice.longitude !== null && <button type="button" className="text-button" aria-expanded={map === notice.id} onClick={() => setMap(current => current === notice.id ? null : notice.id)}>{map === notice.id ? "Ocultar mapa" : "Ver lugar del avistamiento"}</button>}
          {!notice.read_at && <button type="button" className="text-button" disabled={marking === notice.id} onClick={() => void read(notice.id)}>Marcar como leída</button>}
        </div>
        {map === notice.id && notice.latitude !== null && notice.longitude !== null && <LocationMap latitude={notice.latitude} longitude={notice.longitude} editable={false} />}
        {notice.match_id && <MatchFeedback id={notice.match_id} caseId={notice.lost_case_id} status={notice.match_status} onSaved={result => feedbackSaved(notice.id, result)} />}
        {notice.email_status === "SENT" && <p className="field-help">Alerta enviada también por correo.</p>}
        {notice.email_status === "PREVIEWED" && <p className="field-help">Correo generado en el servidor local de pruebas.</p>}
        {notice.email_status === "FAILED" && <p className="field-help">El correo no pudo enviarse. La notificación quedó guardada acá.</p>}
        {notice.email_status === "PENDING" && <p className="field-help">La alerta por correo está pendiente de envío.</p>}
      </article>)}</div>}
      {inbox && inbox.total > 20 && <nav className="lost-dogs-pagination" aria-label="Páginas de notificaciones"><button type="button" className="button button-secondary" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 20))}>Anterior</button><span>Página {Math.floor(offset / 20) + 1}</span><button type="button" className="button button-secondary" disabled={offset + inbox.items.length >= inbox.total} onClick={() => setOffset(offset + 20)}>Siguiente</button></nav>}
    </>}
    {error && <p role="alert" className="notice notice-error">{error}</p>}
  </main>;
}
