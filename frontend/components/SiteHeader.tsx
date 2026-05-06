"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLang } from "@/lib/i18n/LangContext";
import { LangToggle } from "@/components/LangToggle";

export function SiteHeader({ minimal = false }: { minimal?: boolean }) {
  const pathname = usePathname();
  const { t } = useLang();
  const NAV: { href: string; label: string }[] = [
    { href: "/archetypes", label: t.nav.archetypes },
    { href: "/test", label: t.nav.takeTest },
  ];
  return (
    <header className="w-full sticky top-0 z-30 backdrop-blur bg-cream/80 border-b border-saffron-700/10">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
        <Link href="/" className="flex items-center gap-2 group">
          <span className="text-xl">🪔</span>
          <span className="font-black text-navy-text tracking-tight group-hover:text-saffron-700 transition-colors">
            MindPrism <span className="text-saffron-700">India</span>
          </span>
        </Link>
        {!minimal && (
          <nav className="hidden sm:flex items-center gap-1 text-sm font-medium">
            {NAV.map((item) => {
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-3 py-1.5 rounded-full transition-colors ${
                    active
                      ? "bg-saffron-200 text-saffron-900 font-semibold"
                      : "text-navy-text/75 hover:text-navy-text hover:bg-white"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        )}
        <div className="flex items-center gap-3">
          <LangToggle className="hidden sm:inline-flex" />
          <Link
            href="/test"
            className="hidden md:inline-flex bg-india-green-500 hover:bg-india-green-600 text-white text-sm font-bold px-4 py-2 rounded-full shadow-md transition-all"
          >
            {t.nav.startFree}
          </Link>
        </div>
      </div>
    </header>
  );
}
