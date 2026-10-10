import { NextRequest, NextResponse } from "next/server";
import { authorization, boundedBody, proxyHeaders, sameOrigin, serverApi } from "@/lib/server-api";

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
async function handle(request: NextRequest, context: { params: Promise<{ path?: string[] }> }) {
  const { path = [] } = await context.params;
  const publicRead = request.method === "GET" && path.length === 0;
  const ownReview = path.length === 2 && path[0] === "lost-cases" && uuid.test(path[1]) && ["GET", "POST", "DELETE"].includes(request.method);
  if ((!publicRead && !ownReview) || (request.method !== "GET" && !sameOrigin(request))) {
    return NextResponse.json({ detail: "Solicitud no permitida." }, { status: 403 });
  }
  try {
    const body = request.method === "POST" ? Buffer.from(await boundedBody(request, 8192)) : undefined;
    const upstream = await fetch(`${serverApi}/${publicRead ? "public/reviews?limit=6" : `reviews/${path.join("/")}`}`, {
      method: request.method, headers: { ...(publicRead ? proxyHeaders(request) : authorization(request)), ...(body ? { "Content-Type": "application/json" } : {}) },
      body, cache: "no-store", signal: AbortSignal.timeout(15000),
    });
    if (upstream.status === 204) return new Response(null, { status: 204, headers: { "Cache-Control": "no-store" } });
    return NextResponse.json(await upstream.json(), { status: upstream.status, headers: { "Cache-Control": "no-store" } });
  } catch (cause) {
    const tooLarge = cause instanceof Error && cause.message === "BODY_TOO_LARGE";
    return NextResponse.json({ detail: tooLarge ? "La reseña es demasiado larga." : "No pudimos consultar o guardar la reseña. Intentá de nuevo." }, { status: tooLarge ? 413 : 503 });
  }
}
export const GET = handle;
export const POST = handle;
export const DELETE = handle;
