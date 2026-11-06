"use client";

import { useEffect, useState } from "react";

export function FoundReporterContact({ matchId }: { matchId: string }) {
  const [contact, setContact] = useState<{ name: string; phone: string } | null>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setReady(false); setContact(null); setError("");
    void fetch(`/api/matches/${encodeURIComponent(matchId)}/reporter-contact`, { cache: "no-store", signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error(response.status === 403 ? "Confirmá que es tu mascota para ver el contacto." : "No pudimos consultar el contacto. Intentá de nuevo.");
      const data = await response.json();
      if (!controller.signal.aborted) { setContact(data.contact); setReady(true); }
    }).catch(cause => { if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : "No pudimos consultar el contacto."); });
    return () => controller.abort();
  }, [matchId, retry]);

  return <section className="found-reporter-contact" aria-label="Contacto de la persona que tiene a tu mascota">
    <h3>Coordiná el reencuentro</h3>
    {contact ? <><p>Confirmaste que es tu mascota. Estos son los datos que dejó la persona que la tiene a salvo.</p><dl><div><dt>Nombre</dt><dd>{contact.name}</dd></div><div><dt>Teléfono</dt><dd><a href={`tel:${contact.phone.replace(/[^+0-9]/g, "")}`}>{contact.phone}</a></dd></div></dl><p className="field-help">La búsqueda sigue abierta. Cuando vuelva con vos, marcá “Ya la recuperé”.</p></>
      : error ? <><p role="alert">{error}</p><button type="button" className="text-button" onClick={() => setRetry(v => v + 1)}>Reintentar</button></>
      : <p role="status">{ready ? "Este reporte no tiene datos de contacto disponibles." : "Consultando el contacto…"}</p>}
  </section>;
}
