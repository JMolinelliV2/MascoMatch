"use client";

import { useState } from "react";
import { lostDogsEndpoint } from "@/lib/lost-dogs";
import type { LostDogNotice } from "@/lib/lost-dogs";
import { Icon } from "../ui/pictogram";

export function DogPhoto({ dog }: { dog: Pick<LostDogNotice, "id" | "name" | "photo_url"> }) {
  const [failed, setFailed] = useState(false);
  return <div className="dog-photo">
    {dog.photo_url && !failed
      ? <img src={`${lostDogsEndpoint}/${dog.id}/photo`} alt={`Foto de ${dog.name}`} loading="lazy" onError={() => setFailed(true)} />
      : <div className="dog-photo-placeholder"><Icon name="paw" /><span>{failed ? "Foto no disponible" : "Sin foto"}</span></div>}
  </div>;
}
