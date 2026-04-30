import Link from "next/link";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";

export default function NotFound() {
  return (
    <>
      <SiteHeader minimal />
      <main className="flex-1 bg-india-radial flex items-center justify-center px-6 py-20 text-center">
        <div className="max-w-md">
          <div className="text-6xl mb-4">🪔</div>
          <p className="text-xs font-bold uppercase tracking-widest text-saffron-700 mb-2">
            404 · arre yaar
          </p>
          <h1 className="text-3xl font-black text-navy-text mb-3">
            This page wandered off
          </h1>
          <p className="text-navy-text/70 mb-8">
            Maybe the link is old, maybe we deleted it. Either way — try one of
            these.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/"
              className="bg-india-green-500 hover:bg-india-green-600 text-white font-bold px-6 py-3 rounded-full"
            >
              Go home
            </Link>
            <Link
              href="/test"
              className="bg-white text-navy-text font-bold px-6 py-3 rounded-full border border-saffron-700/20 hover:bg-saffron-50"
            >
              Take the test
            </Link>
          </div>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
