import { Icon } from "./pictogram";

/** Shared visual only: it never delays content or starts a request. */
export function LoadingState({ title = "Cargando", description, compact = false, className = "" }: {
  title?: string; description?: string; compact?: boolean; className?: string;
}) {
  return <div className={`masco-loading${compact ? " masco-loading--compact" : ""} ${className}`} role="status" aria-live="polite" aria-atomic="true">
    <div className="masco-loading-brand" aria-hidden="true"><span className="brand-mark"><Icon name="paw" /></span><span>Masco<span className="brand-accent">Match</span></span></div>
    <div className="masco-loading-scene" aria-hidden="true">
      <span className="masco-loading-ground" />
      <span className="masco-loading-pup">
        <svg className="masco-loading-dog" viewBox="0 0 140 90" fill="none" focusable="false">
          <g stroke="#183b51" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round">
            <path className="masco-loading-tail" d="M30 42C16 40 12 28 9 21" />
            <path className="masco-loading-leg masco-loading-leg--back-far" d="m41 53-9 13 5 13h8" stroke="#b99a79" strokeWidth="7" />
            <path className="masco-loading-leg masco-loading-leg--front-far" d="m80 52 12 13-7 14h8" stroke="#b99a79" strokeWidth="7" />
            <path d="M28 43c2-14 23-20 42-15l21 9-4 22c-16 11-45 8-55-1-4-4-6-10-4-15Z" fill="#d6b48b" />
            <path className="masco-loading-leg masco-loading-leg--back" d="m39 56 9 10-12 13h-9" stroke="#d6b48b" strokeWidth="8" />
            <path className="masco-loading-leg masco-loading-leg--front" d="m83 54-8 13 12 12h8" stroke="#d6b48b" strokeWidth="8" />
            <path d="m82 39 8-19c3-7 17-7 25 0l5 10 12 7c3 3 1 11-4 12l-17 2-17 9-11-11" fill="#d6b48b" />
            <path d="m89 26-4 16c-2 9 8 13 13 6l4-14" fill="#9c7654" />
            <path d="m109 38 20-2 3 8c-5 8-16 9-24 3" fill="#f8e7cf" stroke="none" />
            <path d="m84 40 12 10-11 10-7-13" fill="#df354a" stroke="none" />
            <path d="m86 52-7 12 14-7" fill="#df354a" stroke="none" />
            <ellipse cx="130" cy="38" rx="5" ry="3.8" fill="#183b51" stroke="none" />
            <circle cx="113" cy="29" r="2.7" fill="#183b51" stroke="none" />
            <circle cx="113.7" cy="28.2" r=".8" fill="white" stroke="none" />
            <path d="M120 46c3 1 5 1 7-1" strokeWidth="2" />
          </g>
        </svg>
      </span>
    </div>
    <p className="masco-loading-title">{title}<span className="masco-loading-dots" aria-hidden="true"><i /><i /><i /></span></p>
    {description && <p className="masco-loading-description">{description}</p>}
  </div>;
}
