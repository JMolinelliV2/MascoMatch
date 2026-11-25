import test from "node:test";
import assert from "node:assert/strict";
import { matchSupportKind } from "../lib/match-support.ts";

test("invita a apoyar después de una confirmación nueva y distingue pista, contacto y recuperación", () => {
  assert.equal(matchSupportKind(null, "RESOLVED", false, false), "sighting");
  assert.equal(matchSupportKind("CONFIRMED_RELEVANT", "RESOLVED", false, true), "contact");
  assert.equal(matchSupportKind(null, "RESOLVED", true, true), "recovered");
});

test("no invita al descartar, marcar como posible o cerrar una búsqueda cuyo match ya se confirmó", () => {
  assert.equal(matchSupportKind(null, "FALSE_MATCH", false, false), null);
  assert.equal(matchSupportKind(null, "CONFIRMED_RELEVANT", false, true), null);
  assert.equal(matchSupportKind("RESOLVED", "RESOLVED", true, true), null);
});
