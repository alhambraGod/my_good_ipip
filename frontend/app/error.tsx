"use client";

import Link from "next/link";
import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    if (typeof window !== "undefined") {
      console.error("Unhandled error:", error);
    }
  }, [error]);

  return (
    <main className="min-h-screen flex items-center justify-center bg-india-radial px-6 py-20 text-center">
      <div className="max-w-md">
        <div className="text-6xl mb-4">🪔</div>
        <p className="text-xs font-bold uppercase tracking-widest text-saffron-700 mb-2">
          Something cracked
        </p>
        <h1 className="text-3xl font-black text-navy-text mb-3">We hit a bump</h1>
        <p className="text-navy-text/70 mb-2">
          {error?.message || "Unexpected error."}
        </p>
        {error?.digest && (
          <p className="text-xs text-navy-text/40 mb-6">ref: {error.digest}</p>
        )}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            type="button"
            onClick={reset}
            className="bg-india-green-500 hover:bg-india-green-600 text-white font-bold px-6 py-3 rounded-full"
          >
            Try again
          </button>
          <Link
            href="/"
            className="bg-white text-navy-text font-bold px-6 py-3 rounded-full border border-saffron-700/20 hover:bg-saffron-50"
          >
            Go home
          </Link>
        </div>
      </div>
    </main>
  );
}
