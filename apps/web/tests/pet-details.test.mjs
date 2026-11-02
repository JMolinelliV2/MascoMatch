import test from "node:test";
import assert from "node:assert/strict";
import { colorLabel, colorValue, readPetDetails, accessoryLabels } from "../lib/pet-details.ts";

test("colores sugeridos y libres conservan sus valores y etiquetas", () => {
  assert.equal(colorValue(" Marrón "), "brown");
  assert.equal(colorLabel("brown"), "Marrón");
  assert.equal(colorValue(" Gris azulado "), "Gris azulado");
  assert.equal(colorLabel("Gris azulado"), "Gris azulado");
  assert.equal(colorValue(""), "unknown");
  assert.equal(colorLabel("unknown"), "");
});
test("todos los formularios guardan raza libre, varios colores y accesorios", () => {
  const form = new FormData();
  for (const [key, value] of Object.entries({ breed: " Cruza poco común ", color: "Blanco", secondary_colors: "Negro, gris azulado, Negro", collar_status: "yes", collar_color: "Turquesa", clothing_status: "yes", clothing_description: "Pañuelo", clothing_color: "Violeta" })) form.set(key, value);
  const result = readPetDetails(form);
  assert.equal(result.breed, "Cruza poco común");
  assert.equal(result.primary_color, "white");
  assert.deepEqual(result.secondary_colors, ["black", "gris azulado"]);
  assert.deepEqual(accessoryLabels(result), ["Collar · Turquesa", "Pañuelo · Violeta"]);
  form.set("collar_status", "no");
  assert.equal(readPetDetails(form).collar_color, null);
});
test("el avistamiento breve admite no completar características", () => {
  const result = readPetDetails(new FormData());
  assert.equal(result.breed, "unknown");
  assert.equal(result.collar_status, "unknown");
  assert.deepEqual(result.secondary_colors, []);
  assert.deepEqual(accessoryLabels(result), []);
});
