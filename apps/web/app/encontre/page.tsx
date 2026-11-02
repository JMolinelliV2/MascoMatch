import { ReportForm } from "../report-form";
import { LinkedSightingForm } from "../linked-sighting-form";

export default async function FoundAnimalPage({ searchParams }: { searchParams: Promise<{ aviso?: string | string[] }> }) {
  const { aviso } = await searchParams;
  return typeof aviso === "string" ? <LinkedSightingForm caseId={aviso} kind="found" /> : <ReportForm kind="found" />;
}

