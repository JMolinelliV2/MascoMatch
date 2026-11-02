import test from "node:test";
import assert from "node:assert/strict";
import { purinaBreedOptions, purinaBreedSources } from "../lib/breed-catalog.ts";
import { breedOptions } from "../lib/pet-details.ts";

const key = value => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es");

test("el catálogo incluye las 18 páginas de perros y las 5 páginas de gatos", () => {
  for (const [species, pages, count] of [["dog", 18, 214], ["cat", 5, 53]]) {
    const source = purinaBreedSources[species];
    assert.equal(source.pages.length, pages);
    assert.equal(source.count, count);
    assert.equal(source.pages.reduce((total, page) => total + page.count, 0), count);
    assert.deepEqual(source.pages.map(page => page.number), Array.from({length: pages}, (_, index) => index + 1));
    assert.equal(purinaBreedOptions[species].length, count);
  }
});

test("todas las razas importadas están disponibles sin duplicados ni nombres truncados", () => {
  for (const species of ["dog", "cat"]) {
    assert.equal(breedOptions[species][0], "Mestizo");
    assert.equal(new Set(breedOptions[species].map(key)).size, breedOptions[species].length);
    for (const name of purinaBreedOptions[species]) {
      assert.ok(breedOptions[species].includes(name), `${species}: falta ${name}`);
      assert.ok(name.length > 0 && name.length <= 120);
    }
  }
});

test("las razas de las últimas páginas y las variedades mantienen su especie", () => {
  for (const dog of ["Terrier escocés (scottish terrier)", "Xoloitzcuintle (mediano)", "Chihuahua (de pelo largo)", "Chihuahua (de pelo suave)"]) {
    assert.ok(breedOptions.dog.includes(dog));
    assert.ok(!breedOptions.cat.includes(dog));
  }
  for (const cat of ["Snowshoe", "Tiffanie", "Tonquinés", "Van turco", "Bobtail japonés de pelo corto", "Bobtail japonés de pelo largo"]) {
    assert.ok(breedOptions.cat.includes(cat));
    assert.ok(!breedOptions.dog.includes(cat));
  }
  assert.ok(breedOptions.dog.includes("Shih tzu"));
  assert.ok(breedOptions.cat.includes("Khao Manee"));
  assert.ok(!breedOptions.dog.some(name => name.includes("guía completa")));
});
