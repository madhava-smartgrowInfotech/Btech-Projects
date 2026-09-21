import { useId } from "react";

import { cn } from "@/lib/utils";

export function LogoMark({ className }: { className?: string }) {
  const id = useId().replace(/:/g, "");
  return (
    <svg viewBox="0 0 32 32" fill="none" className={cn("size-8 shrink-0", className)} aria-hidden="true">
      <defs>
        <linearGradient id={`pl-${id}`} x1="2" y1="2" x2="30" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#2dd4bf" />
          <stop offset="1" stopColor="#0f766e" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="30" height="30" rx="9" fill={`url(#pl-${id})`} />
      <path
        d="M9.5 7.5h8l5 5v11a1.5 1.5 0 0 1-1.5 1.5H9.5A1.5 1.5 0 0 1 8 23.5V9a1.5 1.5 0 0 1 1.5-1.5Z"
        fill="#fff"
        fillOpacity=".96"
      />
      <path d="M17.5 7.5v3.5a1.5 1.5 0 0 0 1.5 1.5h3.5" fill="#ccfbf1" />
      <circle cx="14.6" cy="17.2" r="4.1" stroke="#0f766e" strokeWidth="1.9" />
      <path d="m17.6 20.2 3 3" stroke="#0f766e" strokeWidth="2" strokeLinecap="round" />
      <path d="m12.9 17.3 1.2 1.2 2.3-2.5" stroke="#0f766e" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark />
      {!compact && (
        <span className="font-display text-lg font-bold tracking-tight">
          Policy<span className="text-primary">Lens</span>
        </span>
      )}
    </span>
  );
}
