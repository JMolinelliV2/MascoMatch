"use client";
import { useEffect, useId, useRef, useState } from "react";
import type { FormEvent } from "react";
import { Icon } from "../ui/pictogram";

export function ContactForm() {
  const id = useId();
  const request = useRef<{ id: string; values: string } | null>(null);
  const confirmation = useRef<HTMLHeadingElement>(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<{ name?: string; message?: string }>({});

  useEffect(() => { if (sent) confirmation.current?.focus(); }, [sent]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || sent) return;
    const form = event.currentTarget;
    const values = new FormData(form);
    const body = {
      name: String(values.get("name") || "").trim(),
      email: String(values.get("email") || "").trim().toLowerCase(),
      topic: String(values.get("topic") || "improvement"),
      message: message.trim(),
      website: String(values.get("website") || ""),
    };
    const invalid = { name: body.name ? undefined : "Escribí tu nombre.", message: body.message.length < 10 ? "Contanos un poco más: escribí al menos 10 caracteres." : undefined };
    setFieldErrors(invalid); setError("");
    if (invalid.name || invalid.message) {
      form.querySelector<HTMLInputElement | HTMLTextAreaElement>(invalid.name ? '[name="name"]' : '[name="message"]')?.focus();
      return;
    }
    setBusy(true);
    try {
      const signature = JSON.stringify(body);
      if (!request.current || request.current.values !== signature) request.current = { id: crypto.randomUUID(), values: signature };
      const response = await fetch("/api/contact", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...body, request_id: request.current.id }),
        signal: AbortSignal.timeout(15000),
      });
      const data = await response.json();
      if (!response.ok || data.ok !== true) {
        if (response.status === 409) request.current = null;
        throw new Error(response.status === 429 ? "Recibimos varios envíos. Esperá un rato antes de volver a escribirnos."
          : typeof data.detail === "string" ? data.detail : "No pudimos recibir tu mensaje. Intentá de nuevo.");
      }
      setSent(true);
    } catch (cause) {
      setError(cause instanceof Error && cause.name === "Error" ? cause.message : "No pudimos confirmar el envío. Intentá de nuevo; conservamos tu mensaje.");
    } finally { setBusy(false); }
  }

  if (sent) return <section className="notification-login account-form contact-success" aria-labelledby={`${id}-success`}>
    <span className="saved-changes-mark" aria-hidden="true"><Icon name="check" /></span>
    <h2 id={`${id}-success`} ref={confirmation} tabIndex={-1}>Gracias por ayudarnos a mejorar</h2>
    <p role="status">Tu mensaje quedó recibido. Lo enviaremos al equipo de MascoMatch para que pueda revisarlo y responderte al correo que indicaste.</p>
    <button className="button button-secondary" type="button" onClick={() => { request.current = null; setMessage(""); setError(""); setFieldErrors({}); setSent(false); }}>Enviar otro mensaje</button>
  </section>;

  return <form className="notification-login account-form contact-form" onSubmit={submit} aria-busy={busy}>
    <fieldset disabled={busy} className="section-fields">
      <legend className="contact-legend">Contanos tu idea</legend>
      <div className="field-label"><label htmlFor={`${id}-name`}>Tu nombre</label>
        <input id={`${id}-name`} className="form-input" name="name" required maxLength={120} autoComplete="name" aria-invalid={Boolean(fieldErrors.name)} aria-describedby={fieldErrors.name ? `${id}-name-error` : undefined} />
        {fieldErrors.name && <span className="field-error" id={`${id}-name-error`}>{fieldErrors.name}</span>}
      </div>
      <div className="field-label"><label htmlFor={`${id}-email`}>Correo electrónico</label>
        <input id={`${id}-email`} className="form-input" name="email" type="email" required maxLength={320} autoComplete="email" aria-describedby={`${id}-email-help`} />
        <span className="field-help" id={`${id}-email-help`}>Lo usaremos para responderte.</span>
      </div>
      <label className="field-label">¿Sobre qué querés escribirnos?
        <select className="form-input" name="topic" defaultValue="improvement"><option value="improvement">Sugerir una mejora</option><option value="problem">Informar un problema</option><option value="other">Hacer una consulta</option></select>
      </label>
      <div className="field-label"><label htmlFor={`${id}-message`}>Tu mensaje</label>
        <textarea id={`${id}-message`} className="form-input" name="message" required minLength={10} maxLength={4000} rows={6} value={message} onChange={event => setMessage(event.target.value)} placeholder="Contanos qué mejorarías o qué pasó. Si hubo un problema, indicá en qué pantalla lo encontraste." aria-invalid={Boolean(fieldErrors.message)} aria-describedby={`${id}-message-help${fieldErrors.message ? ` ${id}-message-error` : ""}`} />
        {fieldErrors.message && <span className="field-error" id={`${id}-message-error`}>{fieldErrors.message}</span>}
        <span className="field-help contact-count" id={`${id}-message-help`}>{message.length} / 4000 caracteres</span>
      </div>
      <div className="contact-trap" aria-hidden="true"><label>Dejá este campo vacío<input name="website" tabIndex={-1} autoComplete="off" maxLength={200} /></label></div>
      <p className="field-help contact-privacy">Tu mensaje y tu correo se comparten con el equipo de MascoMatch para atender la consulta. No se publican en la página.</p>
      <button className="button button-primary" type="submit">{busy ? "Enviando…" : "Enviar mensaje"}<Icon name="arrow" /></button>
    </fieldset>
    {error && <p role="alert" className="notice notice-warning">{error}</p>}
  </form>;
}
