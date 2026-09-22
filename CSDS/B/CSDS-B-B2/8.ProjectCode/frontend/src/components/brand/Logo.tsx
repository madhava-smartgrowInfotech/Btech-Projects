import { useId } from "react";
import { cn } from "@/lib/utils";

/** Map pin with signal arcs: "scout" + "signal". */
export function LogoMark({ className }: { className?: string }) {
  const id = useId();
  return (
    <svg viewBox="0 0 32 32" fill="none" aria-hidden="true" className={cn("h-8 w-8 shrink-0", className)}>
      <defs>
        <linearGradient id={id} x1="6" y1="2" x2="26" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#5b74ff" />
          <stop offset="1" stopColor="#2440e0" />
        </linearGradient>
      </defs>
      <path
        d="M16 1.8C9.8 1.8 4.8 6.7 4.8 12.8c0 7.8 9.4 16.3 10.3 17.1a1.3 1.3 0 0 0 1.8 0c.9-.8 10.3-9.3 10.3-17.1 0-6.1-5-11-11.2-11z"
        fill={`url(#${id})`}
      />
      <path d="M11.9 12.3a5.8 5.8 0 0 1 8.2 0M9.1 9.5a9.8 9.8 0 0 1 13.8 0" stroke="#fff" strokeWidth="2" strokeLinecap="round" />
      <circle cx="16" cy="15.4" r="1.9" fill="#22d3ee" />
    </svg>
  );
}

export function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <LogoMark />
      {!compact && (
        <span className="font-display text-lg font-bold tracking-tight">
          Signal<span className="text-primary">Scout</span>
        </span>
      )}
    </span>
  );
}
