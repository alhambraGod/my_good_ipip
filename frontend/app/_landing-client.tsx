"use client";

import Link from "next/link";
import { useLang } from "@/lib/i18n/LangContext";
import { type V3ArchetypeSummary } from "@/lib/v3-api";

const FAQ_ITEMS_EN = [
  {
    q: "Is this scientifically valid?",
    a: "It uses two peer-reviewed instruments — Holland's RIASEC for career interests and Big Five (IPIP-NEO) for personality. We tune the wording for Indian context but never weaken the underlying science.",
  },
  {
    q: "Why ₹49?",
    a: "We're in early-bird launch — first 1,000 reports get the promo price; after that it's ₹99. The free results page already shows your archetype, slogan, radar, and your top career match.",
  },
  {
    q: "Do I need to log in?",
    a: "No. You can take the full test and read your free results without signing up. We only ask for your account when you choose to unlock the paid report — so we can email it to you.",
  },
  {
    q: "Where does my data live?",
    a: "On a small server we own. We don't sell your data, we don't run ads, we don't share answers with third parties. You can email us to delete everything at any time.",
  },
  {
    q: "How is this different from a Buzzfeed quiz?",
    a: "Buzzfeed quizzes are pure entertainment with no theoretical grounding. Our 45 items map to known psychometric scales, and your archetype comes out of two well-validated frameworks rather than vibes.",
  },
];

const FAQ_ITEMS_HI = [
  {
    q: "Yeh sahi hai? Scientifically?",
    a: "Haan — Holland's RIASEC (career interests) aur Big Five (IPIP-NEO) — dono peer-reviewed instruments. Wording Indian context me hai, science kabhi kamzor nahi karte.",
  },
  {
    q: "₹49 hi kyon?",
    a: "Hum early-bird me hain — pehle 1,000 report ke liye promo price; uske baad ₹99. Free result page me archetype, slogan, radar aur top career match toh dikhta hi hai.",
  },
  {
    q: "Login zaroori hai kya?",
    a: "Nahi. Pura test do, free result padho — bina sign-up. Login tab maangte hain jab paid report unlock karna ho — taaki email kar sakein.",
  },
  {
    q: "Mera data kahaan hai?",
    a: "Humare apne chhote server pe. Hum data bechte nahi, ads nahi chalate, third-party ke saath share nahi karte. Kabhi bhi delete request bhej sakte ho.",
  },
  {
    q: "Buzzfeed quiz se kya farak hai?",
    a: "Buzzfeed pure entertainment hota hai — koi theory nahi. Hamare 45 sawal real psychometric scales pe map hote hain, aur archetype 2 well-validated frameworks se aata hai.",
  },
];

export function LandingClient({ featured }: { featured: V3ArchetypeSummary[] }) {
  const { lang, t } = useLang();
  const FAQ = lang === "hi" ? FAQ_ITEMS_HI : FAQ_ITEMS_EN;
  return (
    <main className="flex flex-col">
      <section className="bg-india-hero px-6 py-20 md:py-28 text-center relative overflow-hidden">
        <div className="absolute top-6 left-6 text-3xl">🪔</div>
        <div className="relative z-10 max-w-3xl mx-auto">
          <div className="text-xs font-semibold tracking-[0.25em] uppercase text-saffron-700 mb-4">
            {t.landing.eyebrow}
          </div>
          <h1 className="text-4xl md:text-6xl font-bold leading-tight mb-6 text-navy-text">
            {t.landing.headline1} <br />
            <span className="bg-clip-text text-transparent bg-gradient-to-br from-saffron-700 to-india-green-500">
              {t.landing.headline2}
            </span>
          </h1>
          <p className="text-lg md:text-xl text-navy-text/80 mb-8 max-w-2xl mx-auto">
            {t.landing.pitch}
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/test"
              className="inline-block bg-india-green-500 hover:bg-india-green-600 text-white font-bold text-lg px-10 py-4 rounded-full transition-all shadow-lg hover:shadow-xl hover:scale-[1.02]"
            >
              {t.landing.ctaPrimary}
            </Link>
            <Link
              href="/archetypes"
              className="inline-block bg-white/70 hover:bg-white text-navy-text font-semibold text-lg px-8 py-4 rounded-full border border-saffron-700/15 backdrop-blur transition-all"
            >
              {t.landing.ctaSecondary}
            </Link>
          </div>
          <p className="mt-6 text-saffron-800 text-sm font-medium">
            {t.landing.socialProof}
          </p>
        </div>
      </section>

      <section className="bg-cream px-6 py-16">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12 text-navy-text">
            {t.landing.whatYouGet}
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                emoji: "🎯",
                title: t.landing.featureArchetype,
                desc:
                  lang === "hi"
                    ? "24 hand-curated Indian personality cells me se ek (jaise The 3AM Chai Philosopher). Holland ki hexagon theory pe based, Indian context me re-written."
                    : "One of 24 hand-curated Indian personality cells (e.g., The 3AM Chai Philosopher). Built on Holland's hexagon theory with India-flavored copy.",
              },
              {
                emoji: "💼",
                title: t.landing.featureCareer,
                desc:
                  lang === "hi"
                    ? "Aapke archetype se match 5+ Indian career paths — real companies (Razorpay, Swiggy, TCS, Marwari business families) aur lakh-based salary."
                    : "5+ Indian career paths matched to your archetype, with real companies (Razorpay, Swiggy, TCS, Marwari business families) and lakh-based salary ranges.",
              },
              {
                emoji: "📤",
                title: t.landing.featureShare,
                desc:
                  lang === "hi"
                    ? "Pre-likhi share lines + share image taaki dosti me dosti pata kar sakein."
                    : "Pre-written share lines + share image so your friends can take the test and discover their archetype.",
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

      {featured.length > 0 && (
        <section className="bg-india-radial px-6 py-16">
          <div className="max-w-5xl mx-auto">
            <div className="flex items-baseline justify-between flex-wrap gap-3 mb-8">
              <h2 className="text-3xl font-bold text-navy-text">
                {t.landing.gallery}
              </h2>
              <Link
                href="/archetypes"
                className="text-india-green-700 font-semibold hover:underline"
              >
                {t.landing.seeAll}
              </Link>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {featured.map((a) => (
                <Link
                  key={a.cell_id}
                  href={`/archetypes/${a.cell_id}`}
                  className="group bg-white rounded-2xl p-6 border border-saffron-700/10 hover:border-india-green-400 hover:shadow-lg transition-all"
                >
                  <div className="flex items-baseline justify-between mb-2">
                    <span className="text-3xl font-black text-navy-text group-hover:text-saffron-700 transition-colors tracking-tight">
                      {a.cell_id}
                    </span>
                    <span className="text-[10px] font-bold uppercase tracking-widest text-india-green-700">
                      {a.rarity_pct}% rare
                    </span>
                  </div>
                  <p className="font-semibold text-navy-text">
                    {lang === "hi" && a.label_hi ? a.label_hi : a.label_en}
                  </p>
                  <p className="text-sm text-navy-text/55 italic mt-1">
                    &ldquo;{a.slogan_en}&rdquo;
                  </p>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      <section
        id="science"
        className="bg-cream px-6 py-16 border-y border-saffron-700/10"
      >
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-10">
            <div className="text-xs font-semibold tracking-widest uppercase text-saffron-700 mb-2">
              {lang === "hi" ? "Bharosa kyon karein" : "Why trust this"}
            </div>
            <h2 className="text-3xl font-bold text-navy-text">
              {t.landing.science}
            </h2>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            {[
              {
                h: "Holland RIASEC",
                p: "John L. Holland's hexagon theory of vocational interests is one of the most studied career-fit frameworks (cited 30,000+ times). Your responses map to the 6 RIASEC types and the dominant 2 form your cell.",
              },
              {
                h: "Big Five (IPIP-NEO)",
                p: "OCEAN — Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism — is the most cross-culturally validated personality model. We use IPIP-NEO public-domain items.",
              },
              {
                h: lang === "hi" ? "Indian context me wording" : "India-tuned wording",
                p:
                  lang === "hi"
                    ? "Wahi scientific scales — par EMI realities, joint family, IIT/IIM scripts, Tier-1/2/3 city dynamics ke saath."
                    : "Same scientific scales, but rewritten for Indian context: EMI realities, joint family pressure, IIT/IIM scripts, Tier-1/2/3 city dynamics.",
              },
              {
                h: lang === "hi" ? "Soft paywall" : "Soft paywall",
                p:
                  lang === "hi"
                    ? "Free me archetype, slogan, top career, radar — sab dekho. Sirf deep version, OCEAN, full career list aur PDF ke liye pay karo."
                    : "We show you the meaningful stuff for free — archetype, slogan, top career, radar. Pay only if you want the deep version, OCEAN, full career list and PDF.",
              },
            ].map((c) => (
              <div
                key={c.h}
                className="bg-white rounded-2xl p-6 border border-saffron-200/40"
              >
                <h3 className="font-bold text-navy-text mb-2">{c.h}</h3>
                <p className="text-sm text-navy-text/75 leading-relaxed">{c.p}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="faq" className="bg-cream px-6 py-16">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-navy-text mb-10">
            {t.landing.faq}
          </h2>
          <div className="space-y-3">
            {FAQ.map((item) => (
              <details
                key={item.q}
                className="group bg-white rounded-2xl border border-saffron-700/10 px-5 py-4 open:shadow-md"
              >
                <summary className="cursor-pointer font-semibold text-navy-text flex items-center justify-between marker:hidden">
                  {item.q}
                  <span className="ml-4 text-saffron-700 transition-transform group-open:rotate-45 text-xl leading-none">
                    +
                  </span>
                </summary>
                <p className="text-sm text-navy-text/70 mt-3 leading-relaxed">
                  {item.a}
                </p>
              </details>
            ))}
          </div>
          <p
            id="privacy"
            className="text-xs text-navy-text/50 mt-8 text-center max-w-md mx-auto"
          >
            {t.landing.privacy}
          </p>
        </div>
      </section>

      <section className="bg-gradient-to-br from-india-green-500 to-india-green-700 text-white py-16 px-6 text-center">
        <h2 className="text-3xl font-bold mb-4">{t.landing.ctaTail}</h2>
        <p className="text-india-green-50 mb-8 max-w-lg mx-auto">
          {lang === "hi"
            ? "5 min · login nahi · ₹49 agar full report chahiye (pehle 1,000 users)."
            : "5 minutes. No login. ₹49 if you want the full report (first 1,000 users)."}
        </p>
        <Link
          href="/test"
          className="inline-block bg-white text-india-green-700 font-bold text-lg px-10 py-4 rounded-full hover:bg-saffron-50 transition-all shadow-lg"
        >
          {lang === "hi" ? "Abhi shuru karo" : "Start now"}
        </Link>
      </section>
    </main>
  );
}
