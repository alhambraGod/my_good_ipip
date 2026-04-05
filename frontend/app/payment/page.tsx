"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { createPaymentSession } from "@/lib/api";
import { Suspense } from "react";

function PaymentContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const assessmentId = searchParams.get("id");
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
      const session = await createPaymentSession(assessmentId);
      if (session.checkout_url) {
        window.location.href = session.checkout_url;
      }
    } catch {
      setError("Payment failed. Please try again.");
      setProcessing(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-3xl shadow-xl border border-slate-100 overflow-hidden">
          {/* Header */}
          <div className="gradient-bg text-white px-8 py-6 text-center">
            <h1 className="text-xl font-bold mb-1">Unlock Your Report</h1>
            <p className="text-indigo-200 text-sm">
              One-time payment, instant access
            </p>
          </div>

          <div className="p-8">
            {/* Product */}
            <div className="flex items-center justify-between mb-6 pb-6 border-b border-slate-100">
              <div>
                <h2 className="font-semibold text-slate-800">
                  MindIQ Personality Report
                </h2>
                <p className="text-sm text-slate-500">
                  Complete AI-powered analysis
                </p>
              </div>
              <div className="text-2xl font-bold gradient-text">$3.99</div>
            </div>

            {/* What you get */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-slate-600 uppercase tracking-wider mb-3">
                What&apos;s Included
              </h3>
              <ul className="space-y-2">
                {[
                  "Comprehensive Big Five personality analysis",
                  "5-7 career path recommendations",
                  "Personal strengths & growth strategies",
                  "Team dynamics & communication insights",
                  "Actionable next steps",
                  "Downloadable PDF report",
                ].map((item) => (
                  <li
                    key={item}
                    className="flex items-start gap-2 text-sm text-slate-600"
                  >
                    <span className="text-green-500 mt-0.5">&#10003;</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {error && (
              <p className="text-red-500 text-sm text-center mb-4">{error}</p>
            )}

            {/* Pay button */}
            <button
              onClick={handlePay}
              disabled={processing}
              className="w-full bg-indigo-600 text-white font-bold text-lg py-4 rounded-2xl hover:bg-indigo-700 transition-colors shadow-lg disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {processing ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Processing...
                </span>
              ) : (
                "Pay $3.99"
              )}
            </button>

            {/* Trust */}
            <div className="flex items-center justify-center gap-4 mt-4 text-xs text-slate-400">
              <span>&#9740; Secure</span>
              <span>&#9889; Instant</span>
              <span>&#8634; Refundable</span>
            </div>

            <button
              onClick={() =>
                router.push(`/results?id=${assessmentId}`)
              }
              className="block w-full text-center mt-4 text-sm text-slate-400 hover:text-slate-600 transition-colors"
            >
              &larr; Back to results
            </button>
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
        <main className="min-h-screen flex items-center justify-center bg-slate-50">
          <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
        </main>
      }
    >
      <PaymentContent />
    </Suspense>
  );
}
