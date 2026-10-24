import { useId } from "react";

import { cn } from "@/lib/utils";

export function LogoMark({ className }: { className?: string }) {
  const id = useId().replace(/:/g, "");
  return (
    <svg viewBox="0 0 32 32" fill="none" className={cn("size-8 shrink-0", className)} aria-hidden="true">
      <defs>
        <linearGradient id={`sr-${id}`} x1="2" y1="2" x2="30" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7C5CFF" />
          <stop offset="0.55" stopColor="#B06BF0" />
          <stop offset="1" stopColor="#22D3EE" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="30" height="30" rx="9" fill={`url(#sr-${id})`} />
      <rect x="1.5" y="1.5" width="29" height="29" rx="8.5" stroke="#fff" strokeOpacity=".35" />
      {/* eye */}
      <path
        d="M5.5 16.5C8 11.8 11.8 9.5 16 9.5s8 2.3 10.5 7c-2.5 4.7-6.3 7-10.5 7s-8-2.3-10.5-7Z"
        stroke="#fff"
        strokeOpacity=".95"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <circle cx="16" cy="16.5" r="3.6" fill="#fff" />
      {/* warning tick */}
      <path d="M16 3.5v3" stroke="#fff" strokeOpacity=".7" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

export function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark />
      {!compact && (
        <span className="font-display text-lg font-bold tracking-tight">
          Smart<span className="text-gradient">Rider</span>
        </span>
      )}
    </span>
  );
}
