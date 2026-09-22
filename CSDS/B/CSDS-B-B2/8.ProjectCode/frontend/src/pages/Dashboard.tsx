import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { ArrowRight, BrainCircuit, CheckCircle2, Database, QrCode, Server, XCircle } from "lucide-react";
import { PageHeader, ErrorState } from "@/components/common/states";
import { ROLE_LABEL } from "@/components/layout/UserMenu";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api, apiError, type Health } from "@/lib/api";
import { useAuth } from "@/lib/auth";

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
      <span className={ok ? "text-xs text-muted-foreground" : "text-xs font-medium text-zone-dead"}>{detail ?? (ok ? "Ready" : "Missing")}</span>
    </li>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const health = useQuery({ queryKey: ["health"], queryFn: async () => (await api.get<Health>("/api/health")).data, refetchInterval: 30_000 });
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

  return (
    <>
      <PageHeader title={`${greeting}, ${user?.name.split(" ")[0] ?? ""}`} description={`Signed in as ${user ? ROLE_LABEL[user.role] : ""}. Here is the state of this SignalScout installation.`} />

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
