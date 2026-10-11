"use client";

import { useState } from "react";

export function ReportId({ id, publicId, label = "ID del aviso", copyable = false }: {
  id?: string; publicId?: string; label?: string; copyable?: boolean;
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

  return <div className="report-reference">
    <span className="report-id"><span>{label}:</span> <strong>{value}</strong></span>
    {copyable && <button type="button" className="text-button report-id-copy" aria-label={`Copiar ${label.toLowerCase()} ${value}`} onClick={() => void copy()}>Copiar ID</button>}
    {copyable && <span role="status" className="report-id-message">{message}</span>}
  </div>;
}
