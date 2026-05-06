import type { ReactNode } from "react";
import type { Metadata } from "next";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001";
const SITE = (process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000").replace(/\/$/, "");

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  try {
    const r = await fetch(`${API_BASE}/api/v3/assessment/${id}/results`, {
      next: { revalidate: 300 },
    });
    if (!r.ok) {
      return { title: "MindPrism · Results" };
    }
    const d = (await r.json()) as {
      cell_id: string;
      cell_label_en: string;
      slogan_en: string;
    };
    const title = `${d.cell_id} · ${d.cell_label_en} | MindPrism India`;
    const description =
      typeof d.slogan_en === "string" && d.slogan_en.length > 0
        ? d.slogan_en.slice(0, 200)
        : "Holland RIASEC + OCEAN for Indian Gen-Z.";
    const ogImage = `${SITE}/api/og/${id}`;
    return {
      title,
      description,
      openGraph: {
        title,
        description,
        images: [{ url: ogImage, width: 1200, height: 630 }],
      },
      twitter: {
        card: "summary_large_image",
        title,
        description,
        images: [ogImage],
      },
    };
  } catch {
    return { title: "MindPrism · Results" };
  }
}

export default function ResultsIdLayout({ children }: { children: ReactNode }) {
  return children;
}
