import { useId } from "react";

import { cn } from "@/lib/utils";

export function LogoMark({ className }: { className?: string }) {
  const id = useId().replace(/:/g, "");
  return (
    <svg viewBox="0 0 32 32" fill="none" className={cn("size-8 shrink-0", className)} aria-hidden="true">
      <defs>
        <linearGradient id={`tg-${id}`} x1="2" y1="2" x2="30" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7C5CFF" />
          <stop offset="0.55" stopColor="#B06BF0" />
          <stop offset="1" stopColor="#22D3EE" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="30" height="30" rx="9" fill={`url(#tg-${id})`} />
      <rect x="1.5" y="1.5" width="29" height="29" rx="8.5" stroke="#fff" strokeOpacity=".35" />
      <path
        d="M8 7.5h12a1.5 1.5 0 0 1 1.5 1.5v14a1.5 1.5 0 0 1-1.5 1.5H8A1.5 1.5 0 0 1 6.5 23V9A1.5 1.5 0 0 1 8 7.5Z"
        fill="#fff"
        fillOpacity=".95"
      />
      <path d="M9.5 11.5h8M9.5 14.5h8M9.5 17.5h4" stroke="#6241F0" strokeWidth="1.6" strokeLinecap="round" />
      <circle cx="21.5" cy="21.5" r="5.2" fill="#0E93AD" stroke="#fff" strokeWidth="1.5" />
      <path d="m19.2 21.6 1.6 1.6 3-3.2" stroke="#fff" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark />
      {!compact && (
        <span className="font-display text-lg font-bold tracking-tight">
          Truth<span className="text-gradient">Glow</span>
        </span>
      )}
    </span>
  );
}
