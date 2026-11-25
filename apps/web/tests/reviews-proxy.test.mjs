import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";
import ts from "typescript";
import { NextRequest } from "next/server.js";

const require = createRequire(import.meta.url);
async function compiled(path, imports = {}) {
  const source = await readFile(new URL(path, import.meta.url), "utf8");
  let { outputText } = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } });
  for (const [specifier, target] of Object.entries(imports)) outputText = outputText.replaceAll(JSON.stringify(specifier), JSON.stringify(target));
  return `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`;
}
const api = await compiled("../lib/server-api.ts");
const { GET, PATCH, DELETE } = await import(await compiled("../app/api/reviews/[[...path]]/route.ts", {
  "@/lib/server-api": api, "next/server": pathToFileURL(require.resolve("next/server.js")).href,
}));
const context = path => ({ params: Promise.resolve({ path }) });
const request = (path, method, body, origin = "http://localhost:3000") => new NextRequest(`http://localhost:3000/api/reviews/${path}`, {
  method, headers: { host: "localhost:3000", origin, cookie: "mascomatch_session=review-test-session", "Content-Type": "application/json" },
  ...(body !== undefined ? { body: typeof body === "string" ? body : JSON.stringify(body) } : {}),
});

test("la edición de reseña usa la sesión y permite la misma opinión desde cuenta o aviso", async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  const payload = { anonymous: true, rating: 5, comment: "Mi opinión editada sin ningún apodo.", consent: true };
  globalThis.fetch = async (url, options) => { calls.push({ url, options }); return Response.json({ id: "same-review", ...payload }); };
  try {
    for (const path of [["me"], ["lost-cases", "11111111-1111-4111-8111-111111111111"]]) {
      const response = await PATCH(request(path.join("/"), "PATCH", payload), context(path));
      assert.equal(response.status, 200);
      assert.equal(response.headers.get("Cache-Control"), "no-store");
      const call = calls.at(-1);
      assert.ok(call.url.endsWith(`/reviews/${path.join("/")}`));
      assert.equal(call.options.headers.Authorization, "Bearer review-test-session");
      assert.deepEqual(JSON.parse(call.options.body.toString()), payload);
    }
  } finally { globalThis.fetch = originalFetch; }
});

test("el proxy impide cambios de reseñas desde otros sitios o rutas no autorizadas", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = () => assert.fail("Una solicitud rechazada no debe alcanzar la API");
  try {
    assert.equal((await PATCH(request("me", "PATCH", {}, "https://otro.example"), context(["me"]))).status, 403);
    assert.equal((await PATCH(request("other-user", "PATCH", {}), context(["other-user"]))).status, 403);
    assert.equal((await DELETE(request("me", "DELETE", undefined, "https://otro.example"), context(["me"]))).status, 403);
    assert.equal((await PATCH(request("me", "PATCH", "x".repeat(8193)), context(["me"]))).status, 413);
  } finally { globalThis.fetch = originalFetch; }
});

test("consultar la reseña existente no cambia ni vuelve a publicar su contenido", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    assert.equal(options.method, "GET");
    assert.equal(options.body, undefined);
    assert.ok(url.endsWith("/reviews/me"));
    return Response.json({ review: { id: "same-review", comment: "La experiencia que se mantiene." } });
  };
  try {
    const response = await GET(request("me?author_id=ignored", "GET"), context(["me"]));
    assert.equal((await response.json()).review.id, "same-review");
  } finally { globalThis.fetch = originalFetch; }
});
