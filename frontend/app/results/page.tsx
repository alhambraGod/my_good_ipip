"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { getAssessment, type AssessmentResult } from "@/lib/api";
import { Suspense } from "react";

const isDevMode = process.env.NEXT_PUBLIC_DEV_MODE === "true";

const DIMENSION_LABELS: Record<string, string> = {
  openness: "Openness to Experience",
  conscientiousness: "Conscientiousness",
  extraversion: "Extraversion",
  agreeableness: "Agreeableness",
  neuroticism: "Emotional Stability",
};

const DIMENSION_COLORS: Record<string, string> = {
  openness: "from-violet-500 to-purple-500",
  conscientiousness: "from-blue-500 to-indigo-500",
  extraversion: "from-amber-500 to-orange-500",
  agreeableness: "from-emerald-500 to-teal-500",
  neuroticism: "from-rose-500 to-pink-500",
};

function ResultsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const assessmentId = searchParams.get("id");
  const [data, setData] = useState<AssessmentResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!assessmentId) {
      router.push("/");
      return;
    }
    getAssessment(assessmentId)
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
        router.push("/");
      });
  }, [assessmentId, router]);

  if (loading || !data || !data.scores || !data.percentiles) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
      </main>
    );
  }

  const scores = data.scores;
  const percentiles = data.percentiles;

  // Convert neuroticism to emotional stability for display
  const displayScore = (dim: string, score: number) =>
    dim === "neuroticism" ? Math.round(100 - score) : Math.round(score);
  const displayPercentile = (dim: string, pct: number) =>
    dim === "neuroticism" ? 100 - pct : pct;

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="gradient-bg text-white px-4 py-8 text-center">
        <h1 className="text-2xl font-bold mb-1">Your Personality Profile</h1>
        <p className="text-indigo-200 text-sm">
          Based on the Big Five Personality Model
        </p>
      </div>

      <div className="max-w-lg mx-auto px-4 -mt-4">
        {/* Score cards */}
        <div className="bg-white rounded-2xl shadow-lg border border-slate-100 p-6 mb-6">
          <h2 className="text-lg font-bold text-slate-800 mb-4">
            Your Scores
          </h2>
          <div className="space-y-5">
            {Object.entries(scores).map(([dim, score], i) => (
              <motion.div
                key={dim}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.15 }}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-slate-700">
                    {DIMENSION_LABELS[dim] || dim}
                  </span>
                  <span className="text-sm text-slate-500">
                    {displayScore(dim, score)}/100 &middot;{" "}
                    {displayPercentile(dim, percentiles[dim])}th percentile
                  </span>
                </div>
                <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full rounded-full bg-gradient-to-r ${DIMENSION_COLORS[dim] || "from-indigo-500 to-purple-500"}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${displayScore(dim, score)}%` }}
                    transition={{ duration: 0.8, delay: i * 0.15 + 0.2 }}
                  />
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Blurred preview / Report access */}
        {data.paid || isDevMode ? (
          <div className="bg-white rounded-2xl shadow-lg border border-slate-100 p-6 mb-6 text-center">
            <div className="w-14 h-14 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-2xl mx-auto mb-4">
              &#10003;
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-2">
              Your Report is Ready
            </h3>
            <p className="text-slate-500 text-sm mb-6">
              View your complete AI-generated personality analysis
            </p>
            <button
              onClick={() => router.push(`/report/${assessmentId}`)}
              className="bg-indigo-600 text-white font-bold px-8 py-3 rounded-full hover:bg-indigo-700 transition-colors shadow-lg"
            >
              View Full Report
            </button>
          </div>
        ) : (
          <div className="relative mb-6">
            <div className="blur-lock bg-white rounded-2xl shadow-lg border border-slate-100 p-6">
              <h2 className="text-lg font-bold text-slate-800 mb-3">
                Detailed Personality Analysis
              </h2>
              <p className="text-slate-600 text-sm mb-3">
                Your unique combination of high conscientiousness and moderate
                extraversion suggests you thrive in structured environments where
                you can take initiative. You bring both discipline and social
                energy to your work, making you an effective team contributor who
                also excels at independent tasks...
              </p>
              <h3 className="text-md font-semibold text-slate-700 mb-2">
                Career Recommendations
              </h3>
              <p className="text-slate-600 text-sm mb-3">
                Based on your personality profile, the following career paths are
                excellent matches: Software Engineering, Product Management,
                Management Consulting, Data Science, Government Services...
              </p>
              <h3 className="text-md font-semibold text-slate-700 mb-2">
                Your Key Strengths
              </h3>
              <p className="text-slate-600 text-sm">
                1. Strategic thinking and long-term planning 2. Ability to work
                both independently and in teams 3. Strong attention to detail...
              </p>
            </div>

            {/* Paywall overlay */}
            <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-t from-white via-white/80 to-transparent rounded-2xl">
              <div className="text-center px-6">
                <div className="w-14 h-14 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-2xl mx-auto mb-4">
                  &#9919;
                </div>
                <h3 className="text-xl font-bold text-slate-800 mb-2">
                  Unlock Your Full Report
                </h3>
                <p className="text-slate-500 text-sm mb-4">
                  Get your complete AI-generated personality analysis
                </p>
                <div className="text-3xl font-bold gradient-text mb-4">$3.99</div>
                <ul className="text-sm text-slate-600 space-y-2 mb-6 text-left max-w-xs mx-auto">
                  <li className="flex items-center gap-2">
                    <span className="text-green-500">&#10003;</span> Detailed
                    personality analysis
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-500">&#10003;</span> Career
                    recommendations
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-500">&#10003;</span> Growth
                    strategies & action plan
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-green-500">&#10003;</span> PDF download
                  </li>
                </ul>
                <button
                  onClick={() =>
                    router.push(`/payment?id=${assessmentId}`)
                  }
                  className="bg-indigo-600 text-white font-bold px-8 py-3 rounded-full hover:bg-indigo-700 transition-colors shadow-lg pulse-glow"
                >
                  Unlock Report
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Trust badges */}
        <div className="flex items-center justify-center gap-6 text-xs text-slate-400 pb-12">
          <span className="flex items-center gap-1">
            &#9740; Secure Payment
          </span>
          <span className="flex items-center gap-1">
            &#9889; Instant Access
          </span>
          <span className="flex items-center gap-1">
            &#10003; Money-Back Guarantee
          </span>
        </div>
      </div>
    </main>
  );
}

export default function ResultsPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen flex items-center justify-center bg-slate-50">
          <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
        </main>
      }
    >
      <ResultsContent />
    </Suspense>
  );
}
