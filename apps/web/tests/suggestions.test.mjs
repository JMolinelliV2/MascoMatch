import test from "node:test";
import assert from "node:assert/strict";
import { applySuggestion, matchingSuggestions } from "../lib/suggestions.ts";
import { breedOptions } from "../lib/pet-details.ts";

test("las sugerencias reconocen mayúsculas y acentos sin alterar el texto mostrado", () => {
  assert.deepEqual(matchingSuggestions(["Negro", "Marrón", "Blanco"], "MARRON"), ["Marrón"]);
  assert.ok(matchingSuggestions(breedOptions.dog, "pastor aleman").includes("Pastor alemán"));
});

test("el catálogo completo sigue disponible y las opciones repetidas se unifican", () => {
  assert.equal(matchingSuggestions(breedOptions.cat, "").length, breedOptions.cat.length);
  assert.ok(matchingSuggestions(breedOptions.dog, "").includes(breedOptions.dog.at(-1)));
  assert.deepEqual(matchingSuggestions(["Marrón", "MARRON", "Negro"], ""), ["Marrón", "Negro"]);
});

test("las sugerencias de varios colores conservan los colores anteriores y evitan repetirlos", () => {
  assert.deepEqual(matchingSuggestions(["Marrón", "Negro", "Blanco"], "Marron, ne", true), ["Negro"]);
  assert.deepEqual(matchingSuggestions(["Marrón", "Negro", "Blanco"], "Marron, ", true), ["Negro", "Blanco"]);
  assert.equal(applySuggestion("Blanco, gris azulado, ne", "Negro", true), "Blanco, gris azulado, Negro");
});

test("un valor libre no se reemplaza por una sugerencia que el usuario no eligió", () => {
  assert.deepEqual(matchingSuggestions(["Marrón", "Negro"], "Turquesa"), []);
  assert.equal(applySuggestion("", "Mestizo"), "Mestizo");
  assert.equal(applySuggestion("Raza escrita por la persona", "Van turco"), "Van turco");
});
