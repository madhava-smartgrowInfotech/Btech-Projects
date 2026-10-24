import { useId } from "react";

import { cn } from "@/lib/utils";

export function LogoMark({ className }: { className?: string }) {
  const id = useId().replace(/:/g, "");
  return (
    <svg viewBox="0 0 32 32" fill="none" className={cn("size-8 shrink-0", className)} aria-hidden="true">
      <defs>
        <linearGradient id={`av-${id}`} x1="2" y1="2" x2="30" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#22A06B" />
          <stop offset="0.55" stopColor="#6EE7B7" />
          <stop offset="1" stopColor="#2DD4BF" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="30" height="30" rx="9" fill={`url(#av-${id})`} />
      <rect x="1.5" y="1.5" width="29" height="29" rx="8.5" stroke="#fff" strokeOpacity=".35" />
      <path d="M8 23C7.5 14 13 8.5 24.5 8c.5 11-5 17-13.5 16.2-1.3-.1-2.3-.5-3-1.2Z" fill="#fff" fillOpacity=".96" />
      <path d="M9.5 22.5c3.2-5.2 7-8.6 11.5-11" stroke="#15803D" strokeWidth="1.7" strokeLinecap="round" />
      <path d="M14.2 17.6l.4-3.2M17.3 14.7l2.9.6" stroke="#15803D" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

export function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark />
      {!compact && (
        <span className="font-display text-lg font-bold tracking-tight">
          Agri<span className="text-gradient">Vision</span>
        </span>
      )}
    </span>
  );
}
