"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { createV3PaymentIntent } from "@/lib/v3-api";

function PaymentContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const assessmentId =
    searchParams.get("assessment_id") || searchParams.get("id");
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!assessmentId) router.push("/");
  }, [assessmentId, router]);

  const handlePay = async () => {
    if (!assessmentId || processing) return;
    setProcessing(true);
    setError("");

    try {
      const intent = await createV3PaymentIntent(assessmentId);
      if (intent.payment_url) {
        window.location.href = intent.payment_url;
        return;
      }
      setError("No payment URL returned. Try again.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Payment failed. Please try again.");
    } finally {
      setProcessing(false);
    }
  };

  if (!assessmentId) {
    return null;
  }

  return (
    <main className="min-h-screen bg-india-radial flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-3xl shadow-xl border border-saffron-700/15 overflow-hidden">
          <div className="bg-india-hero text-navy-text px-8 py-6 text-center relative">
            <div className="absolute top-3 right-4 text-2xl">🪔</div>
            <h1 className="text-xl font-bold mb-1">Unlock full CareerDNA</h1>
            <p className="text-navy-text/80 text-sm">
              Holland + OCEAN deep report · one-time payment
            </p>
          </div>

          <div className="p-8">
            <div className="flex items-center justify-between mb-6 pb-6 border-b border-saffron-700/10">
              <div>
                <h2 className="font-semibold text-navy-text">
                  Detailed report pack
                </h2>
                <p className="text-sm text-navy-text/60">
                  Amount confirmed when you tap pay (promo pricing may apply)
                </p>
              </div>
              <div className="text-right">
                <div className="text-xs font-bold text-saffron-700 uppercase tracking-wider">
                  INR
                </div>
                <div className="text-lg font-bold text-india-green-700">
                  from ₹49*
                </div>
              </div>
            </div>

            <div className="mb-6">
              <h3 className="text-xs font-bold text-saffron-700 uppercase tracking-wider mb-3">
                What you get
              </h3>
              <ul className="space-y-2">
                {[
                  "Full archetype deep dive (India-relevant copy)",
                  "OCEAN scores + percentiles",
                  "5+ career matches with salary & city notes",
                  "Strengths & growth tips",
                  "Share-ready lines & rarity context",
                ].map((item) => (
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

            <p className="text-xs text-navy-text/45 mb-4">
              *Early-bird promo while quota lasts; otherwise full price applies.
            </p>

            {error && (
              <p className="text-red-600 text-sm text-center mb-4">{error}</p>
            )}

            <button
              type="button"
              onClick={handlePay}
              disabled={processing}
              className="w-full bg-gradient-to-r from-india-green-600 to-india-green-700 text-white font-bold text-lg py-4 rounded-2xl hover:from-india-green-700 hover:to-india-green-800 transition-all shadow-lg disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {processing ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Opening checkout…
                </span>
              ) : (
                <>Pay with Razorpay (or instant mock in dev)</>
              )}
            </button>

            <div className="flex items-center justify-center gap-4 mt-4 text-xs text-navy-text/40">
              <span>Secure checkout</span>
              <span>·</span>
              <span>Instant unlock</span>
            </div>

            <Link
              href={`/results/${assessmentId}`}
              className="block w-full text-center mt-4 text-sm text-navy-text/50 hover:text-navy-text transition-colors"
            >
              ← Back to results
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
