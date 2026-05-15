"use client";

import type { MonthBucket } from "@/lib/revenue";
import { formatEuro } from "@/lib/format";

interface Props {
  buckets: MonthBucket[];
}

export function RevenueChart({ buckets }: Props) {
  const max = Math.max(1, ...buckets.map((b) => b.total_cents));
  const W = 600;
  const H = 200;
  const padX = 32;
  const padY = 24;
  const innerW = W - padX * 2;
  const innerH = H - padY * 2;
  const barW = (innerW / buckets.length) * 0.6;
  const gap = (innerW / buckets.length) * 0.4;
  const step = innerW / buckets.length;

  return (
    <div className="rounded-2xl border border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)] p-5">
      <div className="mb-3 flex items-baseline justify-between">
        <h2 className="font-display text-base">Ultimi 6 mesi</h2>
        <span className="text-[11px] uppercase tracking-[0.16em] text-[color:var(--color-text-muted)]">
          Lordo riuscito
        </span>
      </div>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="h-auto w-full"
        role="img"
        aria-label="Andamento revenue ultimi 6 mesi"
      >
        {/* baseline */}
        <line
          x1={padX}
          y1={H - padY}
          x2={W - padX}
          y2={H - padY}
          stroke="currentColor"
          opacity="0.15"
        />
        {buckets.map((b, i) => {
          const h = (b.total_cents / max) * innerH;
          const x = padX + i * step + gap / 2;
          const y = H - padY - h;
          return (
            <g key={`${b.year}-${b.month}`}>
              <rect
                x={x}
                y={y}
                width={barW}
                height={h}
                rx={4}
                className="fill-[color:var(--color-teal)]"
                opacity="0.85"
              >
                <title>
                  {b.label} {b.year}: {formatEuro(b.total_cents)}
                </title>
              </rect>
              <text
                x={x + barW / 2}
                y={H - padY + 14}
                textAnchor="middle"
                className="fill-[color:var(--color-text-muted)]"
                fontSize="10"
              >
                {b.label}
              </text>
              {b.total_cents > 0 && (
                <text
                  x={x + barW / 2}
                  y={y - 4}
                  textAnchor="middle"
                  className="fill-[color:var(--color-text-soft)]"
                  fontSize="9"
                >
                  {formatEuro(b.total_cents)}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
