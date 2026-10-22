import { useId } from "react";

import { cn } from "@/lib/utils";

export function LogoMark({ className }: { className?: string }) {
  const id = useId().replace(/:/g, "");
  return (
    <svg viewBox="0 0 32 32" fill="none" className={cn("size-8 shrink-0", className)} aria-hidden="true">
      <defs>
        <linearGradient id={`fj-${id}`} x1="2" y1="2" x2="30" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7C5CFF" />
          <stop offset="0.55" stopColor="#B06BF0" />
          <stop offset="1" stopColor="#22D3EE" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="30" height="30" rx="9" fill={`url(#fj-${id})`} />
      <rect x="1.5" y="1.5" width="29" height="29" rx="8.5" stroke="#fff" strokeOpacity=".35" />
      <rect x="8.5" y="17" width="3.6" height="6.5" rx="1.2" fill="#fff" fillOpacity=".88" />
      <rect x="14.2" y="13" width="3.6" height="10.5" rx="1.2" fill="#fff" fillOpacity=".92" />
      <rect x="19.9" y="9" width="3.6" height="14.5" rx="1.2" fill="#fff" />
      <path d="M8 13.2 13 9.8l4 2.4 6.8-5.2" stroke="#fff" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" opacity=".85" />
      <circle cx="23.8" cy="7" r="1.8" fill="#fff" />
    </svg>
  );
}

export function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark />
      {!compact && (
        <span className="font-display text-lg font-bold tracking-tight">
          FIN<span className="text-gradient">JARVIS</span>
        </span>
      )}
    </span>
  );
}
