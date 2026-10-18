import { motion, useReducedMotion } from "framer-motion";
import { useId } from "react";

import { riskColor } from "@/lib/domain";

/** Half-circle risk meter (0-100): green below 30, amber below 70, red above (same bands as the Streamlit gauge). */
export function RiskGauge({ score, title = "Risk score", className }: { score: number; title?: string; className?: string }) {
  const id = useId().replace(/:/g, "");
  const reduce = useReducedMotion();
  const clamped = Math.max(0, Math.min(100, score));
  const r = 80;
  const len = Math.PI * r;
  const color = riskColor(clamped);
  return (
    <div className={className} role="img" aria-label={`${title}: ${Math.round(clamped)} out of 100`}>
      <svg viewBox="0 0 200 118" className="mx-auto w-full max-w-[240px]">
        <defs>
          <linearGradient id={`g-${id}`} x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stopColor="#34D399" />
            <stop offset="45%" stopColor="#FBBF24" />
            <stop offset="100%" stopColor="#FB7185" />
          </linearGradient>
        </defs>
        <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="var(--muted)" strokeWidth="16" strokeLinecap="round" />
        <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke={`url(#g-${id})`} strokeWidth="16" strokeLinecap="round" opacity="0.18" />
        <motion.path
          d="M20 100 A80 80 0 0 1 180 100"
          fill="none"
          stroke={color}
          strokeWidth="16"
          strokeLinecap="round"
          strokeDasharray={len}
          initial={{ strokeDashoffset: reduce ? len * (1 - clamped / 100) : len }}
          animate={{ strokeDashoffset: len * (1 - clamped / 100) }}
          transition={{ duration: reduce ? 0 : 1.1, ease: [0.22, 1, 0.36, 1] }}
          style={{ filter: `drop-shadow(0 0 6px ${color}88)` }}
        />
        <text x="100" y="92" textAnchor="middle" className="fill-foreground font-display" fontSize="38" fontWeight="600">
          {Math.round(clamped)}
        </text>
        <text x="100" y="112" textAnchor="middle" className="fill-muted-foreground" fontSize="11">
          {title}
        </text>
      </svg>
    </div>
  );
}
