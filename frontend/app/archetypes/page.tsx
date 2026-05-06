import Link from "next/link";
import type { Metadata } from "next";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { listArchetypes, type V3ArchetypeSummary } from "@/lib/v3-api";

export const metadata: Metadata = {
  title: "All 24 archetypes",
  description:
    "Browse the 24 CareerDNA India archetypes — Holland RIASEC double-letter codes with India-flavored slogans.",
};

export const revalidate = 600;

export default async function ArchetypesIndex() {
  let archetypes: V3ArchetypeSummary[] = [];
  try {
    archetypes = await listArchetypes();
  } catch {
    archetypes = [];
  }

  const grouped: Record<string, V3ArchetypeSummary[]> = {};
  for (const a of archetypes) {
    const main = a.cell_id[0];
    grouped[main] = grouped[main] || [];
    grouped[main].push(a);
  }

  const RIASEC_FULL: Record<string, string> = {
    R: "Realistic — builders, doers",
    I: "Investigative — thinkers, analysts",
    A: "Artistic — creators, expressives",
    S: "Social — helpers, connectors",
    E: "Enterprising — sellers, leaders",
    C: "Conventional — organisers, planners",
  };

  return (
    <>
      <SiteHeader />
      <main className="bg-cream">
        <section className="bg-india-hero px-6 py-16 md:py-20">
          <div className="max-w-4xl mx-auto text-center">
            <div className="text-3xl mb-3">🪔</div>
            <h1 className="text-3xl md:text-5xl font-black text-navy-text mb-3">
              The 24 CareerDNA archetypes
            </h1>
            <p className="text-navy-text/80 max-w-2xl mx-auto">
              Holland&apos;s 6 RIASEC types form a hexagon. Pair the dominant
              type with its second-strongest neighbour and you get one of these
              24 cells — each with India-flavored copy.
            </p>
          </div>
        </section>

        <section className="max-w-6xl mx-auto px-6 py-12 space-y-12">
          {archetypes.length === 0 ? (
            <p className="text-center text-navy-text/75">
              Couldn&apos;t load archetypes. Make sure the backend is running.
            </p>
          ) : (
            Object.entries(grouped).map(([main, items]) => (
              <div key={main}>
                <div className="flex items-baseline justify-between mb-4 border-b border-saffron-700/15 pb-2">
                  <h2 className="text-xl md:text-2xl font-bold text-navy-text">
                    <span className="text-saffron-700">{main}</span> ·{" "}
                    {RIASEC_FULL[main] || ""}
                  </h2>
                  <span className="text-xs text-navy-text/40">
                    {items.length} cells
                  </span>
                </div>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {items.map((a) => (
                    <Link
                      key={a.cell_id}
                      href={`/archetypes/${a.cell_id}`}
                      className="group bg-white border border-saffron-700/10 rounded-2xl p-5 hover:border-india-green-400 hover:shadow-lg transition-all"
                    >
                      <div className="flex items-baseline justify-between mb-1">
                        <span className="text-2xl font-black text-navy-text group-hover:text-saffron-700 transition-colors tracking-tight">
                          {a.cell_id}
                        </span>
                        <span className="text-[10px] font-bold uppercase tracking-widest text-india-green-700">
                          {a.rarity_pct}% rare
                        </span>
                      </div>
                      <p className="font-semibold text-navy-text mb-1">{a.label_en}</p>
                      <p className="text-xs text-navy-text/55 italic">
                        &ldquo;{a.slogan_en}&rdquo;
                      </p>
                    </Link>
                  ))}
                </div>
              </div>
            ))
          )}
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
