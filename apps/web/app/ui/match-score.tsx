export function MatchScore({ score }: { score?: number }) {
  if (score === undefined || !Number.isFinite(score)) return null;
  return <span className={`match-score ${score >= .82 ? "match-score-high" : "match-score-review"}`}>
    <strong>{Math.round(Math.max(0, Math.min(1, score)) * 100)}%</strong>
    <span>{score >= .82 ? "Compatibilidad alta" : "Para revisar"}</span>
  </span>;
}
