import type { LayerGroup, Map as LeafletMap, Popup } from "leaflet";
import type { MapReportPoint } from "./public-observations";
import { observationDate, observationTraits } from "./public-observations";

export type ObservationMapSelection = { points: MapReportPoint[]; selectedId: string; content: HTMLDivElement; popup: Popup; onLayout: () => void };
export type ObservationMapHandle = { open: (id?: string) => void; dispose: () => void };

export function observationMapLocations(points: MapReportPoint[]): MapReportPoint[][] {
  const locations = new Map<string, MapReportPoint[]>();
  for (const point of points) {
    const key = `${point.latitude},${point.longitude}`;
    const location = locations.get(key) || [];
    location.push(point); locations.set(key, location);
  }
  return [...locations.values()];
}

export function addObservationMapMarker(L: typeof import("leaflet"), map: LeafletMap, group: LayerGroup, points: MapReportPoint[], onOpen: (selection: ObservationMapSelection) => void, onClose: (content: HTMLDivElement) => void, shiftX = 0): ObservationMapHandle {
  const point = points[0];
  const title = points.length > 1 ? `${points.length} avistamientos o animales encontrados en esta zona. Ver detalles.` : `${point.title} · ${observationTraits(point)} · ${observationDate(point.when)}. Ver foto y detalles.`;
  const content = document.createElement("div");
  const icon = document.createElement("span");
  icon.className = "observation-map-dot";
  if (points.length > 1) { const count = document.createElement("span"); count.className = "observation-map-count"; count.textContent = String(points.length); icon.append(count); }
  const popup = L.popup({ minWidth: 200, maxWidth: 260, maxHeight: Math.max(120, Math.min(400, map.getContainer().clientHeight - 80)), className: "observation-map-popup", autoPanPadding: [16, 16] }).setContent(content);
  const marker = L.marker([point.latitude, point.longitude], { title, alt: title, keyboard: true, riseOnHover: true,
    icon: L.divIcon({ className: `observation-map-pin observation-map-${points.some(item => item.layer === "found") && points.some(item => item.layer === "sighting") ? "mixed" : point.layer}`, html: icon, iconSize: [44, 44], iconAnchor: [22 - shiftX, 22], popupAnchor: [shiftX, -14] }),
  }).addTo(group).bindPopup(popup);
  marker.off("click").off("keypress");
  const element = marker.getElement()!;
  element.setAttribute("aria-label", title); element.setAttribute("aria-expanded", "false");
  let disposed = false;
  let selectedId = point.id;
  let popupElement: HTMLElement | undefined;
  const onLayout = () => { if (!disposed && popup.isOpen()) popup.update(); };
  function open(id = point.id) {
    if (disposed) return;
    selectedId = points.some(item => item.id === id) ? id : point.id;
    if (popup.isOpen()) onOpen({ points, selectedId, content, popup, onLayout });
    else marker.openPopup();
    popup.getElement()?.querySelector<HTMLAnchorElement>(".leaflet-popup-close-button")?.focus();
  }
  function escape(event: KeyboardEvent) {
    if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); marker.closePopup(); element.focus(); }
  }
  function keyboard(event: KeyboardEvent) {
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); event.stopPropagation(); open(); }
    else escape(event);
  }
  function detachPopup() { popupElement?.removeEventListener("keydown", escape); popupElement = undefined; }
  marker.on("click", () => open());
  marker.on("popupopen", () => {
    if (disposed) return;
    element.setAttribute("aria-expanded", "true"); detachPopup(); popupElement = popup.getElement();
    popupElement?.addEventListener("keydown", escape);
    const close = popupElement?.querySelector(".leaflet-popup-close-button");
    close?.setAttribute("aria-label", "Cerrar detalles"); close?.setAttribute("title", "Cerrar detalles");
    onOpen({ points, selectedId, content, popup, onLayout });
  });
  marker.on("popupclose", () => { element.setAttribute("aria-expanded", "false"); detachPopup(); if (!disposed) onClose(content); });
  element.addEventListener("keydown", keyboard);
  function dispose() { if (disposed) return; disposed = true; detachPopup(); element.removeEventListener("keydown", keyboard); marker.closePopup(); marker.off(); }
  marker.on("remove", dispose);
  return { open, dispose };
}
