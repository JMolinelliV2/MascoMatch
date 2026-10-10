"use client";
import Link from "next/link";
import { useEffect, useState } from "react";

export function VerifyEmailNotice({ email, showInstructions = true }: { email?: string; showInstructions?: boolean }) {
  const [busy, setBusy] = useState<"send" | "check" | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [preview, setPreview] = useState(false);
  const [waitUntil, setWaitUntil] = useState(0);
  const [remaining, setRemaining] = useState(0);

  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | undefined;
    const update = () => { const seconds = Math.max(0, Math.ceil((waitUntil - Date.now()) / 1000)); setRemaining(seconds); if (!seconds && timer) clearInterval(timer); };
    update();
    if (!waitUntil || waitUntil <= Date.now()) return;
    timer = setInterval(update, 1000);
    return () => clearInterval(timer);
  }, [waitUntil]);

  async function request() {
    if (busy || remaining) return;
    setBusy("send"); setError(""); setMessage("");
    try {
      const response = await fetch("/api/account-access/request-verification", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
      const data = await response.json();
      if (response.status === 429) {
        const retry = Number(response.headers.get("Retry-After"));
        setWaitUntil(Date.now() + (Number.isFinite(retry) && retry > 0 ? Math.min(retry, 3600) : 60) * 1000);
      }
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "No pudimos enviar el enlace. Intentá de nuevo.");
      if (data.already_verified) {
        setMessage("Tu correo ya está confirmado.");
        window.dispatchEvent(new Event("mascomatch:session"));
        return;
      }
      const local = data.delivery_mode === "preview";
      setPreview(local); setWaitUntil(Date.now() + 60_000);
      setMessage(local ? "El enlace llegará al buzón local de Mailpit." : "Revisá tu correo y abrí el enlace de confirmación. Si no aparece, revisá Spam.");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No pudimos enviar el enlace. Intentá de nuevo."); }
    finally { setBusy(null); }
  }

  async function check() {
    if (busy) return;
    setBusy("check"); setError(""); setMessage("");
    try {
      const response = await fetch("/api/session", { cache: "no-store" });
      if (!response.ok) throw new Error("No pudimos consultar tu cuenta. Intentá de nuevo.");
      const data = await response.json();
      if (!data.user) throw new Error("Tu sesión venció. Volvé a ingresar.");
      if (!data.user.email_verified) throw new Error("Tu correo todavía no está confirmado. Abrí el enlace del correo y tocá “Confirmar mi correo”.");
      setMessage("Tu correo está confirmado. Ya podés publicar.");
      window.dispatchEvent(new Event("mascomatch:session"));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No pudimos consultar la confirmación."); }
    finally { setBusy(null); }
  }

  return <aside className="notice email-verification-notice">
    <h3>Confirmá tu correo para publicar</h3>
    <p>{email ? <>Buscá el correo de MascoMatch en <strong>{email}</strong> y abrí el enlace de confirmación.</> : "Buscá el correo de MascoMatch y abrí el enlace de confirmación."} El enlace sirve una vez y vence a las 24 horas.</p>
    <p className="field-help">Si no lo encontrás, revisá Spam o pedí otro enlace.</p>
    <div className="location-actions">
      <button className="text-button" type="button" disabled={Boolean(busy) || remaining > 0} onClick={() => void request()}>{busy === "send" ? "Enviando…" : remaining > 0 ? `Reenviar en ${remaining}s` : "Reenviar enlace"}</button>
      <button className="text-button" type="button" disabled={Boolean(busy)} onClick={() => void check()}>{busy === "check" ? "Consultando…" : "Ya confirmé mi correo"}</button>
    </div>
    {message && <p role="status">{message}</p>}
    {error && <p role="alert" className="field-error">{error}</p>}
    {preview && <a href="http://localhost:8025" className="text-button" target="_blank" rel="noreferrer">Abrir buzón local de Mailpit</a>}
    {showInstructions && <Link href="/confirmar-correo" target="_blank" rel="noreferrer" className="text-button">Ver instrucciones de confirmación en otra pestaña</Link>}
  </aside>;
}
