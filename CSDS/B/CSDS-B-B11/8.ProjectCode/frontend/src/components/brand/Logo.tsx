import { useId } from "react";

import { cn } from "@/lib/utils";

/** Leaf mark in the Aurora gradient (NutriSense brand glyph). */
export function LogoMark({ className }: { className?: string }) {
  const id = useId().replace(/:/g, "");
  return (
    <svg viewBox="0 0 32 32" fill="none" className={cn("size-8 shrink-0", className)} aria-hidden="true">
      <defs>
        <linearGradient id={`ns-${id}`} x1="2" y1="2" x2="30" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7C5CFF" />
          <stop offset="0.55" stopColor="#B06BF0" />
          <stop offset="1" stopColor="#22D3EE" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="30" height="30" rx="9" fill={`url(#ns-${id})`} />
      <rect x="1.5" y="1.5" width="29" height="29" rx="8.5" stroke="#fff" strokeOpacity=".35" />
      <path
        d="M22.5 9.5c-6.2.2-10.6 3.4-11.7 9.7-.3 1.7-.1 3.2.6 4.3 1.6-5.5 4.9-8.8 10.9-10.5.2-1.3.2-2.3.2-3.5Z"
        fill="#fff"
        fillOpacity=".95"
      />
      <path d="M11.2 23.6c1.6-4.2 4.5-7.6 9.2-9.8" stroke="#6241F0" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}

export function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark />
      {!compact && (
        <span className="font-display text-lg font-bold tracking-tight">
          Nutri<span className="text-gradient">Sense</span>
        </span>
      )}
    </span>
  );
}
