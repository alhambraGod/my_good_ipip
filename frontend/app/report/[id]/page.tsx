"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { getReport, getReportPdfUrl, type ReportData } from "@/lib/api";

const DIMENSION_LABELS: Record<string, string> = {
  openness: "Openness",
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

export default function ReportPage() {
  const params = useParams();
  const router = useRouter();
  const assessmentId = params.id as string;
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!assessmentId) return;
    getReport(assessmentId)
      .then((data) => {
        setReport(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [assessmentId]);

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-500">Loading your report...</p>
        </div>
      </main>
    );
  }

  if (error === "Payment required") {
    return (
      <main className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
        <div className="text-center">
          <h1 className="text-xl font-bold text-slate-800 mb-2">
            Payment Required
          </h1>
          <p className="text-slate-500 mb-6">
            You need to unlock this report before viewing.
          </p>
          <button
            onClick={() => router.push(`/results?id=${assessmentId}`)}
            className="bg-indigo-600 text-white px-6 py-2 rounded-full hover:bg-indigo-700 transition-colors"
          >
            Go to Results
          </button>
        </div>
      </main>
    );
  }

  if (error || !report) {
    return (
      <main className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
        <div className="text-center">
          <h1 className="text-xl font-bold text-slate-800 mb-2">
            Something went wrong
          </h1>
          <p className="text-slate-500 mb-6">{error || "Report not found"}</p>
          <button
            onClick={() => router.push("/")}
            className="bg-indigo-600 text-white px-6 py-2 rounded-full hover:bg-indigo-700 transition-colors"
          >
            Go Home
          </button>
        </div>
      </main>
    );
  }

  const displayScore = (dim: string, score: number) =>
    dim === "neuroticism" ? Math.round(100 - score) : Math.round(score);
  const displayPercentile = (dim: string, pct: number) =>
    dim === "neuroticism" ? 100 - pct : pct;

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="gradient-bg text-white px-4 py-6 sticky top-0 z-20 shadow-lg">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">MindIQ Report</h1>
            <p className="text-indigo-200 text-xs">
              Your Personality Assessment
            </p>
          </div>
          <a
            href={getReportPdfUrl(assessmentId)}
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white/20 hover:bg-white/30 text-white text-sm font-medium px-4 py-2 rounded-full transition-colors flex items-center gap-1.5"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Download PDF
          </a>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Score Overview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-lg border border-slate-100 p-6 mb-8"
        >
          <h2 className="text-lg font-bold text-slate-800 mb-5">
            Score Overview
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {Object.entries(report.scores).map(([dim, score]) => (
              <div
                key={dim}
                className="bg-slate-50 rounded-xl p-4 border border-slate-100"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold text-slate-700">
                    {DIMENSION_LABELS[dim] || dim}
                  </span>
                  <span className="text-xs text-slate-500">
                    {displayPercentile(dim, report.percentiles[dim])}th pct
                  </span>
                </div>
                <div className="text-2xl font-bold text-slate-800 mb-2">
                  {displayScore(dim, score)}
                  <span className="text-sm text-slate-400 font-normal">
                    /100
                  </span>
                </div>
                <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full rounded-full bg-gradient-to-r ${DIMENSION_COLORS[dim] || "from-indigo-500 to-purple-500"}`}
                    initial={{ width: 0 }}
                    animate={{
                      width: `${displayScore(dim, score)}%`,
                    }}
                    transition={{ duration: 0.8, delay: 0.3 }}
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Full Report */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-2xl shadow-lg border border-slate-100 p-6 md:p-8 mb-8"
        >
          <div
            className="prose prose-slate max-w-none prose-headings:text-slate-800 prose-h2:text-xl prose-h2:border-b prose-h2:border-slate-100 prose-h2:pb-2 prose-h3:text-lg prose-h4:text-indigo-600 prose-p:text-slate-600 prose-li:text-slate-600 prose-strong:text-slate-800"
            dangerouslySetInnerHTML={{ __html: report.report_html }}
          />
        </motion.div>

        {/* Floating PDF button (mobile) */}
        <div className="fixed bottom-6 right-6 md:hidden z-30">
          <a
            href={getReportPdfUrl(assessmentId)}
            target="_blank"
            rel="noopener noreferrer"
            className="w-14 h-14 bg-indigo-600 text-white rounded-full shadow-xl flex items-center justify-center hover:bg-indigo-700 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </a>
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-slate-400 pb-12">
          <p>
            This report was generated by MindIQ using the IPIP-NEO Big Five
            personality framework.
          </p>
          <p className="mt-1">
            For informational purposes only. Not a clinical assessment.
          </p>
          <p className="mt-1">&copy; 2026 MindIQ. All rights reserved.</p>
        </div>
      </div>
    </main>
  );
}
