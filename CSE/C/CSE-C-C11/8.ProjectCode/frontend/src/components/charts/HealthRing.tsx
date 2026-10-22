import { motion } from "framer-motion";

export function HealthRing({ score, size = "size-24" }: { score: number; size?: string }) {
  const r = 38;
  const c = 2 * Math.PI * r;
  return (
    <svg viewBox="0 0 100 100" className={`${size} shrink-0 -rotate-90`} role="img" aria-label={`Financial health score ${Math.round(score)} out of 100`}>
      <defs>
        <linearGradient id="health-ring" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#7C5CFF" />
          <stop offset="1" stopColor="#22D3EE" />
        </linearGradient>
      </defs>
      <circle cx="50" cy="50" r={r} fill="none" stroke="var(--glass-border)" strokeWidth="9" />
      <motion.circle
        cx="50"
        cy="50"
        r={r}
        fill="none"
        stroke="url(#health-ring)"
        strokeWidth="9"
        strokeLinecap="round"
        strokeDasharray={c}
        initial={{ strokeDashoffset: c }}
        animate={{ strokeDashoffset: c * (1 - score / 100) }}
        transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1], delay: 0.3 }}
      />
      <text
        x="50"
        y="50"
        transform="rotate(90 50 50)"
        textAnchor="middle"
        dominantBaseline="central"
        className="fill-foreground font-display text-[24px] font-semibold"
      >
        {Math.round(score)}
      </text>
    </svg>
  );
}
