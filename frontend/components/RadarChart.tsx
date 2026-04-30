"use client";

const TYPES = ["R", "I", "A", "S", "E", "C"] as const;
type RIASEC = (typeof TYPES)[number];

const FULL_LABEL: Record<RIASEC, string> = {
  R: "Realistic",
  I: "Investigative",
  A: "Artistic",
  S: "Social",
  E: "Enterprising",
  C: "Conventional",
};

export function RadarChart({
  scores,
  size = 260,
  max = 20,
}: {
  scores: Record<string, number>;
  size?: number;
  max?: number;
}) {
  const cx = size / 2;
  const cy = size / 2;
  const r = size * 0.36;
  const labelR = r + 22;

  const points = TYPES.map((t, i) => {
    const angle = (i * Math.PI) / 3 - Math.PI / 2;
    const score = scores[t] ?? 0;
    const ratio = Math.max(0, Math.min(1, score / max));
    return [cx + Math.cos(angle) * r * ratio, cy + Math.sin(angle) * r * ratio] as const;
  });

  const grid = [0.25, 0.5, 0.75, 1].map((g) =>
    TYPES.map((_, i) => {
      const angle = (i * Math.PI) / 3 - Math.PI / 2;
      return `${cx + Math.cos(angle) * r * g},${cy + Math.sin(angle) * r * g}`;
    }).join(" "),
  );

  return (
    <div className="flex flex-col items-center">
      <svg viewBox={`0 0 ${size} ${size}`} role="img" aria-label="Holland RIASEC radar" className="w-full max-w-md">
        {grid.map((pts, i) => (
          <polygon
            key={i}
            points={pts}
            fill={i === 3 ? "rgba(255, 250, 240, 0.7)" : "none"}
            stroke="#FFD58F"
            strokeWidth={i === 3 ? 1 : 0.5}
            strokeDasharray={i === 3 ? "0" : "2 3"}
          />
        ))}

        {TYPES.map((_, i) => {
          const angle = (i * Math.PI) / 3 - Math.PI / 2;
          return (
            <line
              key={`spoke-${i}`}
              x1={cx}
              y1={cy}
              x2={cx + Math.cos(angle) * r}
              y2={cy + Math.sin(angle) * r}
              stroke="#FFE8C7"
              strokeWidth={0.5}
            />
          );
        })}

        <polygon
          points={points.map(([x, y]) => `${x},${y}`).join(" ")}
          fill="rgba(255, 153, 51, 0.32)"
          stroke="#FF9933"
          strokeWidth={2}
        />

        {points.map(([x, y], i) => (
          <circle key={`pt-${i}`} cx={x} cy={y} r={3.5} fill="#B45309" />
        ))}

        {TYPES.map((t, i) => {
          const angle = (i * Math.PI) / 3 - Math.PI / 2;
          const x = cx + Math.cos(angle) * labelR;
          const y = cy + Math.sin(angle) * labelR;
          return (
            <g key={`lbl-${t}`}>
              <text
                x={x}
                y={y}
                textAnchor="middle"
                fill="#1A202C"
                fontSize="14"
                fontWeight="700"
                dy="4"
              >
                {t}
              </text>
            </g>
          );
        })}

        {[0.25, 0.5, 0.75, 1].map((g, i) => (
          <text
            key={`tick-${i}`}
            x={cx + 3}
            y={cy - r * g + 3}
            fill="#B45309"
            fontSize="9"
            opacity={0.5}
          >
            {Math.round(max * g)}
          </text>
        ))}
      </svg>

      <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 w-full max-w-md mt-4 text-[11px] font-medium text-navy-text/70">
        {TYPES.map((t) => (
          <div key={t} className="flex flex-col items-center">
            <span className="font-bold text-navy-text">{t}</span>
            <span className="opacity-70">{FULL_LABEL[t]}</span>
            <span className="text-saffron-700 font-bold tabular-nums">
              {scores[t] ?? 0}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
