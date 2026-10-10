"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { AccountSession } from "../account-session";
import type { SessionUser } from "../account-session";

async function requestChange(method: string, payload?: object, action?: "cancel" | "resend") {
  const response = await fetch(`/api/account-settings${action ? `?action=${action}` : ""}`, {
    method, headers: { "Content-Type": "application/json" }, body: payload ? JSON.stringify(payload) : undefined,
  });
  const data = response.status === 204 ? null : await response.json();
  if (!response.ok) throw new Error(response.status === 401 ? "Tu sesión venció. Ingresá nuevamente."
    : typeof data?.detail === "string" ? data.detail : "Revisá los datos e intentá de nuevo.");
  return data;
}

function Settings({ user, onDeleted }: { user: SessionUser; onDeleted: () => void }) {
  const [name, setName] = useState(user.name);
  const [phone, setPhone] = useState(user.phone || "");
  const [email, setEmail] = useState(user.email || "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [deleteError, setDeleteError] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const changingEmail = email.trim().toLowerCase() !== user.email;
  useEffect(() => { setName(user.name); setPhone(user.phone || ""); setEmail(user.email || ""); }, [user.name, user.phone, user.email]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const form = event.currentTarget;
    const values = new FormData(form);
    setBusy(true); setError(""); setMessage("");
    try {
      const updated: SessionUser = await requestChange("PATCH", { name: name.trim(), phone: phone.trim() || null, email: email.trim(),
        ...(changingEmail ? { password: String(values.get("password") || "") } : {}) });
      const password = form.elements.namedItem("password");
      if (password instanceof HTMLInputElement) password.value = "";
      setEmail(updated.email || "");
      setMessage(updated.pending_email ? "Datos guardados. Revisá el correo de la nueva dirección para confirmar el cambio." : "Tus datos de contacto quedaron actualizados.");
      window.dispatchEvent(new Event("mascomatch:session"));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No pudimos guardar tus datos."); }
    finally { setBusy(false); }
  }

  async function emailAction(action: "cancel" | "resend") {
    if (busy) return;
    setBusy(true); setError(""); setMessage("");
    try {
      await requestChange("POST", undefined, action);
      setMessage(action === "cancel" ? "El cambio de correo fue cancelado." : "Te enviamos otro enlace a la nueva dirección.");
      window.dispatchEvent(new Event("mascomatch:session"));
    } catch (cause) { setError(cause instanceof Error ? cause.message : "No pudimos completar la solicitud."); }
    finally { setBusy(false); }
  }

  async function remove(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || confirmation !== "ELIMINAR") return;
    const values = new FormData(event.currentTarget);
    setBusy(true); setDeleteError("");
    try {
      await requestChange("DELETE", { password: String(values.get("password") || ""), confirmation });
      onDeleted();
      window.dispatchEvent(new Event("mascomatch:session"));
      window.dispatchEvent(new Event("mascomatch:cases"));
    } catch (cause) { setDeleteError(cause instanceof Error ? cause.message : "No pudimos eliminar tu cuenta."); }
    finally { setBusy(false); }
  }

  return <>
    <section className="notification-login account-form account-settings" aria-labelledby="contact-title">
      <h2 id="contact-title">Datos de contacto</h2>
      <p className="field-help">El correo se usa para ingresar y recibir alertas. Tu teléfono solo se comparte en los reportes donde lo hayas autorizado.</p>
      <form onSubmit={save} aria-busy={busy}>
        <fieldset className="section-fields" disabled={busy}>
          <label className="field-label">Nombre<input className="form-input" required maxLength={120} autoComplete="name" value={name} onChange={event => setName(event.target.value)} /></label>
          <label className="field-label">Teléfono <span className="field-help">(opcional)</span><input className="form-input" type="tel" maxLength={32} autoComplete="tel" value={phone} onChange={event => setPhone(event.target.value)} /></label>
          <label className="field-label">Correo electrónico<input className="form-input" type="email" required maxLength={320} autoComplete="email" value={email} onChange={event => setEmail(event.target.value)} /><span className="field-help">Para cambiarlo, confirmá la nueva dirección. Hasta entonces seguirá funcionando {user.email}.</span></label>
          {changingEmail && <label className="field-label">Contraseña actual<input className="form-input" type="password" name="password" required maxLength={128} autoComplete="current-password" /><span className="field-help">Al confirmar el nuevo correo, tendrás que ingresar nuevamente.</span></label>}
          <button className="button button-primary" type="submit">{busy ? "Guardando…" : "Guardar cambios"}</button>
        </fieldset>
      </form>
      {user.pending_email && <aside className="notice account-pending"><h3>Cambio de correo pendiente</h3><p>Confirmá el enlace enviado a <strong>{user.pending_email}</strong>. Vence a las 24 horas. Tu dirección actual todavía no cambió.</p><div className="location-actions"><button className="text-button" type="button" disabled={busy} onClick={() => void emailAction("resend")}>Reenviar confirmación</button><button className="text-button" type="button" disabled={busy} onClick={() => void emailAction("cancel")}>Cancelar cambio</button></div></aside>}
      {message && <p className="notice" role="status">{message}</p>}
      {error && <p className="notice notice-warning" role="alert">{error}</p>}
      <Link href="/notificaciones" className="text-button">Configurar notificaciones por correo</Link>
    </section>
    <details className="account-danger">
      <summary>Eliminar mi cuenta</summary>
      <h2>Esta acción es definitiva</h2>
      <p>Se eliminarán tu cuenta, todos tus avisos de mascotas perdidas —incluidos los cerrados—, las fotos de esos avisos y tus reseñas.</p>
      <p>Tus avistamientos y reportes de animales encontrados se conservarán para ayudar en otras búsquedas, sin vincularlos a tu cuenta ni compartir tu contacto.</p>
      <form onSubmit={remove} aria-busy={busy}><fieldset className="section-fields" disabled={busy}>
        <label className="field-label">Contraseña actual<input className="form-input" type="password" name="password" required maxLength={128} autoComplete="current-password" /></label>
        <label className="field-label">Escribí ELIMINAR para confirmar<input className="form-input" required value={confirmation} autoComplete="off" spellCheck={false} onChange={event => setConfirmation(event.target.value)} /></label>
        <button type="submit" className="button button-primary" disabled={confirmation !== "ELIMINAR"}>{busy ? "Eliminando…" : "Eliminar cuenta definitivamente"}</button>
      </fieldset></form>
      {deleteError && <p role="alert" className="notice notice-warning">{deleteError}</p>}
    </details>
  </>;
}

export function AccountSettings() {
  const [deleted, setDeleted] = useState(false);
  if (deleted) return <section className="notification-login account-form"><h2>Tu cuenta fue eliminada</h2><p role="status">Se quitaron tus avisos de mascotas perdidas. Los avistamientos se conservaron sin vincularlos a tu cuenta.</p><Link href="/" className="button button-primary">Volver al inicio</Link></section>;
  return <AccountSession>{user => <Settings key={user.id} user={user} onDeleted={() => setDeleted(true)} />}</AccountSession>;
}
