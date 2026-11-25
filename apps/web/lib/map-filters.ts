export const MAX_MAP_RADIUS_KM = 500;
export const ALL_MAP_DISTANCES = MAX_MAP_RADIUS_KM + 1;
export const DEFAULT_MAP_RADIUS_KM = 15;
export const COUNTRY_MAP_BOUNDS: [[number, number], [number, number]] = [[-35.1, -58.6], [-30, -53]];
export type MapOrigin = { latitude: number; longitude: number };
export type MapSearchFilters = {
  species: string; from: string; to: string; radius: number | null;
  center: MapOrigin | null; compatible: boolean;
};

export function mapDateRangeError(from: string, to: string): string {
  for (const value of [from, to]) {
    if (value && (!/^\d{4}-\d{2}-\d{2}$/.test(value) || value.startsWith("0000-") || !Number.isFinite(Date.parse(`${value}T00:00:00Z`))
      || new Date(`${value}T00:00:00Z`).toISOString().slice(0, 10) !== value)) return "Ingresá fechas válidas.";
  }
  if (to === "9999-12-31") return "Ingresá una fecha hasta válida.";
  return from && to && from > to ? "La fecha desde debe ser anterior o igual a la fecha hasta." : "";
}

export function parseMapRadius(value: string): number | undefined {
  if (!/^\d+$/.test(value)) return undefined;
  const radius = Number(value);
  return Number.isInteger(radius) && radius >= 0 && radius <= MAX_MAP_RADIUS_KM ? radius : undefined;
}

export function mapSearchParams(filters: MapSearchFilters): URLSearchParams {
  const params = new URLSearchParams({ species: filters.species, days: "0", compatible_only: String(filters.compatible) });
  if (filters.from) params.set("date_from", filters.from);
  if (filters.to) params.set("date_to", filters.to);
  if (filters.center && filters.radius !== null) {
    params.set("latitude", String(filters.center.latitude));
    params.set("longitude", String(filters.center.longitude));
    params.set("radius_km", String(filters.radius));
  }
  return params;
}

/** Reuse a location grant without opening a permission prompt on page load. */
export async function knownMapLocation(browser: Pick<Navigator, "permissions" | "geolocation">): Promise<MapOrigin | null> {
  try {
    if (!browser.permissions || !browser.geolocation) return null;
    if ((await browser.permissions.query({ name: "geolocation" })).state !== "granted") return null;
    const position = await new Promise<GeolocationPosition>((resolve, reject) => browser.geolocation.getCurrentPosition(resolve, reject,
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 }));
    return { latitude: position.coords.latitude, longitude: position.coords.longitude };
  } catch { return null; }
}
