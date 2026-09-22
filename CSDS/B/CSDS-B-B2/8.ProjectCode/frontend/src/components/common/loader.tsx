import { LogoMark } from "@/components/brand/Logo";

export function FullPageLoader({ label = "Loading SignalScout" }: { label?: string }) {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-4" role="status" aria-live="polite">
      <div className="relative">
        <span className="absolute inset-0 rounded-full bg-primary/30 animate-pulsering" aria-hidden />
        <LogoMark className="relative h-12 w-12" />
      </div>
      <p className="text-sm text-muted-foreground">{label}…</p>
    </div>
  );
}
