"use client";
import { useEffect, useState } from "react";
import { publicObservationsEndpoint } from "@/lib/public-observations";
import { Icon } from "./pictogram";

export function ObservationPhoto({ id, hasPhoto, found = false, onLoad }: { id: string; hasPhoto: boolean; found?: boolean; onLoad?: () => void }) {
  const [failed, setFailed] = useState(false);
  useEffect(() => { setFailed(false); }, [id, hasPhoto]);
  return <div className="dog-photo">
    {hasPhoto && !failed ? <img src={`${publicObservationsEndpoint}/${encodeURIComponent(id)}/photo`} alt={found ? "Foto del animal encontrado" : "Foto del animal avistado"} loading="lazy" onLoad={onLoad} onError={() => setFailed(true)} />
      : <div className="dog-photo-placeholder"><Icon name={found ? "heart" : "eye"} /><span>{failed ? "Foto no disponible" : "Sin foto"}</span></div>}
  </div>;
}
