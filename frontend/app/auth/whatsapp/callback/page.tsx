"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { finishWhatsAppOAuth, setAuth } from "@/lib/api";

function WhatsAppCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState("");
  const code = searchParams.get("code");
  const state = searchParams.get("state");

  useEffect(() => {
    if (!code) return;

    finishWhatsAppOAuth({ code, state: state || "" })
      .then((res) => {
        setAuth(res);
        router.replace("/profile");
      })
      .catch(() => setError("WhatsApp login failed"));
  }, [router, code, state]);

  return (
    <main className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-3xl shadow-xl border border-slate-100 p-8 text-center">
        {!error && code ? (
          <>
            <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4" />
            <p className="text-slate-600">Finalizing WhatsApp login...</p>
          </>
        ) : (
          <>
            <p className="text-red-500 mb-4">{error || "Missing WhatsApp callback parameters"}</p>
            <button
              onClick={() => router.replace("/profile")}
              className="bg-indigo-600 text-white px-5 py-2 rounded-full"
            >
              Back to profile
            </button>
          </>
        )}
      </div>
    </main>
  );
}

export default function WhatsAppCallbackPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-slate-50 flex items-center justify-center">
          <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
        </main>
      }
    >
      <WhatsAppCallbackContent />
    </Suspense>
  );
}
