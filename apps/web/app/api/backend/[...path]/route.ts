import { NextRequest, NextResponse } from "next/server";
import { authorization, boundedBody, sameOrigin, serverApi } from "@/lib/server-api";
import { admitUpload, releaseUpload } from "@/lib/upload-admission";

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
async function handle(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const create = request.method === "POST" && path.length === 1 && ["pets", "lost-cases", "observations"].includes(path[0]);
  const upload = request.method === "POST" && path.join("/") === "photos/upload";
  const analysis = request.method === "GET" && path.length === 3 && path[0] === "analysis" && ["pet", "lost_case", "observation"].includes(path[1]) && uuid.test(path[2]);
  const retry = request.method === "POST" && path.length === 4 && path[0] === "analysis" && path[1] === "jobs" && uuid.test(path[2]) && path[3] === "retry";
  if ((!create && !upload && !analysis && !retry) || (request.method !== "GET" && !sameOrigin(request))) {
    return NextResponse.json({ detail: "Solicitud no permitida." }, { status: 403 });
  }
  let lease: string | null = null;
  try {
    if (upload) lease = await admitUpload(request);
    const body = request.method === "POST" ? Buffer.from(await boundedBody(request, upload ? 11 * 1024 * 1024 : 16384)) : undefined;
    const upstream = await fetch(`${serverApi}/${path.join("/")}`, {
      method: request.method, headers: { ...authorization(request), ...(body ? { "Content-Type": request.headers.get("content-type") || "application/json" } : {}) },
      body, cache: "no-store", signal: AbortSignal.timeout(30000),
    });
    const data = await upstream.json();
    if (upload && upstream.ok) delete data.signed_url;
    return NextResponse.json(data, { status: upstream.status, headers: { "Cache-Control": "no-store" } });
  } catch (error) {
    const tooLarge = error instanceof Error && error.message === "BODY_TOO_LARGE";
    const busy = error instanceof Error && error.message === "UPLOAD_BUSY";
    return NextResponse.json({ detail: tooLarge ? "La carga es demasiado grande." : busy ? "Estamos recibiendo otras fotos. Intentá en unos segundos." : "No pudimos guardar el reporte." }, { status: tooLarge ? 413 : busy ? 429 : 503 });
  } finally { await releaseUpload(request, lease); }
}
export const GET = handle;
export const POST = handle;
