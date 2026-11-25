/** Keep useful user-facing messages, replacing browser/network exception text. */
export function requestError(cause: unknown, fallback: string): string {
  return cause instanceof Error && !["TypeError", "TimeoutError", "AbortError", "SyntaxError"].includes(cause.name) && cause.message
    ? cause.message : fallback;
}
