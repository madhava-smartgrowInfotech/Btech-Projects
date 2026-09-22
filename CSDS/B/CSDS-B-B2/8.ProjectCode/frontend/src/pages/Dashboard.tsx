import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { Activity, ArrowRight, BarChart3, BrainCircuit, CheckCircle2, Database, FileWarning, MapPinned, QrCode, Server, ShieldCheck, XCircle } from "lucide-react";
import { ClassShareChart, StatTile } from "@/components/charts/charts";
import { ComplaintList } from "@/components/complaints/ComplaintList";
import { EmptyState, PageHeader, ErrorState } from "@/components/common/states";
import { ROLE_LABEL } from "@/components/layout/UserMenu";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { hoursText, useSummary, useTrends, type AnalyticsFilters } from "@/lib/analytics";
import { api, apiError, hasRole, type Health } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { OPEN, type ComplaintPage } from "@/lib/complaints";

const FILTERS: AnalyticsFilters = { operator: null, days: 30, includeSample: true };

const MODEL_NAMES: Record<string, string> = {
  zone_classifier: "Zone classifier",
  radio_estimate: "Radio-condition estimate",
  gp_signal: "Better-signal predictor",
};

function StatusRow({ ok, label, detail }: { ok: boolean; label: string; detail?: string }) {
  return (
    <li className="flex items-center justify-between gap-3 py-2">
      <span className="flex items-center gap-2 text-sm">
        {ok ? <CheckCircle2 className="h-4 w-4 text-zone-strong" aria-hidden /> : <XCircle className="h-4 w-4 text-zone-dead" aria-hidden />}
        {label}
      </span>
      <span className={ok ? "text-xs text-muted-foreground" : "text-xs font-medium text-ink-dead"}>{detail ?? (ok ? "Ready" : "Missing")}</span>
    </li>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const health = useQuery({ queryKey: ["health"], queryFn: async () => (await api.get<Health>("/api/health")).data, refetchInterval: 30_000 });
  const summary = useSummary(FILTERS);
  const trends = useTrends(FILTERS);
  const recent = useQuery({
    queryKey: ["complaints", "dashboard"],
    queryFn: async () => (await api.get<ComplaintPage>("/api/complaints", { params: { status: OPEN.join(","), limit: 4 } })).data,
    refetchInterval: 30_000,
  });
  const engineer = hasRole(user, "engineer");
  const s = summary.data;
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  return (
    <>
      <PageHeader title={`${greeting}, ${user?.name.split(" ")[0] ?? ""}`} description={`Signed in as ${user ? ROLE_LABEL[user.role] : ""}. Here is the state of this SignalScout installation.`} />

      {summary.isError ? <ErrorState message={apiError(summary.error)} onRetry={() => summary.refetch()} className="mb-4" /> : (
        <div className="mb-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
          {!s ? [0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-28" />) : (
            <>
              <StatTile icon={<MapPinned className="h-4 w-4" />} label="Zones monitored" value={s.zones_monitored.toLocaleString()} hint={`${s.readings_total.toLocaleString()} readings`} />
              <StatTile icon={<BarChart3 className="h-4 w-4" />} label="Weak or dead zones" value={s.zones_bad.toLocaleString()} tone={s.zones_dead ? "bad" : undefined}
                hint={s.bad_zone_share != null ? `${Math.round(s.bad_zone_share * 100)}% of zones · ${s.zones_dead} dead` : "No zones yet"} />
              <StatTile icon={<FileWarning className="h-4 w-4" />} label="Open complaints" value={s.complaints_open}
                hint={engineer ? `${s.complaints_needing_action} waiting for action` : `${s.complaints_verified} fixes verified`} />
              {engineer ? (
                <StatTile icon={<ShieldCheck className="h-4 w-4" />} label="Median time to resolve" value={hoursText(s.median_hours_to_resolve)} hint={`${s.complaints_verified} fixes verified`} />
              ) : (
                <StatTile icon={<Activity className="h-4 w-4" />} label="Your readings" value={(s.mine?.readings ?? 0).toLocaleString()} hint={`${s.mine?.complaints ?? 0} complaints from your data`} />
              )}
            </>
          )}
        </div>
      )}

      <div className="mb-4 grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <Card className="flex flex-col">
          <CardHeader className="pb-3">
            <CardTitle>Service quality, last 30 days</CardTitle>
            <CardDescription>Share of readings in each class per day. <Link to="/app/analytics" className="text-primary underline underline-offset-2">Open analytics</Link></CardDescription>
          </CardHeader>
          <CardContent className="flex min-h-[300px] flex-1 flex-col">
            {trends.isPending ? <Skeleton className="flex-1" /> : trends.isError ? <ErrorState message={apiError(trends.error)} /> :
              trends.data.some((d) => d.readings) ? <ClassShareChart data={trends.data} className="flex-1" /> : <p className="py-16 text-center text-sm text-muted-foreground">No readings in the last 30 days.</p>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex-row items-start justify-between gap-3 space-y-0 pb-3">
            <div>
              <CardTitle>Open complaints</CardTitle>
              <CardDescription className="mt-1.5">{engineer ? "Most recently updated in the queue." : "Complaints from zones you measured."}</CardDescription>
            </div>
            <Button asChild variant="ghost" size="sm"><Link to={engineer ? "/app/desk" : "/app/complaints"}>View all <ArrowRight /></Link></Button>
          </CardHeader>
          <CardContent>
            {recent.isPending ? <div className="space-y-2">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-14" />)}</div>
              : recent.isError ? <ErrorState message={apiError(recent.error)} onRetry={() => recent.refetch()} />
              : recent.data.items.length ? <ComplaintList items={recent.data.items} />
              : <EmptyState icon={ShieldCheck} title="No open complaints" description="Zones that stay weak or dead are registered here automatically." className="py-8" />}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="h-4 w-4 text-primary" /> System status
              </CardTitle>
              <CardDescription>API, database and trained models</CardDescription>
            </CardHeader>
            <CardContent>
              {health.isPending ? (
                <div className="space-y-3">
                  {[0, 1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-5 w-full" />
                  ))}
                </div>
              ) : health.isError ? (
                <ErrorState message={apiError(health.error)} onRetry={() => health.refetch()} className="py-6" />
              ) : (
                <ul className="divide-y">
                  <StatusRow ok={health.data.status === "ok"} label="API server" detail={`v${health.data.version}`} />
                  <StatusRow ok={health.data.database === "ok"} label="Database" detail={health.data.database === "ok" ? "Connected" : health.data.database} />
                  {Object.entries(health.data.models).map(([k, ok]) => (
                    <StatusRow key={k} ok={ok} label={MODEL_NAMES[k] ?? k} detail={ok ? "Loaded" : "Not trained yet"} />
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <QrCode className="h-4 w-4 text-primary" /> Measure with your phone
              </CardTitle>
              <CardDescription>Open the field probe on an Android phone with Chrome - no app install needed.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <ol className="space-y-2 text-sm text-muted-foreground">
                <li>1. Scan the QR code on the Connect page.</li>
                <li>2. Sign in on the phone and allow location.</li>
                <li>3. Switch off Wi-Fi so the mobile network is measured.</li>
              </ol>
              <Button asChild variant="outline" className="w-full">
                <Link to="/app/connect">
                  Connect a phone <ArrowRight />
                </Link>
              </Button>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }} className="md:col-span-2 xl:col-span-1">
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BrainCircuit className="h-4 w-4 text-primary" /> How zones are judged
              </CardTitle>
              <CardDescription>Each reading gets a class and a confidence.</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2.5 text-sm">
                <li className="flex gap-2"><span className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full bg-zone-strong" aria-hidden /><span><strong>Strong</strong> - reliable calls and data.</span></li>
                <li className="flex gap-2"><span className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full bg-zone-weak" aria-hidden /><span><strong>Weak</strong> - slow, laggy or unstable service.</span></li>
                <li className="flex gap-2"><span className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full bg-zone-dead" aria-hidden /><span><strong>Dead</strong> - no usable connection.</span></li>
              </ul>
              <p className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
                <Database className="h-3.5 w-3.5" aria-hidden /> Zones that stay Weak or Dead become complaints automatically.
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </>
  );
}
