import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { getArchetypeDetail } from "@/lib/v3-api";

export const revalidate = 600;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ cell: string }>;
}): Promise<Metadata> {
  const { cell } = await params;
  try {
    const d = await getArchetypeDetail(cell);
    return {
      title: `${d.cell_id} — ${d.label_en}`,
      description: d.slogan_en,
      openGraph: {
        title: `${d.cell_id} — ${d.label_en}`,
        description: d.slogan_en,
      },
    };
  } catch {
    return { title: "Archetype not found" };
  }
}

export default async function ArchetypeDetailPage({
  params,
}: {
  params: Promise<{ cell: string }>;
}) {
  const { cell } = await params;
  let detail;
  try {
    detail = await getArchetypeDetail(cell);
  } catch {
    notFound();
  }

  const paragraphs = detail.deep_description_en.split(/\n\n+/).filter(Boolean);

  return (
    <>
      <SiteHeader />
      <main className="bg-cream min-h-screen">
        <section className="bg-india-hero px-6 py-16">
          <div className="max-w-3xl mx-auto text-center">
            <div className="text-saffron-700 text-xs font-bold tracking-[0.3em] uppercase mb-3">
              archetype
            </div>
            <div className="text-7xl md:text-8xl font-black text-navy-text mb-3">
              {detail.cell_id}
            </div>
            <h1 className="text-2xl md:text-3xl font-bold text-navy-text mb-3">
              {detail.label_en}
            </h1>
            <p className="text-navy-text/80 italic max-w-md mx-auto bg-white/60 backdrop-blur p-4 rounded-2xl">
              &ldquo;{detail.slogan_en}&rdquo;
            </p>
            <p className="text-sm text-india-green-700 font-bold mt-4">
              Rarity ~{detail.rarity_pct}%
            </p>
          </div>
        </section>

        <section className="max-w-3xl mx-auto px-6 py-12 space-y-8">
          <div className="bg-white border border-saffron-700/10 rounded-3xl p-6 md:p-8 shadow-sm">
            <h2 className="text-xs font-bold uppercase tracking-widest text-saffron-700 mb-3">
              Core insight
            </h2>
            <p className="text-navy-text/80 leading-relaxed">{detail.core_insight_en}</p>
          </div>

          <div className="bg-white border border-saffron-700/10 rounded-3xl p-6 md:p-8 shadow-sm">
            <h2 className="text-base font-bold text-navy-text mb-3">Deep dive</h2>
            <div className="space-y-3 text-navy-text/80 text-sm leading-relaxed">
              {paragraphs.map((p, idx) => (
                <p key={idx}>{p}</p>
              ))}
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white border border-saffron-700/10 rounded-3xl p-6">
              <h3 className="font-bold mb-3">Strengths</h3>
              <ul className="space-y-2">
                {detail.strengths_en.map((s) => (
                  <li
                    key={s}
                    className="text-sm text-navy-text/80 flex gap-2 items-start"
                  >
                    <span className="text-india-green-600">★</span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
            <div className="bg-white border border-saffron-700/10 rounded-3xl p-6">
              <h3 className="font-bold mb-3">Growth tips</h3>
              <ul className="space-y-2">
                {detail.growth_tips_en.map((s) => (
                  <li
                    key={s}
                    className="text-sm text-navy-text/80 flex gap-2 items-start"
                  >
                    <span className="text-saffron-600">→</span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="bg-white border border-saffron-700/10 rounded-3xl p-6">
            <h3 className="font-bold mb-3">Career directions</h3>
            <div className="flex flex-wrap gap-2 text-sm">
              {detail.career_directions.map((c) => (
                <span
                  key={c}
                  className="px-3 py-1 rounded-full bg-saffron-50 border border-saffron-200 text-saffron-700"
                >
                  {c.replace(/_/g, " ")}
                </span>
              ))}
            </div>
          </div>

          <div className="bg-gradient-to-br from-india-green-500 to-india-green-700 text-white rounded-3xl p-8 text-center shadow-lg">
            <h3 className="text-2xl font-bold mb-2">Is this you?</h3>
            <p className="text-india-green-50 mb-6 text-sm">
              Take the 5-minute test to find your real archetype + matched
              careers in INR.
            </p>
            <Link
              href="/test"
              className="inline-block bg-white text-india-green-700 font-bold px-8 py-3 rounded-full hover:bg-saffron-50 transition-all shadow-md"
            >
              Start free test →
            </Link>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
