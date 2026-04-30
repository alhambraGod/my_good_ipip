"use client";

import { useCallback, useSyncExternalStore } from "react";

const STORAGE_KEY = "careerdna_test_progress";
const SCHEMA_VERSION = 2;

export type AssessmentProgress = {
  v: number;
  assessmentId: string | null;
  seed: string;
  demographicAnswers: Record<string, string>;
  demographicIdx: number;
  mainAnswers: Record<string, number>;
  mainIdx: number;
  updatedAt: number;
};

const DEFAULT: AssessmentProgress = {
  v: SCHEMA_VERSION,
  assessmentId: null,
  seed: "",
  demographicAnswers: {},
  demographicIdx: 0,
  mainAnswers: {},
  mainIdx: 0,
  updatedAt: 0,
};

let cachedSnapshot: AssessmentProgress = DEFAULT;
let lastReadKey: string | null = null;
const listeners = new Set<() => void>();

function notify(): void {
  for (const l of listeners) l();
}

function readFromStorage(): AssessmentProgress {
  if (typeof window === "undefined") return DEFAULT;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw === lastReadKey) return cachedSnapshot;
    lastReadKey = raw;
    if (!raw) {
      cachedSnapshot = DEFAULT;
      return cachedSnapshot;
    }
    const parsed = JSON.parse(raw) as Partial<AssessmentProgress> & { v?: number };
    if (parsed?.v !== SCHEMA_VERSION) {
      cachedSnapshot = DEFAULT;
      return cachedSnapshot;
    }
    if (Date.now() - (parsed.updatedAt || 0) > 1000 * 60 * 60 * 24 * 7) {
      cachedSnapshot = DEFAULT;
      return cachedSnapshot;
    }
    cachedSnapshot = { ...DEFAULT, ...parsed, v: SCHEMA_VERSION };
    return cachedSnapshot;
  } catch {
    cachedSnapshot = DEFAULT;
    return cachedSnapshot;
  }
}

function writeToStorage(next: AssessmentProgress): void {
  if (typeof window === "undefined") return;
  try {
    const stamped: AssessmentProgress = { ...next, updatedAt: Date.now() };
    const json = JSON.stringify(stamped);
    window.localStorage.setItem(STORAGE_KEY, json);
    cachedSnapshot = stamped;
    lastReadKey = json;
    notify();
  } catch {
    /* quota / private mode */
  }
}

function subscribe(cb: () => void): () => void {
  listeners.add(cb);
  if (typeof window !== "undefined") {
    const onStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) {
        lastReadKey = null;
        readFromStorage();
        notify();
      }
    };
    window.addEventListener("storage", onStorage);
    return () => {
      listeners.delete(cb);
      window.removeEventListener("storage", onStorage);
    };
  }
  return () => listeners.delete(cb);
}

function getSnapshot(): AssessmentProgress {
  return readFromStorage();
}

function getServerSnapshot(): AssessmentProgress {
  return DEFAULT;
}

export function clearAssessmentProgress(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(STORAGE_KEY);
    lastReadKey = null;
    cachedSnapshot = DEFAULT;
    notify();
  } catch {
    /* ignore */
  }
}

/** Reads + persists assessment progress across reloads. */
export function useAssessmentProgress() {
  const progress = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const update = useCallback((patch: Partial<AssessmentProgress>) => {
    const next: AssessmentProgress = { ...readFromStorage(), ...patch };
    writeToStorage(next);
  }, []);

  const reset = useCallback(() => {
    clearAssessmentProgress();
  }, []);

  return { progress, update, reset };
}
