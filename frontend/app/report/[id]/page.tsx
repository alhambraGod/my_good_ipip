"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { getV3Report, type V3ReportResponse } from "@/lib/v3-api";
import { TableOfContents, type TocItem } from "@/components/TableOfContents";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001";

const OCEAN_LABELS: Record<string, string> = {
  openness: "Openness",
  conscientiousness: "Conscientiousness",
  extraversion: "Extraversion",
  agreeableness: "Agreeableness",
  neuroticism: "Neuroticism",
};

const OCEAN_COLORS: Record<string, string> = {
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
  const [report, setReport] = useState<V3ReportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!assessmentId) return;
    getV3Report(assessmentId)
      .then((data) => {
        setReport(data);
        setLoading(false);
      })
      .catch((err: Error) => {
        setError(err.message);
        setLoading(false);
      });
  }, [assessmentId]);

  if (loading) {
    return (
      <main className="min-h-screen bg-india-radial flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-saffron-200 border-t-saffron-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-navy-text/70">Loading your report…</p>
        </div>
      </main>
    );
  }

  if (error === "Payment required") {
    return (
      <main className="min-h-screen bg-india-radial flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <h1 className="text-xl font-bold text-navy-text mb-2">
            Unlock required
          </h1>
          <p className="text-navy-text/65 mb-6 text-sm">
            Pay once to open your full MindPrism report.
          </p>
          <Link
            href={`/payment?assessment_id=${assessmentId}`}
            className="inline-block bg-india-green-600 text-white px-6 py-2 rounded-full hover:bg-india-green-700 transition-colors font-bold"
          >
            Unlock report
          </Link>
          <button
            type="button"
            onClick={() => router.push(`/results/${assessmentId}`)}
            className="block mx-auto mt-4 text-sm text-navy-text/50 hover:text-navy-text"
          >
            ← Free results
          </button>
        </div>
      </main>
    );
  }

  if (error || !report) {
    return (
      <main className="min-h-screen bg-india-radial flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <h1 className="text-xl font-bold text-navy-text mb-2">
            Something went wrong
          </h1>
          <p className="text-navy-text/65 mb-6 text-sm">{error || "Report not found"}</p>
          <button
            type="button"
            onClick={() => router.push("/")}
            className="bg-india-green-600 text-white px-6 py-2 rounded-full hover:bg-india-green-700 transition-colors"
          >
            Go home
          </button>
        </div>
      </main>
    );
  }

  const pdfHref =
    report.pdf_path &&
    (report.pdf_path.startsWith("http")
      ? report.pdf_path
      : `${API_BASE.replace(/\/$/, "")}/${report.pdf_path.replace(/^\//, "")}`);

  const descriptionParagraphs = report.deep_description_en
    .split(/\n\n+/)
    .map((p) => p.trim())
    .filter(Boolean);

  const isPreview = !!report.is_preview;

  return (
    <main className="min-h-screen bg-cream relative">
      {/* Diagonal "PREVIEW" watermark — only when serving an unpaid report in dev. */}
      {isPreview && (
        <div
          aria-hidden
          className="pointer-events-none fixed inset-0 z-30 overflow-hidden select-none"
        >
          <div
            className="absolute inset-0 flex items-center justify-center"
            style={{ transform: "rotate(-30deg)" }}
          >
            <p className="text-saffron-700/20 font-black text-[15vw] leading-none whitespace-nowrap tracking-widest">
              PREVIEW · DEV
            </p>
          </div>
        </div>
      )}

      <header className="bg-india-hero text-navy-text px-4 py-5 sticky top-0 z-20 shadow-md border-b border-saffron-700/20">
        <div className="max-w-3xl mx-auto flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-2xl mb-0.5">🪔</div>
            <h1 className="text-lg font-black tracking-tight">
              MindPrism · {isPreview ? "Preview report (unpaid)" : "Full report"}
            </h1>
            <p className="text-xs text-navy-text/70">
              {report.cell_id} · {report.cell_label_en}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {isPreview && (
              <Link
                href={`/payment?assessment_id=${assessmentId}`}
                className="text-sm font-bold bg-saffron-600 hover:bg-saffron-700 text-white px-4 py-2 rounded-full transition-colors"
              >
                Unlock the real report →
              </Link>
            )}
            {!isPreview && pdfHref && (
              <a
                href={pdfHref}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-bold bg-india-green-600 text-white px-4 py-2 rounded-full hover:bg-india-green-700 transition-colors"
              >
                Download PDF
              </a>
            )}
            <Link
              href={`/results/${assessmentId}`}
              className="text-sm font-medium text-navy-text/80 px-4 py-2 rounded-full border border-navy-text/20 hover:bg-white/50"
            >
              Summary
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-8 lg:grid lg:grid-cols-[200px_minmax(0,1fr)] lg:gap-10">
        <TableOfContents
          items={
            [
              { id: "overview", label: "Overview", emoji: "🎯" },
              { id: "deep-dive", label: "Deep dive", emoji: "🧠" },
              { id: "strengths-growth", label: "Strengths & growth", emoji: "★" },
              { id: "ocean", label: "OCEAN profile", emoji: "🌊" },
              { id: "careers", label: `Careers (${report.careers.length})`, emoji: "💼" },
            ] satisfies TocItem[]
          }
        />
        <div className="space-y-8 lg:max-w-3xl">
        <motion.section
          id="overview"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-3xl border border-saffron-700/15 shadow-lg p-6 md:p-8 scroll-mt-32"
        >
          <p className="text-saffron-700 text-xs font-bold uppercase tracking-widest mb-2">
            Your code
          </p>
          <div className="text-5xl md:text-6xl font-black text-transparent bg-clip-text bg-gradient-to-br from-navy-text to-saffron-600 mb-2">
            {report.cell_id}
          </div>
          <p className="text-lg font-semibold text-navy-text mb-1">
            {report.cell_label_en}
          </p>
          <p className="text-navy-text/75 italic border-l-4 border-india-green-500 pl-4 py-1">
            &ldquo;{report.slogan_en}&rdquo;
          </p>
          <p className="text-sm text-navy-text/55 mt-3">
            Holland {report.holland_code} · ~{report.rarity_pct}% rarity band ·{" "}
            {report.is_mast_trigger ? "MAST highlight" : "standard window"}
          </p>
        </motion.section>

        <motion.section
          id="deep-dive"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="bg-white rounded-3xl border border-saffron-700/15 shadow-lg p-6 md:p-8 scroll-mt-32"
        >
          <h2 className="text-lg font-bold text-navy-text mb-4">Deep dive</h2>
          <div className="space-y-4 text-navy-text/85 text-sm leading-relaxed">
            {descriptionParagraphs.map((para, idx) => (
              <p key={idx}>{para}</p>
            ))}
          </div>
        </motion.section>

        <div id="strengths-growth" className="grid md:grid-cols-2 gap-6 scroll-mt-32">
          <motion.section
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-3xl border border-saffron-700/15 shadow-lg p-6"
          >
            <h2 className="text-base font-bold text-navy-text mb-4">Strengths</h2>
            <ul className="space-y-2">
              {report.strengths_en.map((s) => (
                <li
                  key={s}
                  className="text-sm text-navy-text/80 flex gap-2 items-start"
                >
                  <span className="text-india-green-600 shrink-0">★</span>
                  {s}
                </li>
              ))}
            </ul>
          </motion.section>
          <motion.section
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.12 }}
            className="bg-white rounded-3xl border border-saffron-700/15 shadow-lg p-6"
          >
            <h2 className="text-base font-bold text-navy-text mb-4">Growth tips</h2>
            <ul className="space-y-2">
              {report.growth_tips_en.map((s) => (
                <li
                  key={s}
                  className="text-sm text-navy-text/80 flex gap-2 items-start"
                >
                  <span className="text-saffron-600 shrink-0">→</span>
                  {s}
                </li>
              ))}
            </ul>
          </motion.section>
        </div>

        <motion.section
          id="ocean"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="bg-white rounded-3xl border border-saffron-700/15 shadow-lg p-6 md:p-8 scroll-mt-32"
        >
          <h2 className="text-lg font-bold text-navy-text mb-5">OCEAN profile</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            {Object.entries(report.ocean_scores).map(([dim, score]) => (
              <div
                key={dim}
                className="bg-cream rounded-xl p-4 border border-saffron-700/10"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold text-navy-text">
                    {OCEAN_LABELS[dim] || dim}
                  </span>
                  <span className="text-xs text-navy-text/50">
                    {report.ocean_percentiles[dim] ?? "—"}th pct
                  </span>
                </div>
                <div className="text-xl font-bold text-navy-text mb-2">
                  {Math.round(score)}
                  <span className="text-sm text-navy-text/40 font-normal">/100</span>
                </div>
                <div className="h-2 bg-saffron-700/15 rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full rounded-full bg-gradient-to-r ${OCEAN_COLORS[dim] || "from-india-green-500 to-india-green-700"}`}
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(100, Math.max(0, score))}%` }}
                    transition={{ duration: 0.7, delay: 0.2 }}
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.section>

        <motion.section
          id="careers"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.18 }}
          className="pb-16 scroll-mt-32"
        >
          <h2 className="text-lg font-bold text-navy-text mb-4">
            Career matches ({report.careers.length})
          </h2>
          <div className="space-y-4">
            {report.careers.map((c, i) => (
              <motion.article
                key={c.career_id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * i }}
                className="bg-white rounded-2xl border border-india-green-600/20 shadow-md p-5"
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2 mb-1">
                  <h3 className="text-lg font-bold text-navy-text">{c.name_en}</h3>
                  <span className="text-xs font-medium text-navy-text/50">
                    {c.name_hi}
                  </span>
                </div>
                {c.tagline_en && (
                  <p className="text-sm text-india-green-700 font-medium mb-2">
                    {c.tagline_en}
                  </p>
                )}
                {c.why_match[report.cell_id] && (
                  <p className="text-sm text-navy-text/75 mb-3">
                    {c.why_match[report.cell_id]}
                  </p>
                )}
                <div className="grid sm:grid-cols-2 gap-3 text-xs text-navy-text/70">
                  <div>
                    <span className="font-bold text-navy-text">Salary (INR)</span>
                    <p>
                      Entry {c.salary_inr.entry} · Mid {c.salary_inr.mid} · Sr{" "}
                      {c.salary_inr.senior}
                    </p>
                  </div>
                  <div>
                    <span className="font-bold text-navy-text">Hot cities</span>
                    <p>{c.city_distribution.slice(0, 4).join(", ")}</p>
                  </div>
                </div>
                {c.indian_companies.length > 0 && (
                  <p className="text-xs text-navy-text/60 mt-2">
                    <span className="font-semibold text-navy-text/80">Hiring:</span>{" "}
                    {c.indian_companies.slice(0, 6).join(", ")}
                  </p>
                )}
              </motion.article>
            ))}
          </div>
        </motion.section>

          <footer className="text-center text-xs text-navy-text/45 pb-8">
            <p>MindPrism — RIASEC + OCEAN for Indian urban youth. Not clinical.</p>
          </footer>
        </div>
      </div>
    </main>
  );
}
