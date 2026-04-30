import type { MetadataRoute } from "next";
import { listArchetypes } from "@/lib/v3-api";

const SITE = (process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000").replace(/\/$/, "");

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();
  const baseUrls: MetadataRoute.Sitemap = [
    { url: `${SITE}/`, lastModified: now, changeFrequency: "weekly", priority: 1 },
    { url: `${SITE}/archetypes`, lastModified: now, changeFrequency: "weekly", priority: 0.9 },
    { url: `${SITE}/test`, lastModified: now, changeFrequency: "monthly", priority: 0.8 },
  ];

  try {
    const archetypes = await listArchetypes();
    for (const a of archetypes) {
      baseUrls.push({
        url: `${SITE}/archetypes/${a.cell_id}`,
        lastModified: now,
        changeFrequency: "monthly",
        priority: 0.7,
      });
    }
  } catch {
    /* if backend unreachable at build time, skip per-archetype URLs */
  }

  return baseUrls;
}
