import { NextRequest, NextResponse } from "next/server";
import { authorization, sameOrigin, serverApi } from "@/lib/server-api";

type Context = { params: Promise<{ path?: string[] }> };
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

async function proxy(request: NextRequest, context: Context) {
  if (request.method !== "GET" && !sameOrigin(request)) return NextResponse.json({ detail: "Solicitud no permitida." }, { status: 403 });
  const path = (await context.params).path || [];
  const valid = (request.method === "GET" && path.length === 0)
    || (request.method === "GET" && path.length === 1 && uuid.test(path[0]))
    || (request.method === "GET" && path.length === 3 && uuid.test(path[0]) && path[1] === "photos" && uuid.test(path[2]))
    || (request.method === "GET" && path.length === 4 && uuid.test(path[0]) && path[1] === "photos" && uuid.test(path[2]) && path[3] === "large")
    || (request.method === "PATCH" && path.length === 2 && uuid.test(path[0]) && path[1] === "read");
  if (!valid) return NextResponse.json({ detail: "Ruta no válida." }, { status: 404 });
  try {
    const query = path.length === 0 ? request.nextUrl.search : "";
    const upstream = await fetch(`${serverApi}/notifications${path.length ? `/${path.join("/")}` : ""}${query}`, { method: request.method, headers: authorization(request), cache: "no-store", signal: AbortSignal.timeout(15000) });
    return new Response(upstream.body, { status: upstream.status, headers: { "Content-Type": upstream.headers.get("content-type") || "application/json", "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" } });
  } catch { return NextResponse.json({ detail: "No pudimos consultar las notificaciones." }, { status: 503 }); }
}
export const GET = proxy;
export const PATCH = proxy;
