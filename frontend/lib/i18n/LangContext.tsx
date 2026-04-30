"use client";

import {
  createContext,
  useCallback,
  useContext,
  useSyncExternalStore,
  type ReactNode,
} from "react";
import { STRINGS, type Lang, type StringsTree } from "./strings";

const STORAGE_KEY = "careerdna_lang";

let cached: Lang | null = null;
const listeners = new Set<() => void>();

function readLang(): Lang {
  if (typeof window === "undefined") return "en";
  if (cached) return cached;
  try {
    const v = window.localStorage.getItem(STORAGE_KEY);
    if (v === "hi" || v === "en") {
      cached = v;
      return v;
    }
  } catch {
    /* ignore */
  }
  if (typeof navigator !== "undefined" && /^hi\b/i.test(navigator.language)) {
    cached = "hi";
    return "hi";
  }
  cached = "en";
  return "en";
}

function writeLang(next: Lang): void {
  cached = next;
  if (typeof window !== "undefined") {
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      /* ignore */
    }
    document.documentElement.lang = next;
  }
  for (const cb of listeners) cb();
}

function subscribe(cb: () => void): () => void {
  listeners.add(cb);
  if (typeof window !== "undefined") {
    const onStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) {
        cached = null;
        for (const inner of listeners) inner();
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

function getServerSnapshot(): Lang {
  return "en";
}

type Ctx = {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: StringsTree;
};

const LangContext = createContext<Ctx | null>(null);

export function LangProvider({ children }: { children: ReactNode }) {
  const lang = useSyncExternalStore(subscribe, readLang, getServerSnapshot);
  const setLang = useCallback((l: Lang) => writeLang(l), []);
  const t = STRINGS[lang];
  return (
    <LangContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang(): Ctx {
  const ctx = useContext(LangContext);
  if (!ctx) {
    return {
      lang: "en",
      setLang: () => undefined,
      t: STRINGS.en,
    };
  }
  return ctx;
}
