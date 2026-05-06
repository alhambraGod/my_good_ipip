"use client";

import type { V3PaymentProvider } from "@/lib/v3-api";

const ICON: Record<string, string> = {
  razorpay: "💳",
  cashfree: "🏦",
  payu: "🔁",
  upi: "📱",
  mock: "🧪",
  stripe: "🌐",
};

export function PaymentMethodPicker({
  providers,
  active,
  onChange,
}: {
  providers: V3PaymentProvider[];
  active: string;
  onChange: (id: string) => void;
}) {
  if (providers.length <= 1) {
    return null;          // single-provider deployment — hide the picker
  }
  return (
    <div className="mb-6">
      <h3 className="text-xs font-bold text-saffron-700 uppercase tracking-wider mb-3">
        Choose how to pay
      </h3>
      <div className="grid gap-2">
        {providers.map((p) => {
          const isActive = p.id === active;
          return (
            <button
              key={p.id}
              type="button"
              onClick={() => onChange(p.id)}
              className={`text-left flex items-start gap-3 px-4 py-3 rounded-xl border-2 transition-all ${
                isActive
                  ? "border-india-green-500 bg-india-green-50"
                  : "border-saffron-200 bg-white hover:border-india-green-400 hover:bg-india-green-50/40"
              }`}
            >
              <span className="text-xl shrink-0" aria-hidden>
                {ICON[p.id] ?? "💸"}
              </span>
              <span className="flex-1 min-w-0">
                <span className="flex items-center gap-2">
                  <span className="font-semibold text-navy-text text-sm">
                    {p.label_en}
                  </span>
                  {p.recommended && (
                    <span className="text-[10px] font-bold uppercase text-india-green-700 bg-india-green-100 px-1.5 py-0.5 rounded">
                      Recommended
                    </span>
                  )}
                </span>
                <span className="block text-xs text-navy-text/60 leading-snug mt-0.5">
                  {p.description_en}
                </span>
                {p.supports_methods.length > 1 && (
                  <span className="block text-[11px] text-navy-text/45 mt-1">
                    {p.supports_methods.join(" · ")}
                  </span>
                )}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
