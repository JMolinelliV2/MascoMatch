import Link from "next/link";
import { lostDate, speciesLabel } from "@/lib/lost-dogs";
import type { LostDogNotice } from "@/lib/lost-dogs";
import type { LostMapPoint } from "@/lib/lost-map-marker";
import { DogPhoto } from "../perdidos/dog-photo";
import { Icon } from "../ui/pictogram";

export type MapReportPoint = LostMapPoint & {
  layer: "lost" | "sighting" | "found";
  species: string; area: string | null; when: string; url: string | null;
};
const reportLabels = { lost: "Animal perdido", sighting: "Avistamiento", found: "Animal encontrado" };
const dateLabels = { lost: "Perdido desde el", sighting: "Visto el", found: "Encontrado el" };

export function MapReportCard({ point, href }: { point: MapReportPoint; href?: string }) {
  const photo = point.layer === "lost"
    ? <DogPhoto dog={{ id: point.id, name: point.title, photo_url: point.photo_url || null }} />
    : <div className="dog-photo"><div className="dog-photo-placeholder"><Icon name={point.layer === "found" ? "heart" : "eye"} /><span>Miniatura no disponible</span></div></div>;
  return <article className={`map-report-card map-report-${point.layer}`}>
    {href ? <Link className="map-report-photo" href={href} aria-label={`Ver el aviso de ${point.title}`}>{photo}</Link> : <div className="map-report-photo">{photo}</div>}
    <div className="map-report-content">
      <span className="map-report-type">{reportLabels[point.layer]}</span>
      <h3>{href ? <Link href={href}>{point.title}</Link> : point.title}</h3>
      <p className="map-report-species">{speciesLabel(point.species as LostDogNotice["species"]) || "Animal"}</p>
      <p className="map-report-area"><Icon name="pin" />{point.area || "Zona aproximada"}</p>
      <p className="map-report-date"><Icon name="calendar" /><span>{dateLabels[point.layer]} <time dateTime={point.when}>{lostDate(point.when)}</time></span></p>
      {href && <Link href={href} className="text-button map-report-action">Ver aviso <Icon name="arrow" /></Link>}
    </div>
  </article>;
}
