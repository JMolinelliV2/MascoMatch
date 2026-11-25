"use client";
import { useEffect, useId, useState } from "react";
import type { FormEvent } from "react";
import { VerifyEmailNotice } from "./verify-email-notice";
import { Icon } from "./ui/pictogram";
import { RecoveryExperience } from "./recovery-experience";
import { ReviewSummary } from "./ui/review-summary";
import { ReviewIdentity } from "./ui/review-identity";
import type { AccountReview, ReviewState } from "@/lib/reviews";
import { ErrorState } from "./ui/error-state";
import { requestError } from "@/lib/request-error";

export function ReviewRequest({ caseId, recovered = false }: { caseId?: string; recovered?: boolean }) {
  const id = useId();
  const [state, setState] = useState<ReviewState | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [kept, setKept] = useState(false);
  const [rating, setRating] = useState(0);
  const [anonymous, setAnonymous] = useState(true);
  const [comment, setComment] = useState("");
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [refresh, setRefresh] = useState(0);
  const endpoint = caseId ? `/api/reviews/lost-cases/${encodeURIComponent(caseId)}` : "/api/reviews/me";

  useEffect(() => {
    const controller = new AbortController();
    const reload = () => setRefresh(value => value + 1);
    const sessionChanged = () => { setState(null); setExpanded(false); setMessage(""); setRefresh(value => value + 1); };
    window.addEventListener("mascomatch:reviews", reload);
    window.addEventListener("mascomatch:session", sessionChanged);
    window.addEventListener("focus", reload);
    void fetch(endpoint, { cache: "no-store", signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error(response.status === 401 ? "Ingresá de nuevo para consultar tu reseña." : "No pudimos consultar tu reseña.");
      const data: ReviewState = await response.json();
      if (!controller.signal.aborted) { setState(data); setError(""); }
    }).catch(cause => { if (!controller.signal.aborted) { setState(null); setError(requestError(cause, "No pudimos consultar tu reseña. Reintentá en unos instantes.")); } });
    return () => { controller.abort(); window.removeEventListener("mascomatch:reviews", reload); window.removeEventListener("mascomatch:session", sessionChanged); window.removeEventListener("focus", reload); };
  }, [endpoint, refresh]);

  function edit() {
    setRating(state?.review?.rating ?? 0);
    setComment(state?.review?.comment ?? "");
    setAnonymous(state?.review?.anonymous ?? true);
    setConsent(false); setExpanded(true); setDismissed(false); setKept(false); setError(""); setMessage("");
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || !state) return;
    if (!rating || comment.trim().length < 20 || !consent) { setError("Elegí una puntuación, escribí al menos 20 caracteres y autorizá la publicación."); return; }
    const editing = Boolean(state.review);
    setBusy(true); setError(""); setMessage("");
    try {
      const response = await fetch(endpoint, { method: editing ? "PATCH" : "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ rating, anonymous, comment: comment.trim(), consent }) });
      const data = await response.json();
      if (!response.ok) { if (response.status === 409) setRefresh(value => value + 1); throw new Error(typeof data.detail === "string" ? data.detail : "No pudimos guardar tu reseña."); }
      setState(current => current ? { ...current, review: data as AccountReview } : current);
      setExpanded(false); setKept(false); setConsent(false);
      setMessage(data.visibility === "HIDDEN" ? "Los cambios quedaron guardados. La reseña sigue oculta por moderación." : editing ? "Tu reseña quedó actualizada." : "Gracias por compartir tu experiencia.");
      window.dispatchEvent(new Event("mascomatch:reviews"));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No pudimos guardar tu reseña."); }
    finally { setBusy(false); }
  }

  async function withdraw() {
    if (busy) return;
    setBusy(true); setError(""); setMessage("");
    try {
      const response = await fetch(endpoint, { method: "DELETE" });
      if (!response.ok) throw new Error("No pudimos retirar tu reseña. Intentá de nuevo.");
      setState(current => current?.review ? { ...current, review: { ...current.review, visibility: "WITHDRAWN" } } : current);
      setKept(false); setMessage("Tu reseña dejó de mostrarse en la portada.");
      window.dispatchEvent(new Event("mascomatch:reviews"));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No pudimos retirar tu reseña."); }
    finally { setBusy(false); }
  }

  if (!state && !error) return null;
  if (state && !state.eligible && !state.review) return null;
  if (dismissed && !expanded && !state?.review) return <div className="review-later"><button type="button" className="text-button" onClick={edit}>Dejar una reseña de MascoMatch</button></div>;
  return <section className="review-request" aria-labelledby={`${id}-title`}>
    {recovered && caseId && <RecoveryExperience caseId={caseId} />}
    <div className="review-request-heading"><span className="feature-icon"><Icon name="heart" /></span><div>
      <h3 id={`${id}-title`}>{state?.review ? "Tu reseña de MascoMatch" : "¿Cómo fue tu experiencia con MascoMatch?"}</h3>
      <p>{state?.review ? "Esta es la reseña que ya compartiste. Tenés una sola por cuenta: podés dejarla como está o actualizar tu experiencia." : recovered ? "Nos alegra que tu mascota esté con vos. Si querés, contanos cómo fue la búsqueda." : caseId ? "Ahora que cerraste el aviso, podés contarnos cómo fue la búsqueda, cualquiera haya sido el resultado." : "Podés compartir tu experiencia después de cerrar un aviso o recuperar a tu mascota."}</p>
    </div></div>
    {state?.review && !expanded && <>
      <ReviewSummary review={state.review} />
      <div className="location-actions">
        <button type="button" disabled={busy} className="button button-secondary" onClick={edit}>{state.review.visibility === "WITHDRAWN" ? "Editar y volver a publicar" : "Editar mi reseña"}</button>
        {!kept && <button type="button" disabled={busy} className="text-button" onClick={() => { setKept(true); setMessage("Tu reseña se mantiene sin cambios."); }}>Dejarla así</button>}
        {state.review.visibility !== "WITHDRAWN" && <button type="button" disabled={busy} className="text-button" onClick={() => void withdraw()}>{busy ? "Retirando…" : "Retirar de la portada"}</button>}
      </div>
    </>}
    {state && !state.review && !expanded && <div className="location-actions"><button type="button" className="button button-secondary" onClick={edit}>Escribir una reseña</button><button type="button" className="text-button" onClick={() => setDismissed(true)}>Ahora no</button><p className="field-help">Es opcional{caseId ? `. Tu aviso ya quedó ${recovered ? "marcado como encontrado" : "cerrado"}` : ""}.</p></div>}
    {state && expanded && <>
      {!state.email_verified && <VerifyEmailNotice />}
      <form onSubmit={submit} className="review-form">
        <fieldset disabled={busy || !state.email_verified} className="section-fields">
          <fieldset className="review-rating-options"><legend>¿Cómo valorarías tu experiencia?</legend><div>{[1, 2, 3, 4, 5].map(value => <label key={value} className={rating === value ? "is-selected" : ""}><input type="radio" name={`${id}-rating`} value={value} required checked={rating === value} onChange={() => setRating(value)} /><span>{value}<span aria-hidden="true"> ★</span><span className="sr-only"> {value === 1 ? "estrella" : "estrellas"} de 5</span></span></label>)}</div></fieldset>
          <ReviewIdentity id={id} accountName={state.account_display_name} anonymous={anonymous} onChange={setAnonymous} />
          <label className="field-label" htmlFor={`${id}-comment`}>Tu experiencia<textarea id={`${id}-comment`} className="form-input" rows={4} required minLength={20} maxLength={800} value={comment} onChange={event => setComment(event.target.value)} placeholder="Contanos qué te resultó útil y qué podríamos mejorar." aria-describedby={`${id}-comment-help`} /><span className="field-help" id={`${id}-comment-help`}>{comment.length}/800 · Mínimo 20 caracteres. Evitá incluir teléfonos, direcciones o datos de otras personas.</span></label>
          <label className="review-consent"><input type="checkbox" checked={consent} required onChange={event => setConsent(event.target.checked)} /><span>Autorizo que mi reseña se publique en la portada {anonymous ? "de forma anónima, sin mi foto" : `con el nombre ${state.account_display_name} y mi foto de perfil, si tengo`}.</span></label>
          {state.review?.visibility === "HIDDEN" && <p className="field-help">Editar tu opinión no cambia la decisión de moderación: seguirá oculta hasta que sea revisada.</p>}
          <div className="location-actions"><button type="submit" className="button button-primary">{busy ? "Guardando…" : state.review?.visibility === "WITHDRAWN" ? "Guardar y volver a publicar" : state.review ? "Guardar cambios" : "Publicar reseña"}</button><button type="button" className="text-button" disabled={busy} onClick={() => setExpanded(false)}>Cancelar</button></div>
        </fieldset>
      </form>
    </>}
    {message && <p className="notice notice-success" role="status">{message}</p>}
    {error && (!state ? <ErrorState compact headingLevel={3} title="No pudimos consultar tu reseña" description={error} onRetry={() => setRefresh(value => value + 1)} /> : <p className="notice notice-warning" role="alert">{error}</p>)}
  </section>;
}
