import test from "node:test";
import assert from "node:assert/strict";
import { knownMapLocation, mapDateRangeError, mapSearchParams, parseMapRadius } from "../lib/map-filters.ts";

const filters = { species: "", from: "", to: "", radius: null, center: null, compatible: false };
const origin = { latitude: -34.9, longitude: -56.16 };

test("sin ubicación o al elegir todo el país no aplica un radio oculto ni limita la antigüedad", () => {
  for (const selection of [{}, { radius: 15 }, { center: origin }]) {
    const params = mapSearchParams({ ...filters, ...selection });
    assert.equal(params.get("days"), "0");
    assert.equal(params.has("latitude"), false);
    assert.equal(params.has("radius_km"), false);
  }
});

test("el radio cero, las fechas y los demás filtros se conservan en la consulta", () => {
  const params = mapSearchParams({ ...filters, species: "cat", center: origin, radius: 0, from: "2024-01-04", to: "2024-01-04", compatible: true });
  assert.equal(params.get("radius_km"), "0");
  assert.equal(params.get("latitude"), "-34.9");
  assert.equal(params.get("longitude"), "-56.16");
  assert.equal(params.get("date_from"), "2024-01-04");
  assert.equal(params.get("date_to"), "2024-01-04");
  assert.equal(params.get("species"), "cat");
  assert.equal(params.get("compatible_only"), "true");
});

test("permite rangos abiertos y un solo día, pero rechaza fechas invertidas o inválidas", () => {
  for (const [from, to] of [["", ""], ["2024-01-04", ""], ["", "2024-01-04"], ["2024-01-04", "2024-01-04"]]) assert.equal(mapDateRangeError(from, to), "");
  for (const [from, to] of [["2024-01-05", "2024-01-04"], ["2024-02-31", ""], ["0000-01-01", ""], ["invalid", ""], ["", "9999-12-31"]]) assert.ok(mapDateRangeError(from, to));
});

test("el número editable admite kilómetros enteros de 0 a 500 y rechaza entradas aleatorias", () => {
  assert.equal(parseMapRadius("0"), 0);
  assert.equal(parseMapRadius("37"), 37);
  assert.equal(parseMapRadius("500"), 500);
  for (const value of ["", "-1", "501", "1.5", "hola", "999999999999999999999"]) assert.equal(parseMapRadius(value), undefined);
});

test("la ubicación automática solo se solicita cuando ya existe permiso", async () => {
  for (const state of ["prompt", "denied"]) {
    let called = false;
    const browser = { permissions: { query: async () => ({ state }) }, geolocation: { getCurrentPosition: () => { called = true; } } };
    assert.equal(await knownMapLocation(browser), null);
    assert.equal(called, false);
  }
  const browser = { permissions: { query: async () => ({ state: "granted" }) }, geolocation: { getCurrentPosition: resolve => resolve({ coords: origin }) } };
  assert.deepEqual(await knownMapLocation(browser), origin);
});

test("si falla el permiso o el GPS se conserva la vista de todas las zonas", async () => {
  assert.equal(await knownMapLocation({}), null);
  assert.equal(await knownMapLocation({ permissions: { query: async () => { throw new Error("unsupported"); } }, geolocation: {} }), null);
  assert.equal(await knownMapLocation({ permissions: { query: async () => ({ state: "granted" }) }, geolocation: { getCurrentPosition: (_, reject) => reject(new Error("timeout")) } }), null);
});
