"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { verifyV3Payment } from "@/lib/v3-api";

function SuccessContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const assessmentId = searchParams.get("assessment_id");
  const [verified, setVerified] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!assessmentId) {
      router.push("/");
      return;
    }
    verifyV3Payment(assessmentId)
      .then((res) => {
        if (res.paid) {
          setVerified(true);
        } else {
          setError(true);
        }
      })
      .catch(() => setError(true));
  }, [assessmentId, router]);

  if (error) {
    return (
      <main className="min-h-screen bg-india-radial flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 rounded-full bg-red-100 text-red-600 flex items-center justify-center text-3xl mx-auto mb-4">
            ✗
          </div>
          <h1 className="text-xl font-bold text-navy-text mb-2">
            Payment not confirmed yet
          </h1>
          <p className="text-navy-text/65 mb-6 text-sm">
            If you paid via Razorpay, wait a few seconds and open your report
            from results. In dev mock mode, try the unlock button again.
          </p>
          <Link
            href={assessmentId ? `/results/${assessmentId}` : "/"}
            className="inline-block bg-india-green-600 text-white px-6 py-2 rounded-full hover:bg-india-green-700 transition-colors"
          >
            Back to results
          </Link>
        </div>
      </main>
    );
  }

  if (!verified) {
    return (
      <main className="min-h-screen bg-india-radial flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-saffron-200 border-t-saffron-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-navy-text/70">Confirming your payment…</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-india-radial flex items-center justify-center px-4">
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", duration: 0.6 }}
        className="text-center max-w-md"
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          className="w-20 h-20 rounded-full bg-india-green-100 text-india-green-700 flex items-center justify-center text-4xl mx-auto mb-6"
        >
          ✓
        </motion.div>

        <h1 className="text-2xl font-bold text-navy-text mb-2">You&apos;re in</h1>
        <p className="text-navy-text/70 mb-8 text-sm">
          Your full CareerDNA report is unlocked — OCEAN, careers, and deep
          archetype notes.
        </p>

        <button
          type="button"
          onClick={() =>
            assessmentId && router.push(`/report/${assessmentId}`)
          }
          className="bg-gradient-to-r from-saffron-500 to-saffron-600 text-navy-text font-bold text-lg px-10 py-4 rounded-full hover:from-saffron-600 hover:to-saffron-700 transition-all shadow-lg w-full sm:w-auto"
        >
          View full report
        </button>
      </motion.div>
    </main>
  );
}

export default function PaymentSuccessPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen flex items-center justify-center bg-india-radial">
          <div className="w-12 h-12 border-4 border-saffron-200 border-t-saffron-600 rounded-full animate-spin" />
        </main>
      }
    >
      <SuccessContent />
    </Suspense>
  );
}
