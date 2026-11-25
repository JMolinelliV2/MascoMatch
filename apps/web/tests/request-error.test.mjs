import test from "node:test";
import assert from "node:assert/strict";
import { requestError } from "../lib/request-error.ts";

const fallback = "No pudimos consultar la información. Intentá de nuevo.";
test("conserva el contexto útil de errores de acceso y disponibilidad", () => {
  assert.equal(requestError(new Error("Tu sesión venció. Ingresá nuevamente."), fallback), "Tu sesión venció. Ingresá nuevamente.");
  assert.equal(requestError(new Error("Este reporte ya no está disponible."), fallback), "Este reporte ya no está disponible.");
});
test("no muestra excepciones técnicas o contenidos de una respuesta malformada", () => {
  for (const cause of [new TypeError("Failed to fetch"), new SyntaxError("Unexpected token: PRIVATE_RESPONSE"), Object.assign(new Error("Network operation failed"), { name: "TimeoutError" }), Object.assign(new Error("Request aborted"), { name: "AbortError" })]) {
    assert.equal(requestError(cause, fallback), fallback);
  }
});
test("los errores vacíos o desconocidos reciben un mensaje legible", () => {
  for (const cause of [null, undefined, "Failed to fetch", { message: "Internal details" }, new Error("")]) assert.equal(requestError(cause, fallback), fallback);
});
