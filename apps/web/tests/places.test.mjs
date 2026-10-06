import { test } from "node:test";
import assert from "node:assert/strict";
import { normalizePlaces, rankPlaces } from "../lib/places.ts";

function point(coordinates, properties = {}) {
  return { geometry: { type: "Point", coordinates }, properties };
}

test("conserva el orden longitud/latitud de GeoJSON y arma una dirección legible", () => {
  const places = normalizePlaces({ features: [point([-55.95, -34.79], {
    name: "Avenida Pérez Butler", street: "Avenida Pérez Butler", housenumber: "1200", city: "El Pinar", country: "Uruguay",
  })] });
  assert.equal(places[0].latitude, -34.79);
  assert.equal(places[0].longitude, -55.95);
  assert.equal(places[0].label, "Avenida Pérez Butler 1200");
  assert.equal(places[0].detail, "El Pinar, Uruguay");
  assert.equal(places[0].locality, "El Pinar, Uruguay");
});

test("rechaza coordenadas fuera de rango o ausentes y respuestas no estructuradas", () => {
  assert.deepEqual(normalizePlaces(null), []);
  assert.deepEqual(normalizePlaces({ features: [null, point([0, 91]), point([181, 0]), point([NaN, 0]), point(["-55", "-34"])] }), []);
});

test("elimina duplicados sin perder lugares distintos con el mismo nombre", () => {
  const first = point([-55.95, -34.79], { name: "Plaza", city: "El Pinar" });
  const second = point([-56.18, -34.90], { name: "Plaza", city: "Montevideo" });
  assert.equal(normalizePlaces({ features: [first, first, second] }).length, 2);
});

const origin = { latitude: -34.79, longitude: -55.95, countryCode: "UY" };
function candidate(name, coordinates, countrycode = "UY", city = "El Pinar") {
  return normalizePlaces({ features: [point(coordinates, { name, city, countrycode })] })[0];
}

test("excluye otros países incluso si tienen coincidencia exacta o están más cerca", () => {
  const foreign = candidate("Plaza Independencia", [-55.95, -34.79], "AR");
  const local = candidate("Plaza Independencia Norte", [-55.96, -34.80]);
  const unknown = { ...local, id: "unknown", countryCode: undefined };
  const results = rankPlaces([foreign, unknown, local], "Plaza Independencia", "UY", origin);
  assert.deepEqual(results.map(place => place.id), [local.id]);
});

test("una coincidencia exacta del mismo país aparece antes que coincidencias parciales cercanas", () => {
  const nearby = candidate("Plaza Independencia Norte", [-55.95, -34.791]);
  const exact = candidate("Plaza Independencia", [-56.20, -34.91], "UY", "Montevideo");
  const results = rankPlaces([nearby, exact], "plaza independencia", "UY", origin);
  assert.equal(results[0].id, exact.id);
  assert.ok(results[0].distanceMeters > results[1].distanceMeters);
});

test("las coincidencias parciales se ordenan por distancia a la persona", () => {
  const far = candidate("Plaza del Centro", [-56.20, -34.91]);
  const nearby = candidate("Plaza del Barrio", [-55.95, -34.791]);
  const results = rankPlaces([far, nearby], "plaz", "UY", origin);
  assert.equal(results[0].id, nearby.id);
  assert.ok(results[0].distanceMeters < 200);
});

test("una búsqueda genérica como plaza prioriza cercanía aunque haya un lugar llamado Plaza", () => {
  const far = candidate("Plaza", [-56.20, -34.91]);
  const nearby = candidate("Plaza del Barrio", [-55.95, -34.791]);
  assert.equal(rankPlaces([far, nearby], "plaza", "UY", origin)[0].id, nearby.id);
});

test("reconoce coincidencias exactas con acentos y ciudad sin duplicar candidatos", () => {
  const exact = candidate("Plaza Pérez", [-56.20, -34.91], "UY", "Montevideo");
  const nearby = candidate("Plaza Pérez Norte", [-55.95, -34.791]);
  const results = rankPlaces([nearby, exact, exact], "Plaza Perez, Montevideo", "UY", origin);
  assert.equal(results.length, 2);
  assert.equal(results[0].id, exact.id);
});

test("sin ubicación del dispositivo mantiene la restricción de país y no inventa distancias", () => {
  const foreign = candidate("El Pinar", [-58.38, -34.60], "AR");
  const local = candidate("El Pinar", [-55.95, -34.79]);
  const results = rankPlaces([foreign, local], "El Pinar", "UY");
  assert.equal(results.length, 1);
  assert.equal(results[0].distanceMeters, undefined);
});
