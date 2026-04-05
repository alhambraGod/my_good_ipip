"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { finishTelegramOAuth, setAuth } from "@/lib/api";

function TelegramCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState("");
  const id = searchParams.get("id");
  const auth_date = searchParams.get("auth_date");
  const hash = searchParams.get("hash");

  useEffect(() => {
    if (!id || !auth_date || !hash) {
      return;
    }

    finishTelegramOAuth({
      id,
      first_name: searchParams.get("first_name") || undefined,
      last_name: searchParams.get("last_name") || undefined,
      username: searchParams.get("username") || undefined,
      photo_url: searchParams.get("photo_url") || undefined,
      auth_date,
      hash,
    })
      .then((res) => {
        setAuth(res);
        router.replace("/profile");
      })
      .catch(() => setError("Telegram login failed"));
  }, [router, searchParams, id, auth_date, hash]);

  return (
    <main className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-3xl shadow-xl border border-slate-100 p-8 text-center">
        {!error && id && auth_date && hash ? (
          <>
            <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4" />
            <p className="text-slate-600">Finalizing Telegram login...</p>
          </>
        ) : (
          <>
            <p className="text-red-500 mb-4">{error || "Missing Telegram callback parameters"}</p>
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

export default function TelegramCallbackPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-slate-50 flex items-center justify-center">
          <div className="w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
        </main>
      }
    >
      <TelegramCallbackContent />
    </Suspense>
  );
}
