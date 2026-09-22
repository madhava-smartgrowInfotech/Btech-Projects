import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { CircleCheck, CircleX, Clock, Gauge, MapPin, MonitorSmartphone, Play, Radio, Square, TriangleAlert, Upload, Wifi, WifiOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ProbeController } from "@/lib/probe/useProbe";
import { cn, timeAgo } from "@/lib/utils";
import { ZONE_COLOR, type ZoneLabel } from "@/lib/zones";

const ICON = { Strong: CircleCheck, Weak: TriangleAlert, Dead: CircleX } as const;

function Meter({ label, confidence, provisional, measuring }: { label: ZoneLabel | null; confidence: number | null; provisional: boolean; measuring: boolean }) {
  const color = label ? ZONE_COLOR[label] : "hsl(var(--muted-foreground))";
  const fill = label === "Strong" ? 1 : label === "Weak" ? 0.55 : label === "Dead" ? 0.12 : 0;
  const r = 84;
  const c = 2 * Math.PI * r;
  const Icon = label ? ICON[label] : Radio;
  return (
    <div className="relative mx-auto h-56 w-56">
      <svg viewBox="0 0 200 200" className="h-full w-full -rotate-90" aria-hidden>
        <circle cx="100" cy="100" r={r} fill="none" stroke="hsl(var(--muted))" strokeWidth="14" />
        <motion.circle
          cx="100" cy="100" r={r} fill="none" stroke={color} strokeWidth="14" strokeLinecap="round" strokeDasharray={c}
          initial={false} animate={{ strokeDashoffset: c * (1 - fill) }} transition={{ type: "spring", stiffness: 80, damping: 18 }}
        />
      </svg>
      {measuring && <span className="absolute inset-3 rounded-full border-2 border-primary/40 animate-pulsering" aria-hidden />}
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center" role="status" aria-live="polite">
        <Icon className="h-8 w-8" style={{ color }} aria-hidden />
        <p className="mt-1 font-display text-3xl font-bold" style={{ color: label === "Weak" ? "#b77800" : color }}>{label ?? "—"}</p>
        <p className="text-xs text-muted-foreground">
          {label ? (provisional ? "provisional · syncing" : confidence != null ? `${Math.round(confidence * 100)}% confidence` : "measured") : "no reading yet"}
        </p>
      </div>
    </div>
  );
}

function Stat({ icon: Icon, label, value, unit }: { icon: typeof Clock; label: string; value: string | null; unit: string }) {
  return (
    <div className="rounded-xl border bg-card p-3">
      <p className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        <Icon className="h-3.5 w-3.5" aria-hidden /> {label}
      </p>
      <p className="mt-1 font-mono text-lg font-semibold tabular">
        {value ?? "–"} <span className="text-xs font-normal text-muted-foreground">{value ? unit : ""}</span>
      </p>
    </div>
  );
}

function Chip({ ok, children }: { ok: boolean; children: React.ReactNode }) {
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs", ok ? "border-zone-strong/40 text-foreground" : "border-zone-weak/50 bg-zone-weak/10")}>
      <span className={cn("h-1.5 w-1.5 rounded-full", ok ? "bg-zone-strong" : "bg-zone-weak")} aria-hidden />
      {children}
    </span>
  );
}

export function LiveTab({ probe }: { probe: ProbeController }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(t);
  }, []);
  const rec = probe.last;
  const r = rec?.reading;
  const label = (rec?.server?.zone_label ?? rec?.provisional.label ?? null) as ZoneLabel | null;
  const reasons = rec?.server?.reasons?.length ? rec.server.reasons : rec?.provisional.reasons ?? [];
  const next = probe.nextAt ? Math.max(0, Math.ceil((probe.nextAt - now) / 1000)) : null;
  const acc = probe.position?.coords.accuracy;
  const lastSpeed = probe.records.find((x) => x.reading.dl_mbps != null)?.reading;   // speed is tested every few readings

  return (
    <div className="space-y-5">
      <Meter label={label} confidence={rec?.server?.zone_confidence ?? null} provisional={!!rec && !rec.server} measuring={probe.measuring} />

      <div className="flex flex-wrap justify-center gap-1.5">
        <Chip ok={probe.online}>{probe.online ? <>Online</> : <><WifiOff className="h-3 w-3" /> Offline</>}</Chip>
        <Chip ok={!!probe.position && (acc ?? 999) <= 50}>
          <MapPin className="h-3 w-3" /> {probe.position ? `GPS ±${Math.round(acc ?? 0)} m` : "No GPS yet"}
        </Chip>
        {probe.running && <Chip ok={probe.awake}><MonitorSmartphone className="h-3 w-3" /> {probe.awake ? "Screen kept on" : "Screen may sleep"}</Chip>}
        <Chip ok={probe.queued === 0}>{probe.queued === 0 ? "All synced" : `${probe.queued} waiting to sync`}</Chip>
      </div>

      <div className="rounded-2xl border bg-card p-4">
        <Button size="lg" className="h-14 w-full text-base" variant={probe.running ? "outline" : "default"} onClick={probe.running ? probe.stop : probe.start}>
          {probe.running ? <><Square className="fill-current" /> Stop measuring</> : <><Play className="fill-current" /> Start measuring</>}
        </Button>
        <p className="mt-2 text-center text-xs text-muted-foreground">
          {probe.running
            ? probe.phase || (next != null ? `Next reading in ${next} s · every ${probe.settings.intervalS} s` : "Starting…")
            : "Keep this screen open while you walk. Readings are saved on the phone first."}
        </p>
        {probe.gpsError && <p className="mt-2 rounded-lg bg-zone-weak/15 px-3 py-2 text-xs" role="alert">{probe.gpsError}</p>}
      </div>

      <div className="grid grid-cols-2 gap-2.5">
        <Stat icon={Clock} label="Latency" value={r?.latency_ms != null ? String(Math.round(r.latency_ms)) : null} unit="ms" />
        <Stat icon={Wifi} label="Jitter · loss" value={r?.jitter_ms != null ? `${Math.round(r.jitter_ms)} · ${Math.round((r.packet_loss ?? 0) * 100)}%` : null} unit="ms" />
        <Stat icon={Gauge} label="Download" value={lastSpeed?.dl_mbps != null ? lastSpeed.dl_mbps.toFixed(1) : null} unit="Mbps" />
        <Stat icon={Upload} label="Upload" value={lastSpeed?.ul_mbps != null ? lastSpeed.ul_mbps.toFixed(1) : null} unit="Mbps" />
      </div>

      {rec && (
        <div className="rounded-2xl border bg-card p-4 text-sm">
          <p className="font-medium">Why {label}</p>
          <ul className="mt-1.5 list-disc space-y-1 pl-5 text-muted-foreground">
            {reasons.slice(0, 3).map((x) => <li key={x}>{x}</li>)}
          </ul>
          {rec.server?.radio_estimate && (
            <p className="mt-3 border-t pt-3 text-xs text-muted-foreground">
              Estimated radio condition from the speed test: <strong className="text-foreground">{rec.server.radio_estimate}</strong> ({Math.round((rec.server.radio_estimate_conf ?? 0) * 100)}%). This is an estimate; the class above is measured.
            </p>
          )}
          <p className="mt-3 text-xs text-muted-foreground">
            Last reading {timeAgo(r?.ts)}
            {lastSpeed ? ` · speed tested ${timeAgo(lastSpeed.ts)}` : probe.settings.dataSaver || !probe.settings.speedtestS ? " · speed tests off" : ""}
          </p>
        </div>
      )}
    </div>
  );
}
