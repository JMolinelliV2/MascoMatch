export type SightingResult = { id: string; status: string; owner_notified: boolean };

export function sightingMessage(result: SightingResult, hasPhoto = false): string {
  switch (result.status) {
    case "PENDING": return "Estamos revisando las fotos y comparándolas con el aviso. Si hay características compatibles, se notificará al dueño.";
    case "UNVERIFIED": return result.owner_notified
      ? `Generamos una alerta para el dueño con el lugar que indicaste. ${hasPhoto ? "Las fotos necesitan revisión;" : "Como no hay foto,"} el avistamiento está por confirmar.`
      : "El avistamiento quedó guardado como un reporte por confirmar.";
    case "POSSIBLE_MATCH": return result.owner_notified
      ? "Las características de las fotos son compatibles con el aviso y generamos una alerta para el dueño. La identidad todavía necesita confirmación."
      : "Las características de las fotos son compatibles con el aviso. La identidad todavía necesita confirmación.";
    case "NOT_COMPATIBLE": return "El avistamiento quedó guardado, pero los datos no resultaron compatibles con el aviso. No se generó una alerta de coincidencia.";
    case "INACTIVE": return "El avistamiento quedó guardado, pero el aviso ya no está activo.";
    default: return "El avistamiento quedó guardado. Las fotos no aportaron suficiente información para generar una alerta automática de coincidencia.";
  }
}

export function localDateTime(date = new Date()): string {
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}
