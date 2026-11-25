export type MatchSupportKind = "sighting" | "contact" | "recovered";

export function matchSupportKind(previous: string | null, saved: string, recovered: boolean, hasContact: boolean): MatchSupportKind | null {
  if (saved !== "RESOLVED" || previous === "RESOLVED") return null;
  if (recovered) return "recovered";
  return hasContact ? "contact" : "sighting";
}

export const supportShareUrl = "https://mascomatch.com/";
export const supportShareText = "¿Conocés MascoMatch? Es gratis para buscar mascotas perdidas y avisar si viste una. Compartilo con tu comunidad para que más mascotas puedan volver a casa. 🐾";
