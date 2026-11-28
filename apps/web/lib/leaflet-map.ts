import type { MapOptions, Point } from "leaflet";

const WHEEL_PIXELS_PER_LEVEL = 160;

export function createLeafletMap(L: typeof import("leaflet"), container: HTMLElement, options?: MapOptions) {
  const map = L.map(container, { ...options, scrollWheelZoom: false, zoomSnap: 0 });
  const view = container.ownerDocument.defaultView ?? window;
  const reducedMotion = view.matchMedia("(prefers-reduced-motion: reduce)");
  let pending: { delta: number; point: Point } | undefined;
  let frame: number | undefined;
  let zooming = false;

  function applyZoom() {
    frame = undefined;
    if (zooming) return;
    const gesture = pending;
    pending = undefined;
    if (!gesture?.delta) return;
    const current = map.getZoom();
    const change = L.Browser.any3d
      ? Math.max(-1, Math.min(1, gesture.delta / WHEEL_PIXELS_PER_LEVEL))
      : Math.sign(gesture.delta);
    const target = Math.min(map.getMaxZoom(), Math.max(map.getMinZoom(), current + change));
    if (target === current) return;

    // Leaflet ignores setView updates during an active zoom transition.
    zooming = true;
    map.setZoomAround(gesture.point, target, { animate: !reducedMotion.matches });
  }

  function scheduleZoom() {
    if (!zooming && frame === undefined && pending?.delta) {
      frame = view.requestAnimationFrame(applyZoom);
    }
  }

  function onWheel(event: WheelEvent) {
    if (!event.ctrlKey || event.defaultPrevented) return;
    const delta = L.DomEvent.getWheelDelta(event);
    if (!delta) return;
    event.preventDefault();
    pending = { delta: (pending?.delta ?? 0) + delta, point: map.mouseEventToContainerPoint(event) };
    scheduleZoom();
  }

  function onZoomStart() { zooming = true; }
  function onZoomEnd() {
    zooming = false;
    scheduleZoom();
  }

  // Capture Ctrl + wheel over popups too, while allowing their normal scroll.
  container.addEventListener("wheel", onWheel, { capture: true, passive: false });
  map.on("zoomstart", onZoomStart);
  map.on("zoomend", onZoomEnd);
  map.once("unload", () => {
    container.removeEventListener("wheel", onWheel, { capture: true });
    map.off("zoomstart", onZoomStart);
    map.off("zoomend", onZoomEnd);
    if (frame !== undefined) view.cancelAnimationFrame(frame);
    pending = undefined;
  });
  return map;
}
