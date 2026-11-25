"use client";

import { useEffect, useId, useRef, useState } from "react";
import { phoneError, PHONE_HELP } from "@/lib/phone-numbers";

export function PhoneField({ name = "phone", label = "Teléfono", value, onChange, required = false }: {
  name?: string; label?: string; value?: string; onChange?: (value: string) => void; required?: boolean;
}) {
  const id = useId();
  const input = useRef<HTMLInputElement>(null);
  const [localValue, setLocalValue] = useState("");
  const [touched, setTouched] = useState(false);
  const current = value ?? localValue;
  const error = phoneError(current, required);
  useEffect(() => { input.current?.setCustomValidity(error); }, [error]);

  return <label className="field-label" htmlFor={id}>
    <span>{label}{!required && <span className="field-help"> (opcional)</span>}</span>
    <input ref={input} id={id} name={name} type="tel" inputMode="tel" autoComplete="tel" className="form-input"
      required={required} maxLength={32} placeholder="Ej.: 099 123 456" value={current}
      aria-invalid={touched && Boolean(error)} aria-describedby={`${id}-help${touched && error ? ` ${id}-error` : ""}`}
      onBlur={() => setTouched(true)} onInvalid={() => setTouched(true)}
      onChange={event => { const next = event.target.value; setLocalValue(next); onChange?.(next); event.currentTarget.setCustomValidity(phoneError(next, required)); }} />
    <span id={`${id}-help`} className="field-help">{PHONE_HELP}</span>
    {touched && error && <span id={`${id}-error`} className="field-error" role="alert">{error}</span>}
  </label>;
}
