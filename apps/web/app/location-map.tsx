"use client";

import { useEffect, useId, useRef, useState } from "react";
import type { Map as LeafletMap, Marker, TileLayer } from "leaflet";

type Props = { latitude: number; longitude: number; onMove?: (latitude: number, longitude: number) => void; editable?: boolean; label?: string };

export function LocationMap({ latitude, longitude, onMove, editable = true, label }: Props) {
  const id = useId();
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<LeafletMap | null>(null);
  const markerRef = useRef<Marker | null>(null);
  const tilesRef = useRef<TileLayer | null>(null);
  const current = useRef({ latitude, longitude, onMove });
  current.current = { latitude, longitude, onMove };
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let disposed = false;
    let observer: ResizeObserver | undefined;
    void import("leaflet").then(L => {
      if (disposed || !container.current) return;
      const point: [number, number] = [current.current.latitude, current.current.longitude];
      const map = L.map(container.current, { scrollWheelZoom: false, zoomControl: false }).setView(point, 16);
      L.control.zoom({ zoomInTitle: "Acercar", zoomOutTitle: "Alejar" }).addTo(map);
      mapRef.current = map;
      const tiles = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).addTo(map);
      tilesRef.current = tiles;
      tiles.on("tileerror", () => { if (!disposed) setError("No pudimos cargar el mapa. Podés conservar el lugar elegido o intentar de nuevo."); });
      const marker = L.marker(point, {
        draggable: editable, autoPan: editable,
        title: editable ? "Ubicación elegida. Usá las flechas del teclado para mover el pin." : label || "Lugar del avistamiento",
        alt: editable ? "Ubicación elegida. Usá las flechas del teclado para mover el pin." : label || "Lugar del avistamiento",
        icon: L.divIcon({ className: "location-pin", html: '<span class="location-pin-shape"></span>', iconSize: [44, 44], iconAnchor: [22, 42] }),
      }).addTo(map);
      markerRef.current = marker;
      function move(lat: number, lon: number) {
        const wrapped = L.latLng(Math.max(-85, Math.min(85, lat)), lon).wrap();
        marker.setLatLng(wrapped);
        current.current.onMove?.(wrapped.lat, wrapped.lng);
      }
      if (editable) {
        marker.on("dragend", () => { const position = marker.getLatLng(); move(position.lat, position.lng); });
        map.on("click", (event: L.LeafletMouseEvent) => move(event.latlng.lat, event.latlng.lng));
      }
      const pin = marker.getElement();
      if (pin && editable) {
        pin.setAttribute("aria-describedby", `${id}-help`);
        pin.addEventListener("keydown", event => {
          const offsets: Record<string, [number, number]> = { ArrowLeft: [-20, 0], ArrowRight: [20, 0], ArrowUp: [0, -20], ArrowDown: [0, 20] };
          const offset = offsets[event.key];
          if (!offset) return;
          event.preventDefault(); event.stopPropagation();
          const pixel = map.latLngToContainerPoint(marker.getLatLng()).add(offset);
          const position = map.containerPointToLatLng(pixel);
          move(position.lat, position.lng);
          map.panInside(marker.getLatLng());
        });
      }
      // The form keeps its stages mounted. Refresh the map when this stage becomes visible again.
      observer = new ResizeObserver(() => map.invalidateSize());
      observer.observe(container.current);
      setReady(true);
    }).catch(() => { if (!disposed) setError("No pudimos abrir el mapa. Podés seguir usando la búsqueda de direcciones."); });
    return () => {
      disposed = true; observer?.disconnect(); mapRef.current?.remove();
      mapRef.current = null; markerRef.current = null; tilesRef.current = null;
    };
  }, [id, editable, label]);

  useEffect(() => {
    const marker = markerRef.current;
    if (!marker) return;
    const point = marker.getLatLng();
    if (point.lat !== latitude || point.lng !== longitude) {
      marker.setLatLng([latitude, longitude]);
      mapRef.current?.panTo([latitude, longitude]);
    }
  }, [latitude, longitude]);

  return <div className="location-map-section">
    <p id={`${id}-help`} className="field-help">{editable ? "Arrastrá el pin o tocá el mapa para elegir otro punto. También podés mover el pin con las flechas del teclado." : label || "Lugar indicado por la persona que envió el avistamiento."}</p>
    <div ref={container} className="location-map" role="region" aria-label={label || (editable ? "Mapa para ajustar la ubicación" : "Mapa del avistamiento")} aria-describedby={`${id}-help`} />
    {!ready && !error && <p role="status" className="status-text">Cargando mapa…</p>}
    {error && <div className="notice notice-warning" role="alert">{error} {ready && <button type="button" className="text-button" onClick={() => { setError(""); tilesRef.current?.redraw(); }}>Reintentar</button>}</div>}
  </div>;
}
