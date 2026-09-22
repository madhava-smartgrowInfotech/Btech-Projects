import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
import { Activity, List, Navigation, RefreshCw, Settings, TriangleAlert, Wifi } from "lucide-react";
import { toast } from "sonner";
import { LogoMark } from "@/components/brand/Logo";
import { FullPageLoader } from "@/components/common/loader";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import { probeStore, type ProbeMeta } from "@/lib/probe/store";
import { useProbe } from "@/lib/probe/useProbe";
import { cn } from "@/lib/utils";
import { LiveTab } from "./LiveTab";
import { LogTab, SettingsTab, SyncTab } from "./OtherTabs";
import { Pair } from "./Pair";
import { SignalTab } from "./SignalTab";

type Tab = "live" | "signal" | "log" | "sync" | "settings";
const TABS: { id: Tab; label: string; icon: typeof Activity }[] = [
  { id: "live", label: "Live", icon: Activity },
  { id: "signal", label: "Better signal", icon: Navigation },
  { id: "log", label: "Readings", icon: List },
  { id: "sync", label: "Sync", icon: RefreshCw },
  { id: "settings", label: "Settings", icon: Settings },
];

function ProbeMain({ meta, onUnpair }: { meta: ProbeMeta; onUnpair: () => void }) {
  const probe = useProbe(meta);
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>("live");
  const carrier = probe.whoami?.carrier;
  const operator = probe.settings.operator ?? probe.sync?.operator ?? carrier?.operator ?? null;
  const onWifi = probe.sync?.link === "wifi" || carrier?.kind === "broadband" || carrier?.kind === "local";

  return (
    <div className="mx-auto flex min-h-dvh max-w-lg flex-col">
      <header className="sticky top-0 z-20 flex items-center gap-2 border-b bg-background/90 px-4 py-3 backdrop-blur">
        <LogoMark className="h-7 w-7" />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-semibold leading-tight">Field probe</p>
          <p className="truncate text-xs text-muted-foreground">
            {operator ? `${operator} · ${onWifi ? "Wi-Fi" : "mobile data"}` : "Detecting operator…"}
          </p>
        </div>
        {probe.running && (
          <span className="flex items-center gap-1.5 rounded-full bg-zone-strong/15 px-2.5 py-1 text-xs font-medium text-[hsl(120_70%_28%)] dark:text-[hsl(120_60%_62%)]">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-zone-strong" aria-hidden /> Measuring
          </span>
        )}
        <ThemeToggle />
      </header>

      <AnimatePresence>
        {onWifi && (
          <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }} className="overflow-hidden">
            <p className="flex items-start gap-2 border-b border-zone-weak/40 bg-zone-weak/15 px-4 py-2.5 text-xs">
              <Wifi className="mt-0.5 h-4 w-4 shrink-0" aria-hidden /> You're on Wi-Fi. Switch Wi-Fi off so SignalScout measures your mobile network - readings over Wi-Fi are kept separate.
            </p>
          </motion.div>
        )}
        {probe.needsPairing && (
          <p className="flex items-center gap-2 border-b border-destructive/30 bg-destructive/10 px-4 py-2.5 text-xs" role="alert">
            <TriangleAlert className="h-4 w-4 shrink-0" /> This phone's key was replaced.
            <Button size="sm" variant="outline" className="ml-auto h-7" onClick={onUnpair}>Register again</Button>
          </p>
        )}
      </AnimatePresence>

      <main className="flex-1 px-4 pb-28 pt-5">
        <motion.div key={tab} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.18 }}>
          {tab === "live" && <LiveTab probe={probe} />}
          {tab === "signal" && <SignalTab probe={probe} />}
          {tab === "log" && <LogTab probe={probe} />}
          {tab === "sync" && <SyncTab probe={probe} meta={meta} />}
          {tab === "settings" && (
            <SettingsTab probe={probe} meta={meta} onUnpair={() => { probe.stop(); onUnpair(); }}
              onSignOut={() => { probe.stop(); logout(); toast.success("Signed out"); navigate("/login?next=/probe"); }} />
          )}
        </motion.div>
      </main>

      <nav className="safe-bottom fixed inset-x-0 bottom-0 z-20 border-t bg-background/95 backdrop-blur" aria-label="Probe">
        <ul className="mx-auto grid max-w-lg grid-cols-5">
          {TABS.map((t) => (
            <li key={t.id}>
              <button
                onClick={() => setTab(t.id)}
                aria-current={tab === t.id ? "page" : undefined}
                className={cn("relative flex w-full flex-col items-center gap-1 pb-1 pt-2.5 text-[11px] font-medium", tab === t.id ? "text-primary" : "text-muted-foreground")}
              >
                {tab === t.id && <motion.span layoutId="probe-tab" className="absolute inset-x-5 top-0 h-0.5 rounded-full bg-primary" />}
                <span className="relative">
                  <t.icon className="h-5 w-5" aria-hidden />
                  {t.id === "sync" && probe.queued > 0 && (
                    <span className="absolute -right-2.5 -top-1.5 rounded-full bg-zone-weak px-1 text-[9px] font-bold text-black tabular">{probe.queued > 99 ? "99+" : probe.queued}</span>
                  )}
                </span>
                {t.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}

export default function ProbeApp() {
  const { user } = useAuth();
  const [meta, setMeta] = useState<ProbeMeta | null | undefined>(undefined);
  useEffect(() => {
    void probeStore.getMeta().then((m) => setMeta(m && m.userId === user?.id ? m : null));
  }, [user?.id]);
  if (meta === undefined) return <FullPageLoader label="Opening the field probe" />;
  if (!meta) return <Pair onPaired={setMeta} />;
  return (
    <ProbeMain
      meta={meta}
      onUnpair={async () => {
        await probeStore.clearMeta();
        setMeta(null);
      }}
    />
  );
}
