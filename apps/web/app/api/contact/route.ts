import { NextRequest, NextResponse } from "next/server";
import { boundedBody, proxyHeaders, sameOrigin, serverApi } from "@/lib/server-api";

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return NextResponse.json({ detail: "Solicitud no permitida." }, { status: 403 });
  if (request.headers.get("content-type")?.split(";", 1)[0].trim().toLowerCase() !== "application/json") return NextResponse.json({ detail: "Enviá el mensaje desde el formulario de contacto." }, { status: 415 });
  try {
    const body = Buffer.from(await boundedBody(request, 24576));
    const response = await fetch(`${serverApi}/contact`, {
      method: "POST", headers: { ...proxyHeaders(request), "Content-Type": "application/json" }, body,
      cache: "no-store", signal: AbortSignal.timeout(10000),
    });
    const result = NextResponse.json(await response.json(), { status: response.status, headers: { "Cache-Control": "no-store" } });
    const retry = response.headers.get("Retry-After");
    if (retry) result.headers.set("Retry-After", retry);
    return result;
  } catch (cause) {
    return NextResponse.json({ detail: "No pudimos confirmar el envío. Intentá de nuevo; conservamos tu mensaje." },
      { status: cause instanceof Error && cause.message === "BODY_TOO_LARGE" ? 413 : 503, headers: { "Cache-Control": "no-store" } });
  }
}
