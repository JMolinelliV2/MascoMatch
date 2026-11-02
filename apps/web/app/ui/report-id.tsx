"use client";

import { Icon } from "./pictogram";
import { useState } from "react";

export function ReportId({ id, publicId, label = "ID del aviso", copyable = false, compact = !copyable }: {
  id?: string; publicId?: string; label?: string; copyable?: boolean; compact?: boolean;
}) {
  const [message, setMessage] = useState("");
  const value = publicId || id;
  if (!value) return null;

  async function copy() {
    try {
      await navigator.clipboard.writeText(value!);
      setMessage("ID copiado.");
    } catch {
      setMessage("No pudimos copiarlo. Seleccioná el ID para copiarlo manualmente.");
    }
  }

  if (compact) return <span className="report-reference-inline" title={`${label}: ${value}`}><span className="sr-only">{label}: </span>{value}{copyable && <button type="button" className="report-id-copy-icon" aria-label={`Copiar ${label.toLowerCase()} ${value}`} onClick={() => void copy()}><Icon name="copy" /></button>}{message && <span className="sr-only" role="status">{message}</span>}</span>;

  return <div className="report-reference">
    <span className="report-id"><span>{label}:</span> <strong>{value}</strong></span>
    {copyable && <button type="button" className="text-button report-id-copy" aria-label={`Copiar ${label.toLowerCase()} ${value}`} onClick={() => void copy()}>Copiar ID</button>}
    {copyable && <span role="status" className="report-id-message">{message}</span>}
  </div>;
}
