"use client";

import { useId } from "react";
import type { ReactNode } from "react";
import { Icon } from "./pictogram";

/** Display only: retries remain explicit and preserve each screen's filters/data. */
export function ErrorState({ title = "No pudimos cargar esta información", description, onRetry, retryLabel = "Reintentar", retrying = false, compact = false, headingLevel = 2, children, className = "" }: {
  title?: string; description?: string; onRetry?: () => void; retryLabel?: string; retrying?: boolean;
  compact?: boolean; headingLevel?: 1 | 2 | 3; children?: ReactNode; className?: string;
}) {
  const id = useId();
  const Heading = headingLevel === 1 ? "h1" : headingLevel === 3 ? "h3" : "h2";
  return <section className={`masco-error${compact ? " masco-error--compact" : ""} ${className}`}
    role="alert" aria-labelledby={`${id}-title`} aria-describedby={description ? `${id}-description` : undefined}>
    <img className="masco-error-dog" src="/images/error-dog.webp?v=2" width={1254} height={1254} alt="" aria-hidden="true" decoding="async" draggable={false} />
    <div className="masco-error-copy">
      <Heading id={`${id}-title`} className="masco-error-title">{title}</Heading>
      {description && <p id={`${id}-description`} className="masco-error-description">{description}</p>}
    </div>
    {(onRetry || children) && <div className="masco-error-actions">
      {onRetry && <button type="button" className={`button ${compact ? "button-secondary" : "button-primary"}`} disabled={retrying} onClick={onRetry}><Icon name="refresh" />{retrying ? "Reintentando…" : retryLabel}</button>}
      {children}
    </div>}
  </section>;
}
