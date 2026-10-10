"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import type { SessionUser } from "../account-session";
import { VerifyEmailNotice } from "../verify-email-notice";

export function RegistrationForm() {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [checking, setChecking] = useState(true);
  const [sessionUnavailable, setSessionUnavailable] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    setChecking(true); setSessionUnavailable(false); setError("");
    void fetch("/api/session", { cache: "no-store", signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error("No pudimos consultar tu sesión. Intentá de nuevo.");
      const data = await response.json();
      if (!controller.signal.aborted) setUser(data.user);
    }).catch(cause => {
      if (!controller.signal.aborted) { setSessionUnavailable(true); setError(cause instanceof Error ? cause.message : "No pudimos consultar tu sesión."); }
    }).finally(() => { if (!controller.signal.aborted) setChecking(false); });
    return () => controller.abort();
  }, [refresh]);

  async function register(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || user) return;
    const form = event.currentTarget;
    const values = new FormData(form);
    const name = String(values.get("name") || "").trim();
    const password = String(values.get("password") || "");
    setError("");
    if (!name) { setError("Ingresá tu nombre o un apodo."); return; }
    if (password !== values.get("confirmPassword")) { setError("Las contraseñas no coinciden. Volvé a escribirlas."); return; }
    setBusy(true);
    try {
      const response = await fetch("/api/session", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: "register", name, email: String(values.get("email") || "").trim(), password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(response.status === 409 ? "Ya existe una cuenta con ese correo. Ingresá o recuperá tu contraseña."
        : response.status === 422 ? "Revisá tus datos: ingresá un correo válido y una contraseña de entre 12 y 128 caracteres."
        : response.status === 429 ? "Hubo demasiados intentos. Esperá unos minutos y volvé a intentar."
        : "No pudimos crear tu cuenta. Intentá de nuevo.");
      form.reset(); setUser(data.user); setCreated(true);
      window.dispatchEvent(new Event("mascomatch:session"));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No pudimos crear tu cuenta. Intentá de nuevo."); }
    finally { setBusy(false); }
  }

  async function logout() {
    setBusy(true); setError("");
    try {
      const response = await fetch("/api/session", { method: "DELETE" });
      if (!response.ok) throw new Error("No pudimos cerrar tu sesión. Intentá de nuevo.");
      setUser(null); setCreated(false);
      window.dispatchEvent(new Event("mascomatch:session"));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No pudimos cerrar tu sesión."); }
    finally { setBusy(false); }
  }

  if (checking) return <p role="status">Consultando tu sesión…</p>;
  if (sessionUnavailable) return <div className="notice notice-warning" role="alert"><p>{error}</p><button type="button" className="text-button" onClick={() => setRefresh(value => value + 1)}>Reintentar</button></div>;
  if (user) return <section className="notification-login account-registration">
    <h2>{created ? "Tu cuenta está creada" : "Ya tenés una sesión iniciada"}</h2>
    <p role={created ? "status" : undefined}>{created ? "Ya ingresaste a MascoMatch. Podés empezar a usar tu cuenta." : `Estás usando la cuenta de ${user.name}.`}</p>
    {user.email_verification_required && !user.email_verified && <VerifyEmailNotice />}
    <div className="location-actions"><Link href="/mis-avisos" className="button button-primary">Ir a mi cuenta</Link><Link href="/perdidos" className="text-button">Ver animales perdidos</Link></div>
    <button type="button" className="text-button" disabled={busy} onClick={() => void logout()}>{busy ? "Cerrando sesión…" : "Cerrar sesión"}</button>
    {error && <p role="alert" className="notice notice-warning">{error}</p>}
  </section>;

  return <form className="notification-login account-registration" onSubmit={register} aria-busy={busy}>
    <fieldset className="section-fields" disabled={busy}>
      <label className="field-label">Nombre o apodo<input className="form-input" name="name" required minLength={1} maxLength={120} autoComplete="nickname" /></label>
      <label className="field-label">Correo electrónico<input className="form-input" name="email" type="email" required maxLength={320} autoComplete="email" /><span className="field-help">Para recibir alertas y recuperar el acceso a tu cuenta.</span></label>
      <label className="field-label">Contraseña<input className="form-input" name="password" type="password" required minLength={12} maxLength={128} autoComplete="new-password" /><span className="field-help">Usá al menos 12 caracteres.</span></label>
      <label className="field-label">Repetí la contraseña<input className="form-input" name="confirmPassword" type="password" required minLength={12} maxLength={128} autoComplete="new-password" /></label>
      <button className="button button-primary" type="submit">{busy ? "Creando cuenta…" : "Crear cuenta"}</button>
    </fieldset>
    {error && <p role="alert" className="notice notice-warning">{error}</p>}
    <p>¿Ya tenés una cuenta? <Link className="text-button" href="/mis-avisos">Ingresar</Link></p>
    <Link className="text-button" href="/recuperar">Olvidé mi contraseña</Link>
  </form>;
}
