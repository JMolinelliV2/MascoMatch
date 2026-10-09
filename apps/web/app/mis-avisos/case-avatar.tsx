"use client";
import { useEffect, useState } from "react";
import { lostDogsEndpoint } from "@/lib/lost-dogs";
import type { LostDogNotice } from "@/lib/lost-dogs";
import { DogPhoto } from "../perdidos/dog-photo";
import { Icon } from "../ui/pictogram";

export function CaseAvatar({ id, active, refresh }: { id: string; active: boolean; refresh: number }) {
  const [notice, setNotice] = useState<LostDogNotice | null>(null);
  useEffect(() => {
    setNotice(null);
    if (!active) return;
    const controller = new AbortController();
    void fetch(`${lostDogsEndpoint}/${id}`, { cache: "no-store", signal: controller.signal }).then(async response => {
      if (!response.ok) return;
      const result: LostDogNotice = await response.json();
      if (!controller.signal.aborted) setNotice(result);
    }).catch(() => { /* The owner controls remain usable if the public photo is unavailable. */ });
    return () => controller.abort();
  }, [id, active, refresh]);
  return <div className="case-avatar">{notice ? <DogPhoto key={`${id}-${refresh}`} dog={notice} /> : <div className="case-avatar-empty" aria-hidden="true"><Icon name="paw" /></div>}</div>;
}
