"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
type Attribute = { value: string | string[]; confidence: number; source: "text" | "image" };
type Job = {
  id: string;
  source_type: "text" | "image";
  status: string;
  feature_set: { features: Record<string, Attribute> } | null;
};
type Analysis = { enabled: boolean; jobs: Job[] };
const pendingStates = new Set(["PENDING", "DISPATCHING", "QUEUED", "RUNNING"]);
const unknownValues = new Set(["unknown", "not_visible", "uncertain"]);
const featureLabels: Record<string, string> = {
  species: "Animal", breed_type: "Tipo o raza", size: "Tamaño", primary_color: "Color principal",
  secondary_colors: "Otros colores", coat_length: "Pelaje", coat_pattern: "Patrón del pelaje",
  ear_shape: "Orejas", tail_description: "Cola", face_features: "Rasgos de la cara",
  distinctive_features: "Rasgos distintivos", accessories: "Collar y accesorios",
};
const valueLabels: Record<string, string> = {
  dog: "Perro", cat: "Gato", rabbit: "Conejo", bird: "Ave", other: "Otro animal",
  tiny: "Muy pequeño", small: "Pequeño", medium: "Mediano", large: "Grande",
  black: "Negro", white: "Blanco", brown: "Marrón", gray: "Gris", cream: "Crema", orange: "Naranja",
  tan: "Beige / canela", red: "Rojizo", multicolor: "Varios colores",
  short: "Corto", long: "Largo", curly: "Rizado", wire: "Áspero", hairless: "Sin pelo",
  solid: "Uniforme", spotted: "Manchado", striped: "Rayado", tuxedo: "Bicolor tipo esmoquin",
  merle: "Merle", brindle: "Atigrado", mixed: "Mixto",
};

function visibleFeatures(features: Record<string, Attribute>) {
  return Object.entries(features).filter(([, attribute]) => attribute.confidence > 0
    && (Array.isArray(attribute.value) ? attribute.value.length > 0 : !unknownValues.has(attribute.value)));
}

export function ReportAnalysis({ ownerType, ownerId, token }: { ownerType: "lost_case" | "observation"; ownerId: string; token: string }) {
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [message, setMessage] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [retrying, setRetrying] = useState<string | null>(null);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    const deadline = Date.now() + 5 * 60_000;
    setPaused(false);
    async function load() {
      try {
        const response = await fetch(`${API}/analysis/${ownerType}/${ownerId}`, {
          headers: { Authorization: `Bearer ${token}` }, signal: controller.signal,
        });
        if (!response.ok) throw new Error("No pudimos consultar el análisis. Tu reporte sigue guardado.");
        const data: Analysis = await response.json();
        if (controller.signal.aborted) return;
        setAnalysis(data);
        setMessage("");
        const pending = data.enabled && data.jobs.some(job => pendingStates.has(job.status));
        if (pending && Date.now() < deadline) timer = setTimeout(load, 5000);
        else if (pending) setPaused(true);
      } catch (error) {
        if (!controller.signal.aborted) setMessage(error instanceof Error ? error.message : "No pudimos consultar el análisis.");
      }
    }
    void load();
    return () => { controller.abort(); if (timer) clearTimeout(timer); };
  }, [ownerType, ownerId, token, refresh]);

  async function retry(id: string) {
    setRetrying(id);
    setMessage("");
    try {
      const response = await fetch(`${API}/analysis/jobs/${id}/retry`, { method: "POST", headers: { Authorization: `Bearer ${token}` } });
      if (response.status === 429) throw new Error("Esperá un minuto antes de volver a intentar el análisis.");
      if (!response.ok) throw new Error("El análisis no pudo reiniciarse. Tu reporte sigue guardado.");
      setRefresh(count => count + 1);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No pudimos volver a intentar el análisis.");
    } finally { setRetrying(null); }
  }

  if (!analysis && !message) return null;
  if (analysis && !analysis.enabled && !analysis.jobs.some(job => job.feature_set)) return null;
  if (analysis && !analysis.jobs.length && !message) return null;

  return (
    <section className="analysis-section" aria-labelledby="analysis-heading">
      <h2 id="analysis-heading">Características sugeridas</h2>
      <p className="field-help">El análisis puede tener errores. Conservamos la descripción y los datos que ingresaste.</p>
      <div className="analysis-status" role="status">
        {analysis?.jobs.some(job => pendingStates.has(job.status)) && <p>{paused ? "El análisis está tardando. Podés consultar su estado de nuevo." : "Estamos analizando las características del animal…"}</p>}
      </div>
      {analysis?.jobs.map(job => {
        const features = job.feature_set ? visibleFeatures(job.feature_set.features) : [];
        if (job.status !== "SUCCEEDED" && job.status !== "FAILED") return null;
        return (
          <div className="analysis-result" key={job.id}>
            <h3>{job.source_type === "image" ? "Según la foto" : "Según la descripción"}</h3>
            {job.status === "FAILED" ? <>
              <p className="status-text">El análisis no pudo completarse. La información del reporte está guardada.</p>
              <button type="button" className="text-button" disabled={retrying === job.id || !analysis.enabled} onClick={() => void retry(job.id)}>{retrying === job.id ? "Reintentando…" : "Volver a intentar"}</button>
            </> : features.length ? <dl className="analysis-details">
              {features.map(([name, attribute]) => <div key={name}>
                <dt>{featureLabels[name] ?? name}</dt>
                <dd>{(Array.isArray(attribute.value) ? attribute.value : [attribute.value]).map(value => valueLabels[value] ?? value).join(", ")}
                  {attribute.confidence < .7 && <span className="analysis-uncertain"> · Por revisar</span>}
                </dd>
              </div>)}
            </dl> : <p className="status-text">No pudimos extraer características con suficiente información.</p>}
          </div>
        );
      })}
      {message && <p role="alert" className="notice notice-warning">{message}</p>}
      {(paused || message) && <button type="button" className="text-button" onClick={() => setRefresh(count => count + 1)}>Actualizar análisis</button>}
    </section>
  );
}
