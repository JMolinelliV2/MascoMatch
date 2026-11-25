"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import { observationEditHref } from "@/lib/owned-observations";
import { usePublicationOwnership } from "../use-publication-ownership";
import { Icon } from "./pictogram";

export function PublicationEditLink({ id, kind, found = false, compact = false, onLayout, owned }: {
  id: string; kind: "lost_case" | "observation"; found?: boolean; compact?: boolean; onLayout?: () => void; owned?: boolean;
}) {
  const ownership = usePublicationOwnership(id, kind, owned === undefined);
  const layout = useRef(onLayout);
  layout.current = onLayout;
  const allowed = owned ?? ownership.allowed;
  useEffect(() => { if (allowed) layout.current?.(); }, [allowed]);

  if (!allowed) return null;
  const href = kind === "lost_case" ? `/mis-avisos?editar=${encodeURIComponent(id)}#editar-${encodeURIComponent(id)}` : observationEditHref(id);
  return <Link href={href} className={compact ? "text-button observation-edit-link" : "button button-secondary publication-edit-button"}>
    <Icon name="edit" />{kind === "lost_case" ? "Editar mi aviso" : found ? "Editar mi reporte" : "Editar mi avistamiento"}
  </Link>;
}
