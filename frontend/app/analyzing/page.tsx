"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Suspense } from "react";

const DIMENSIONS = [
  { key: "openness", label: "Openness to Experience" },
  { key: "conscientiousness", label: "Conscientiousness" },
  { key: "extraversion", label: "Extraversion" },
  { key: "agreeableness", label: "Agreeableness" },
  { key: "emotional_stability", label: "Emotional Stability" },
];

function AnalyzingContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const assessmentId = searchParams.get("id");
  const [step, setStep] = useState(-1);

  useEffect(() => {
    if (!assessmentId) {
      router.push("/");
      return;
    }

    // Sequence: -1 (intro) -> 0..4 (dimensions) -> 5 (generating) -> redirect
    const timers: ReturnType<typeof setTimeout>[] = [];

    timers.push(setTimeout(() => setStep(0), 1000));
    timers.push(setTimeout(() => setStep(1), 2000));
    timers.push(setTimeout(() => setStep(2), 3000));
    timers.push(setTimeout(() => setStep(3), 4000));
    timers.push(setTimeout(() => setStep(4), 5000));
    timers.push(setTimeout(() => setStep(5), 6000));
    timers.push(
      setTimeout(() => {
        router.push(`/results?id=${assessmentId}`);
      }, 7500)
    );

    return () => timers.forEach(clearTimeout);
  }, [assessmentId, router]);

  return (
    <main className="min-h-screen gradient-bg flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        {/* Spinner */}
        <div className="mb-8">
          <div className="w-20 h-20 mx-auto relative">
            <div className="absolute inset-0 border-4 border-white/20 rounded-full" />
            <div className="absolute inset-0 border-4 border-transparent border-t-white rounded-full animate-spin" />
          </div>
        </div>

        {/* Status text */}
        <AnimatePresence mode="wait">
          {step < 0 && (
            <motion.p
              key="intro"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="text-white text-xl font-medium"
            >
              Analyzing your responses...
            </motion.p>
          )}
          {step >= 0 && step <= 4 && (
            <motion.div
              key={`dim-${step}`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="text-white"
            >
              <p className="text-lg font-medium mb-4">
                Analyzing {DIMENSIONS[step].label}...
              </p>
              {/* Progress bar for this dimension */}
              <div className="h-2 bg-white/20 rounded-full overflow-hidden max-w-xs mx-auto">
                <motion.div
                  className="h-full bg-white rounded-full"
                  initial={{ width: "0%" }}
                  animate={{ width: "100%" }}
                  transition={{ duration: 0.8 }}
                />
              </div>
            </motion.div>
          )}
          {step === 5 && (
            <motion.p
              key="generating"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="text-white text-xl font-medium"
            >
              Generating your personality profile...
            </motion.p>
          )}
        </AnimatePresence>

        {/* Dimension checklist */}
        <div className="mt-10 space-y-3 text-left max-w-xs mx-auto">
          {DIMENSIONS.map((dim, i) => (
            <motion.div
              key={dim.key}
              initial={{ opacity: 0.3 }}
              animate={{ opacity: step >= i ? 1 : 0.3 }}
              className="flex items-center gap-3 text-white/80"
            >
              <div
                className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                  step > i
                    ? "bg-green-400 text-green-900"
                    : step === i
                    ? "bg-white/30"
                    : "bg-white/10"
                }`}
              >
                {step > i ? "\u2713" : ""}
              </div>
              <span className="text-sm">{dim.label}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </main>
  );
}

export default function AnalyzingPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen gradient-bg flex items-center justify-center">
          <div className="w-12 h-12 border-4 border-white/20 border-t-white rounded-full animate-spin" />
        </main>
      }
    >
      <AnalyzingContent />
    </Suspense>
  );
}
