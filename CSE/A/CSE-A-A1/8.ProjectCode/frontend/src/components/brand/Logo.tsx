import { useId } from "react";

import { cn } from "@/lib/utils";

export function LogoMark({ className }: { className?: string }) {
  const id = useId().replace(/:/g, "");
  return (
    <svg viewBox="0 0 32 32" fill="none" className={cn("size-8 shrink-0", className)} aria-hidden="true">
      <defs>
        <linearGradient id={`al-${id}`} x1="2" y1="2" x2="30" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7C5CFF" />
          <stop offset="0.55" stopColor="#B06BF0" />
          <stop offset="1" stopColor="#22D3EE" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="30" height="30" rx="9" fill={`url(#al-${id})`} />
      <rect x="1.5" y="1.5" width="29" height="29" rx="8.5" stroke="#fff" strokeOpacity=".35" />
      <path d="M16 6.5 5.5 11.8 16 17.1l8.4-4.25V19h1.9v-7.2z" fill="#fff" fillOpacity=".95" />
      <path d="M9.6 16v4.1c0 1.7 2.9 3.2 6.4 3.2s6.4-1.5 6.4-3.2V16L16 19.3z" fill="#E2DBFF" />
      <circle cx="25.2" cy="22.6" r="1.5" fill="#22D3EE" />
    </svg>
  );
}

export function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark />
      {!compact && (
        <span className="font-display text-lg font-bold tracking-tight">
          Adaptive<span className="text-gradient">Learning</span>
        </span>
      )}
    </span>
  );
}
