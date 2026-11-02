"use client";
import Link from "next/link";
import { useId, useState } from "react";
import { Icon } from "./pictogram";

export function AuthPasswordField({ name, label, autoComplete, minLength, hint, recovery = false, visibilityLabel = "contraseña" }: {
  name: string;
  label: string;
  autoComplete: "current-password" | "new-password";
  minLength?: number;
  hint?: string;
  recovery?: boolean;
  visibilityLabel?: string;
}) {
  const id = useId();
  const [visible, setVisible] = useState(false);
  return <div className="auth-password-field">
    <div className="auth-password-heading">
      <label className="field-label" htmlFor={id}>{label}</label>
      {recovery && <Link href="/recuperar">Olvidé mi contraseña</Link>}
    </div>
    <div className="auth-password-input">
      <input id={id} className="form-input" name={name} type={visible ? "text" : "password"} required minLength={minLength} maxLength={128} autoComplete={autoComplete} aria-describedby={hint ? `${id}-hint` : undefined} />
      <button type="button" className="auth-password-toggle" aria-label={`${visible ? "Ocultar" : "Mostrar"} ${visibilityLabel}`} aria-controls={id} aria-pressed={visible} onClick={() => setVisible(value => !value)}><Icon name={visible ? "eyeOff" : "eye"} /></button>
    </div>
    {hint && <span className="field-help" id={`${id}-hint`}>{hint}</span>}
  </div>;
}
