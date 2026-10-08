"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

export function NotificationsLink() {
  const [count, setCount] = useState(0);
  useEffect(() => {
    let disposed = false;
    let controller: AbortController | undefined;
    async function load() {
      controller?.abort(); controller = new AbortController();
      const signal = controller.signal;
      try {
        const sessionResponse = await fetch("/api/session", { cache: "no-store", signal });
        const session = await sessionResponse.json();
        if (!session.user) { if (!disposed && !signal.aborted) setCount(0); return; }
        const response = await fetch("/api/notifications?limit=1", { cache: "no-store", signal });
        if (!response.ok) return;
        const data = await response.json();
        if (!disposed && !signal.aborted) setCount(data.unread_count || 0);
      } catch { /* A temporary failure must not interrupt navigation. */ }
    }
    void load();
    const timer = setInterval(load, 20000);
    window.addEventListener("focus", load);
    window.addEventListener("mascomatch:session", load);
    window.addEventListener("mascomatch:notifications", load);
    return () => {
      disposed = true; controller?.abort(); clearInterval(timer);
      window.removeEventListener("focus", load); window.removeEventListener("mascomatch:session", load); window.removeEventListener("mascomatch:notifications", load);
    };
  }, []);
  return <Link href="/notificaciones" aria-label={count ? `Notificaciones, ${count} sin leer` : "Notificaciones"}>Notificaciones {count > 0 && <span className="notification-count">{count > 99 ? "99+" : count}</span>}</Link>;
}
