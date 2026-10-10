"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import type { SessionUser } from "../account-session";
import { useSessionRefresh } from "../use-session-refresh";
import { AccountLoading } from "../ui/account-loading";

export function LoginForm() {
  const sessionVersion = useSessionRefresh();
  const router = useRouter();
  const [user, setUser] = useState<SessionUser | null>(null);
  const [checking, setChecking] = useState(true);
  const [sessionUnavailable, setSessionUnavailable] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    setSessionUnavailable(false); setError("");
    void fetch("/api/session", { cache: "no-store", signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error("No pudimos consultar tu sesión. Intentá de nuevo.");
      const data = await response.json();
      if (!controller.signal.aborted) setUser(data.user);
    }).catch(cause => {
      if (!controller.signal.aborted) { setSessionUnavailable(true); setError(cause instanceof Error ? cause.message : "No pudimos consultar tu sesión."); }
    }).finally(() => { if (!controller.signal.aborted) setChecking(false); });
    return () => controller.abort();
  }, [refresh, sessionVersion]);

  useEffect(() => {
    if (user) router.replace(user.email_verified ? "/mis-avisos" : "/confirmar-correo");
  }, [user, router]);

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || user || checking || sessionUnavailable) return;
    const form = event.currentTarget;
    const values = new FormData(form);
    setBusy(true); setError("");
    try {
      const response = await fetch("/api/session", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: "login", email: String(values.get("email") || "").trim(), password: String(values.get("password") || "") }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(response.status === 401 ? "El correo o la contraseña no son correctos."
        : response.status === 403 ? "Esta cuenta no está disponible."
        : response.status === 422 ? "Revisá el correo y la contraseña que ingresaste."
        : response.status === 429 ? "Hubo demasiados intentos. Esperá unos minutos y volvé a intentar."
        : "No pudimos iniciar sesión. Intentá de nuevo.");
      form.reset(); setUser(data.user);
      window.dispatchEvent(new Event("mascomatch:session"));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No pudimos iniciar sesión. Intentá de nuevo."); }
    finally { setBusy(false); }
  }

  if (checking) return <AccountLoading description="Estamos abriendo tu espacio en MascoMatch." />;
  if (sessionUnavailable) return <div className="notice notice-warning" role="alert"><p>{error}</p><button type="button" className="text-button" onClick={() => { setChecking(true); setRefresh(value => value + 1); }}>Reintentar</button></div>;
  if (user) return <AccountLoading title={user.email_verified ? "Abriendo tus avisos" : "Abriendo la confirmación de correo"} description={user.email_verified ? "Enseguida vas a poder seguir tus búsquedas." : "Ya falta un paso para empezar a publicar."} />;

  return <form className="notification-login account-form" onSubmit={login} aria-busy={busy}>
    <fieldset className="section-fields" disabled={busy}>
      <label className="field-label">Correo electrónico<input className="form-input" name="email" type="email" required maxLength={320} autoComplete="email" /></label>
      <label className="field-label">Contraseña<input className="form-input" name="password" type="password" required maxLength={128} autoComplete="current-password" /></label>
      <button className="button button-primary" type="submit">{busy ? "Ingresando…" : "Ingresar"}</button>
    </fieldset>
    {error && <p role="alert" className="notice notice-warning">{error}</p>}
    <p>¿Todavía no tenés cuenta? <Link className="text-button" href="/crear-cuenta">Crear cuenta</Link></p>
    <Link className="text-button" href="/recuperar">Olvidé mi contraseña</Link>
  </form>;
}
