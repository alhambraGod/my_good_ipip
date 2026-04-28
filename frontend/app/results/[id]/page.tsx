"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  getV3Results,
  type V3ResultsResponse,
  type V3CareerPreview,
} from "@/lib/v3-api";

const RIASEC_LABELS: Record<string, string> = {
  R: "Realistic",
  I: "Investigative",
  A: "Artistic",
  S: "Social",
  E: "Enterprising",
  C: "Conventional",
};

export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const assessmentId = params?.id as string | undefined;
  const [data, setData] = useState<V3ResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!assessmentId) {
      router.push("/");
      return;
    }
    getV3Results(assessmentId)
      .then(setData)
      .catch(() => router.push("/"))
      .finally(() => setLoading(false));
  }, [assessmentId, router]);

  if (loading || !data) {
    return (
      <main className="min-h-screen bg-india-radial flex items-center justify-center">
        <p className="text-navy-text/70">Loading…</p>
      </main>
    );
  }

  return (
    <main className="bg-cream">
      {/* Screen 1: Personality Card */}
      <section className="bg-india-hero min-h-screen flex flex-col items-center justify-center px-6 py-16 text-center relative">
        <div className="absolute top-6 left-6 text-3xl">🪔</div>
        <div className="absolute top-6 right-6 text-xs font-bold bg-white/70 backdrop-blur px-3 py-1 rounded-full text-saffron-700 border border-saffron-700/30">
          RARE {data.rarity_pct}%
        </div>
        <motion.div
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.6 }}
        >
          <div className="text-saffron-700 text-xs font-bold tracking-[0.3em] uppercase mb-3">
            Your Personality Code
          </div>
          <div className="text-8xl md:text-9xl font-black bg-clip-text text-transparent bg-gradient-to-br from-navy-text to-saffron-700 mb-2">
            {data.cell_id}
          </div>
          <div className="text-2xl md:text-3xl font-bold text-navy-text mb-3">
            {data.cell_label_en}
          </div>
          <p className="text-lg text-navy-text/80 italic max-w-md mx-auto bg-white/60 backdrop-blur p-4 rounded-2xl">
            &ldquo;{data.slogan_en}&rdquo;
          </p>
          <p className="text-sm text-india-green-700 font-bold mt-4">
            ★ You&apos;re {data.rarity_pct}% of Indian Gen Z ★
          </p>
        </motion.div>
        <ShareButton
          shareUrl={data.share_url}
          text={`I'm ${data.cell_id}. ${data.slogan_en} Try the test → ${data.share_url}`}
        />
      </section>

      {/* Screen 2: Holland Radar */}
      <section className="min-h-screen flex flex-col items-center justify-center px-6 py-16 bg-cream">
        <div className="max-w-md w-full">
          <h2 className="text-2xl font-bold text-navy-text text-center mb-6">Holland Radar</h2>
          <RadarChart scores={data.holland_radar} />
          <p className="text-navy-text/70 text-center mt-6">
            <strong>{RIASEC_LABELS[data.holland_code[0]]}</strong>-dominant +{" "}
            <strong>{RIASEC_LABELS[data.holland_code[1]]}</strong>-supporting
          </p>
        </div>
      </section>

      {/* Screen 3: Core Insight */}
      <section className="min-h-screen flex flex-col items-center justify-center px-6 py-16 bg-india-radial">
        <div className="max-w-2xl">
          <h2 className="text-saffron-700 text-xs font-bold tracking-widest uppercase mb-4 text-center">
            Core Insight
          </h2>
          <p className="text-lg md:text-xl text-navy-text leading-relaxed bg-white/80 backdrop-blur p-8 rounded-3xl shadow-lg">
            {data.core_insight_en}
          </p>
        </div>
      </section>

      {/* Screen 4: Careers Teaser */}
      <section className="min-h-screen flex flex-col items-center justify-center px-6 py-16 bg-cream">
        <div className="max-w-2xl w-full">
          <h2 className="text-2xl font-bold text-navy-text text-center mb-8">Career Paths</h2>
          <div className="space-y-4">
            {data.careers_preview.map((career, i) => (
              <CareerCard key={career.career_id} career={career} index={i} />
            ))}
          </div>
        </div>
      </section>

      {/* Screen 5: Dual CTA */}
      <section className="bg-gradient-to-br from-india-green-500 to-india-green-700 text-white py-16 px-6 text-center">
        <h2 className="text-3xl font-bold mb-4">Want the full report?</h2>
        <p className="text-india-green-50 mb-8 max-w-md mx-auto">
          Unlock all 5+ careers, OCEAN analysis, strengths, growth tips, and PDF download.
        </p>
        <div className="flex flex-col md:flex-row gap-4 max-w-md mx-auto">
          <ShareButton
            shareUrl={data.share_url}
            text={`I'm ${data.cell_id}. ${data.slogan_en} → ${data.share_url}`}
            variant="white-outline"
          />
          {data.is_paid ? (
            <Link
              href={`/report/${data.assessment_id}`}
              className="flex-1 bg-saffron-500 hover:bg-saffron-600 text-navy-text font-bold py-3 px-6 rounded-full transition-all shadow-lg text-center"
            >
              View full report →
            </Link>
          ) : (
            <Link
              href={`/payment?assessment_id=${data.assessment_id}`}
              className="flex-1 bg-saffron-500 hover:bg-saffron-600 text-navy-text font-bold py-3 px-6 rounded-full transition-all shadow-lg text-center"
            >
              Unlock full report →
            </Link>
          )}
        </div>
      </section>
    </main>
  );
}

function ShareButton({
  shareUrl,
  text,
  variant = "default",
}: {
  shareUrl: string;
  text: string;
  variant?: string;
}) {
  const handleShare = async () => {
    if (typeof navigator !== "undefined" && navigator.share) {
      try {
        await navigator.share({ text, url: shareUrl });
        return;
      } catch {
        /* fall through to wa.me */
      }
    }
    const wa = `https://wa.me/?text=${encodeURIComponent(text)}`;
    window.open(wa, "_blank");
  };
  const cls =
    variant === "white-outline"
      ? "flex-1 bg-white/10 border border-white text-white font-bold py-3 px-6 rounded-full hover:bg-white/20 transition-all"
      : "mt-8 bg-india-green-500 hover:bg-india-green-600 text-white font-bold px-6 py-3 rounded-full transition-all shadow-lg";
  return (
    <button onClick={handleShare} className={cls}>
      📤 Share to WhatsApp
    </button>
  );
}

function CareerCard({ career, index }: { career: V3CareerPreview; index: number }) {
  if (career.locked) {
    return (
      <div className="bg-white/60 border-2 border-saffron-200/50 rounded-2xl p-6 backdrop-blur">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🔒</span>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-navy-text/50">{career.name_en}</h3>
            <p className="text-navy-text/40 text-sm">Unlock to see this career&apos;s deep dive.</p>
          </div>
        </div>
      </div>
    );
  }
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="bg-white border-2 border-india-green-300 rounded-2xl p-6 shadow-lg"
    >
      <div className="text-saffron-700 text-xs font-bold uppercase tracking-widest mb-2">
        Top match
      </div>
      <h3 className="text-2xl font-bold text-navy-text mb-2">{career.name_en}</h3>
      <p className="text-navy-text/70 mb-3">{career.tagline_en}</p>
      <div className="text-india-green-700 text-sm font-bold">{career.salary_inr_summary}</div>
    </motion.div>
  );
}

function RadarChart({ scores }: { scores: Record<string, number> }) {
  const types = ["R", "I", "A", "S", "E", "C"];
  const max = 20;
  const cx = 100;
  const cy = 100;
  const r = 80;
  const points = types.map((t, i) => {
    const angle = (i * Math.PI) / 3 - Math.PI / 2;
    const score = scores[t] ?? 0;
    const ratio = score / max;
    return [cx + Math.cos(angle) * r * ratio, cy + Math.sin(angle) * r * ratio];
  });
  const grid = [0.25, 0.5, 0.75, 1.0].map((g) => {
    const gridPoints = types.map((_, i) => {
      const angle = (i * Math.PI) / 3 - Math.PI / 2;
      return [cx + Math.cos(angle) * r * g, cy + Math.sin(angle) * r * g];
    });
    return gridPoints.map(([x, y]) => `${x},${y}`).join(" ");
  });
  return (
    <svg viewBox="0 0 200 200" className="w-full">
      {grid.map((pts, i) => (
        <polygon key={i} points={pts} fill="none" stroke="#FFD58F" strokeWidth="0.5" />
      ))}
      <polygon
        points={points.map(([x, y]) => `${x},${y}`).join(" ")}
        fill="rgba(255, 153, 51, 0.3)"
        stroke="#FF9933"
        strokeWidth="2"
      />
      {types.map((t, i) => {
        const angle = (i * Math.PI) / 3 - Math.PI / 2;
        return (
          <text
            key={t}
            x={cx + Math.cos(angle) * (r + 10)}
            y={cy + Math.sin(angle) * (r + 10)}
            textAnchor="middle"
            fill="#1A202C"
            fontSize="10"
            fontWeight="bold"
            dy="3"
          >
            {t}
          </text>
        );
      })}
    </svg>
  );
}
