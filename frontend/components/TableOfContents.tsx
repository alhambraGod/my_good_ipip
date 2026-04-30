"use client";

import { useEffect, useRef, useState } from "react";

export type TocItem = { id: string; label: string; emoji?: string };

export function TableOfContents({ items }: { items: TocItem[] }) {
  const [activeId, setActiveId] = useState<string>(items[0]?.id ?? "");
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    if (typeof window === "undefined" || !("IntersectionObserver" in window)) return;
    if (observerRef.current) observerRef.current.disconnect();

    const visible = new Set<string>();
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) visible.add(e.target.id);
          else visible.delete(e.target.id);
        });
        const ordered = items.find((i) => visible.has(i.id));
        if (ordered) setActiveId(ordered.id);
      },
      {
        rootMargin: "-25% 0px -55% 0px",
        threshold: [0, 0.25, 0.5, 0.75, 1],
      },
    );
    items.forEach((i) => {
      const el = document.getElementById(i.id);
      if (el) obs.observe(el);
    });
    observerRef.current = obs;
    return () => obs.disconnect();
  }, [items]);

  const handleClick = (id: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      history.replaceState(null, "", `#${id}`);
    }
  };

  return (
    <>
      <nav
        aria-label="Report sections"
        className="hidden lg:block sticky top-24 self-start text-sm"
      >
        <p className="text-[11px] font-bold uppercase tracking-widest text-saffron-700 mb-3">
          On this page
        </p>
        <ul className="space-y-1">
          {items.map((item) => {
            const active = activeId === item.id;
            return (
              <li key={item.id}>
                <a
                  href={`#${item.id}`}
                  onClick={handleClick(item.id)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all ${
                    active
                      ? "bg-saffron-50 text-saffron-700 font-bold border-l-2 border-saffron-500 pl-[10px]"
                      : "text-navy-text/60 hover:text-navy-text hover:bg-white/70"
                  }`}
                >
                  {item.emoji && <span aria-hidden>{item.emoji}</span>}
                  <span>{item.label}</span>
                </a>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Mobile/tablet: horizontal scroll chips, sticky under the header */}
      <div className="lg:hidden sticky top-[60px] z-20 -mx-4 mb-4 overflow-x-auto">
        <div className="flex gap-2 px-4 py-2 bg-cream/90 backdrop-blur border-y border-saffron-700/10">
          {items.map((item) => {
            const active = activeId === item.id;
            return (
              <a
                key={item.id}
                href={`#${item.id}`}
                onClick={handleClick(item.id)}
                className={`shrink-0 text-xs font-semibold px-3 py-1.5 rounded-full transition-colors ${
                  active
                    ? "bg-saffron-600 text-white"
                    : "bg-white text-navy-text/65 border border-saffron-700/10 hover:text-navy-text"
                }`}
              >
                {item.emoji && <span className="mr-1">{item.emoji}</span>}
                {item.label}
              </a>
            );
          })}
        </div>
      </div>
    </>
  );
}
