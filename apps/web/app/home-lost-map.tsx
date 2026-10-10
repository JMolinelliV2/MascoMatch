"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import type { LayerGroup, Map as LeafletMap, Popup, TileLayer } from "leaflet";
import { dogTraits, lostDate, lostDogsEndpoint, speciesLabel } from "@/lib/lost-dogs";
import type { LostDogNotice } from "@/lib/lost-dogs";
import { DogPhoto } from "./perdidos/dog-photo";
import { Icon } from "./ui/pictogram";

type Point = { id: string; layer: "lost" | "sighting" | "found"; title: string; latitude: number; longitude: number };
type Selection = { points: Point[]; content: HTMLDivElement; popup: Popup };
const API = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");

function LostMapPreview({ point, onLayout, onRefresh }: { point: Point; onLayout: () => void; onRefresh: () => void }) {
  const [animal, setAnimal] = useState<LostDogNotice | null>(null);
  const [error, setError] = useState("");
  const [missing, setMissing] = useState(false);
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setAnimal(null); setError(""); setMissing(false);
    void fetch(`${lostDogsEndpoint}/${encodeURIComponent(point.id)}`, { cache: "no-store", signal: controller.signal }).then(async response => {
      if (response.status === 404) { if (!controller.signal.aborted) setMissing(true); return; }
      if (!response.ok) throw new Error("No pudimos cargar la miniatura.");
      const data: LostDogNotice = await response.json();
      if (!controller.signal.aborted) setAnimal(data);
    }).catch(cause => { if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : "No pudimos cargar la miniatura."); });
    return () => controller.abort();
  }, [point.id, refresh]);
  useEffect(() => { onLayout(); }, [animal, error, missing, onLayout]);
  const href = `/perdidos/${encodeURIComponent(point.id)}?origen=inicio`;
  return <div className="home-map-preview">
    {missing ? <><h4>Este aviso ya no está disponible</h4><p>Puede que la mascota haya sido encontrada o que el aviso se haya cerrado.</p><button type="button" className="text-button" onClick={onRefresh}>Actualizar mapa</button></>
      : error ? <><h4>{point.title}</h4><p role="alert">{error}</p><button type="button" className="text-button" onClick={() => setRefresh(value => value + 1)}>Reintentar</button></>
        : !animal ? <><h4>{point.title}</h4><p role="status">Cargando miniatura…</p></>
          : <><Link href={href} aria-label={`Ver el aviso de ${animal.name}`}><DogPhoto dog={animal} /></Link><span className="lost-status">Sigue perdido</span><h4>{animal.name}</h4><p className="home-map-traits">{[speciesLabel(animal.species), ...dogTraits(animal)].join(" · ")}</p><p>{animal.public_location || "Zona aproximada"}</p><p className="home-map-date">Perdido desde el {lostDate(animal.lost_at)}</p><Link href={href} className="button button-primary">Ver aviso <Icon name="arrow" /></Link></>}
  </div>;
}

function LocationPreview({ selection, onRefresh }: { selection: Selection; onRefresh: () => void }) {
  const [selectedId, setSelectedId] = useState(selection.points[0].id);
  const point = selection.points.find(item => item.id === selectedId) || selection.points[0];
  return <div className="home-map-popup-content">
    {selection.points.length > 1 && <label className="field-label">{selection.points.length} animales en esta zona<select className="form-input" value={point.id} onChange={event => setSelectedId(event.target.value)}>{selection.points.map(item => <option value={item.id} key={item.id}>{item.title}</option>)}</select></label>}
    <LostMapPreview key={point.id} point={point} onLayout={() => selection.popup.update()} onRefresh={onRefresh} />
  </div>;
}

export function HomeLostMap() {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<LeafletMap | null>(null);
  const group = useRef<LayerGroup | null>(null);
  const tiles = useRef<TileLayer | null>(null);
  const [ready, setReady] = useState(false);
  const [mapError, setMapError] = useState("");
  const [points, setPoints] = useState<Point[]>([]);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [mapRefresh, setMapRefresh] = useState(0);

  useEffect(() => {
    let disposed = false;
    let observer: ResizeObserver | undefined;
    setReady(false); setMapError("");
    void import("leaflet").then(L => {
      if (disposed || !container.current) return;
      const instance = L.map(container.current, { scrollWheelZoom: false, zoomControl: false }).setView([-34.9, -56.16], 11);
      map.current = instance;
      L.control.zoom({ zoomInTitle: "Acercar", zoomOutTitle: "Alejar" }).addTo(instance);
      tiles.current = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).addTo(instance).on("tileerror", () => { if (!disposed) setMapError("No pudimos cargar algunas partes del mapa. Los avisos siguen disponibles en el catálogo."); });
      group.current = L.layerGroup().addTo(instance);
      observer = new ResizeObserver(() => instance.invalidateSize({ pan: false }));
      observer.observe(container.current);
      setReady(true);
    }).catch(() => { if (!disposed) setMapError("No pudimos abrir el mapa. Podés consultar los animales perdidos en el catálogo."); });
    return () => { disposed = true; observer?.disconnect(); map.current?.remove(); map.current = null; group.current = null; tiles.current = null; };
  }, [mapRefresh]);

  useEffect(() => {
    const controller = new AbortController();
    const reload = () => setRefresh(value => value + 1);
    window.addEventListener("focus", reload); window.addEventListener("mascomatch:cases", reload);
    setBusy(true);
    void fetch(`${API}/public/map?days=0&layer=lost`, { cache: "no-store", signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error("No pudimos cargar los animales en el mapa.");
      const data: { points: Point[] } = await response.json();
      if (!controller.signal.aborted) { setPoints(data.points.filter(point => point.layer === "lost")); setError(""); }
    }).catch(cause => { if (!controller.signal.aborted) { setPoints([]); setError(cause instanceof Error ? cause.message : "No pudimos cargar los animales en el mapa."); } })
      .finally(() => { if (!controller.signal.aborted) setBusy(false); });
    return () => { controller.abort(); window.removeEventListener("focus", reload); window.removeEventListener("mascomatch:cases", reload); };
  }, [refresh]);

  useEffect(() => {
    if (!ready) return;
    let disposed = false;
    void import("leaflet").then(L => {
      if (disposed || !map.current || !group.current) return;
      group.current.clearLayers(); setSelection(null);
      const locations = new Map<string, Point[]>();
      for (const point of points) {
        const key = `${point.latitude},${point.longitude}`;
        const location = locations.get(key) || [];
        location.push(point); locations.set(key, location);
      }
      const bounds: [number, number][] = [];
      for (const location of locations.values()) {
        const point = location[0];
        const content = document.createElement("div");
        const title = location.length > 1 ? `${location.length} animales perdidos en esta zona. Ver miniaturas.` : `${point.title}. Ver miniatura y aviso.`;
        const popup = L.popup({ minWidth: 200, maxWidth: 260, maxHeight: 340, className: "home-case-popup", autoPanPadding: [20, 20] }).setContent(content);
        const marker = L.marker([point.latitude, point.longitude], {
          title, alt: title, keyboard: true, riseOnHover: true,
          icon: L.divIcon({ className: "location-pin home-lost-pin", html: `<span class="location-pin-shape"></span>${location.length > 1 ? `<span class="home-map-pin-count">${location.length}</span>` : ""}`, iconSize: [44, 44], iconAnchor: [22, 42], popupAnchor: [0, -36] }),
        }).addTo(group.current).bindPopup(popup);
        marker.on("popupopen", () => {
          if (disposed) return;
          const close = popup.getElement()?.querySelector(".leaflet-popup-close-button");
          close?.setAttribute("aria-label", "Cerrar miniatura"); close?.setAttribute("title", "Cerrar miniatura");
          setSelection({ points: location, content, popup });
        });
        marker.on("popupclose", () => { if (!disposed) setSelection(current => current?.content === content ? null : current); });
        bounds.push([point.latitude, point.longitude]);
      }
      if (bounds.length) map.current.fitBounds(bounds, { padding: [32, 32], maxZoom: 13 });
    });
    return () => { disposed = true; };
  }, [points, ready]);

  function retryMap() {
    setMapError("");
    if (map.current) tiles.current?.redraw();
    else setMapRefresh(value => value + 1);
  }

  return <section id="mapa-perdidos" className="home-lost-map" aria-labelledby="home-lost-map-title">
    <div className="home-lost-map-heading"><div><h3 id="home-lost-map-title"><Icon name="pin" />Animales perdidos en el mapa</h3><p>Tocá un punto para ver su miniatura y abrir el aviso.</p></div><Link href="/mapa" className="text-button">Abrir mapa completo <Icon name="arrow" /></Link></div>
    <p className="home-map-status" role="status">{busy || !ready && !mapError ? "Cargando mapa…" : error ? "Los avisos del mapa no están disponibles en este momento." : points.length ? `${points.length} ${points.length === 1 ? "animal perdido con ubicación" : "animales perdidos con ubicación"}` : "No hay avisos activos con ubicación por ahora."}</p>
    <div ref={container} className="home-lost-map-canvas" role="region" aria-label="Mapa de animales perdidos" aria-describedby="home-lost-map-help" />
    {selection && createPortal(<LocationPreview key={selection.points[0].id} selection={selection} onRefresh={() => setRefresh(value => value + 1)} />, selection.content)}
    <p className="field-help" id="home-lost-map-help">Los puntos muestran zonas aproximadas. Los avisos sin ubicación se pueden consultar en el catálogo.</p>
    {error && <p className="notice notice-warning" role="alert">{error} <button type="button" className="text-button" onClick={() => setRefresh(value => value + 1)}>Reintentar</button></p>}
    {mapError && <p className="notice notice-warning" role="alert">{mapError} <button type="button" className="text-button" onClick={retryMap}>Reintentar mapa</button></p>}
  </section>;
}
