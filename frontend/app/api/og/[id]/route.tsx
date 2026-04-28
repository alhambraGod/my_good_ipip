import { ImageResponse } from "next/og";

export const runtime = "nodejs";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001";

export async function GET(
  _request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const { id } = await context.params;

  let cellId = "DNA";
  let label = "CareerDNA India";
  let slogan = "Holland RIASEC + OCEAN · Built for Indian Gen-Z";

  try {
    const r = await fetch(`${API_BASE}/api/v3/assessment/${id}/results`, {
      cache: "no-store",
    });
    if (r.ok) {
      const d = (await r.json()) as {
        cell_id: string;
        cell_label_en: string;
        slogan_en: string;
      };
      cellId = d.cell_id || cellId;
      label = d.cell_label_en || label;
      slogan = (d.slogan_en || slogan).slice(0, 140);
    }
  } catch {
    /* fallback graphic */
  }

  return new ImageResponse(
    (
      <div
        style={{
          height: "100%",
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "linear-gradient(135deg, #FF9933 0%, #FFFAF0 45%, #138808 100%)",
          fontFamily:
            'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial',
          padding: 48,
        }}
      >
        <div style={{ fontSize: 28, marginBottom: 12 }}>🪔</div>
        <div
          style={{
            fontSize: 120,
            fontWeight: 900,
            letterSpacing: -4,
            color: "#1A202C",
            lineHeight: 1,
          }}
        >
          {cellId}
        </div>
        <div
          style={{
            fontSize: 34,
            fontWeight: 700,
            color: "#1A202C",
            marginTop: 24,
            textAlign: "center",
            maxWidth: 900,
          }}
        >
          {label}
        </div>
        <div
          style={{
            fontSize: 22,
            color: "#374151",
            marginTop: 20,
            textAlign: "center",
            maxWidth: 900,
            fontStyle: "italic",
          }}
        >
          {`"${slogan}"`}
        </div>
        <div
          style={{
            fontSize: 20,
            fontWeight: 600,
            color: "#B45309",
            marginTop: 36,
            textTransform: "uppercase",
            letterSpacing: "0.2em",
          }}
        >
          CareerDNA India
        </div>
      </div>
    ),
    { width: 1200, height: 630 },
  );
}
