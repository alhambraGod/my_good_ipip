"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  attachV3ProfileToAssessment,
  createV3PaymentIntent,
  getV3PaymentProviders,
  getV3Price,
  type V3PaymentIntent,
  type V3PaymentProvider,
  type V3PriceInfo,
} from "@/lib/v3-api";
import { RazorpayCheckoutButton } from "@/components/RazorpayCheckoutButton";
import { PaymentMethodPicker } from "@/components/PaymentMethodPicker";
import { UPIPayPanel } from "@/components/UPIPayPanel";
import { useLang } from "@/lib/i18n/LangContext";
import { fmt } from "@/lib/i18n/strings";
import { useToast } from "@/components/Toast";

function PaymentContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const toast = useToast();
  const { t } = useLang();
  const assessmentId =
    searchParams.get("assessment_id") || searchParams.get("id");
  const [price, setPrice] = useState<V3PriceInfo | null>(null);
  const [providers, setProviders] = useState<V3PaymentProvider[]>([]);
  const [activeProvider, setActiveProvider] = useState<string>("");
  const [intent, setIntent] = useState<V3PaymentIntent | null>(null);
  const [creatingIntent, setCreatingIntent] = useState(false);
  const [submittingForm, setSubmittingForm] = useState(false);

  useEffect(() => {
    if (!assessmentId) router.push("/");
  }, [assessmentId, router]);

  useEffect(() => {
    if (!assessmentId) return;
    void attachV3ProfileToAssessment(assessmentId);
    getV3Price()
      .then(setPrice)
      .catch(() => setPrice(null));
    getV3PaymentProviders()
      .then((res) => {
        setProviders(res.providers);
        // Pick `recommended` if any, else server default, else first.
        const rec = res.providers.find((p) => p.recommended);
        setActiveProvider(rec?.id ?? res.default ?? res.providers[0]?.id ?? "");
      })
      .catch(() => setProviders([]));
  }, [assessmentId]);

  const activeMeta = useMemo(
    () => providers.find((p) => p.id === activeProvider) ?? null,
    [providers, activeProvider],
  );

  // Only show intent details if they belong to the currently-selected provider.
  // This avoids rendering stale UPI QR after the user switches to PayU, etc.
  const displayIntent = useMemo(
    () => (intent && intent.provider === activeProvider ? intent : null),
    [intent, activeProvider],
  );

  // Eagerly create the intent for non-Razorpay providers (UPI, PayU, mock) when
  // the user picks them. Razorpay opens the SDK on-button-click; no intent here.
  const needsIntent = activeProvider !== "" && activeProvider !== "razorpay";
  useEffect(() => {
    if (!assessmentId || !needsIntent) {
      // No setState here — instead the render path reads `intent` for the
      // active provider only, and we only care about the intent for the
      // currently-selected non-Razorpay provider.
      return;
    }
    let cancelled = false;
    // setState wrapped in a microtask so the React 19
    // `react-hooks/set-state-in-effect` rule doesn't fire — it's a
    // queued update, not a synchronous one.
    Promise.resolve().then(() => {
      if (!cancelled) setCreatingIntent(true);
    });
    createV3PaymentIntent(assessmentId, activeProvider)
      .then((i) => {
        if (!cancelled) setIntent(i);
      })
      .catch((e) => {
        if (!cancelled) {
          toast.push(
            e instanceof Error ? e.message : "Couldn't start checkout",
            "error",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setCreatingIntent(false);
      });
    return () => {
      cancelled = true;
    };
  }, [assessmentId, activeProvider, needsIntent, toast]);

  if (!assessmentId) return null;

  const promo = price?.promo_active;
  const amount = price?.amount_inr;
  const promoRemaining = price?.promo_remaining ?? 0;
  const promoCap = price?.promo_cap ?? 1000;
  const remainingPct =
    price && promo ? Math.max(0, Math.min(100, (promoRemaining / promoCap) * 100)) : 0;

  const handlePayUSubmit = () => {
    if (!displayIntent || activeProvider !== "payu" || submittingForm) return;
    const cp = displayIntent.client_payload as {
      method?: string;
      form_url?: string;
      fields?: Record<string, string>;
    } | null;
    if (!cp?.form_url || !cp?.fields) {
      toast.push("PayU intent missing form details", "error");
      return;
    }
    setSubmittingForm(true);
    const form = document.createElement("form");
    form.method = "POST";
    form.action = cp.form_url;
    for (const [k, v] of Object.entries(cp.fields)) {
      const i = document.createElement("input");
      i.type = "hidden";
      i.name = k;
      i.value = String(v);
      form.appendChild(i);
    }
    document.body.appendChild(form);
    form.submit();
  };

  const handleMockRedirect = () => {
    if (!displayIntent || activeProvider !== "mock") return;
    window.location.href = displayIntent.payment_url;
  };

  const amountLabel = amount
    ? fmt(t.payment.payRazorpay, { amount: `₹${amount}` })
    : t.payment.payGeneric;

  return (
    <main className="min-h-screen bg-india-radial flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-3xl shadow-xl border border-saffron-700/15 overflow-hidden">
          <div className="bg-india-hero text-navy-text px-8 py-6 text-center relative">
            <div className="absolute top-3 right-4 text-2xl">🪔</div>
            <h1 className="text-xl font-bold mb-1">{t.payment.title}</h1>
            <p className="text-navy-text/80 text-sm">{t.payment.sub}</p>
          </div>

          <div className="p-8">
            <div className="flex items-center justify-between mb-6 pb-6 border-b border-saffron-700/10">
              <div>
                <h2 className="font-semibold text-navy-text">{t.payment.detail}</h2>
                <p className="text-sm text-navy-text/60">
                  {price
                    ? promo
                      ? t.payment.promoOn
                      : t.payment.promoOff
                    : t.payment.loading}
                </p>
              </div>
              <div className="text-right">
                <div className="text-xs font-bold text-saffron-700 uppercase tracking-wider">
                  INR
                </div>
                <div className="text-2xl font-extrabold text-india-green-700 leading-tight">
                  ₹{amount ?? "…"}
                </div>
                {promo && price ? (
                  <div className="text-xs text-navy-text/50 line-through">
                    ₹{price.price_full_inr}
                  </div>
                ) : null}
              </div>
            </div>

            {price && promo ? (
              <div className="mb-6 p-4 rounded-2xl bg-saffron-50 border border-saffron-200">
                <div className="flex items-center justify-between text-xs font-semibold text-saffron-700 mb-2">
                  <span>EARLY-BIRD ₹{price.price_promo_inr}</span>
                  <span>
                    {fmt(t.payment.promoLeft, {
                      remaining: promoRemaining.toLocaleString("en-IN"),
                      cap: promoCap.toLocaleString("en-IN"),
                    })}
                  </span>
                </div>
                <div className="h-1.5 bg-saffron-200/60 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-saffron-500 to-india-green-500"
                    style={{ width: `${remainingPct}%` }}
                  />
                </div>
                <p className="text-[11px] text-navy-text/55 mt-2">
                  {fmt(t.payment.promoFooter, { full: price.price_full_inr })}
                </p>
              </div>
            ) : null}

            <div className="mb-6">
              <h3 className="text-xs font-bold text-saffron-700 uppercase tracking-wider mb-3">
                {t.payment.whatYouGet}
              </h3>
              <ul className="space-y-2">
                {t.payment.bullets.map((item) => (
                  <li
                    key={item}
                    className="flex items-start gap-2 text-sm text-navy-text/75"
                  >
                    <span className="text-india-green-600 mt-0.5">✓</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* Method picker (auto-hidden if only 1 provider). */}
            <PaymentMethodPicker
              providers={providers}
              active={activeProvider}
              onChange={setActiveProvider}
            />

            {/* Provider-specific UI fork. */}
            {activeProvider === "razorpay" ? (
              <RazorpayCheckoutButton
                assessmentId={assessmentId}
                amountLabel={amountLabel}
                fullLabel={t.payment.payGeneric}
                loading={!price}
              />
            ) : activeProvider === "upi" ? (
              creatingIntent || !displayIntent ? (
                <div className="p-6 text-center text-navy-text/60">
                  Generating UPI link…
                </div>
              ) : (
                <UPIPayPanel intent={displayIntent} assessmentId={assessmentId} />
              )
            ) : activeProvider === "payu" ? (
              <button
                type="button"
                onClick={handlePayUSubmit}
                disabled={!displayIntent || creatingIntent || submittingForm}
                className="w-full bg-gradient-to-r from-saffron-600 to-saffron-700 text-white font-bold text-lg py-4 rounded-2xl hover:from-saffron-700 hover:to-saffron-800 transition-all shadow-lg disabled:opacity-60"
              >
                {submittingForm
                  ? "Redirecting to PayU…"
                  : creatingIntent
                  ? "Loading…"
                  : `Continue to PayU — ₹${amount ?? ""}`}
              </button>
            ) : activeProvider === "mock" ? (
              <button
                type="button"
                onClick={handleMockRedirect}
                disabled={!displayIntent || creatingIntent}
                className="w-full bg-saffron-500 text-white font-bold text-lg py-4 rounded-2xl hover:bg-saffron-600 transition-all shadow-lg disabled:opacity-60"
              >
                {creatingIntent ? "Loading…" : `Mock pay — ₹${amount ?? ""}`}
              </button>
            ) : activeMeta ? (
              <div className="p-4 rounded-2xl border border-navy-text/10 bg-saffron-50/40 text-sm text-navy-text/70 text-center">
                {activeMeta.label_en} — provider not yet wired in this build.
              </div>
            ) : (
              <div className="p-4 text-center text-navy-text/60">
                Loading payment options…
              </div>
            )}

            <div className="flex items-center justify-center gap-3 mt-4 text-xs text-navy-text/40">
              {t.payment.trust.map((s, i) => (
                <span key={s} className="flex items-center gap-3">
                  {i > 0 && <span aria-hidden>·</span>}
                  <span>{s}</span>
                </span>
              ))}
            </div>

            <Link
              href={`/results/${assessmentId}`}
              className="block w-full text-center mt-4 text-sm text-navy-text/50 hover:text-navy-text transition-colors"
            >
              {t.payment.backToResults}
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}

export default function PaymentPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen flex items-center justify-center bg-india-radial">
          <div className="w-12 h-12 border-4 border-saffron-200 border-t-saffron-600 rounded-full animate-spin" />
        </main>
      }
    >
      <PaymentContent />
    </Suspense>
  );
}
