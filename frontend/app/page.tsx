import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { LandingClient } from "./_landing-client";
import { listArchetypes, type V3ArchetypeSummary } from "@/lib/v3-api";

const FEATURED_CELL_IDS = ["IA", "EC", "SE", "AS", "RC", "CI"];

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
      <LandingClient featured={featured} />
      <SiteFooter />
    </>
  );
}
