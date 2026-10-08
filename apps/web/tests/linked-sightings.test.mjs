import test from "node:test";
import assert from "node:assert/strict";
import { localDateTime, sightingMessage } from "../lib/linked-sightings.ts";

test("el reporte sin foto se presenta como un avistamiento por confirmar", () => {
  assert.match(sightingMessage({ id: "1", status: "UNVERIFIED", owner_notified: true }), /por confirmar/);
  assert.match(sightingMessage({ id: "1", status: "UNVERIFIED", owner_notified: false }), /guardado/);
});
test("la foto compatible no se presenta como certeza de identidad", () => {
  assert.match(sightingMessage({ id: "1", status: "POSSIBLE_MATCH", owner_notified: true }), /todavía necesita confirmación/);
});
test("una foto inconclusa se conserva como un reporte para revisión humana", () => {
  const message = sightingMessage({ id: "1", status: "UNVERIFIED", owner_notified: true }, true);
  assert.match(message, /fotos necesitan revisión/);
  assert.doesNotMatch(message, /no hay foto/);
});
test("un reporte pendiente o incompatible no asegura que el dueño recibió una alerta", () => {
  assert.match(sightingMessage({ id: "1", status: "PENDING", owner_notified: false }), /se notificará/);
  assert.match(sightingMessage({ id: "1", status: "NOT_COMPATIBLE", owner_notified: false }), /No se generó/);
});
test("la hora opcional conserva el formato que acepta datetime-local", () => {
  assert.match(localDateTime(new Date("2026-10-07T20:00:00Z")), /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/);
});
