"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

export default function LandingPage() {
  const [stats, setStats] = useState({ total_assessments: 1247, today_assessments: 47 });

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001"}/api/stats`)
      .then((r) => r.json())
      .then(setStats)
      .catch(() => {});
  }, []);

  return (
    <main className="flex flex-col min-h-screen">
      {/* Hero */}
      <section className="bg-india-hero px-6 py-20 md:py-28 text-center relative overflow-hidden">
        <div className="absolute top-6 left-6 text-3xl">🪔</div>
        <div className="relative z-10 max-w-3xl mx-auto">
          <div className="text-xs font-semibold tracking-[0.25em] uppercase text-saffron-700 mb-4">
            Indian-built personality + career mapping
          </div>
          <h1 className="text-4xl md:text-6xl font-bold leading-tight mb-6 text-navy-text">
            Find Your <br />
            <span className="bg-clip-text text-transparent bg-gradient-to-br from-saffron-700 to-india-green-500">
              Indian Career DNA
            </span>
          </h1>
          <p className="text-lg md:text-xl text-navy-text/80 mb-8 max-w-2xl mx-auto">
            45 questions. 5 minutes. Built on Holland RIASEC + Big Five (OCEAN). Tuned for Indian Gen-Z reality —
            Bangalore IT, Marwari hustle, Sharma ji&apos;s beta, EMI math, all of it.
          </p>
          <Link
            href="/test"
            className="inline-block bg-india-green-500 hover:bg-india-green-600 text-white font-bold text-lg px-10 py-4 rounded-full transition-all shadow-lg hover:shadow-xl hover:scale-105"
          >
            Start Free Test →
          </Link>
          <p className="mt-6 text-saffron-800 text-sm font-medium">
            {stats.today_assessments.toLocaleString()}+ Indians took the test today · No login needed to start
          </p>
        </div>
      </section>

      {/* What you get */}
      <section className="bg-cream px-6 py-16">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12 text-navy-text">
            What you get
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                emoji: "🎯",
                title: "Your archetype",
                desc: "One of 24 hand-curated Indian personality cells (e.g., The 3AM Chai Philosopher). Built on Holland's hexagon theory + IBTI Indian context.",
              },
              {
                emoji: "💼",
                title: "Career match",
                desc: "5+ Indian career paths matched to your archetype, with real companies (Razorpay, Swiggy, TCS, Marwari business families) and lakh-based salary ranges.",
              },
              {
                emoji: "📤",
                title: "WhatsApp-ready share",
                desc: "Pre-written share lines + share image so your friends can take the test and find their archetype.",
              },
            ].map((f) => (
              <div
                key={f.title}
                className="bg-white rounded-2xl p-8 border border-saffron-200/50 hover:shadow-xl transition-shadow"
              >
                <div className="text-4xl mb-4">{f.emoji}</div>
                <h3 className="text-xl font-semibold mb-3 text-navy-text">
                  {f.title}
                </h3>
                <p className="text-navy-text/70 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-gradient-to-br from-india-green-500 to-india-green-700 text-white py-16 px-6 text-center">
        <h2 className="text-3xl font-bold mb-4">
          Ready to find your archetype?
        </h2>
        <p className="text-india-green-50 mb-8 max-w-lg mx-auto">
          5 minutes. No login. ₹49 if you want the full report (first 1,000 users).
        </p>
        <Link
          href="/test"
          className="inline-block bg-white text-india-green-700 font-bold text-lg px-10 py-4 rounded-full hover:bg-saffron-50 transition-all shadow-lg"
        >
          Start Now
        </Link>
      </section>

      {/* Footer */}
      <footer className="bg-navy-text text-saffron-100/60 py-8 px-6 text-center text-sm">
        <p>&copy; 2026 CareerDNA · For Indian Gen-Z, by Indians.</p>
        <p className="mt-1 text-saffron-100/40">
          Built on IPIP-NEO Big Five + Holland RIASEC personality science.
        </p>
      </footer>
    </main>
  );
}
