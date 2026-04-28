const STORAGE_KEY = "mindiq_oauth_next_path";

/** Call before redirecting to an OAuth provider so the callback can return here. */
export function setOAuthNextPath(path: string): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(STORAGE_KEY, path);
  } catch {
    /* ignore quota / private mode */
  }
}

/** Consume redirect path after OAuth (caller should navigate). */
export function consumeOAuthNextPath(fallback = "/profile"): string {
  if (typeof window === "undefined") return fallback;
  try {
    const p = sessionStorage.getItem(STORAGE_KEY);
    sessionStorage.removeItem(STORAGE_KEY);
    if (p && p.startsWith("/")) return p;
  } catch {
    /* ignore */
  }
  return fallback;
}
