"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import type { SessionUser } from "../account-session";
import { VerifyEmailNotice } from "../verify-email-notice";

export function ConfirmationForm() {
  const code = useSearchParams().get("codigo");
  const [user, setUser] = useState<SessionUser | null>(null);
  const [checking, setChecking] = useState(true);
  const [sessionError, setSessionError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [busy, setBusy] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [emailChanged, setEmailChanged] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let controller: AbortController | undefined;
    async function load() {
      controller?.abort(); controller = new AbortController();
      const signal = controller.signal;
      try {
        const response = await fetch("/api/session", { cache: "no-store", signal });
        if (!response.ok) throw new Error("No pudimos consultar tu cuenta. Intentá de nuevo.");
        const data = await response.json();
        if (!signal.aborted) { setUser(data.user); setSessionError(""); }
      } catch (cause) { if (!signal.aborted) setSessionError(cause instanceof Error ? cause.message : "No pudimos consultar tu cuenta."); }
      finally { if (!signal.aborted) setChecking(false); }
    }
    void load(); window.addEventListener("mascomatch:session", load); window.addEventListener("focus", load);
    return () => { controller?.abort(); window.removeEventListener("mascomatch:session", load); window.removeEventListener("focus", load); };
  }, [refresh]);

  async function confirm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || !code) return;
    setBusy(true); setError("");
    try {
      const response = await fetch("/api/account-access/verify-email", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ code }) });
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "No pudimos confirmar el correo. Intentá de nuevo.");
      setConfirmed(true);
      setEmailChanged(Boolean(data.email_changed));
      if (data.email_changed) setUser(null);
      window.history.replaceState(null, "", "/confirmar-correo");
      window.dispatchEvent(new Event("mascomatch:session"));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No pudimos confirmar tu correo. Intentá de nuevo."); }
    finally { setBusy(false); }
  }

  if (confirmed || (!code && user?.email_verified)) return <section className="notification-login account-form">
    <h2>{emailChanged ? "Tu correo quedó actualizado" : confirmed ? "Tu correo quedó confirmado" : "Tu correo ya está confirmado"}</h2>
    <p role="status">{emailChanged ? "Ingresá con tu nuevo correo y tu contraseña habitual. Las sesiones anteriores se cerraron." : "Ya podés publicar avisos desde tu cuenta y recibir alertas por correo."}</p>
    <div className="location-actions"><Link href={!emailChanged && user?.email_verified ? "/mi-cuenta" : "/login"} className="button button-primary">{!emailChanged && user?.email_verified ? "Ir a mi cuenta" : "Ingresar"}</Link>{!emailChanged && <Link href="/perdi" className="text-button">Publicar una mascota perdida</Link>}</div>
    <p className="field-help">Si tenés un formulario abierto en otra pestaña, volvé a él. Tus datos siguen ahí.</p>
  </section>;

  if (code) return <form className="notification-login account-form account-confirmation" onSubmit={confirm} aria-busy={busy}>
    <h2>Confirmá que este correo es tuyo</h2>
    <p>Un paso para ayudar a mantener los avisos confiables. El enlace sirve una sola vez y vence a las 24 horas.</p>
    <button className="button button-primary" type="submit" disabled={busy}>{busy ? "Confirmando…" : "Confirmar mi correo"}</button>
    {error && <><p role="alert" className="notice notice-warning">{error}</p><Link href="/confirmar-correo" className="text-button" onClick={() => setError("")}>Pedir un nuevo enlace</Link></>}
  </form>;

  if (checking) return <p role="status">Consultando tu cuenta…</p>;
  if (sessionError) return <div className="notice notice-warning" role="alert"><p>{sessionError}</p><button type="button" className="text-button" onClick={() => setRefresh(value => value + 1)}>Reintentar</button></div>;
  if (user) return <section className="notification-login account-form"><VerifyEmailNotice email={user.email} showInstructions={false} /><Link href="/mi-cuenta" className="text-button">Ir a mi cuenta</Link></section>;
  return <section className="notification-login account-form"><h2>Abrí el enlace de tu correo</h2><p>Buscá el mensaje de MascoMatch y tocá “Confirmar mi correo”. Si necesitás otro enlace, ingresá a tu cuenta para reenviarlo.</p><div className="location-actions"><Link href="/login" className="button button-primary">Ingresar</Link><Link href="/crear-cuenta" className="text-button">Crear cuenta</Link></div></section>;
}
