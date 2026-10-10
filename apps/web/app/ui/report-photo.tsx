"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Icon } from "./pictogram";
import type { IconName } from "./pictogram";
import { PhotoViewer } from "./photo-viewer";

export function ReportPhoto({ src, alt, galleryEndpoint, placeholderIcon, href, onOpenReport, onLoad }: {
  src: string | null; alt: string; galleryEndpoint: string; placeholderIcon: IconName;
  href?: string; onOpenReport?: () => void; onLoad?: () => void;
}) {
  const [failed, setFailed] = useState(false);
  const [expanded, setExpanded] = useState(false);
  useEffect(() => { setFailed(false); setExpanded(false); }, [src]);
  const image = src && !failed ? <img src={src} alt={alt} loading="lazy" onLoad={onLoad} onError={() => setFailed(true)} />
    : <div className="dog-photo-placeholder"><Icon name={placeholderIcon} /><span>{failed ? "Foto no disponible" : "Sin foto"}</span></div>;
  const enlarge = <span className="photo-enlarge-mark" aria-hidden="true"><Icon name="expand" /></span>;
  return <div className="dog-photo report-photo">
    {href ? <Link href={href} className="report-photo-primary" aria-label={`Ver aviso: ${alt}`}>{image}</Link>
      : onOpenReport ? <button type="button" className="report-photo-primary" aria-label={`Ver detalles: ${alt}`} onClick={onOpenReport}>{image}</button>
        : src && !failed ? <button type="button" className="report-photo-primary" aria-label={`Ampliar ${alt}`} aria-haspopup="dialog" onClick={() => setExpanded(true)}>{image}{enlarge}</button> : image}
    {src && !failed && (href || onOpenReport) && <button type="button" className="report-photo-zoom" aria-label={`Ampliar ${alt}`} aria-haspopup="dialog" onClick={() => setExpanded(true)}><Icon name="expand" /></button>}
    {expanded && <PhotoViewer galleryEndpoint={galleryEndpoint} title={alt} onClose={() => setExpanded(false)} />}
  </div>;
}
