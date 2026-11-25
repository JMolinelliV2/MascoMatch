"use client";

import { useEffect, useState } from "react";
import { useSessionRefresh } from "./use-session-refresh";

export function usePublicationOwnership(id: string, kind: "lost_case" | "observation", enabled = true) {
  const version = useSessionRefresh();
  const [retry, setRetry] = useState(0);
  const [result, setResult] = useState<{
    id: string; kind: string; version: number; retry: number; allowed: boolean; signedIn: boolean; status?: string; error?: string;
  } | null>(null);
  const current = result?.id === id && result.kind === kind && result.version === version && result.retry === retry ? result : null;

  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    async function check() {
      let access: { allowed: boolean; signedIn: boolean; status?: string; error?: string } = { allowed: false, signedIn: false };
      try {
        const signal = AbortSignal.any([controller.signal, AbortSignal.timeout(15000)]);
        const session = await fetch("/api/session", { cache: "no-store", signal });
        if (!session.ok) throw new Error("session");
        access.signedIn = Boolean((await session.json()).user);
        if (access.signedIn) {
          const path = kind === "lost_case" ? `lost-cases/${encodeURIComponent(id)}` : `observations/${encodeURIComponent(id)}/edit`;
          const response = await fetch(`/api/account/${path}`, { cache: "no-store", signal });
          if (response.ok) {
            const data = await response.json();
            access = { allowed: true, signedIn: true, status: data.status };
          } else if (response.status !== 404) throw new Error("ownership");
        }
      } catch {
        access = { ...access, allowed: false, error: "No pudimos comprobar las opciones de tu cuenta. Intentá de nuevo." };
      }
      if (!controller.signal.aborted) setResult({ id, kind, version, retry, ...access });
    }
    void check();
    return () => controller.abort();
  }, [id, kind, enabled, version, retry]);

  return {
    allowed: enabled && Boolean(current?.allowed),
    signedIn: enabled && Boolean(current?.signedIn),
    checking: enabled && !current,
    status: enabled ? current?.status : undefined,
    error: enabled ? current?.error : undefined,
    retry: () => setRetry(value => value + 1),
  };
}
