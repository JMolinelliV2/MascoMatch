import test from "node:test";
import assert from "node:assert/strict";
import { phoneError } from "../lib/phone-numbers.ts";

test("acepta teléfonos uruguayos locales y teléfonos internacionales según su país", () => {
  for (const value of [
    "099 123 456", "99 123 456", "098765432", "2400 1234",
    "+598 99 123 456", "+598 98 765 432", "+598 2400 1234",
    "00598 99 123 456", "+54 9 11 2345 6789", "+55 11 91234-5678",
    "+44 20 8366 1177", "+34 612 34 56 78", "+1 (202) 555-0123",
    "  +598 99 123 456  ",
  ]) assert.equal(phoneError(value, true), "", value);
});

test("rechaza números imposibles, prefijos inexistentes, texto y extensiones", () => {
  for (const value of [
    "8812391923012301023", "11111111", "00000000", "09912345", "0991234567",
    "+598 11111111", "+598 123", "+999 99123456", "+1 200 123 0101",
    "abc", "099123456abc", "Llamar al +59899123456", "+59899123456 ext 123",
    "+598+99123456", "０９９１２３４５６", "12345678901234567890123456789012345",
  ]) assert.match(phoneError(value), /teléfono válido/, value);
});

test("el teléfono de cuenta es opcional y el de quien resguarda una mascota es obligatorio", () => {
  for (const value of ["", "   "]) {
    assert.equal(phoneError(value), "");
    assert.match(phoneError(value, true), /teléfono de contacto/);
  }
});
