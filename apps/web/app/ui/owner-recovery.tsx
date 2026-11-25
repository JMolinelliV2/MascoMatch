"use client";

import Link from "next/link";
import { useEffect, useId, useRef, useState } from "react";
import { ReviewRequest } from "../review-request";
import { Icon } from "./pictogram";
import { ownerRecoveryLoginHref } from "@/lib/login-return";

export function OwnerRecoveryLogin({ caseId }: { caseId: string }) {
  return <p className="owner-recovery-login">
    <Link className="text-button" href={ownerRecoveryLoginHref(caseId)}>Soy el dueño del aviso</Link>
    <span className="field-help">Ingresá con tu cuenta para marcar que ya la recuperaste.</span>
  </p>;
}

export function MarkRecovered({ caseId, onRecovered }: { caseId: string; onRecovered: () => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const pending = useRef(false);

  async function recover() {
    if (pending.current) return;
    pending.current = true; setBusy(true); setError("");
    try {
      const response = await fetch(`/api/account/lost-cases/${encodeURIComponent(caseId)}`, {
        method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: "FOUND" }),
      });
      if (!response.ok) throw new Error(response.status === 401 ? "Tu sesión venció. Volvé a ingresar para cerrar tu búsqueda." : "No pudimos marcar tu mascota como encontrada. Intentá de nuevo.");
      if ((await response.json()).status !== "FOUND") throw new Error("No pudimos confirmar el cambio. Revisá tu aviso e intentá de nuevo.");
      onRecovered();
      window.dispatchEvent(new Event("mascomatch:cases"));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "No pudimos actualizar tu aviso.");
    } finally { pending.current = false; setBusy(false); }
  }

  return <div className="owner-recovery-action" aria-busy={busy}>
    <button type="button" className="button button-primary" disabled={busy} onClick={() => void recover()}><Icon name="heart" />{busy ? "Guardando…" : "Ya la tengo conmigo"}</button>
    {error && <p className="notice notice-warning" role="alert">{error}</p>}
  </div>;
}

export function RecoverySuccess({ caseId, name }: { caseId: string; name?: string }) {
  const id = useId();
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => { heading.current?.focus(); }, []);

  return <>
    <section className="confirmation-card recovery-confirmation" aria-labelledby={id}>
      <div className="confirmation-summary">
        <span className="confirmation-status"><Icon name="check" />Mascota recuperada</span>
        <h1 id={id} ref={heading} tabIndex={-1}>{name ? `¡${name} volvió a casa!` : "¡Tu mascota volvió a casa!"}</h1>
        <p className="confirmation-message">Tu aviso quedó marcado como encontrado. La búsqueda está cerrada y ya no aparece entre las mascotas perdidas ni en el mapa.</p>
        <div className="confirmation-actions"><Link href="/mis-avisos" className="button button-primary"><Icon name="grid" />Gestionar mis avisos</Link></div>
      </div>
    </section>
    <ReviewRequest caseId={caseId} recovered />
  </>;
}
