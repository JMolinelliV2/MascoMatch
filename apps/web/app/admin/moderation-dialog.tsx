"use client";
import { useEffect, useId, useRef, useState } from "react";
import type { FormEvent } from "react";

export type ModerationAction = { url: string; status: string; title: string; description: string };
export function ModerationDialog({ action, onClose, onSaved }: { action: ModerationAction; onClose: () => void; onSaved: (message: string) => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [reason, setReason] = useState("");
  const id = useId();
  useEffect(() => {
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    dialog.current?.showModal();
    return () => { document.body.style.overflow = previous; };
  }, []);
  async function confirm(event: FormEvent) {
    event.preventDefault();
    if (reason.trim().length < 3) { setError("Escribí un motivo de al menos 3 caracteres."); return; }
    setBusy(true); setError("");
    try {
      const response = await fetch(action.url, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: action.status, reason: reason.trim() }) });
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "No pudimos aplicar el cambio.");
      onSaved("Cambio aplicado y registrado en la auditoría.");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No pudimos aplicar el cambio."); }
    finally { setBusy(false); }
  }
  return <dialog ref={dialog} className="saved-changes-dialog admin-moderation-dialog" aria-labelledby={`${id}-title`} aria-describedby={`${id}-description`} onClose={onClose} onCancel={event => { if (busy) event.preventDefault(); }}>
    <h2 id={`${id}-title`}>{action.title}</h2><p id={`${id}-description`}>{action.description}</p>
    <form onSubmit={confirm}><label className="field-label" htmlFor={`${id}-reason`}>Motivo de la acción<textarea id={`${id}-reason`} className="form-input" required minLength={3} maxLength={1000} value={reason} onChange={event => setReason(event.target.value)} disabled={busy} /></label>
      {error && <p role="alert" className="notice notice-warning">{error}</p>}
      <div className="admin-dialog-actions"><button type="button" className="button button-secondary" autoFocus disabled={busy} onClick={() => dialog.current?.close()}>Cancelar</button><button type="submit" className="button button-primary" disabled={busy}>{busy ? "Aplicando…" : "Confirmar cambio"}</button></div>
    </form>
  </dialog>;
}
