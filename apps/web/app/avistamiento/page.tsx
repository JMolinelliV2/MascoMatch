import { ReportForm } from "../report-form";
import { LinkedSightingForm } from "../linked-sighting-form";

export default async function SightingPage({ searchParams }: { searchParams: Promise<{ aviso?: string | string[] }> }) {
  const { aviso } = await searchParams;
  return typeof aviso === "string" ? <LinkedSightingForm caseId={aviso} /> : <ReportForm kind="sighting" />;
}

