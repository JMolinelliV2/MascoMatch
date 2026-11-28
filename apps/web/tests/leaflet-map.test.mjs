import assert from "node:assert/strict";
import test from "node:test";
import { createLeafletMap } from "../lib/leaflet-map.ts";

function setupMap(initialZoom = 10, { reducedMotion = false } = {}) {
  const container = new EventTarget();
  const changes = [];
  const listeners = new Map();
  const frames = new Map();
  let zoom = initialZoom;
  let frameId = 0;
  container.ownerDocument = { defaultView: {
    matchMedia: () => ({ matches: reducedMotion }),
    requestAnimationFrame(callback) { frames.set(++frameId, callback); return frameId; },
    cancelAnimationFrame(id) { frames.delete(id); },
  } };
  const leaflet = {
    map(element, options) {
      assert.equal(element, container);
      assert.equal(options.scrollWheelZoom, false);
      assert.equal(options.zoomSnap, 0);
      return {
        getZoom: () => zoom,
        getMinZoom: () => 0,
        getMaxZoom: () => 19,
        mouseEventToContainerPoint: event => ({ x: event.clientX, y: event.clientY }),
        setZoomAround(point, level, { animate }) {
          listeners.get("zoomstart")?.();
          zoom = level;
          changes.push({ point, level, animate });
          if (!animate) listeners.get("zoomend")?.();
        },
        on(name, callback) { listeners.set(name, callback); },
        off(name) { listeners.delete(name); },
        once(name, callback) { listeners.set(name, callback); },
      };
    },
    Browser: { any3d: true },
    DomEvent: { getWheelDelta: event => -event.deltaY },
  };
  createLeafletMap(leaflet, container);

  function wheel({ ctrlKey, deltaY, x = 20, y = 40 }) {
    const event = Object.assign(new Event("wheel", { cancelable: true }), {
      ctrlKey, deltaY, clientX: x, clientY: y,
    });
    container.dispatchEvent(event);
    return event;
  }

  return {
    changes,
    wheel,
    renderFrame() {
      const callbacks = [...frames.values()];
      frames.clear();
      for (const callback of callbacks) callback();
    },
    finishZoom: () => listeners.get("zoomend")?.(),
    unload: () => listeners.get("unload")?.(),
  };
}

test("la rueda sola conserva el desplazamiento de la página", () => {
  const { changes, wheel, renderFrame } = setupMap();
  assert.equal(wheel({ ctrlKey: false, deltaY: -40 }).defaultPrevented, false);
  renderFrame();
  assert.deepEqual(changes, []);
});

test("Ctrl y rueda animan un zoom fraccionario desde el cursor y acumulan el giro durante la transición", () => {
  const { changes, wheel, renderFrame, finishZoom } = setupMap();
  assert.equal(wheel({ ctrlKey: true, deltaY: -40 }).defaultPrevented, true);
  renderFrame();
  assert.deepEqual(changes, [{ point: { x: 20, y: 40 }, level: 10.25, animate: true }]);

  assert.equal(wheel({ ctrlKey: true, deltaY: 40 }).defaultPrevented, true);
  wheel({ ctrlKey: true, deltaY: 40, x: 50, y: 30 });
  renderFrame();
  assert.equal(changes.length, 1);
  finishZoom();
  renderFrame();
  assert.deepEqual(changes, [
    { point: { x: 20, y: 40 }, level: 10.25, animate: true },
    { point: { x: 50, y: 30 }, level: 9.75, animate: true },
  ]);
});

test("alcanzar el límite o desmontar el mapa evita cambios de zoom pendientes", () => {
  const { changes, wheel, renderFrame, unload } = setupMap(19);
  wheel({ ctrlKey: true, deltaY: -40 });
  renderFrame();
  wheel({ ctrlKey: true, deltaY: 40 });
  unload();
  assert.equal(wheel({ ctrlKey: true, deltaY: 40 }).defaultPrevented, false);
  renderFrame();
  assert.deepEqual(changes, []);
});

test("el movimiento reducido conserva los pasos fraccionarios y desactiva la animación", () => {
  const { changes, wheel, renderFrame } = setupMap(10, { reducedMotion: true });
  wheel({ ctrlKey: true, deltaY: -40 });
  renderFrame();
  wheel({ ctrlKey: true, deltaY: 20 });
  renderFrame();
  assert.deepEqual(changes, [
    { point: { x: 20, y: 40 }, level: 10.25, animate: false },
    { point: { x: 20, y: 40 }, level: 10.125, animate: false },
  ]);
});
