import { useId } from "react";

import { cn } from "@/lib/utils";

/** Shield with a check mark: a pull request that passed review. */
export function LogoMark({ className }: { className?: string }) {
  const id = useId().replace(/:/g, "");
  return (
    <svg viewBox="0 0 32 32" fill="none" className={cn("size-8 shrink-0", className)} aria-hidden="true">
      <defs>
        <linearGradient id={`as-${id}`} x1="2" y1="2" x2="30" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7C5CFF" />
          <stop offset="0.55" stopColor="#B06BF0" />
          <stop offset="1" stopColor="#22D3EE" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="30" height="30" rx="9" fill={`url(#as-${id})`} />
      <rect x="1.5" y="1.5" width="29" height="29" rx="8.5" stroke="#fff" strokeOpacity=".35" />
      <path d="M16 6.4 24.2 9.6v6.3c0 4.7-3.3 8.4-8.2 9.9-4.9-1.5-8.2-5.2-8.2-9.9V9.6L16 6.4Z" fill="#fff" fillOpacity=".95" />
      <path d="M16 6.4 24.2 9.6v6.3c0 4.7-3.3 8.4-8.2 9.9V6.4Z" fill="#E2DBFF" />
      <path d="m12.4 16.1 2.5 2.5 4.8-5.1" stroke="#6241F0" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark />
      {!compact && (
        <span className="font-display text-lg font-bold tracking-tight">
          Auto<span className="text-gradient">SecAI</span>
        </span>
      )}
    </span>
  );
}
