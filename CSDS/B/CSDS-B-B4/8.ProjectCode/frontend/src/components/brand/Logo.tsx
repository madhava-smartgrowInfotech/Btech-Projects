import { useId } from "react";
import { cn } from "@/lib/utils";

export function LogoMark({ className }: { className?: string }) {
  const id = useId().replace(/:/g, "");
  return (
    <svg viewBox="0 0 32 32" className={cn("h-8 w-8", className)} aria-hidden="true">
      <defs>
        <linearGradient id={`g-${id}`} x1="6" y1="3" x2="26" y2="29" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#2dd4bf" />
          <stop offset="0.55" stopColor="#0d9488" />
          <stop offset="1" stopColor="#115e59" />
        </linearGradient>
        <linearGradient id={`s-${id}`} x1="16" y1="3" x2="16" y2="16" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#ffffff" stopOpacity="0.35" />
          <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d="M16 2.4 27.2 6.6v8.2c0 7-4.8 12.5-11.2 14.8C9.6 27.3 4.8 21.8 4.8 14.8V6.6L16 2.4Z" fill={`url(#g-${id})`} />
      <path d="M16 2.4 27.2 6.6v5.2C22 9.6 10 9.6 4.8 11.8V6.6L16 2.4Z" fill={`url(#s-${id})`} />
      <path d="m10.6 16.3 3.8 3.7 7.3-8.1" fill="none" stroke="#fff" strokeWidth="2.7" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="24.6" cy="24.4" r="3.6" fill="#f59e0b" stroke="hsl(var(--background))" strokeWidth="1.4" />
      <path d="M24.6 22.9v1.7l1 .7" fill="none" stroke="#fff" strokeWidth="1.1" strokeLinecap="round" />
    </svg>
  );
}

export function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <LogoMark />
      {!compact && (
        <span className="font-display text-lg font-semibold tracking-tight">
          UPI <span className="text-primary">Guardian</span>
        </span>
      )}
    </span>
  );
}
