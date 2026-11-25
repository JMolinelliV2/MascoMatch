"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import type { SessionUser } from "../account-session";
import { useSessionRefresh } from "../use-session-refresh";
import { AccountLoading } from "../ui/account-loading";
import { AuthPasswordField } from "../ui/auth-password-field";
import { Icon } from "../ui/pictogram";
import { loginDestination, ownerRecoveryReturnPath } from "@/lib/login-return";
import { ErrorState } from "../ui/error-state";

export function LoginForm({ returnTo }: { returnTo?: string }) {
  const sessionVersion = useSessionRefresh();
  const router = useRouter();
  const [user, setUser] = useState<SessionUser | null>(null);
  const [checking, setChecking] = useState(true);
  const [sessionUnavailable, setSessionUnavailable] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const recoveryReturn = ownerRecoveryReturnPath(returnTo);

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
    if (user) router.replace(loginDestination(recoveryReturn, user.email_verified));
  }, [user, router, recoveryReturn]);

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
  if (sessionUnavailable) return <ErrorState compact title="No pudimos comprobar tu sesión" description="No logramos consultar tu cuenta. Reintentá para continuar con el ingreso." onRetry={() => { setChecking(true); setRefresh(value => value + 1); }} />;
  if (user) return <AccountLoading title={recoveryReturn ? "Abriendo tu aviso" : user.email_verified ? "Abriendo tus avisos" : "Abriendo la confirmación de correo"} description={recoveryReturn ? "Estamos comprobando las opciones de tu aviso." : user.email_verified ? "Enseguida vas a poder seguir tus búsquedas." : "Ya falta un paso para empezar a publicar."} />;

  return <form className="auth-form" onSubmit={login} aria-busy={busy}>
    {recoveryReturn && <p className="field-help">Ingresá con la cuenta que creó el aviso. Después podrás marcar que recuperaste a tu mascota sin cargar fotos ni otros datos.</p>}
    <fieldset className="section-fields" disabled={busy}>
      <label className="field-label">Correo electrónico<input className="form-input" name="email" type="email" required maxLength={320} autoComplete="email" placeholder="nombre@ejemplo.com" /></label>
      <AuthPasswordField name="password" label="Contraseña" autoComplete="current-password" recovery />
      <button className="button button-primary auth-submit" type="submit">{busy ? "Ingresando…" : "Ingresar"}<Icon name="arrow" /></button>
    </fieldset>
    {error && <p role="alert" className="notice notice-warning">{error}</p>}
    <p className="auth-alternative">¿Todavía no tenés cuenta? <Link href="/crear-cuenta">Creá tu cuenta</Link></p>
  </form>;
}
