"use client";
import { useId, useState } from "react";
import type { FormEvent } from "react";

export type AdminPeriod = { from: string; to: string };
export const emptyPeriod: AdminPeriod = { from: "", to: "" };
const localMinute = (date: Date) => new Date(date.getTime() - 3 * 3600000).toISOString().slice(0, 16);
export function periodQuery(period: AdminPeriod): Record<string, string> {
  return { ...(period.from ? { from_at: new Date(`${period.from}-03:00`).toISOString() } : {}),
    ...(period.to ? { to_at: new Date(new Date(`${period.to}-03:00`).getTime() + 60000).toISOString() } : {}) };
}
export const adminDate = (value?: string | null) => value ? new Intl.DateTimeFormat("es-UY", {
  dateStyle: "medium", timeStyle: "short", timeZone: "America/Montevideo",
}).format(new Date(value)) : "Sin registro";

export function AdminDateRange({ value, onApply }: { value: AdminPeriod; onApply: (period: AdminPeriod) => void }) {
  const [draft, setDraft] = useState(value);
  const [error, setError] = useState("");
  const id = useId();
  function apply(event: FormEvent) {
    event.preventDefault();
    if (draft.from && draft.to && draft.from > draft.to) { setError("El inicio debe ser anterior o igual al final."); return; }
    setError(""); onApply(draft);
  }
  function preset(days: number) {
    const now = new Date();
    const next = days ? { from: localMinute(new Date(now.getTime() - days * 86400000)), to: localMinute(now) } : emptyPeriod;
    setDraft(next); setError(""); onApply(next);
  }
  return <form className="admin-date-range" onSubmit={apply}>
    <fieldset><legend>Fecha y hora · Uruguay (UTC−3)</legend><div className="admin-date-fields">
      <label className="field-label" htmlFor={`${id}-from`}>Desde<input id={`${id}-from`} className="form-input" type="datetime-local" value={draft.from} onChange={event => setDraft({ ...draft, from: event.target.value })} /></label>
      <label className="field-label" htmlFor={`${id}-to`}>Hasta<input id={`${id}-to`} className="form-input" type="datetime-local" value={draft.to} onChange={event => setDraft({ ...draft, to: event.target.value })} /></label>
      <button type="submit" className="button button-secondary">Aplicar período</button>
    </div><div className="admin-period-presets">{[7, 30, 90, 0].map(days => <button type="button" className="text-button" key={days} onClick={() => preset(days)}>{days ? `Últimos ${days} días` : "Todo el período"}</button>)}</div>
    <p className="field-help">{value.from || value.to ? `Filtro aplicado: ${value.from ? adminDate(`${value.from}-03:00`) : "desde el inicio"} → ${value.to ? adminDate(`${value.to}-03:00`) : "hasta ahora"}.` : "Sin límite de fechas."} El minuto final está incluido.</p>
    {error && <p role="alert" className="notice notice-warning">{error}</p>}</fieldset>
  </form>;
}
