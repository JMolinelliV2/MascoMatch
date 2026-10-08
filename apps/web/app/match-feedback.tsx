"use client";
import { useState } from "react";
export function MatchFeedback({ id, status, onSaved }: { id: string; status: string | null; onSaved?: () => void }) {
  const [busy, setBusy] = useState(false);
  const [current, setCurrent] = useState(status);
  const [message, setMessage] = useState("");
  async function save(value: string) {
    setBusy(true); setMessage("");
    try {
      const response = await fetch(`/api/matches/${id}/feedback`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: value }) });
      if (!response.ok) throw new Error("No pudimos guardar tu respuesta. Intentá de nuevo.");
      setCurrent(value); setMessage("Tu respuesta quedó guardada."); onSaved?.();
    } catch (cause) { setMessage(cause instanceof Error ? cause.message : "No pudimos guardar tu respuesta."); }
    finally { setBusy(false); }
  }
  return <section className="match-feedback" aria-label="Revisar coincidencia"><h3>¿Podría ser tu animal?</h3>
    <div className="location-actions">
      <button type="button" className="text-button" disabled={busy || current === "CONFIRMED_RELEVANT"} onClick={() => void save("CONFIRMED_RELEVANT")}>Sí, podría ser</button>
      <button type="button" className="text-button" disabled={busy || current === "FALSE_MATCH"} onClick={() => void save("FALSE_MATCH")}>No, no es</button>
      <button type="button" className="text-button" disabled={busy || current === "RESOLVED"} onClick={() => void save("RESOLVED")}>Confirmé que es mi animal</button>
    </div><p className="field-help">Confirmar esta coincidencia no cierra automáticamente el aviso de pérdida.</p>
    {message && <p role="status" className="field-help">{message}</p>}
  </section>;
}
