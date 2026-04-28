"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  getDemographicQuestions,
  startV3Assessment,
  submitV3Assessment,
  getV3Milestone,
  type V3Question,
  type V3DemographicAnswers,
} from "@/lib/v3-api";

const LIKERT_OPTIONS = [
  { value: 1, label: "Strongly Disagree" },
  { value: 2, label: "Disagree" },
  { value: 3, label: "Neutral" },
  { value: 4, label: "Agree" },
  { value: 5, label: "Strongly Agree" },
];

const MILESTONE_THRESHOLDS = [10, 20, 30, 40];

type Phase = "loading" | "demographic" | "main" | "milestone" | "submitting";

export default function TestPage() {
  const router = useRouter();
  const [phase, setPhase] = useState<Phase>("loading");
  const [demographicQs, setDemographicQs] = useState<V3Question[]>([]);
  const [demographicAnswers, setDemographicAnswers] = useState<Partial<V3DemographicAnswers>>({});
  const [demographicIdx, setDemographicIdx] = useState(0);

  const [assessmentId, setAssessmentId] = useState<string | null>(null);
  const [seed, setSeed] = useState<string>("");
  const [mainQs, setMainQs] = useState<V3Question[]>([]);
  const [mainIdx, setMainIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});

  const [milestoneText, setMilestoneText] = useState<string>("");
  const [pendingMilestone, setPendingMilestone] = useState<number | null>(null);

  // Load demographic questions
  useEffect(() => {
    getDemographicQuestions()
      .then((qs) => {
        setDemographicQs(qs);
        setPhase("demographic");
      })
      .catch(() => router.push("/"));
  }, [router]);

  const startMainPhase = useCallback(
    async (dem: V3DemographicAnswers) => {
      setPhase("loading");
      try {
        const start = await startV3Assessment(dem);
        setAssessmentId(start.assessment_id);
        setSeed(start.seed);
        setMainQs(start.questions);
        setPhase("main");
      } catch (e) {
        console.error(e);
        router.push("/");
      }
    },
    [router]
  );

  const handleDemographicAnswer = (questionId: string, value: string) => {
    const updated = { ...demographicAnswers, [questionId]: value };
    setDemographicAnswers(updated);
    if (demographicIdx + 1 < demographicQs.length) {
      setDemographicIdx(demographicIdx + 1);
    } else {
      void startMainPhase(updated as V3DemographicAnswers);
    }
  };

  const showMilestone = useCallback(
    async (m: number) => {
      setPhase("milestone");
      setPendingMilestone(m);
      try {
        const res = await getV3Milestone(m, seed);
        setMilestoneText(res.text);
      } catch {
        setMilestoneText("Keep going!");
      }
    },
    [seed]
  );

  const submitAnswers = useCallback(
    async (allAnswers: Record<string, number>) => {
      if (!assessmentId) return;
      setPhase("submitting");
      try {
        await submitV3Assessment(assessmentId, allAnswers);
        router.push(`/results/${assessmentId}`);
      } catch (e) {
        console.error(e);
        alert("Failed to submit. Please try again.");
        setPhase("main");
      }
    },
    [assessmentId, router]
  );

  const handleMainAnswer = (questionId: string, value: number) => {
    const updated = { ...answers, [questionId]: value };
    setAnswers(updated);

    const totalAnswered = Object.keys(updated).length;
    const milestone = MILESTONE_THRESHOLDS.find((m) => m === totalAnswered);

    if (milestone) {
      void showMilestone(milestone);
      return;
    }

    if (mainIdx + 1 < mainQs.length) {
      setMainIdx(mainIdx + 1);
    } else {
      void submitAnswers(updated);
    }
  };

  const continueAfterMilestone = () => {
    setPhase("main");
    setPendingMilestone(null);
    if (mainIdx + 1 < mainQs.length) {
      setMainIdx(mainIdx + 1);
    } else {
      void submitAnswers(answers);
    }
  };

  // ============= Render phases =============

  if (phase === "loading") {
    return (
      <main className="min-h-screen bg-india-radial flex items-center justify-center">
        <p className="text-navy-text/70">🪔 Loading…</p>
      </main>
    );
  }

  if (phase === "demographic") {
    const q = demographicQs[demographicIdx];
    if (!q) return null;
    const progress = ((demographicIdx + 1) / 5) * 100;
    return (
      <main className="min-h-screen bg-india-radial flex flex-col">
        <div className="h-2 bg-saffron-100">
          <div
            className="h-full bg-gradient-to-r from-saffron-500 to-india-green-500 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex-1 flex items-center justify-center px-6 py-12">
          <AnimatePresence mode="wait">
            <motion.div
              key={demographicIdx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="max-w-xl w-full"
            >
              <div className="text-saffron-700 text-xs font-semibold uppercase tracking-widest mb-3">
                Question {demographicIdx + 1} of 5 · Quick start
              </div>
              <h2 className="text-2xl md:text-3xl font-bold text-navy-text mb-8">{q.text}</h2>
              <div className="grid gap-3">
                {q.options?.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => handleDemographicAnswer(q.id, opt.value)}
                    className="text-left px-6 py-4 bg-white rounded-2xl border-2 border-saffron-200 hover:border-india-green-400 hover:bg-india-green-50 transition-all font-medium text-navy-text"
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    );
  }

  if (phase === "milestone") {
    const m = pendingMilestone ?? 0;
    return (
      <main className="min-h-screen bg-india-hero flex flex-col items-center justify-center px-6 text-center">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="max-w-md"
        >
          <div className="text-6xl mb-6">🪔</div>
          <div className="text-7xl font-bold text-saffron-700 mb-4">{m}</div>
          <p className="text-xl text-navy-text font-medium mb-8">{milestoneText || "Keep going!"}</p>
          <button
            onClick={continueAfterMilestone}
            className="bg-india-green-500 hover:bg-india-green-600 text-white font-bold px-8 py-3 rounded-full transition-all shadow-lg"
          >
            Continue
          </button>
        </motion.div>
      </main>
    );
  }

  if (phase === "main") {
    const q = mainQs[mainIdx];
    if (!q) return null;
    const progress = ((5 + mainIdx + 1) / 45) * 100;
    return (
      <main className="min-h-screen bg-india-radial flex flex-col">
        <div className="h-2 bg-saffron-100">
          <div
            className="h-full bg-gradient-to-r from-saffron-500 to-india-green-500 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="flex-1 flex items-center justify-center px-6 py-12">
          <AnimatePresence mode="wait">
            <motion.div
              key={mainIdx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="max-w-xl w-full"
            >
              <div className="text-saffron-700 text-xs font-semibold uppercase tracking-widest mb-3">
                Question {5 + mainIdx + 1} of 45
              </div>
              <h2 className="text-xl md:text-2xl font-medium text-navy-text mb-8">{q.text}</h2>
              <div className="grid gap-2">
                {LIKERT_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => handleMainAnswer(q.id, opt.value)}
                    className="text-left px-6 py-3 bg-white rounded-xl border-2 border-saffron-200 hover:border-india-green-400 hover:bg-india-green-50 transition-all font-medium text-navy-text"
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    );
  }

  // submitting phase
  return (
    <main className="min-h-screen bg-india-radial flex items-center justify-center">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        className="text-5xl"
      >
        🪔
      </motion.div>
      <p className="ml-4 text-navy-text font-medium">Decoding your archetype…</p>
    </main>
  );
}
