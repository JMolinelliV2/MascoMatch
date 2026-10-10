"use client";

import { lostDogsEndpoint } from "@/lib/lost-dogs";
import type { LostDogNotice } from "@/lib/lost-dogs";
import { ReportPhoto } from "../ui/report-photo";

export function DogPhoto({ dog, href }: { dog: Pick<LostDogNotice, "id" | "name" | "photo_url">; href?: string }) {
  const endpoint = `${lostDogsEndpoint}/${encodeURIComponent(dog.id)}`;
  return <ReportPhoto src={dog.photo_url ? `${endpoint}/photo` : null} alt={`Foto de ${dog.name}`} galleryEndpoint={`${endpoint}/photos`} placeholderIcon="paw" href={href} />;
}
