"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  fetchMyAssessments,
  getReportPdfUrl,
  isLoggedIn,
  type AssessmentSummary,
} from "@/lib/api";

const DIMENSION_LABELS: Record<string, string> = {
  openness: "Openness",
  conscientiousness: "Conscientiousness",
  extraversion: "Extraversion",
  agreeableness: "Agreeableness",
  neuroticism: "Neuroticism",
};

export default function DashboardPage() {
  const [assessments, setAssessments] = useState<AssessmentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isLoggedIn()) {
      queueMicrotask(() => {
        setError("No session found. Please log in or start an assessment first.");
        setLoading(false);
      });
      return;
    }
    fetchMyAssessments()
      .then(setAssessments)
      .catch(() => setError("Unable to load your assessments."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-12">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold gradient-text">My Assessments</h1>
            <p className="text-slate-500 text-sm mt-1">
              View your past assessments and reports
            </p>
          </div>
          <Link
            href="/start"
            className="bg-indigo-600 text-white font-semibold px-5 py-2.5 rounded-xl hover:bg-indigo-700 transition-colors text-sm"
          >
            New Assessment
          </Link>
        </div>

        {loading && (
          <div className="text-center py-16">
            <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4" />
            <p className="text-slate-500">Loading...</p>
          </div>
        )}

        {error && (
          <div className="bg-white rounded-2xl shadow p-8 text-center border border-slate-100">
            <p className="text-slate-600 mb-4">{error}</p>
            <Link
              href="/start"
              className="inline-block bg-indigo-600 text-white font-semibold px-6 py-3 rounded-xl hover:bg-indigo-700 transition-colors"
            >
              Start Assessment
            </Link>
          </div>
        )}

        {!loading && !error && assessments.length === 0 && (
          <div className="bg-white rounded-2xl shadow p-8 text-center border border-slate-100">
            <p className="text-slate-600 mb-4">No assessments yet.</p>
            <Link
              href="/start"
              className="inline-block bg-indigo-600 text-white font-semibold px-6 py-3 rounded-xl hover:bg-indigo-700 transition-colors"
            >
              Take Your First Assessment
            </Link>
          </div>
        )}

        <div className="space-y-4">
          {assessments.map((a) => (
            <div
              key={a.id}
              className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="text-xs text-slate-400">
                    {new Date(a.created_at).toLocaleDateString("en-IN", {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                  <p className="font-semibold text-slate-800 mt-1">
                    Personality Assessment
                  </p>
                </div>
                <span
                  className={`text-xs font-medium px-2.5 py-1 rounded-full ${
                    a.completed
                      ? "bg-emerald-50 text-emerald-700"
                      : "bg-amber-50 text-amber-700"
                  }`}
                >
                  {a.completed ? "Completed" : "In Progress"}
                </span>
              </div>

              {a.completed && a.scores && (
                <div className="grid grid-cols-5 gap-2 mb-4">
                  {Object.entries(DIMENSION_LABELS).map(([key, label]) => (
                    <div
                      key={key}
                      className="bg-slate-50 rounded-lg p-2 text-center"
                    >
                      <p className="text-xs text-slate-500 truncate">
                        {label}
                      </p>
                      <p className="font-bold text-indigo-600 text-sm">
                        {a.scores?.[key] != null
                          ? Math.round(a.scores[key])
                          : "—"}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              <div className="flex gap-2 flex-wrap">
                {a.completed && (
                  <Link
                    href={`/results?id=${a.id}`}
                    className="text-sm font-medium text-indigo-600 hover:text-indigo-800 bg-indigo-50 px-3 py-1.5 rounded-lg transition-colors"
                  >
                    View Results
                  </Link>
                )}
                {a.completed && (
                  <Link
                    href={`/report/${a.id}`}
                    className="text-sm font-medium text-indigo-600 hover:text-indigo-800 bg-indigo-50 px-3 py-1.5 rounded-lg transition-colors"
                  >
                    View Report
                  </Link>
                )}
                {a.completed && (
                  <a
                    href={getReportPdfUrl(a.id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm font-medium text-emerald-600 hover:text-emerald-800 bg-emerald-50 px-3 py-1.5 rounded-lg transition-colors"
                  >
                    Download PDF
                  </a>
                )}
                {!a.completed && (
                  <Link
                    href={`/test?assessment_id=${a.id}`}
                    className="text-sm font-medium text-amber-600 hover:text-amber-800 bg-amber-50 px-3 py-1.5 rounded-lg transition-colors"
                  >
                    Continue Test
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 text-center">
          <Link
            href="/"
            className="text-sm text-slate-400 hover:text-slate-600 transition-colors"
          >
            &larr; Back to home
          </Link>
        </div>
      </div>
    </main>
  );
}
