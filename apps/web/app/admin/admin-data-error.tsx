"use client";

import { ErrorState } from "../ui/error-state";
import { useAdminReload } from "./admin-reload";

export function AdminDataError({ description, title = "No pudimos consultar los datos" }: { description: string; title?: string }) {
  const { reload, pending } = useAdminReload();
  return <ErrorState compact title={title} description={description} onRetry={reload} retrying={pending > 0} retryLabel="Recargar datos" />;
}
