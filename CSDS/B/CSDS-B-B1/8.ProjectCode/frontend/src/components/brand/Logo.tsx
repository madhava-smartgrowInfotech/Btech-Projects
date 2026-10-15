import { useId } from "react";

import { cn } from "@/lib/utils";

export function LogoMark({ className }: { className?: string }) {
  const id = useId().replace(/:/g, "");
  return (
    <svg viewBox="0 0 32 32" fill="none" className={cn("size-8 shrink-0", className)} aria-hidden="true">
      <defs>
        <linearGradient id={`cp-${id}`} x1="2" y1="2" x2="30" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7C5CFF" />
          <stop offset="0.55" stopColor="#B06BF0" />
          <stop offset="1" stopColor="#22D3EE" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="30" height="30" rx="9" fill={`url(#cp-${id})`} />
      <rect x="1.5" y="1.5" width="29" height="29" rx="8.5" stroke="#fff" strokeOpacity=".35" />
      {/* a pulse line running through a map pin: civic issues, read as they happen */}
      <path d="M16 6.2a6.3 6.3 0 0 0-6.3 6.3c0 4.6 6.3 10.8 6.3 10.8s6.3-6.2 6.3-10.8A6.3 6.3 0 0 0 16 6.2Z" fill="#fff" fillOpacity=".95" />
      <path d="M11.4 13.2h2.2l1.2-2.7 2.3 5.4 1.3-2.7h1.2" stroke="#6241F0" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M6.5 26h19" stroke="#fff" strokeOpacity=".75" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

export function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark />
      {!compact && (
        <span className="font-display text-lg font-bold tracking-tight">
          Civic<span className="text-gradient">Pulse</span>
        </span>
      )}
    </span>
  );
}
