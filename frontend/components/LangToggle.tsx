"use client";

import { useLang } from "@/lib/i18n/LangContext";

export function LangToggle({ className = "" }: { className?: string }) {
  const { lang, setLang, t } = useLang();
  return (
    <div
      role="group"
      aria-label={t.common.switchLang}
      className={`inline-flex bg-white/70 backdrop-blur border border-saffron-700/15 rounded-full p-0.5 text-xs font-bold ${className}`}
    >
      <button
        type="button"
        onClick={() => setLang("en")}
        aria-pressed={lang === "en"}
        className={`px-3 py-1 rounded-full transition-colors ${
          lang === "en"
            ? "bg-saffron-500 text-white"
            : "text-navy-text/65 hover:text-navy-text"
        }`}
      >
        EN
      </button>
      <button
        type="button"
        onClick={() => setLang("hi")}
        aria-pressed={lang === "hi"}
        className={`px-3 py-1 rounded-full transition-colors ${
          lang === "hi"
            ? "bg-india-green-600 text-white"
            : "text-navy-text/65 hover:text-navy-text"
        }`}
      >
        हि
      </button>
    </div>
  );
}
