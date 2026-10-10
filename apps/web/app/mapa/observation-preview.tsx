"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { observationDate, observationTraits, publicObservationsEndpoint } from "@/lib/public-observations";
import type { PublicObservation } from "@/lib/public-observations";
import type { ObservationMapSelection } from "@/lib/observation-map-marker";
import { ObservationPhoto } from "../ui/observation-photo";
import { Icon } from "../ui/pictogram";

function ObservationPreview({ id, onLayout, onRefresh }: { id: string; onLayout: () => void; onRefresh: () => void }) {
  const [report, setReport] = useState<PublicObservation | null>(null);
  const [missing, setMissing] = useState(false);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setReport(null); setMissing(false); setError("");
    void fetch(`${publicObservationsEndpoint}/${encodeURIComponent(id)}`, { cache: "no-store", signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15000)]) }).then(async response => {
      if (response.status === 404) { if (!controller.signal.aborted) setMissing(true); return; }
      if (!response.ok) throw new Error("No pudimos cargar los detalles.");
      const data: PublicObservation = await response.json();
      if (!controller.signal.aborted) setReport(data);
    }).catch(() => { if (!controller.signal.aborted) setError("No pudimos cargar los detalles."); });
    return () => controller.abort();
  }, [id, refresh]);
  useEffect(() => { onLayout(); }, [report, missing, error, onLayout]);
  if (missing) return <div className="observation-map-preview"><h3>Este reporte ya no está disponible</h3><button type="button" className="text-button" onClick={onRefresh}>Actualizar mapa</button></div>;
  if (error) return <div className="observation-map-preview"><p role="alert">{error}</p><button type="button" className="text-button" onClick={() => setRefresh(value => value + 1)}>Reintentar</button></div>;
  if (!report) return <div className="observation-map-preview"><p role="status">Cargando detalles del reporte…</p></div>;
  const found = report.source_type === "FOUND_ANIMAL";
  return <div className={`observation-map-preview map-report-${found ? "found" : "sighting"}`}>
    <ObservationPhoto id={report.id} hasPhoto={Boolean(report.photo_url)} found={found} onLoad={onLayout} />
    <span className="map-report-type">{found ? "Animal encontrado" : "Avistamiento"}</span>
    <h3>{observationTraits(report)}</h3>
    <p className="map-report-area"><Icon name="pin" />{report.public_location || "Zona aproximada"}</p>
    <p className="map-report-date"><Icon name="calendar" /><span>{found ? "Encontrado el" : "Visto el"} <time dateTime={report.observed_at}>{observationDate(report.observed_at)}</time></span></p>
    <p className="observation-map-help">Hora de Uruguay · Ubicación aproximada</p>
    <h4>Detalles del reporte</h4>
    <p className="observation-map-description">{report.description}</p>
    {report.related_notice && <div className="observation-map-related"><p>Enviado para el aviso de <strong>{report.related_notice.name}</strong>. El vínculo no confirma que sea la misma mascota.</p><Link className="text-button" href={`/perdidos/${encodeURIComponent(report.related_notice.id)}?origen=mapa`}>Ver aviso relacionado <Icon name="arrow" /></Link></div>}
  </div>;
}

export function ObservationLocationPreview({ selection, onRefresh }: { selection: ObservationMapSelection; onRefresh: () => void }) {
  const [selectedId, setSelectedId] = useState(selection.selectedId);
  const point = selection.points.find(item => item.id === selectedId) || selection.points[0];
  return <div className="observation-map-popup-content">
    {selection.points.length > 1 && <label className="field-label">{selection.points.length} reportes en esta zona<select className="form-input" value={point.id} onChange={event => setSelectedId(event.target.value)}>{selection.points.map(item => <option key={item.id} value={item.id}>{item.title} · {observationTraits(item)} · {observationDate(item.when)}</option>)}</select></label>}
    <ObservationPreview key={point.id} id={point.id} onLayout={selection.onLayout} onRefresh={onRefresh} />
  </div>;
}
