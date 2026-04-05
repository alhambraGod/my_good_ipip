"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  bootstrapProfile,
  submitProfileSupplement,
  startPersonalizedAssessment,
  startTwitterOAuth,
  startGoogleOAuth,
  startWhatsAppOAuth,
  emailRegister,
  emailLogin,
  devLogin,
  setAuth,
  type AuthResponse,
} from "@/lib/api";

type Provider = "x" | "telegram" | "manual";
type AuthMode = "login" | "register";

const OPTIONS = {
  career_stage: ["student", "fresher", "mid", "senior"],
  industry: ["it", "finance", "marketing", "operations", "general"],
  work_mode: ["onsite", "hybrid", "remote"],
  career_goal: ["growth", "switch", "stability", "startup"],
  stress_source: ["uncertainty", "family_pressure", "workload", "money"],
  communication_style: ["direct", "balanced", "reserved"],
};

export default function ProfilePage() {
  const router = useRouter();
  const telegramRef = useRef<HTMLDivElement | null>(null);

  const [provider, setProvider] = useState<Provider>("manual");
  const [handle, setHandle] = useState("");
  const [consent, setConsent] = useState(false);
  const [sessionToken, setSessionToken] = useState("");
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Email auth
  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");

  // Dev login
  const [devEmail, setDevEmail] = useState("dev@dev");
  const [devPassword, setDevPassword] = useState("dev@dev");

  const [answers, setAnswers] = useState<Record<string, string>>({
    career_stage: "",
    industry: "",
    work_mode: "",
    career_goal: "",
    stress_source: "",
    communication_style: "",
  });
  const [freeText, setFreeText] = useState<Record<string, string>>({
    city: "",
    role_title: "",
  });

  const botUsername = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME || "";
  const showDevLogin = process.env.NEXT_PUBLIC_DEV_MODE === "true";

  useEffect(() => {
    const token = localStorage.getItem("mindiq_session_token");
    const p = localStorage.getItem("mindiq_provider");
    const h = localStorage.getItem("mindiq_handle");

    if (token) {
      setSessionToken(token);
      setStep(2);
    }
    if (p === "x" || p === "telegram" || p === "manual") {
      setProvider(p);
    }
    if (h) {
      setHandle(h);
    }
  }, []);

  useEffect(() => {
    if (provider !== "telegram" || !botUsername || !telegramRef.current || step !== 1) return;

    telegramRef.current.innerHTML = "";
    const script = document.createElement("script");
    script.async = true;
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.setAttribute("data-telegram-login", botUsername);
    script.setAttribute("data-size", "large");
    script.setAttribute("data-auth-url", `${window.location.origin}/auth/telegram/callback`);
    script.setAttribute("data-request-access", "write");
    telegramRef.current.appendChild(script);
  }, [provider, botUsername, step]);

  const canBootstrap = useMemo(
    () => consent && (provider === "manual" || !!handle.trim()),
    [consent, provider, handle]
  );
  const canSubmitSupplement = useMemo(() => Object.values(answers).every(Boolean), [answers]);

  const handleAuthSuccess = (res: AuthResponse) => {
    setAuth(res);
    setSessionToken(res.session_token);
    setStep(2);
  };

  // --- Auth handlers ---

  const onEmailAuth = async () => {
    if (loading) return;
    setLoading(true);
    setError("");
    try {
      const res =
        authMode === "register"
          ? await emailRegister({ email, password, name: name || undefined })
          : await emailLogin({ email, password });
      handleAuthSuccess(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  const onGoogleLogin = async () => {
    setError("");
    try {
      const data = await startGoogleOAuth();
      window.location.href = data.auth_url;
    } catch {
      setError("Unable to start Google login. Please check OAuth config.");
    }
  };

  const onWhatsAppLogin = async () => {
    setError("");
    try {
      const data = await startWhatsAppOAuth();
      window.location.href = data.auth_url;
    } catch {
      setError("Unable to start WhatsApp login. Please check OAuth config.");
    }
  };

  const onTwitterLogin = async () => {
    setError("");
    try {
      const data = await startTwitterOAuth();
      window.location.href = data.auth_url;
    } catch {
      setError("Unable to start Twitter login. Please check OAuth config.");
    }
  };

  const onDevLogin = async () => {
    if (!showDevLogin || loading) return;
    setLoading(true);
    setError("");
    try {
      const res = await devLogin({ email: devEmail, password: devPassword });
      handleAuthSuccess(res);
    } catch {
      setError("Dev login failed.");
    } finally {
      setLoading(false);
    }
  };

  const onBootstrap = async () => {
    if (!canBootstrap || loading) return;
    setLoading(true);
    setError("");
    try {
      const data = await bootstrapProfile({
        provider,
        handle: handle.trim() || undefined,
        consent_flags: { profile_collection: true },
      });
      setSessionToken(data.session_token);
      localStorage.setItem("mindiq_session_token", data.session_token);
      localStorage.setItem("mindiq_provider", provider);
      if (handle.trim()) localStorage.setItem("mindiq_handle", handle.trim());
      setStep(data.needs_manual_questions ? 2 : 3);
      if (!data.needs_manual_questions) {
        await onStart(data.session_token);
      }
    } catch {
      setError("Unable to start profile setup. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const onSubmitSupplement = async () => {
    if (!sessionToken || !canSubmitSupplement || loading) return;
    setLoading(true);
    setError("");
    try {
      await submitProfileSupplement({
        session_token: sessionToken,
        answers,
        free_text_fields: freeText,
      });
      setStep(3);
      await onStart(sessionToken);
    } catch {
      setError("Unable to save profile answers. Please try again.");
      setLoading(false);
    }
  };

  const onStart = async (token: string) => {
    try {
      const result = await startPersonalizedAssessment(token);
      router.push(`/test?assessment_id=${result.assessment_id}&session_token=${token}`);
    } catch {
      setError("Unable to prepare personalized questions. Please retry.");
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-12">
      <div className="max-w-lg w-full">
        <div className="bg-white rounded-3xl shadow-xl p-8 md:p-10 border border-slate-100">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold gradient-text mb-2">MindIQ</h1>
            <p className="text-slate-500 text-sm">Personalization Setup</p>
          </div>

          {step === 1 && (
            <>
              <h2 className="text-2xl font-bold text-slate-800 mb-4 text-center">
                Sign in to continue
              </h2>
              <p className="text-sm text-slate-500 text-center mb-6">
                Create an account or sign in to save your results.
              </p>

              {/* Email auth form */}
              <div className="mb-6">
                <div className="flex rounded-xl border border-slate-200 overflow-hidden mb-4">
                  <button
                    type="button"
                    onClick={() => setAuthMode("login")}
                    className={`flex-1 py-2.5 text-sm font-medium transition-colors ${
                      authMode === "login"
                        ? "bg-indigo-600 text-white"
                        : "bg-white text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    Login
                  </button>
                  <button
                    type="button"
                    onClick={() => setAuthMode("register")}
                    className={`flex-1 py-2.5 text-sm font-medium transition-colors ${
                      authMode === "register"
                        ? "bg-indigo-600 text-white"
                        : "bg-white text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    Register
                  </button>
                </div>

                <div className="space-y-3">
                  {authMode === "register" && (
                    <input
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Name (optional)"
                      className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                    />
                  )}
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Email"
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Password"
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  />
                  <button
                    disabled={!email || !password || loading}
                    onClick={onEmailAuth}
                    className="w-full bg-indigo-600 text-white font-semibold py-3 rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading
                      ? "Please wait..."
                      : authMode === "register"
                        ? "Create Account"
                        : "Sign In"}
                  </button>
                </div>
              </div>

              {/* Divider */}
              <div className="flex items-center gap-3 mb-6">
                <div className="flex-1 h-px bg-slate-200" />
                <span className="text-xs text-slate-400">or continue with</span>
                <div className="flex-1 h-px bg-slate-200" />
              </div>

              {/* Social login buttons */}
              <div className="space-y-3 mb-6">
                <button
                  onClick={onGoogleLogin}
                  className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-xl border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition-colors font-medium"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                  </svg>
                  Sign in with Google
                </button>

                <button
                  onClick={onWhatsAppLogin}
                  className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-xl border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition-colors font-medium"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="#25D366">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413z" />
                  </svg>
                  Continue with WhatsApp
                </button>

                <button
                  onClick={onTwitterLogin}
                  className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-xl border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 transition-colors font-medium"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                  </svg>
                  Sign in with X
                </button>

                {provider === "telegram" && botUsername && (
                  <div ref={telegramRef} className="flex justify-center" />
                )}
              </div>

              {/* Manual continue option */}
              <div className="border-t border-slate-100 pt-5">
                <label className="flex items-start gap-3 mb-4 text-sm text-slate-600">
                  <input
                    type="checkbox"
                    checked={consent}
                    onChange={(e) => setConsent(e.target.checked)}
                    className="mt-0.5"
                  />
                  <span>
                    I agree to use my profile inputs for personalized question
                    selection.
                  </span>
                </label>

                <button
                  disabled={!consent || loading}
                  onClick={() => {
                    setProvider("manual");
                    onBootstrap();
                  }}
                  className="w-full text-sm text-slate-500 hover:text-slate-700 py-2 transition-colors disabled:opacity-50"
                >
                  Continue without account &rarr;
                </button>
              </div>

              {showDevLogin && (
                <div className="mt-6 border-t border-slate-100 pt-6">
                  <p className="text-sm font-semibold text-slate-700 mb-3">
                    Dev Tester Login
                  </p>
                  <div className="space-y-3">
                    <input
                      value={devEmail}
                      onChange={(e) => setDevEmail(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-slate-200"
                      placeholder="dev email"
                    />
                    <input
                      type="password"
                      value={devPassword}
                      onChange={(e) => setDevPassword(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-slate-200"
                      placeholder="dev password"
                    />
                    <button
                      onClick={onDevLogin}
                      disabled={loading}
                      className="w-full bg-emerald-600 text-white font-semibold py-3 rounded-xl disabled:opacity-50"
                    >
                      Login as Dev Tester
                    </button>
                  </div>
                </div>
              )}
            </>
          )}

          {step === 2 && (
            <>
              <h2 className="text-2xl font-bold text-slate-800 mb-4 text-center">
                Quick profile questions
              </h2>
              <p className="text-sm text-slate-500 text-center mb-6">
                Answer these to generate your personalized 40-question set.
              </p>

              <div className="space-y-4 mb-6">
                {Object.entries(OPTIONS).map(([key, vals]) => (
                  <div key={key}>
                    <label className="text-sm font-medium text-slate-700 mb-1 block capitalize">
                      {key.replaceAll("_", " ")}
                    </label>
                    <select
                      value={answers[key] || ""}
                      onChange={(e) =>
                        setAnswers((prev) => ({ ...prev, [key]: e.target.value }))
                      }
                      className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-300"
                    >
                      <option value="">Select...</option>
                      {vals.map((v) => (
                        <option key={v} value={v}>
                          {v}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}

                <div>
                  <label className="text-sm font-medium text-slate-700 mb-1 block">
                    City (optional)
                  </label>
                  <input
                    value={freeText.city || ""}
                    onChange={(e) =>
                      setFreeText((p) => ({ ...p, city: e.target.value }))
                    }
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700 mb-1 block">
                    Current role (optional)
                  </label>
                  <input
                    value={freeText.role_title || ""}
                    onChange={(e) =>
                      setFreeText((p) => ({ ...p, role_title: e.target.value }))
                    }
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                  />
                </div>
              </div>

              <button
                disabled={!canSubmitSupplement || loading}
                onClick={onSubmitSupplement}
                className="w-full bg-indigo-600 text-white font-bold text-lg py-4 rounded-2xl hover:bg-indigo-700 transition-colors shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Generating questions..." : "Generate Personalized Test"}
              </button>
            </>
          )}

          {step === 3 && (
            <div className="text-center py-8">
              <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4" />
              <p className="text-slate-600">
                Preparing your personalized questionnaire...
              </p>
            </div>
          )}

          {error && (
            <p className="text-red-500 text-sm text-center mt-4">{error}</p>
          )}

          <Link
            href="/start"
            className="block text-center mt-5 text-sm text-slate-400 hover:text-slate-600 transition-colors"
          >
            &larr; Back
          </Link>
        </div>
      </div>
    </main>
  );
}
