import { NextRequest, NextResponse } from "next/server";
import { authorization, boundedBody, proxyHeaders, sameOrigin, serverApi, SESSION_COOKIE } from "@/lib/server-api";

export async function GET(request: NextRequest) {
  if (!request.cookies.has(SESSION_COOKIE)) return NextResponse.json({ user: null }, { headers: { "Cache-Control": "no-store" } });
  try {
    const upstream = await fetch(`${serverApi}/auth/me`, { headers: authorization(request), cache: "no-store", signal: AbortSignal.timeout(10000) });
    const response = NextResponse.json({ user: upstream.ok ? await upstream.json() : null }, { headers: { "Cache-Control": "no-store" } });
    if (upstream.status === 401) response.cookies.delete(SESSION_COOKIE);
    return response;
  } catch { return NextResponse.json({ detail: "No pudimos consultar tu sesión." }, { status: 503 }); }
}

export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return NextResponse.json({ detail: "Solicitud no permitida." }, { status: 403 });
  try {
    const body = JSON.parse(new TextDecoder().decode(await boundedBody(request, 8192)));
    const { mode, ...credentials } = body;
    if (mode !== "register" && mode !== "login") return NextResponse.json({ detail: "Modo de cuenta no válido." }, { status: 400 });
    const upstream = await fetch(`${serverApi}/auth/${mode}`, {
      method: "POST", headers: { ...proxyHeaders(request), "Content-Type": "application/json" }, body: JSON.stringify(credentials),
      cache: "no-store", signal: AbortSignal.timeout(15000),
    });
    const data = await upstream.json();
    const { access_token, token_type, ...publicData } = data;
    const response = NextResponse.json(publicData, { status: upstream.status, headers: { "Cache-Control": "no-store" } });
    if (upstream.ok && typeof data.access_token === "string") {
      const expires = Number.isInteger(data.expires_in) ? Math.min(86400, Math.max(300, data.expires_in)) : 3600;
      response.cookies.set(SESSION_COOKIE, data.access_token, { httpOnly: true, sameSite: "lax", secure: process.env.NODE_ENV === "production", path: "/", maxAge: expires });
    }
    return response;
  } catch { return NextResponse.json({ detail: "No pudimos iniciar sesión. Intentá de nuevo." }, { status: 503 }); }
}

export async function DELETE(request: NextRequest) {
  if (!sameOrigin(request)) return NextResponse.json({ detail: "Solicitud no permitida." }, { status: 403 });
  if (request.cookies.has(SESSION_COOKIE)) {
    try {
      const upstream = await fetch(`${serverApi}/auth/logout`, { method: "POST", headers: authorization(request), cache: "no-store", signal: AbortSignal.timeout(10000) });
      if (!upstream.ok && upstream.status !== 401) throw new Error("LOGOUT_UNAVAILABLE");
    } catch { return NextResponse.json({ detail: "No pudimos cerrar la sesión. Intentá de nuevo." }, { status: 503 }); }
  }
  const response = NextResponse.json({ ok: true });
  response.cookies.delete(SESSION_COOKIE);
  return response;
}

export async function PATCH(request: NextRequest) {
  if (!sameOrigin(request)) return NextResponse.json({ detail: "Solicitud no permitida." }, { status: 403 });
  try {
    const body = await boundedBody(request, 1024);
    const upstream = await fetch(`${serverApi}/auth/notification-preferences`, { method: "PATCH", headers: { ...authorization(request), "Content-Type": "application/json" }, body: Buffer.from(body), cache: "no-store", signal: AbortSignal.timeout(10000) });
    return NextResponse.json(await upstream.json(), { status: upstream.status, headers: { "Cache-Control": "no-store" } });
  } catch { return NextResponse.json({ detail: "No pudimos guardar la preferencia." }, { status: 503 }); }
}
