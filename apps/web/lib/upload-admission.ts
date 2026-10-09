import type { NextRequest } from "next/server";
import { authorization, proxyHeaders, serverApi } from "./server-api";
const internalApi = serverApi.replace(/\/api\/v1$/, "");

export async function admitUpload(request: NextRequest, anonymousFallback = false): Promise<string | null> {
  const send = (headers: Record<string, string>) => fetch(`${internalApi}/internal/uploads/admit`, {
    method:"POST", headers, cache:"no-store", signal:AbortSignal.timeout(5000),
  });
  let response = await send(authorization(request));
  if (response.status === 401 && anonymousFallback) {
    await response.body?.cancel();
    response = await send(proxyHeaders(request));
  }
  if (!response.ok) throw new Error(response.status === 429 ? "UPLOAD_BUSY" : "UPLOAD_UNAVAILABLE");
  return (await response.json()).lease;
}

export async function releaseUpload(request: NextRequest, lease: string | null) {
  if (!lease) return;
  try {
    await fetch(`${internalApi}/internal/uploads/release`, {method:"POST", headers:{...proxyHeaders(request),"Content-Type":"application/json"},
      body:JSON.stringify({lease}), cache:"no-store", signal:AbortSignal.timeout(3000)});
  } catch { /* The short lease expires if the API or web process stopped. */ }
}
