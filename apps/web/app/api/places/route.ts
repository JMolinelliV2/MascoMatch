import { NextRequest, NextResponse } from "next/server";
import { normalizePlaces, rankPlaces } from "@/lib/places";
import type { SearchOrigin } from "@/lib/places";

export async function GET(request: NextRequest) {
  const query = request.nextUrl.searchParams;
  const search = query.get("q")?.trim();
  const latitude = query.get("lat");
  const longitude = query.get("lon");
  const reverse = latitude !== null || longitude !== null;
  const countryCode = (query.get("country") || process.env.NEXT_PUBLIC_SEARCH_COUNTRY || "UY").toUpperCase();
  const biasLatitude = query.get("bias_lat");
  const biasLongitude = query.get("bias_lon");
  let origin: SearchOrigin | undefined;
  if (!reverse && !/^[A-Z]{2}$/.test(countryCode)) {
    return NextResponse.json({ error: "El país de búsqueda no es válido." }, { status: 400 });
  }
  if (!reverse && (biasLatitude !== null || biasLongitude !== null)) {
    if (biasLatitude === null || biasLongitude === null || biasLatitude.trim() === "" || biasLongitude.trim() === ""
      || !Number.isFinite(Number(biasLatitude)) || !Number.isFinite(Number(biasLongitude))
      || Math.abs(Number(biasLatitude)) > 90 || Math.abs(Number(biasLongitude)) > 180) {
      return NextResponse.json({ error: "La ubicación de referencia no es válida." }, { status: 400 });
    }
    origin = { latitude: Number(biasLatitude), longitude: Number(biasLongitude), countryCode };
  }
  if (reverse) {
    if (latitude === null || longitude === null || latitude.trim() === "" || longitude.trim() === ""
      || !Number.isFinite(Number(latitude)) || !Number.isFinite(Number(longitude))
      || Math.abs(Number(latitude)) > 90 || Math.abs(Number(longitude)) > 180) {
      return NextResponse.json({ error: "La ubicación recibida no es válida." }, { status: 400 });
    }
  } else if (!search || search.length < 3 || search.length > 200) {
    return NextResponse.json({ error: "Ingresá entre 3 y 200 caracteres para buscar." }, { status: 400 });
  }

  try {
    const base = process.env.GEOCODER_BASE_URL || "https://photon.komoot.io";
    async function retrieve(bias?: SearchOrigin) {
      const url = new URL(reverse ? "/reverse" : "/api/", base);
      url.searchParams.set("limit", reverse ? "1" : "20");
      if (reverse) {
        // Reverse lookup determines the person's actual country; do not pre-filter it.
        url.searchParams.set("lat", latitude!);
        url.searchParams.set("lon", longitude!);
      } else {
        url.searchParams.set("q", search!);
        url.searchParams.set("countrycode", countryCode);
        if (bias) {
          url.searchParams.set("lat", String(bias.latitude));
          url.searchParams.set("lon", String(bias.longitude));
          url.searchParams.set("zoom", "12");
          url.searchParams.set("location_bias_scale", "0.1");
        }
      }
      const response = await fetch(url, {
        headers: { Accept: "application/json", "Accept-Language": "es", "User-Agent": "MascoMatch/0.1" },
        signal: AbortSignal.any([request.signal, AbortSignal.timeout(8000)]),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Geocoder unavailable");
      return normalizePlaces(await response.json(), 20);
    }
    // An additional country-wide retrieval keeps distant exact names in the candidate set.
    const responses = await Promise.allSettled(origin && !reverse ? [retrieve(origin), retrieve()] : [retrieve()]);
    const successful = responses.filter(result => result.status === "fulfilled");
    if (!successful.length) throw new Error("Geocoder unavailable");
    const candidates = successful.flatMap(result => result.value);
    const places = reverse ? candidates.slice(0, 1) : rankPlaces(candidates, search!, countryCode, origin);
    return NextResponse.json({ places, ...(!reverse ? { countryCode, nearby: Boolean(origin) } : {}) }, {
      headers: { "Cache-Control": "no-store" },
    });
  } catch {
    return NextResponse.json({ error: "La búsqueda de lugares no está disponible ahora. Intentá de nuevo o usá tu ubicación actual." }, { status: 503 });
  }
}

