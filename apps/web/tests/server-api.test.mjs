import test from "node:test";
import assert from "node:assert/strict";
import { authorization, boundedBody, sameOrigin } from "../lib/server-api.ts";

test("los cambios de sesión rechazan solicitudes de otro sitio", () => {
  const request = (origin, site = "same-origin") => new Request("http://localhost:3000/api/session", { headers: { host: "localhost:3000", origin, "sec-fetch-site": site } });
  assert.equal(sameOrigin(request("http://localhost:3000")), true);
  assert.equal(sameOrigin(request("https://other.example")), false);
  assert.equal(sameOrigin(request("http://localhost:3000", "cross-site")), false);
});
test("la sesión se toma de la cookie del servidor y no de parámetros de la URL", () => {
  assert.deepEqual(authorization({ cookies: { get: () => ({ value: "test-session" }) } }), { Authorization: "Bearer test-session" });
  assert.deepEqual(authorization({ cookies: { get: () => undefined } }), {});
});
test("la carga de fotos tiene un límite de tamaño incluso sin Content-Length", async () => {
  const request = body => new Request("http://localhost:3000", { method: "POST", body });
  assert.equal(new TextDecoder().decode(await boundedBody(request("hello"), 5)), "hello");
  await assert.rejects(() => boundedBody(request("too long"), 3), /BODY_TOO_LARGE/);
});
