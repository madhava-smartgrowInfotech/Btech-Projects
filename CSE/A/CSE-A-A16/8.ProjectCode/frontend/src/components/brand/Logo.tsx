import { useId } from "react";

import { cn } from "@/lib/utils";

export function LogoMark({ className }: { className?: string }) {
  const id = useId().replace(/:/g, "");
  return (
    <svg viewBox="0 0 32 32" fill="none" className={cn("size-8 shrink-0", className)} aria-hidden="true">
      <defs>
        <linearGradient id={`ss-${id}`} x1="2" y1="2" x2="30" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7C5CFF" />
          <stop offset="0.55" stopColor="#B06BF0" />
          <stop offset="1" stopColor="#22D3EE" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="30" height="30" rx="9" fill={`url(#ss-${id})`} />
      <rect x="1.5" y="1.5" width="29" height="29" rx="8.5" stroke="#fff" strokeOpacity=".35" />
      {/* open hand */}
      <path
        d="M11 25.5c-1.7-1.5-3-3.6-3.4-5.2l-.9-3.6c-.2-.9.9-1.5 1.5-.8l1.6 1.9V9.4a1.3 1.3 0 0 1 2.6 0V15h.5V7.9a1.3 1.3 0 0 1 2.6 0V15h.5V8.9a1.3 1.3 0 0 1 2.6 0V15h.5v-3.6a1.3 1.3 0 0 1 2.6 0v7.2c0 3.2-1.9 5.9-4.7 6.9-2.2.8-4.3.4-6-.1Z"
        fill="#fff"
        fillOpacity=".96"
      />
      {/* sound waves */}
      <path d="M25.2 6.6a6.2 6.2 0 0 1 0 6.1" stroke="#fff" strokeOpacity=".85" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M27.6 4.6a9.4 9.4 0 0 1 0 10.1" stroke="#fff" strokeOpacity=".5" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

export function Logo({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark />
      {!compact && (
        <span className="font-display text-lg font-bold tracking-tight">
          Sign<span className="text-gradient">Speak</span>
        </span>
      )}
    </span>
  );
}
