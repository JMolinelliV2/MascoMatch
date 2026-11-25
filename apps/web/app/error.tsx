"use client";

import { ErrorState } from "./ui/error-state";

export default function PageError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <main id="main-content" className="page">
    <ErrorState headingLevel={1} title="No pudimos abrir esta página" description="Tuvimos un problema al cargarla. Podés intentar de nuevo en unos instantes." onRetry={reset} />
  </main>;
}
