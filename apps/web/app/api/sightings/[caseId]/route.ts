import { NextRequest, NextResponse } from "next/server";
import { authorization, boundedBody, sameOrigin, serverApi, SESSION_COOKIE } from "@/lib/server-api";

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export async function POST(request: NextRequest, { params }: { params: Promise<{ caseId: string }> }) {
  if (!sameOrigin(request)) return NextResponse.json({ detail: "Solicitud no permitida." }, { status: 403 });
  const { caseId } = await params;
  if (!uuid.test(caseId)) return NextResponse.json({ detail: "Aviso no válido." }, { status: 400 });
  try {
    const body = await boundedBody(request, 42 * 1024 * 1024);
    const auth = authorization(request);
    const send = (headers: Record<string, string>) => fetch(`${serverApi}/public/lost-animals/${caseId}/sightings`, {
      method: "POST", headers: { ...headers, "Content-Type": request.headers.get("content-type") || "multipart/form-data" },
      body: Buffer.from(body), cache: "no-store", signal: AbortSignal.timeout(60000),
    });
    let upstream = await send(auth);
    const expired = upstream.status === 401 && Boolean(auth.Authorization);
    if (expired) { await upstream.body?.cancel(); upstream = await send({}); }
    const response = NextResponse.json(await upstream.json(), { status: upstream.status, headers: { "Cache-Control": "no-store" } });
    if (expired) response.cookies.delete(SESSION_COOKIE);
    return response;
  } catch (error) {
    const oversized = error instanceof Error && error.message === "BODY_TOO_LARGE";
    return NextResponse.json({ detail: oversized ? "Las fotos exceden el tamaño permitido." : "No pudimos enviar el avistamiento. Intentá de nuevo." }, { status: oversized ? 413 : 503 });
  }
}

export async function GET(request: NextRequest, { params }: { params: Promise<{ caseId: string }> }) {
  const { caseId } = await params;
  const id = request.nextUrl.searchParams.get("id") || "";
  if (!uuid.test(caseId) || !uuid.test(id)) return NextResponse.json({ detail: "Avistamiento no válido." }, { status: 400 });
  try {
    const upstream = await fetch(`${serverApi}/public/lost-animals/${caseId}/sightings/${id}/status`, { cache: "no-store", signal: AbortSignal.timeout(10000) });
    return NextResponse.json(await upstream.json(), { status: upstream.status, headers: { "Cache-Control": "no-store" } });
  } catch { return NextResponse.json({ detail: "No pudimos consultar el avistamiento." }, { status: 503 }); }
}
