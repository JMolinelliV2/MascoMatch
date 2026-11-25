const ownerRecoveryPath = /^\/encontre\?aviso=[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function ownerRecoveryReturnPath(value: unknown): string | null {
  return typeof value === "string" && ownerRecoveryPath.exec(value)?.[0] === value ? value : null;
}

export function ownerRecoveryLoginHref(caseId: string): string {
  return `/login?next=${encodeURIComponent(`/encontre?aviso=${encodeURIComponent(caseId)}`)}`;
}

export function loginDestination(returnTo: unknown, emailVerified: boolean | undefined): string {
  // Closing one's own search is allowed while email confirmation is pending.
  // Only this known internal route can override the usual login destination.
  return ownerRecoveryReturnPath(returnTo) ?? (emailVerified ? "/mis-avisos" : "/confirmar-correo");
}
