"use client";
import { useEffect, useState } from "react";

export function useSessionRefresh() {
  const [version, setVersion] = useState(0);
  useEffect(() => {
    const refresh = () => setVersion(value => value + 1);
    window.addEventListener("mascomatch:session", refresh);
    window.addEventListener("focus", refresh);
    return () => { window.removeEventListener("mascomatch:session", refresh); window.removeEventListener("focus", refresh); };
  }, []);
  return version;
}
