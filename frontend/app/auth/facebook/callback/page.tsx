"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { finishFacebookOAuth, setAuth } from "@/lib/api";
import { consumeOAuthNextPath } from "@/lib/oauth-return";

function FacebookCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState("");
  const code = searchParams.get("code");
  const state = searchParams.get("state");

  useEffect(() => {
    if (!code) return;

    finishFacebookOAuth({ code, state: state || "" })
      .then((res) => {
        setAuth(res);
        router.replace(consumeOAuthNextPath("/profile"));
      })
      .catch(() => setError("Facebook login failed"));
  }, [router, code, state]);

  return (
    <main className="min-h-screen bg-india-radial flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-3xl shadow-xl border border-saffron-100 p-8 text-center">
        {!error && code ? (
          <>
            <div className="w-12 h-12 border-4 border-saffron-200 border-t-saffron-600 rounded-full animate-spin mx-auto mb-4" />
            <p className="text-navy-text/70">Finalizing Facebook login…</p>
          </>
        ) : (
          <>
            <p className="text-red-600 mb-4">{error || "Missing Facebook callback parameters"}</p>
            <button
              type="button"
              onClick={() => router.replace("/")}
              className="bg-india-green-600 text-white px-5 py-2 rounded-full"
            >
              Back home
            </button>
          </>
        )}
      </div>
    </main>
  );
}

export default function FacebookCallbackPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen flex items-center justify-center bg-india-radial">
          <div className="w-12 h-12 border-4 border-saffron-200 border-t-saffron-600 rounded-full animate-spin" />
        </main>
      }
    >
      <FacebookCallbackContent />
    </Suspense>
  );
}
