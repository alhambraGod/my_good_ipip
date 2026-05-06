"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  getDemographicQuestions,
  startV3Assessment,
  submitV3Assessment,
  getV3Milestone,
  getV3AssessmentState,
  type V3Question,
  type V3DemographicAnswers,
} from "@/lib/v3-api";
import { useToast } from "@/components/Toast";
import { useLang } from "@/lib/i18n/LangContext";
import { fmt } from "@/lib/i18n/strings";
import {
  useAssessmentProgress,
  clearAssessmentProgress,
} from "@/lib/hooks/useAssessmentProgress";
import { useDigitKey } from "@/lib/hooks/useDigitKey";

const LIKERT_OPTIONS = [
  { value: 1, label: "Strongly Disagree", short: "1" },
  { value: 2, label: "Disagree", short: "2" },
  { value: 3, label: "Neutral", short: "3" },
  { value: 4, label: "Agree", short: "4" },
  { value: 5, label: "Strongly Agree", short: "5" },
];

const MILESTONE_THRESHOLDS = [10, 20, 30, 40];

type Phase = "loading" | "demographic" | "main" | "milestone" | "submitting";

export default function TestPage() {
  const router = useRouter();
  const toast = useToast();
  const { t, lang } = useLang();
  const { progress, update, reset } = useAssessmentProgress();

  const [phase, setPhase] = useState<Phase>("loading");
  const [demographicQs, setDemographicQs] = useState<V3Question[]>([]);
  const [mainQs, setMainQs] = useState<V3Question[]>([]);
  const [milestoneText, setMilestoneText] = useState<string>("");
  const [pendingMilestone, setPendingMilestone] = useState<number | null>(null);
  const [resumeOffered, setResumeOffered] = useState(false);

  const totalDemographic = demographicQs.length || 5;

  const startMainPhase = useCallback(
    async (dem: V3DemographicAnswers) => {
      setPhase("loading");
      try {
        const start = await startV3Assessment(dem);
        update({
          assessmentId: start.assessment_id,
          seed: start.seed,
          mainIdx: 0,
          mainAnswers: {},
        });
        setMainQs(start.questions);
        setPhase("main");
      } catch (e) {
        console.error(e);
        toast.push(t.test.cantStart, "error");
        router.push("/");
      }
    },
    [router, toast, update, t.test.cantStart],
  );

  useEffect(() => {
    let cancelled = false;
    getDemographicQuestions()
      .then((qs) => {
        if (cancelled) return;
        setDemographicQs(qs);
        const hasResumable =
          progress.assessmentId !== null ||
          Object.keys(progress.demographicAnswers).length > 0;
        if (hasResumable && !resumeOffered) {
          setResumeOffered(true);
        }
        if (progress.assessmentId !== null) {
          (async () => {
            try {
              const state = await getV3AssessmentState(progress.assessmentId!);
              update({ seed: state.seed });
              setMainQs(state.questions);
              setPhase("main");
            } catch {
              clearAssessmentProgress();
              setMainQs([]);
              setPhase("demographic");
              toast.push(t.test.resumeFailed, "info");
            }
          })();
          return;
        }
        setPhase("demographic");
      })
      .catch(() => {
        toast.push(t.test.networkErr, "error");
        router.push("/");
      });
    return () => {
      cancelled = true;
    };
  }, [progress.assessmentId, progress.demographicAnswers, resumeOffered, router, toast, update, t.test.networkErr, t.test.resumeFailed]);

  const handleDemographicAnswer = useCallback(
    (questionId: string, value: string) => {
      const updatedAnswers = { ...progress.demographicAnswers, [questionId]: value };
      const nextIdx = progress.demographicIdx + 1;
      update({
        demographicAnswers: updatedAnswers,
        demographicIdx: nextIdx < totalDemographic ? nextIdx : progress.demographicIdx,
      });
      if (nextIdx >= totalDemographic) {
        void startMainPhase(updatedAnswers as unknown as V3DemographicAnswers);
      }
    },
    [progress.demographicAnswers, progress.demographicIdx, totalDemographic, update, startMainPhase],
  );

  const goBackDemographic = useCallback(() => {
    if (progress.demographicIdx === 0) return;
    update({ demographicIdx: progress.demographicIdx - 1 });
  }, [progress.demographicIdx, update]);

  const showMilestone = useCallback(
    async (m: number) => {
      setPhase("milestone");
      setPendingMilestone(m);
      try {
        const res = await getV3Milestone(m, progress.seed, lang);
        setMilestoneText(res.text);
      } catch {
        setMilestoneText("Keep going!");
      }
    },
    [progress.seed, lang],
  );

  const submitAnswers = useCallback(
    async (allAnswers: Record<string, number>) => {
      if (!progress.assessmentId) return;
      setPhase("submitting");
      try {
        await submitV3Assessment(progress.assessmentId, allAnswers);
        const aid = progress.assessmentId;
        clearAssessmentProgress();
        router.push(`/results/${aid}`);
      } catch (e) {
        console.error(e);
        toast.push(t.test.submitFailed, "error");
        setPhase("main");
      }
    },
    [progress.assessmentId, router, toast, t.test.submitFailed],
  );

  const handleMainAnswer = useCallback(
    (questionId: string, value: number) => {
      const updatedAnswers = { ...progress.mainAnswers, [questionId]: value };
      const nextIdx = progress.mainIdx + 1;
      update({
        mainAnswers: updatedAnswers,
        mainIdx: nextIdx < mainQs.length ? nextIdx : progress.mainIdx,
      });

      const totalAnswered = Object.keys(updatedAnswers).length;
      const milestone = MILESTONE_THRESHOLDS.find((m) => m === totalAnswered);
      if (milestone) {
        void showMilestone(milestone);
        return;
      }
      if (nextIdx >= mainQs.length) {
        void submitAnswers(updatedAnswers);
      }
    },
    [progress.mainAnswers, progress.mainIdx, mainQs.length, update, showMilestone, submitAnswers],
  );

  const goBackMain = useCallback(() => {
    if (progress.mainIdx === 0) return;
    const prevIdx = progress.mainIdx - 1;
    const prevQId = mainQs[prevIdx]?.id;
    if (!prevQId) return;
    const updatedAnswers = { ...progress.mainAnswers };
    delete updatedAnswers[prevQId];
    update({ mainIdx: prevIdx, mainAnswers: updatedAnswers });
  }, [progress.mainIdx, progress.mainAnswers, mainQs, update]);

  const continueAfterMilestone = useCallback(() => {
    setPhase("main");
    setPendingMilestone(null);
    if (progress.mainIdx + 1 >= mainQs.length) {
      void submitAnswers(progress.mainAnswers);
    } else {
      update({ mainIdx: progress.mainIdx + 1 });
    }
  }, [mainQs.length, progress.mainIdx, progress.mainAnswers, submitAnswers, update]);

  const currentDemographicQ = demographicQs[progress.demographicIdx];
  const currentMainQ = mainQs[progress.mainIdx];

  useDigitKey(
    Math.max(currentDemographicQ?.options?.length ?? 0, 1),
    (n) => {
      if (phase !== "demographic" || !currentDemographicQ) return;
      const opt = currentDemographicQ.options?.[n - 1];
      if (opt) handleDemographicAnswer(currentDemographicQ.id, opt.value);
    },
    phase === "demographic",
  );

  useDigitKey(
    5,
    (n) => {
      if (phase !== "main" || !currentMainQ) return;
      handleMainAnswer(currentMainQ.id, n);
    },
    phase === "main",
  );

  const handleResetAndRestart = useCallback(() => {
    reset();
    setMainQs([]);
    setPhase("demographic");
    setResumeOffered(false);
  }, [reset]);

  const overallProgress = useMemo(() => {
    if (phase === "demographic") return ((progress.demographicIdx + 1) / totalDemographic) * 100;
    if (phase === "main") {
      const answered = Object.keys(progress.mainAnswers).length;
      return ((5 + answered) / 45) * 100;
    }
    return 100;
  }, [phase, progress.demographicIdx, progress.mainAnswers, totalDemographic]);

  if (phase === "loading") {
    return (
      <main className="min-h-screen bg-india-radial flex items-center justify-center">
        <p className="text-navy-text/70">🪔 Loading…</p>
      </main>
    );
  }

  if (phase === "demographic") {
    const q = currentDemographicQ;
    if (!q) return null;
    return (
      <main className="min-h-screen bg-india-radial flex flex-col">
        <ProgressBar pct={overallProgress} />
        <div className="flex-1 flex items-center justify-center px-6 py-12">
          <AnimatePresence mode="wait">
            <motion.div
              key={progress.demographicIdx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="max-w-xl w-full"
            >
              <TopBar
                left={`Question ${progress.demographicIdx + 1} of ${totalDemographic} · Quick start`}
                onBack={progress.demographicIdx > 0 ? goBackDemographic : undefined}
                onRestart={resumeOffered ? handleResetAndRestart : undefined}
              />
              <h2 className="text-2xl md:text-3xl font-bold text-navy-text mb-6">{q.text}</h2>
              <div className="grid gap-3">
                {q.options?.map((opt, idx) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => handleDemographicAnswer(q.id, opt.value)}
                    className={`text-left flex items-center gap-3 px-5 py-4 bg-white rounded-2xl border-2 transition-all font-medium text-navy-text ${
                      progress.demographicAnswers[q.id] === opt.value
                        ? "border-india-green-500 bg-india-green-50"
                        : "border-saffron-200 hover:border-india-green-400 hover:bg-india-green-50"
                    }`}
                  >
                    <span className="hidden md:inline-flex w-7 h-7 rounded-md bg-saffron-100 text-saffron-700 text-xs font-bold items-center justify-center shrink-0">
                      {idx + 1}
                    </span>
                    <span>{opt.label}</span>
                  </button>
                ))}
              </div>
              <p className="hidden md:block mt-4 text-xs text-navy-text/40">
                {fmt(t.test.tipKeyboard, { n: q.options?.length ?? 0 })}
              </p>
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
            type="button"
            onClick={continueAfterMilestone}
            className="bg-india-green-500 hover:bg-india-green-600 text-white font-bold px-8 py-3 rounded-full transition-all shadow-lg"
          >
            {t.test.continue}
          </button>
        </motion.div>
      </main>
    );
  }

  if (phase === "main") {
    const q = currentMainQ;
    if (!q) return null;
    const selected = progress.mainAnswers[q.id];
    return (
      <main className="min-h-screen bg-india-radial flex flex-col">
        <ProgressBar pct={overallProgress} />
        <div className="flex-1 flex items-center justify-center px-6 py-12">
          <AnimatePresence mode="wait">
            <motion.div
              key={progress.mainIdx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="max-w-xl w-full"
            >
              <TopBar
                left={`Question ${5 + progress.mainIdx + 1} of 45`}
                onBack={progress.mainIdx > 0 ? goBackMain : undefined}
                onRestart={handleResetAndRestart}
              />
              <h2 className="text-xl md:text-2xl font-medium text-navy-text mb-6">{q.text}</h2>
              <div className="grid gap-2">
                {LIKERT_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => handleMainAnswer(q.id, opt.value)}
                    className={`text-left flex items-center gap-3 px-5 py-3 bg-white rounded-xl border-2 transition-all font-medium text-navy-text ${
                      selected === opt.value
                        ? "border-india-green-500 bg-india-green-50"
                        : "border-saffron-200 hover:border-india-green-400 hover:bg-india-green-50"
                    }`}
                  >
                    <span className="hidden md:inline-flex w-7 h-7 rounded-md bg-saffron-100 text-saffron-700 text-xs font-bold items-center justify-center shrink-0">
                      {opt.short}
                    </span>
                    <span>{opt.label}</span>
                  </button>
                ))}
              </div>
              <p className="hidden md:block mt-4 text-xs text-navy-text/40">
                {t.test.tipKeyboardLikert}
              </p>
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-india-radial flex items-center justify-center">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        className="text-5xl"
      >
        🪔
      </motion.div>
      <p className="ml-4 text-navy-text font-medium">{t.test.decoding}</p>
    </main>
  );
}

function ProgressBar({ pct }: { pct: number }) {
  return (
    <div className="h-2 bg-saffron-100">
      <div
        className="h-full bg-gradient-to-r from-saffron-500 to-india-green-500 transition-all"
        style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
      />
    </div>
  );
}

function TopBar({
  left,
  onBack,
  onRestart,
}: {
  left: string;
  onBack?: () => void;
  onRestart?: () => void;
}) {
  const { t } = useLang();
  return (
    <div className="flex items-center justify-between mb-4 gap-3">
      <div className="text-saffron-700 text-xs font-semibold uppercase tracking-widest">
        {left}
      </div>
      <div className="flex gap-2">
        {onBack && (
          <button
            type="button"
            onClick={onBack}
            className="text-xs font-semibold text-navy-text/60 hover:text-navy-text px-3 py-1 rounded-full border border-navy-text/15 hover:bg-white"
          >
            {t.test.back}
          </button>
        )}
        {onRestart && (
          <button
            type="button"
            onClick={onRestart}
            className="text-xs font-semibold text-navy-text/45 hover:text-red-600 px-3 py-1 rounded-full border border-navy-text/10 hover:bg-white"
          >
            {t.test.restart}
          </button>
        )}
      </div>
    </div>
  );
}
