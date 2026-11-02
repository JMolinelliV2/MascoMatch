import { purinaBreedOptions } from "./breed-catalog.ts";

export const colorOptions = ["Marrón", "Negro", "Blanco", "Gris", "Crema", "Naranja", "Beige / canela", "Rojizo", "Varios colores"];
const colors: Record<string, string> = { brown: "Marrón", black: "Negro", white: "Blanco", gray: "Gris", cream: "Crema", orange: "Naranja", tan: "Beige / canela", red: "Rojizo", multicolor: "Varios colores" };
const previousBreedOptions: Record<"dog" | "cat", string[]> = {
  dog: ["Mestizo", "Labrador", "Golden retriever", "Caniche", "Pastor alemán", "Bulldog", "Border collie", "Beagle", "Chihuahua", "Dachshund", "Pitbull", "Rottweiler", "Shih tzu", "Yorkshire terrier", "Husky"],
  cat: ["Mestizo", "Común europeo", "Siamés", "Persa", "Maine coon", "Angora", "Bengalí", "British shorthair", "Ragdoll", "Sphynx"],
};
function suggestions(species: "dog" | "cat"): string[] {
  const seen = new Set<string>();
  const names = [...purinaBreedOptions[species], ...previousBreedOptions[species]].filter(name => {
    const key = name.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es");
    if (key === "mestizo" || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  return ["Mestizo", ...names.sort(new Intl.Collator("es", { sensitivity: "base" }).compare)];
}
export const breedOptions: Record<string, string[]> = { dog: suggestions("dog"), cat: suggestions("cat") };

export type PetDetails = {
  breed?: string; primary_color?: string; secondary_colors?: string[];
  collar_status?: string; collar_color?: string | null; collar_description?: string | null;
  clothing_status?: string; clothing_color?: string | null; clothing_description?: string | null;
};
export function colorLabel(value?: string | null) { return !value || value === "unknown" ? "" : colors[value] || value; }
export function colorValue(value: string) {
  const text = value.trim();
  const key = text.toLocaleLowerCase("es");
  return Object.entries(colors).find(([id, label]) => id === key || label.toLocaleLowerCase("es") === key)?.[0] || text || "unknown";
}
export function readPetDetails(form: FormData) {
  const text = (key: string) => String(form.get(key) || "").trim();
  const optionalColor = (prefix: string) => {
    const color = colorValue(text(`${prefix}_color`));
    return text(`${prefix}_status`) === "no" || color === "unknown" ? null : color;
  };
  return {
    breed: text("breed") || "unknown", primary_color: colorValue(text("color")),
    secondary_colors: [...new Set(text("secondary_colors").split(",").map(colorValue).filter(v => v !== "unknown"))],
    collar_status: text("collar_status") || "unknown", collar_color: optionalColor("collar"),
    collar_description: text("collar_status") === "no" ? null : text("collar_description") || null,
    clothing_status: text("clothing_status") || "unknown", clothing_color: optionalColor("clothing"),
    clothing_description: text("clothing_status") === "no" ? null : text("clothing_description") || null,
  };
}
export function accessoryLabels(details: PetDetails): string[] {
  const result: string[] = [];
  if (details.collar_status === "yes" || details.collar_color || details.collar_description) result.push(["Collar", colorLabel(details.collar_color), details.collar_description].filter(Boolean).join(" · "));
  else if (details.collar_status === "no") result.push("Sin collar");
  if (details.clothing_status === "yes" || details.clothing_description || details.clothing_color) result.push([details.clothing_description || "Prenda / accesorio", colorLabel(details.clothing_color)].filter(Boolean).join(" · "));
  return result;
}

export function petDetailsError(details: PetDetails): string {
  const colors = details.secondary_colors || [];
  return colors.length > 5 || colors.some(color => color.length > 40) ? "Ingresá hasta 5 colores, de hasta 40 caracteres cada uno." : "";
}
