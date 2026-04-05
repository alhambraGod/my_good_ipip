"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { verifyPayment } from "@/lib/api";
import { Suspense } from "react";

function SuccessContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const assessmentId = searchParams.get("assessment_id");
  const sessionId = searchParams.get("session_id");
  const mock = searchParams.get("mock") === "true";
  const [verified, setVerified] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!assessmentId) {
      router.push("/");
      return;
    }
    verifyPayment(assessmentId, sessionId || undefined, mock)
      .then((res) => {
        if (res.paid) {
          setVerified(true);
        } else {
          setError(true);
        }
      })
      .catch(() => setError(true));
  }, [assessmentId, sessionId, mock, router]);

  if (error) {
    return (
      <main className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
        <div className="text-center">
          <div className="w-16 h-16 rounded-full bg-red-100 text-red-500 flex items-center justify-center text-3xl mx-auto mb-4">
            &#10007;
          </div>
          <h1 className="text-xl font-bold text-slate-800 mb-2">
            Payment Verification Failed
          </h1>
          <p className="text-slate-500 mb-6">
            Please try again or contact support.
          </p>
          <button
            onClick={() => router.push(`/results?id=${assessmentId}`)}
            className="bg-indigo-600 text-white px-6 py-2 rounded-full hover:bg-indigo-700 transition-colors"
          >
            Back to Results
          </button>
        </div>
      </main>
    );
  }

  if (!verified) {
    return (
      <main className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-500">Verifying your payment...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", duration: 0.6 }}
        className="text-center max-w-md"
      >
        {/* Success checkmark */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          className="w-20 h-20 rounded-full bg-green-100 text-green-500 flex items-center justify-center text-4xl mx-auto mb-6"
        >
          &#10003;
        </motion.div>

        <h1 className="text-2xl font-bold text-slate-800 mb-2">
          Payment Successful!
        </h1>
        <p className="text-slate-500 mb-8">
          Your personalized report is ready. Discover your unique personality
          insights.
        </p>

        <button
          onClick={() => router.push(`/report/${assessmentId}`)}
          className="bg-indigo-600 text-white font-bold text-lg px-10 py-4 rounded-full hover:bg-indigo-700 transition-colors shadow-lg"
        >
          View Your Report
        </button>
      </motion.div>
    </main>
  );
}

export default function PaymentSuccessPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen flex items-center justify-center bg-slate-50">
          <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
        </main>
      }
    >
      <SuccessContent />
    </Suspense>
  );
}
