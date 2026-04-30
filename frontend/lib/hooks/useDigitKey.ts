"use client";

import { useEffect } from "react";

/** Calls handler(n) when the user presses 1..max as a top-level keystroke. */
export function useDigitKey(max: number, handler: (n: number) => void, enabled = true): void {
  useEffect(() => {
    if (!enabled) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.repeat) return;
      const target = e.target as HTMLElement | null;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable)) {
        return;
      }
      const n = Number.parseInt(e.key, 10);
      if (!Number.isFinite(n) || n < 1 || n > max) return;
      e.preventDefault();
      handler(n);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [max, handler, enabled]);
}
