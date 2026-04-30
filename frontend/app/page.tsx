import Link from "next/link";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { listArchetypes, type V3ArchetypeSummary } from "@/lib/v3-api";

const FEATURED_CELL_IDS = ["IA", "EC", "SE", "AS", "RC", "CI"];

const FAQ_ITEMS = [
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

export const revalidate = 600;

export default async function LandingPage() {
  let featured: V3ArchetypeSummary[] = [];
  try {
    const all = await listArchetypes();
    const map = new Map(all.map((a) => [a.cell_id, a]));
    featured = FEATURED_CELL_IDS.map((id) => map.get(id)).filter(
      (x): x is V3ArchetypeSummary => Boolean(x),
    );
  } catch {
    featured = [];
  }

  return (
    <>
      <SiteHeader />
      <main className="flex flex-col">
        {/* HERO */}
        <section className="bg-india-hero px-6 py-20 md:py-28 text-center relative overflow-hidden">
          <div className="absolute top-6 left-6 text-3xl">🪔</div>
          <div className="relative z-10 max-w-3xl mx-auto">
            <div className="text-xs font-semibold tracking-[0.25em] uppercase text-saffron-700 mb-4">
              Indian-built personality + career mapping
            </div>
            <h1 className="text-4xl md:text-6xl font-bold leading-tight mb-6 text-navy-text">
              Find your <br />
              <span className="bg-clip-text text-transparent bg-gradient-to-br from-saffron-700 to-india-green-500">
                Indian Career DNA
              </span>
            </h1>
            <p className="text-lg md:text-xl text-navy-text/80 mb-8 max-w-2xl mx-auto">
              45 questions. 5 minutes. Built on Holland RIASEC + Big Five (OCEAN). Tuned for
              Bangalore IT, Marwari hustle, Sharma ji&apos;s beta, EMI math, all of it.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link
                href="/test"
                className="inline-block bg-india-green-500 hover:bg-india-green-600 text-white font-bold text-lg px-10 py-4 rounded-full transition-all shadow-lg hover:shadow-xl hover:scale-[1.02]"
              >
                Start Free Test →
              </Link>
              <Link
                href="/archetypes"
                className="inline-block bg-white/70 hover:bg-white text-navy-text font-semibold text-lg px-8 py-4 rounded-full border border-saffron-700/15 backdrop-blur transition-all"
              >
                Browse 24 archetypes
              </Link>
            </div>
            <p className="mt-6 text-saffron-800 text-sm font-medium">
              Free results · No login needed · ₹49 only if you want the full report
            </p>
          </div>
        </section>

        {/* WHAT YOU GET */}
        <section className="bg-cream px-6 py-16">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-12 text-navy-text">
              What you&apos;ll get
            </h2>
            <div className="grid md:grid-cols-3 gap-8">
              {[
                {
                  emoji: "🎯",
                  title: "Your archetype",
                  desc: "One of 24 hand-curated Indian personality cells (e.g., The 3AM Chai Philosopher). Built on Holland's hexagon theory with India-flavored copy.",
                },
                {
                  emoji: "💼",
                  title: "Career match",
                  desc: "5+ Indian career paths matched to your archetype, with real companies (Razorpay, Swiggy, TCS, Marwari business families) and lakh-based salary ranges.",
                },
                {
                  emoji: "📤",
                  title: "WhatsApp-ready share",
                  desc: "Pre-written share lines + share image so your friends can take the test and discover their archetype.",
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

        {/* ARCHETYPE GALLERY */}
        {featured.length > 0 && (
          <section className="bg-india-radial px-6 py-16">
            <div className="max-w-5xl mx-auto">
              <div className="flex items-baseline justify-between flex-wrap gap-3 mb-8">
                <h2 className="text-3xl font-bold text-navy-text">
                  Some archetypes you might be
                </h2>
                <Link
                  href="/archetypes"
                  className="text-india-green-700 font-semibold hover:underline"
                >
                  See all 24 →
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
                    <p className="font-semibold text-navy-text">{a.label_en}</p>
                    <p className="text-sm text-navy-text/55 italic mt-1">
                      &ldquo;{a.slogan_en}&rdquo;
                    </p>
                  </Link>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* SCIENCE / TRUST */}
        <section id="science" className="bg-cream px-6 py-16 border-y border-saffron-700/10">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-10">
              <div className="text-xs font-semibold tracking-widest uppercase text-saffron-700 mb-2">
                Why trust this
              </div>
              <h2 className="text-3xl font-bold text-navy-text">
                Real psychometrics, not vibes
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
                  h: "India-tuned wording",
                  p: "Same scientific scales, but rewritten for Indian context: EMI realities, joint family pressure, IIT/IIM scripts, Tier-1/2/3 city dynamics.",
                },
                {
                  h: "Soft paywall",
                  p: "We show you the meaningful stuff for free — archetype, slogan, top career, radar. Pay only if you want the deep version, OCEAN, full career list and PDF.",
                },
              ].map((t) => (
                <div
                  key={t.h}
                  className="bg-white rounded-2xl p-6 border border-saffron-200/40"
                >
                  <h3 className="font-bold text-navy-text mb-2">{t.h}</h3>
                  <p className="text-sm text-navy-text/75 leading-relaxed">{t.p}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section id="faq" className="bg-cream px-6 py-16">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-3xl font-bold text-center text-navy-text mb-10">
              Honest answers to honest questions
            </h2>
            <div className="space-y-3">
              {FAQ_ITEMS.map((item) => (
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
              Privacy: your answers stay on our server. We don&apos;t sell data,
              don&apos;t run ads, don&apos;t share with third parties. Email
              support to delete your data anytime.
            </p>
          </div>
        </section>

        {/* CTA */}
        <section className="bg-gradient-to-br from-india-green-500 to-india-green-700 text-white py-16 px-6 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to find your archetype?</h2>
          <p className="text-india-green-50 mb-8 max-w-lg mx-auto">
            5 minutes. No login. ₹49 if you want the full report (first 1,000 users).
          </p>
          <Link
            href="/test"
            className="inline-block bg-white text-india-green-700 font-bold text-lg px-10 py-4 rounded-full hover:bg-saffron-50 transition-all shadow-lg"
          >
            Start now
          </Link>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
