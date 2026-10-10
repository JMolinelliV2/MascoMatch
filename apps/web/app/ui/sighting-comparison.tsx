const comparisons: Record<string, { label: string; tone: string }> = {
  PENDING: { label: "Comparación en curso", tone: "info" },
  UNVERIFIED: { label: "Identidad por confirmar", tone: "info" },
  NEEDS_REVIEW: { label: "Necesita revisión manual", tone: "info" },
  NOT_COMPATIBLE: { label: "Comparación: no compatible", tone: "warning" },
  POSSIBLE_MATCH: { label: "Posible coincidencia", tone: "positive" },
  INACTIVE: { label: "Aviso inactivo", tone: "info" },
};

export function SightingComparison({ status, reviewStatus }: { status?: string | null; reviewStatus?: string | null }) {
  const comparison = reviewStatus === "FALSE_MATCH" ? { label: "Descartado por vos", tone: "info" }
    : reviewStatus === "RESOLVED" ? { label: "Avistamiento confirmado · búsqueda activa", tone: "positive" }
      : reviewStatus === "CONFIRMED_RELEVANT" ? { label: "Marcado como posible por vos", tone: "info" }
        : comparisons[status || ""] || comparisons.UNVERIFIED;
  return <span className={`sighting-comparison sighting-comparison-${comparison.tone}`}>{comparison.label}</span>;
}
