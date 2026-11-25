import test from "node:test";
import assert from "node:assert/strict";
import { loginDestination, ownerRecoveryLoginHref, ownerRecoveryReturnPath } from "../lib/login-return.ts";

const caseId = "ca11e123-1234-4321-a123-123456789012";
const recovery = `/encontre?aviso=${caseId}`;

test("el acceso del dueño conserva el aviso y regresa a la recuperación después de ingresar", () => {
  const login = new URL(ownerRecoveryLoginHref(caseId), "https://mascomatch.com");
  assert.equal(login.pathname, "/login");
  const returnTo = login.searchParams.get("next");
  assert.equal(returnTo, recovery);
  assert.equal(ownerRecoveryReturnPath(returnTo), recovery);
  assert.equal(loginDestination(returnTo, true), recovery);
  // Retiring an existing own notice does not require a verified email.
  assert.equal(loginDestination(returnTo, false), recovery);
});

test("el ingreso habitual mantiene sus destinos de avisos y confirmación de correo", () => {
  assert.equal(loginDestination(undefined, true), "/mis-avisos");
  assert.equal(loginDestination(null, false), "/confirmar-correo");
  assert.equal(loginDestination(undefined, undefined), "/confirmar-correo");
});

test("el regreso no permite enlaces externos, rutas arbitrarias ni avisos ambiguos", () => {
  for (const value of [
    "https://evil.example/", "//evil.example/", "javascript:alert(1)",
    "/\\evil.example/", "/admin", "/login", "/encontre", "/encontre?aviso=MM-000008",
    `/encontre?aviso=${caseId}&aviso=other`, `${recovery}&next=https://evil.example/`,
    `${recovery}#fragment`, `${recovery}\n`, `${recovery}\r\n`,
    encodeURIComponent(recovery), [recovery], {}, null, undefined,
  ]) {
    assert.equal(ownerRecoveryReturnPath(value), null);
    assert.equal(loginDestination(value, true), "/mis-avisos");
    assert.equal(loginDestination(value, false), "/confirmar-correo");
  }
});
