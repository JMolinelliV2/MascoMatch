import { CardPhotoCarousel } from "./card-photo-carousel";
import Link from "next/link";
import { dogTraits, lostDate, speciesLabel } from "@/lib/lost-dogs";
import type { LostDogNotice } from "@/lib/lost-dogs";
import { DogPhoto } from "../perdidos/dog-photo";
import { Icon } from "./pictogram";
import { ReportId } from "./report-id";
import { PublicationAuthor } from "./publication-author";

export function PetCard({ animal, compact = false }: { animal: LostDogNotice; compact?: boolean }) {
  return <article className={`lost-dog-card ${compact ? "pet-card-compact" : ""}`}>
    <div className="dog-photo-link">{compact ? <DogPhoto dog={animal} href={`/perdidos/${animal.id}`} /> : <CardPhotoCarousel animal={animal} />}</div>
    <div className="lost-dog-content">
      <div className="report-card-meta"><span className="lost-status">Sigue perdido</span><ReportId id={animal.id} publicId={animal.public_id} /></div>
      <h3><Link href={`/perdidos/${animal.id}`}>{animal.name}</Link></h3>
      <p className="dog-traits">{[speciesLabel(animal.species), ...dogTraits(animal)].join(" · ")}</p>
      <p className="dog-area"><Icon name="pin" />{animal.public_location || "Zona no indicada"}</p>
      <p className="dog-date"><Icon name="calendar" /><span>Perdido desde el <time dateTime={animal.lost_at}>{lostDate(animal.lost_at)}</time></span></p>
      <PublicationAuthor name={animal.publisher_name} />
      <Link href={`/perdidos/${animal.id}`} className="text-button">Ver aviso <Icon name="arrow" /></Link>
    </div>
  </article>;
}
