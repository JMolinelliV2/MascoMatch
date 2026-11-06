"use client";

import { useSyncExternalStore } from "react";
import { createPortal } from "react-dom";
import { Icon } from "./pictogram";

const subscribe = () => () => {};
const clientSnapshot = () => true;
const serverSnapshot = () => false;

/** Shared visual only: it never delays content or starts a request. */
export function LoadingState({ title = "Cargando", description, compact = false, className = "" }: {
  title?: string; description?: string; compact?: boolean; className?: string;
}) {
  const mounted = useSyncExternalStore(subscribe, clientSnapshot, serverSnapshot);

  if (compact) return <div className={`masco-loading masco-loading--compact ${className}`} role="status" aria-live="polite" aria-atomic="true">
    <span className="masco-loading-spinner" aria-hidden="true" />
    <div><p className="masco-loading-title">{title}</p>{description && <p className="masco-loading-description">{description}</p>}</div>
  </div>;

  const content = <div className={`masco-loading masco-loading--viewport ${className}`} role="status" aria-live="polite" aria-atomic="true">
    <div className="masco-loading-content">
      <div className="masco-loading-brand" aria-hidden="true"><span className="brand-mark"><Icon name="paw" /></span><span>Masco<span className="brand-accent">Match</span></span></div>
      <div className="masco-loading-scene" aria-hidden="true">
        <picture>
          <source media="(prefers-reduced-motion: reduce)" srcSet="/images/loading-dog-still.webp" />
          <img className="masco-loading-dog" src="/images/loading-dog.webp" width={500} height={500} alt="" loading="eager" fetchPriority="high" decoding="async" draggable={false} />
        </picture>
      </div>
      <p className="masco-loading-title">{title}<span className="masco-loading-dots" aria-hidden="true"><i /><i /><i /></span></p>
      {description && <p className="masco-loading-description">{description}</p>}
    </div>
  </div>;

  // Keep the viewport independent of cards, auth columns and other stacking contexts.
  return mounted ? createPortal(content, document.body) : content;
}
