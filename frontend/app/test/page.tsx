"use client";

import { Suspense, useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  fetchQuestions,
  submitAssessment,
  submitAssessmentV2,
  type Question,
} from "@/lib/api";

const LIKERT_OPTIONS = [
  { value: 1, label: "Strongly Disagree" },
  { value: 2, label: "Disagree" },
  { value: 3, label: "Neutral" },
  { value: 4, label: "Agree" },
  { value: 5, label: "Strongly Agree" },
];

function TestContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const assessmentId = searchParams.get("assessment_id");
  const sessionToken = searchParams.get("session_token");

  const [questions, setQuestions] = useState<Question[]>([]);
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [direction, setDirection] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadQuestions() {
      try {
        if (assessmentId) {
          const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/assessment/${assessmentId}/questions`
          );
          if (!res.ok) throw new Error("Failed personalized fetch");
          const q = await res.json();
          setQuestions(q);
        } else {
          const q = await fetchQuestions();
          setQuestions(q);
        }
      } catch {
        setQuestions([]);
      } finally {
        setLoading(false);
      }
    }

    loadQuestions();
  }, [assessmentId]);

  const question = questions[current];
  const total = questions.length;
  const answered = Object.keys(answers).length;
  const progress = total > 0 ? (answered / total) * 100 : 0;
  const allAnswered = answered >= total;

  const findNextUnanswered = useCallback(
    (from: number, newAnswers: Record<string, number>): number | null => {
      for (let i = 1; i <= total; i++) {
        const idx = (from + i) % total;
        if (!(questions[idx].id in newAnswers)) return idx;
      }
      return null;
    },
    [questions, total]
  );

  const firstUnansweredIndex = useCallback((): number | null => {
    for (let i = 0; i < total; i++) {
      if (!(questions[i].id in answers)) return i;
    }
    return null;
  }, [questions, answers, total]);

  const handleSubmit = useCallback(
    async (finalAnswers: Record<string, number>) => {
      setSubmitting(true);
      try {
        const result = assessmentId
          ? await submitAssessmentV2({
              assessment_id: assessmentId,
              session_token: sessionToken || undefined,
              answers: finalAnswers,
            })
          : await submitAssessment(finalAnswers);
        router.push(`/analyzing?id=${result.id}`);
      } catch {
        setSubmitting(false);
      }
    },
    [router, assessmentId, sessionToken]
  );

  const handleSelect = useCallback(
    async (value: number) => {
      if (!question || submitting) return;
      const newAnswers = { ...answers, [question.id]: value };
      setAnswers(newAnswers);

      if (Object.keys(newAnswers).length >= total) {
        setTimeout(() => handleSubmit(newAnswers), 300);
        return;
      }

      const next = findNextUnanswered(current, newAnswers);
      if (next !== null) {
        setTimeout(() => {
          setDirection(next > current ? 1 : -1);
          setCurrent(next);
        }, 300);
      }
    },
    [question, answers, current, total, submitting, findNextUnanswered, handleSubmit]
  );

  const goBack = () => {
    if (current > 0) {
      setDirection(-1);
      setCurrent((c) => c - 1);
    }
  };

  const skip = () => {
    if (current < total - 1) {
      setDirection(1);
      setCurrent((c) => c + 1);
    }
  };

  const goToStart = () => {
    if (current !== 0) {
      setDirection(-1);
      setCurrent(0);
    }
  };

  const goToFirstUnanswered = () => {
    const idx = firstUnansweredIndex();
    if (idx !== null && idx !== current) {
      setDirection(idx > current ? 1 : -1);
      setCurrent(idx);
    }
  };

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-500">Loading questions...</p>
        </div>
      </main>
    );
  }

  if (submitting) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-500">Submitting your responses...</p>
        </div>
      </main>
    );
  }

  if (!question) return null;

  return (
    <main className="min-h-screen bg-slate-50 flex flex-col">
      {/* Progress bar */}
      <div className="bg-white border-b border-slate-100 px-4 py-3 sticky top-0 z-20">
        <div className="max-w-lg mx-auto">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-600">
              Question {current + 1} of {total}
            </span>
            <span className="text-sm text-slate-400">
              {answered}/{total} answered
            </span>
          </div>
          <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Question area */}
      <div className="flex-1 flex items-center justify-center px-4 py-8">
        <div className="max-w-lg w-full">
          <AnimatePresence mode="wait" custom={direction}>
            <motion.div
              key={question.id}
              custom={direction}
              initial={{ opacity: 0, x: direction * 60 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: direction * -60 }}
              transition={{ duration: 0.25 }}
            >
              {/* Dimension badge */}
              <div className="text-center mb-2">
                <span className="inline-block text-xs font-medium text-indigo-500 bg-indigo-50 px-3 py-1 rounded-full capitalize">
                  {question.dimension.replace("_", " ")}
                </span>
              </div>

              {/* Question text */}
              <h2 className="text-xl md:text-2xl font-semibold text-slate-800 text-center mb-8 leading-relaxed">
                {question.text}
              </h2>

              {/* Likert options */}
              <div className="space-y-3">
                {LIKERT_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => handleSelect(opt.value)}
                    className={`likert-btn ${
                      answers[question.id] === opt.value ? "selected" : ""
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </motion.div>
          </AnimatePresence>

          {/* Navigation */}
          <div className="flex items-center justify-between mt-8">
            <div className="flex items-center gap-4">
              <button
                onClick={goToStart}
                disabled={current === 0}
                className="text-sm text-slate-400 hover:text-slate-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                &#x21E4; Start
              </button>
              <button
                onClick={goBack}
                disabled={current === 0}
                className="text-sm text-slate-400 hover:text-slate-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                &larr; Back
              </button>
            </div>
            <button
              onClick={goToFirstUnanswered}
              disabled={allAnswered}
              className="text-sm font-medium text-indigo-500 hover:text-indigo-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              {allAnswered ? "All answered" : "Next unanswered"}
            </button>
            <button
              onClick={skip}
              disabled={current >= total - 1}
              className="text-sm text-slate-400 hover:text-slate-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              Skip &rarr;
            </button>
          </div>

          {/* Submit button when all answered */}
          {allAnswered && (
            <div className="mt-6 text-center">
              <button
                onClick={() => handleSubmit(answers)}
                className="px-8 py-3 bg-gradient-to-r from-indigo-500 to-purple-500 text-white font-semibold rounded-full shadow-lg hover:shadow-xl transition-all"
              >
                Submit All Answers
              </button>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

export default function TestPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen flex items-center justify-center bg-slate-50">
          <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
        </main>
      }
    >
      <TestContent />
    </Suspense>
  );
}
