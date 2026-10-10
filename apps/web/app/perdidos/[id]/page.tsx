import type { Metadata } from "next";
import { DogDetail } from "../dog-detail";

export const metadata: Metadata = { title: "Aviso de animal perdido — MascoMatch" };

export default async function DogNoticePage({ params, searchParams }: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ origen?: string | string[] }>;
}) {
  const [{ id }, { origen }] = await Promise.all([params, searchParams]);
  return <DogDetail id={id} fromMap={origen === "mapa"} fromHomeMap={origen === "inicio"} />;
}
