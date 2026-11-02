"use client";

import { LoadingState } from "../ui/loading-state";
import { breedOptions, colorOptions, colorValue } from "@/lib/pet-details";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { lostDogsEndpoint } from "@/lib/lost-dogs";
import type { LostDogList } from "@/lib/lost-dogs";
import { PetCard } from "../ui/pet-card";

const pageSize = 24;
const emptyFilters = { q: "", species: "", breed: "", color: "", sex: "", size: "", lost_from: "", lost_to: "", with_photos: "", collar: "" };
type Filters = typeof emptyFilters;

export function LostDogs() {
  const [draft, setDraft] = useState<Filters>({ ...emptyFilters });
  const [filters, setFilters] = useState<Filters>({ ...emptyFilters });
  const search = Object.values(filters).some(Boolean);
  const setField = (field: keyof Filters, value: string) => setDraft(current => ({ ...current, [field]: value }));
  const [offset, setOffset] = useState(0);
  const [refresh, setRefresh] = useState(0);
  const [result, setResult] = useState<LostDogList | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const resultsHeading = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError("");
    const params = new URLSearchParams({ offset: String(offset), limit: String(pageSize) });
    for (const [key, value] of Object.entries(filters)) if (value) params.set(key, key === "color" ? colorValue(value) : value);
    void fetch(`${lostDogsEndpoint}?${params}`, { signal: controller.signal, cache: "no-store" })
      .then(async response => {
        if (!response.ok) throw new Error("No pudimos cargar los avisos. Intentá de nuevo en un momento.");
        const data: LostDogList = await response.json();
        if (!controller.signal.aborted) {
          if (data.total > 0 && !data.items.length && offset > 0) {
            setOffset(Math.floor((data.total - 1) / pageSize) * pageSize);
          } else setResult(data);
        }
      }).catch(cause => {
        if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : "No pudimos cargar los avisos.");
      }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [filters, offset, refresh]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setFilters(Object.fromEntries(Object.entries(draft).map(([key, value]) => [key, value.trim()])) as Filters); setOffset(0); setRefresh(value => value + 1);
  }
  function changePage(next: number) {
    setOffset(next); resultsHeading.current?.focus();
  }

  return <>
    <form className="lost-dogs-search lost-dogs-filters" role="search" onSubmit={submit}>
      <div className="lost-search-main"><label className="field-label" htmlFor="lost-dogs-query">Buscar por nombre, zona, descripción o ID
        <input id="lost-dogs-query" name="q" type="search" maxLength={120} placeholder="Por ejemplo: Luna, El Pinar o MM-000123" value={draft.q} onChange={e => setField("q", e.target.value)} className="form-input" />
      </label><button type="submit" className="button button-primary">Buscar</button></div>
      <div className="lost-filter-grid">
        <label className="field-label">Especie<select className="form-input" name="species" value={draft.species} onChange={e => setField("species", e.target.value)}><option value="">Perros y gatos</option><option value="dog">Perro</option><option value="cat">Gato</option></select></label>
        <label className="field-label">Raza<input className="form-input" name="breed" list="filter-breeds" maxLength={120} placeholder="Cualquier raza" value={draft.breed} onChange={e => setField("breed", e.target.value)} /></label>
        <datalist id="filter-breeds">{(breedOptions[draft.species] || [...breedOptions.dog, ...breedOptions.cat]).filter((v, i, all) => all.indexOf(v) === i).map(v => <option key={v} value={v} />)}</datalist>
        <label className="field-label">Color<input className="form-input" name="color" list="filter-colors" maxLength={40} placeholder="Cualquier color" value={draft.color} onChange={e => setField("color", e.target.value)} /></label>
        <datalist id="filter-colors">{colorOptions.map(v => <option key={v} value={v} />)}</datalist>
      </div>
      <details className="lost-extra-filters"><summary>Más filtros <span className="field-help">Fecha, sexo, tamaño, fotos y collar</span></summary><div className="lost-filter-grid">
        <label className="field-label">Perdida desde<input className="form-input" name="lost_from" type="date" value={draft.lost_from} max={draft.lost_to || undefined} onChange={e => setField("lost_from", e.target.value)} /></label>
        <label className="field-label">Perdida hasta<input className="form-input" name="lost_to" type="date" value={draft.lost_to} min={draft.lost_from || undefined} onChange={e => setField("lost_to", e.target.value)} /></label>
        <label className="field-label">Sexo<select className="form-input" name="sex" value={draft.sex} onChange={e => setField("sex", e.target.value)}><option value="">Cualquiera</option><option value="male">Macho</option><option value="female">Hembra</option><option value="unknown">Sin indicar</option></select></label>
        <label className="field-label">Tamaño<select className="form-input" name="size" value={draft.size} onChange={e => setField("size", e.target.value)}><option value="">Cualquiera</option><option value="tiny">Muy pequeño</option><option value="small">Pequeño</option><option value="medium">Mediano</option><option value="large">Grande</option><option value="unknown">Sin indicar</option></select></label>
        <label className="field-label">Fotos<select className="form-input" name="with_photos" value={draft.with_photos} onChange={e => setField("with_photos", e.target.value)}><option value="">Con o sin fotos</option><option value="true">Con fotos</option><option value="false">Sin fotos</option></select></label>
        <label className="field-label">Collar<select className="form-input" name="collar" value={draft.collar} onChange={e => setField("collar", e.target.value)}><option value="">Cualquiera</option><option value="yes">Con collar</option><option value="no">Sin collar</option><option value="unknown">Sin indicar</option></select></label>
      </div><p className="field-help">Las fechas corresponden a cuándo se perdió la mascota. Raza y color también admiten texto libre.</p></details>
      <div className="lost-filter-actions">{search && <button type="button" className="text-button" onClick={() => { setDraft({ ...emptyFilters }); setFilters({ ...emptyFilters }); setOffset(0); }}>Limpiar filtros</button>}<button type="submit" className="text-button">Aplicar filtros</button></div>
    </form>
    <section className="lost-dogs-results" aria-labelledby="lost-results-title" aria-busy={loading}>
      <h2 id="lost-results-title" ref={resultsHeading} tabIndex={-1} className="lost-results-title">{search ? "Resultados de búsqueda" : "Últimos avisos"}</h2>
      {loading && <LoadingState title="Cargando mascotas reportadas" description="Buscando los avisos que coinciden con tus filtros." />}
      <div aria-live="polite">

        {!loading && !error && result && <p className="status-text">{result.total === 1 ? "1 mascota sigue perdida" : `${result.total} mascotas siguen perdidas`}</p>}
      </div>
      {error && <div className="notice notice-warning" role="alert">{error} <button type="button" className="text-button" onClick={() => setRefresh(value => value + 1)}>Reintentar</button></div>}
      {!loading && !error && result?.items.length === 0 && <div className="lost-dogs-empty">
        <h3>{search ? "No encontramos avisos con esa búsqueda" : "Todavía no hay avisos activos"}</h3>
        <p>{search ? "Probá con otro nombre o zona, o quitá algunos filtros." : "Cuando alguien publique una mascota perdida, su aviso aparecerá acá."}</p>
        {!search && <Link href="/perdi" className="button button-secondary">Publicar una mascota perdida</Link>}
      </div>}
      {!loading && !error && Boolean(result?.items.length) && <>
        <div className="lost-dogs-grid">
          {result!.items.map(dog => <PetCard key={dog.id} animal={dog} />)}
        </div>
        <nav className="lost-dogs-pagination" aria-label="Páginas de mascotas reportadas">
          <button type="button" className="button button-secondary" disabled={offset === 0} onClick={() => changePage(Math.max(0, offset - pageSize))}>Anterior</button>
          <span>Página {Math.floor(offset / pageSize) + 1} de {Math.max(1, Math.ceil(result!.total / pageSize))}</span>
          <button type="button" className="button button-secondary" disabled={offset + result!.items.length >= result!.total} onClick={() => changePage(offset + pageSize)}>Siguiente</button>
        </nav>
      </>}
    </section>
  </>;
}
