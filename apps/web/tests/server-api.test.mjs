import test from "node:test";
import assert from "node:assert/strict";
import { authorization, boundedBody, proxyHeaders, sameOrigin } from "../lib/server-api.ts";

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

test("el origen público exige el protocolo y dominio configurados", () => {
  process.env.PUBLIC_SITE_URL = "https://mascomatch.com";
  try {
    const request = origin => new Request("http://web:3000/api/session", {headers:{host:"web:3000",origin}});
    assert.equal(sameOrigin(request("https://mascomatch.com")), true);
    assert.equal(sameOrigin(request("http://mascomatch.com")), false);
    assert.equal(sameOrigin(request("https://other.example")), false);
  } finally { delete process.env.PUBLIC_SITE_URL; }
});

test("solo el modo de proxy explícito propaga una dirección válida", () => {
  const request = value => new Request("http://localhost", {headers:{"x-mascomatch-client-ip":value}});
  assert.deepEqual(proxyHeaders(request("198.51.100.10")), {});
  process.env.TRUST_PROXY_HEADERS = "true";
  try {
    assert.deepEqual(proxyHeaders(request("198.51.100.10")), {"X-MascoMatch-Client-IP":"198.51.100.10"});
    assert.deepEqual(proxyHeaders(request("malformed")), {});
  } finally { delete process.env.TRUST_PROXY_HEADERS; }
});
