"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  attachV3ProfileToAssessment,
  getV3Price,
  type V3PriceInfo,
} from "@/lib/v3-api";
import { RazorpayCheckoutButton } from "@/components/RazorpayCheckoutButton";
import { useLang } from "@/lib/i18n/LangContext";
import { fmt } from "@/lib/i18n/strings";

function PaymentContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { t } = useLang();
  const assessmentId =
    searchParams.get("assessment_id") || searchParams.get("id");
  const [price, setPrice] = useState<V3PriceInfo | null>(null);

  useEffect(() => {
    if (!assessmentId) router.push("/");
  }, [assessmentId, router]);

  useEffect(() => {
    if (!assessmentId) return;
    void attachV3ProfileToAssessment(assessmentId);
    getV3Price()
      .then(setPrice)
      .catch(() => setPrice(null));
  }, [assessmentId]);

  if (!assessmentId) {
    return null;
  }

  const promo = price?.promo_active;
  const amount = price?.amount_inr;
  const promoRemaining = price?.promo_remaining ?? 0;
  const promoCap = price?.promo_cap ?? 1000;
  const remainingPct =
    price && promo ? Math.max(0, Math.min(100, (promoRemaining / promoCap) * 100)) : 0;

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

            <RazorpayCheckoutButton
              assessmentId={assessmentId}
              amountLabel={amountLabel}
              fullLabel={t.payment.payGeneric}
              loading={!price}
            />

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
