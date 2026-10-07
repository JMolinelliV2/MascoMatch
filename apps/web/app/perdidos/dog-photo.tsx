"use client";

import { useState } from "react";
import { lostDogsEndpoint } from "@/lib/lost-dogs";
import type { LostDogNotice } from "@/lib/lost-dogs";

export function DogPhoto({ dog }: { dog: LostDogNotice }) {
  const [failed, setFailed] = useState(false);
  return <div className="dog-photo">
    {dog.photo_url && !failed
      ? <img src={`${lostDogsEndpoint}/${dog.id}/photo`} alt={`Foto de ${dog.name}`} loading="lazy" onError={() => setFailed(true)} />
      : <div className="dog-photo-placeholder"><svg viewBox="0 0 64 64" width="56" height="56" aria-hidden="true" fill="currentColor"><ellipse cx="18" cy="19" rx="7" ry="9" /><ellipse cx="34" cy="13" rx="7" ry="9" /><ellipse cx="49" cy="22" rx="7" ry="9" /><path d="M17 45c0-10 8-19 17-19s18 9 18 19c0 7-5 10-10 8-5-2-10-2-15 0-6 2-10-1-10-8Z" /></svg><span>{failed ? "Foto no disponible" : "Sin foto"}</span></div>}
  </div>;
}
