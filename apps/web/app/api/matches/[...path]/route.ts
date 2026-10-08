import { NextRequest, NextResponse } from "next/server";
import { authorization, boundedBody, sameOrigin, serverApi } from "@/lib/server-api";
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
async function handle(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const read = request.method === "GET" && path.length === 2 && ["observations", "lost-cases"].includes(path[0]) && uuid.test(path[1]);
  const write = request.method === "PATCH" && path.length === 2 && uuid.test(path[0]) && path[1] === "feedback";
  if ((!read && !write) || (write && !sameOrigin(request))) return NextResponse.json({ detail: "Solicitud no permitida." }, { status: 403 });
  try {
    const body = write ? Buffer.from(await boundedBody(request, 1024)) : undefined;
    const upstream = await fetch(`${serverApi}/matches/${path.join("/")}`, { method: request.method, headers: { ...authorization(request), ...(write ? { "Content-Type": "application/json" } : {}) }, body, cache: "no-store", signal: AbortSignal.timeout(15000) });
    return NextResponse.json(await upstream.json(), { status: upstream.status, headers: { "Cache-Control": "no-store" } });
  } catch { return NextResponse.json({ detail: "No pudimos consultar las coincidencias." }, { status: 503 }); }
}
export const GET = handle;
export const PATCH = handle;
