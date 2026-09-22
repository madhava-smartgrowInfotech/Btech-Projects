import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BrainCircuit, CircleCheck, FlaskConical, Info, Navigation, Radio } from "lucide-react";
import { StatTile } from "@/components/charts/charts";
import { ErrorState, PageHeader } from "@/components/common/states";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api, apiError, TOKEN_KEY } from "@/lib/api";
import { cn, formatDateTime, safeStorage } from "@/lib/utils";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

const PROFILE = { full: "All metrics", no_sinr_cqi: "No SINR/CQI", level_only: "Level only", rssi_only: "RSSI only" } as Record<string, string>;
const f3 = (v: number | null | undefined) => (v == null ? "–" : v.toFixed(3));
const pct = (v: number | null | undefined) => (v == null ? "–" : `${(v * 100).toFixed(1)}%`);

/** Plots are served with authentication, so they are fetched and shown as object URLs. */
function AuthImage({ run, file, alt }: { run: string; file: string; alt: string }) {
  const [src, setSrc] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let url: string | null = null;
    const token = safeStorage.get(TOKEN_KEY);
    fetch(`/api/ml/models/${run}/artifacts/${file}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then((r) => (r.ok ? r.blob() : Promise.reject()))
      .then((b) => { url = URL.createObjectURL(b); setSrc(url); })
      .catch(() => setFailed(true));
    return () => { if (url) URL.revokeObjectURL(url); };
  }, [run, file]);
  if (failed) return <p className="text-xs text-muted-foreground">Plot not available.</p>;
  if (!src) return <Skeleton className="aspect-[16/10] w-full" />;
  return <img src={src} alt={alt} className="w-full rounded-lg border bg-white" loading="lazy" />;
}

function Table({ head, rows, highlight }: { head: string[]; rows: (string | number)[][]; highlight?: number }) {
  return (
    <div className="overflow-x-auto" tabIndex={0} role="region" aria-label={head.join(", ")}>
      <table className="w-full min-w-[520px] text-sm">
        <thead className="text-left text-xs text-muted-foreground">
          <tr>{head.map((h) => <th key={h} className="whitespace-nowrap py-2 pr-3 font-medium">{h}</th>)}</tr>
        </thead>
        <tbody className="divide-y">
          {rows.map((r, i) => (
            <tr key={i} className={cn(i === highlight && "bg-primary/5 font-medium")}>
              {r.map((c, j) => <td key={j} className={cn("py-2 pr-3", j > 0 && "font-mono tabular")}>{c}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Note({ children }: { children: React.ReactNode }) {
  return <p className="flex gap-2 rounded-lg border border-primary/20 bg-primary/5 px-3 py-2 text-sm"><Info className="mt-0.5 h-4 w-4 shrink-0 text-primary" /><span>{children}</span></p>;
}

function Plots({ run, files, labels }: { run: string; files: string[]; labels: Record<string, string> }) {
  const shown = Object.keys(labels).filter((f) => files.includes(f));
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {shown.map((f) => (
        <figure key={f}>
          <AuthImage run={run} file={f} alt={labels[f]!} />
          <figcaption className="mt-1.5 text-xs text-muted-foreground">{labels[f]}</figcaption>
        </figure>
      ))}
    </div>
  );
}

function ZoneClassifier({ m }: { m: Any }) {
  const cv = m.cross_validation.results;
  const methods = Object.keys(cv);
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Chosen model" value={<span className="text-2xl">{m.chosen}</span>} hint="Best cross-validated macro-F1" />
        <StatTile label="Test accuracy" value={pct(m.test_overall.accuracy)} hint={`${m.dataset.splits.test.traces} held-out traces`} />
        <StatTile label="Test macro-F1" value={f3(m.test_overall.macro_f1)} hint="Across all four device profiles" />
        <StatTile label="Calibration error" value={f3(m.calibration.ece_after)} hint={`was ${f3(m.calibration.ece_before)} before temperature ${m.temperature.toFixed(2)}`} />
      </div>
      <Card>
        <CardHeader className="pb-2"><CardTitle>Cross-validation ({m.cross_validation.folds} folds, by trace)</CardTitle>
          <CardDescription>Macro-F1 mean ± spread over folds. Baselines: the documented ranges on whatever the device reports, and a single tuned threshold.</CardDescription></CardHeader>
        <CardContent>
          <Table head={["Method", ...m.profiles.map((p: string) => PROFILE[p]), "Mean"]} highlight={methods.indexOf(m.chosen)}
            rows={methods.map((k) => [k, ...m.profiles.map((p: string) => `${f3(cv[k][p].mean)} ± ${cv[k][p].std.toFixed(3)}`), f3(cv[k].mean_macro_f1.mean)])} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2"><CardTitle>Held-out test traces</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Table head={["Method", ...m.profiles.map((p: string) => PROFILE[p]), "Mean"]} highlight={Object.keys(m.test).indexOf(m.chosen)}
            rows={Object.keys(m.test).map((k) => [k, ...m.profiles.map((p: string) => f3(m.test[k][p].macro_f1)), f3(m.test[k].mean_macro_f1)])} />
          <Note>With every metric present the labels follow directly from the documented ranges, so the ranges and the learned models reach 1.00 there by construction.
            The model earns its place when metrics are missing: devices without SINR/CQI score clearly higher than the ranges alone. With a single level or RSSI it is on par with a tuned threshold - there is no more information to use - and unlike the fixed ranges it does not collapse on RSSI-only devices.</Note>
        </CardContent>
      </Card>
      <Plots run={m.run} files={m.plots} labels={{
        "cv_profile_scores.png": "Cross-validated macro-F1 by device profile, models vs baselines",
        "confusion_matrix.png": `Confusion matrices of the ${m.chosen} on the test traces`,
        "calibration.png": "Confidence calibration: predicted confidence vs observed accuracy",
        "feature_importance.png": "Permutation importance: drop in macro-F1 when a feature is shuffled",
        "profile_scores.png": "Test macro-F1 by device profile",
        "mlp_training.png": "Neural network training: loss and validation macro-F1 per epoch",
      }} />
      <Card>
        <CardHeader className="pb-2"><CardTitle>Labels and data</CardTitle></CardHeader>
        <CardContent className="space-y-3 text-sm">
          <Table head={["Technology", "Metric", "Strong at or above", "Dead below"]} rows={Object.entries(m.labels.ranges).flatMap(([fam, bands]: [string, Any]) =>
            Object.entries(bands).map(([metric, [weak, dead]]: [string, Any]) => [fam === "lte_nr" ? "LTE / NR" : fam.toUpperCase(), metric === "level" ? (fam === "3g" ? "RSCP" : fam === "2g" ? "RSSI" : "RSRP") : metric === "quality" ? (fam === "3g" ? "Ec/No" : "RSRQ") : "SINR", weak, dead ?? "–"]))} />
          <p className="text-muted-foreground">{m.dataset.name}, {m.dataset.date_range[0].slice(0, 10)} to {m.dataset.date_range[1].slice(0, 10)} · split {m.dataset.split_method}. Train {m.dataset.splits.train.rows.toLocaleString()} rows, validation {m.dataset.splits.val.rows.toLocaleString()}, test {m.dataset.splits.test.rows.toLocaleString()} (four device profiles each). Trained {formatDateTime(m.created_at)}, run {m.run}.</p>
          <p className="text-muted-foreground">Consistency check on the Patna measurements (signal level only): accuracy {pct(m.consistency_check.accuracy)}. {m.consistency_check.note}</p>
        </CardContent>
      </Card>
    </div>
  );
}

function RadioEstimate({ m }: { m: Any }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Per speed test macro-F1" value={f3(m.test_per_speed_test.macro_f1)} hint={`accuracy ${pct(m.test_per_speed_test.accuracy)}`} />
        <StatTile label="Per zone macro-F1" value={f3(m.test_per_zone.macro_f1)} hint={`${m.test_per_zone.zones} zones, accuracy ${pct(m.test_per_zone.accuracy)}`} />
        <StatTile label="Bad-zone detection F1" value={f3(m.test_per_zone.bad_zone_detection?.f1)} hint={m.test_per_zone.bad_zone_detection?.definition} />
        <StatTile label="Calibration error" value={f3(m.calibration.ece)} />
      </div>
      <Note>{m.interpretation}</Note>
      <Card>
        <CardHeader className="pb-2"><CardTitle>Against baselines (test traces)</CardTitle></CardHeader>
        <CardContent>
          <Table head={["Method", "Accuracy", "Macro-F1"]} highlight={0} rows={[
            ["Speed-test model", pct(m.test_per_speed_test.accuracy), f3(m.test_per_speed_test.macro_f1)],
            ["Tuned speed threshold", pct(m.baselines.tuned_speed_threshold.accuracy), f3(m.baselines.tuned_speed_threshold.macro_f1)],
            ["Always the majority class", pct(m.baselines.always_majority.accuracy), f3(m.baselines.always_majority.macro_f1)],
          ]} />
        </CardContent>
      </Card>
      <Plots run={m.run} files={m.plots} labels={{ "confusion_matrix.png": "Confusion matrices per speed test and per zone", "baselines.png": "Model vs baselines", "calibration.png": "Confidence calibration" }} />
    </div>
  );
}

function BetterSignal({ m }: { m: Any }) {
  return (
    <div className="space-y-4">
      {Object.entries(m.targets).map(([t, r]: [string, Any]) => {
        const methods = Object.keys(r.block_cv);
        return (
          <Card key={t}>
            <CardHeader className="pb-2"><CardTitle>{r.label}</CardTitle>
              <CardDescription>Error on 200 m blocks held out entirely ({r.areas} evaluation areas), predicting as the live service does.</CardDescription></CardHeader>
            <CardContent className="space-y-3">
              <Table head={["Method", `RMSE (${r.unit})`, `MAE (${r.unit})`, "Strong/not agreement"]} highlight={0}
                rows={methods.map((k) => [k, f3(r.block_cv[k].rmse), f3(r.block_cv[k].mae), pct(r.block_cv[k].strong_agreement)])} />
              <p className="text-sm text-muted-foreground">
                Uncertainty bands: {pct(r.coverage["95%"])} of held-out readings fall inside the 95% band ({pct(r.coverage["68%"])} inside the 68% band).
                Random-point hold-out RMSE (easier) {f3(r.random_holdout_rmse)}. Length scales {Math.round(r.params.ls_short)} m (street level) and {Math.round(r.params.ls_long)} m (area trend).
              </p>
            </CardContent>
          </Card>
        );
      })}
      <Plots run={m.run} files={m.plots} labels={{ "rmse_comparison.png": "Interpolation error vs baselines", "surface_rsrp.png": "Predicted signal surface with the Strong threshold", "interval_calibration.png": "Are the uncertainty bands honest?", "residuals.png": "Residuals on held-out blocks" }} />
      <p className="text-xs text-muted-foreground">Kernel: {m.kernel}. Run {m.run}, trained {formatDateTime(m.created_at)}.</p>
    </div>
  );
}

function FieldValidation() {
  const q = useQuery({ queryKey: ["field-validation"], queryFn: async () => (await api.get<Any>("/api/ml/field-validation")).data, refetchInterval: 60_000 });
  if (q.isPending) return <Skeleton className="h-64" />;
  if (q.isError) return <ErrorState message={apiError(q.error)} onRetry={() => q.refetch()} />;
  const d = q.data;
  const labels = ["Strong", "Weak", "Dead"];
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Card>
        <CardHeader className="pb-2"><CardTitle className="flex items-center gap-2"><Navigation className="h-4 w-4 text-primary" /> Better-signal predictor</CardTitle>
          <CardDescription>Your own phone speed tests: 20% of measured spots are hidden and predicted from the rest.</CardDescription></CardHeader>
        <CardContent className="text-sm">
          {d.gp.rmse_log10_mbps != null ? (
            <>
              <p className="font-mono text-2xl font-semibold tabular">{d.gp.rmse_log10_mbps.toFixed(3)} <span className="text-sm font-normal text-muted-foreground">RMSE, log10 Mbps</span></p>
              <p className="mt-1 text-muted-foreground">Mean-only baseline {d.gp.mean_baseline_rmse.toFixed(3)} · {Math.round((d.gp.improvement ?? 0) * 100)}% better · {d.gp.cells} measured spots ({d.gp.operator})</p>
            </>
          ) : <p className="text-muted-foreground">{d.gp.note} ({d.gp.cells} so far)</p>}
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2"><CardTitle className="flex items-center gap-2"><FlaskConical className="h-4 w-4 text-primary" /> Phone probe</CardTitle>
          <CardDescription>Measured class vs the speed-based radio estimate - agreement, not accuracy (different questions).</CardDescription></CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>{d.probe.readings.toLocaleString()} readings · {d.probe.with_speed_test.toLocaleString()} with a speed test</p>
          {d.probe.agreement != null ? (
            <>
              <p className="text-muted-foreground">Agreement {pct(d.probe.agreement)}</p>
              <Table head={["Measured \\ estimate", ...labels]} rows={labels.map((a, i) => [a, ...d.probe.matrix[i]])} />
            </>
          ) : <p className="text-muted-foreground">Appears after the first speed tests.</p>}
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2"><CardTitle className="flex items-center gap-2"><Radio className="h-4 w-4 text-primary" /> Radio readings</CardTitle>
          <CardDescription>Field devices that report radio metrics (for example an ESP32 with a cellular modem).</CardDescription></CardHeader>
        <CardContent className="text-sm">
          {d.radio.readings ? (
            <p>{d.radio.readings} readings · model agrees with the documented ranges on {pct(d.radio.agreement_with_ranges)} · mean confidence {pct(d.radio.mean_confidence)}</p>
          ) : <p className="text-muted-foreground">{d.radio.note}</p>}
        </CardContent>
      </Card>
    </div>
  );
}

export default function ModelPerformance() {
  const q = useQuery({ queryKey: ["ml-models"], queryFn: async () => (await api.get<Any>("/api/ml/models")).data });
  return (
    <>
      <PageHeader title="Model performance" description="How each model was trained and evaluated, and how it behaves on the readings collected here. All figures come from the training runs in experiments/ and from live data." />
      {q.isPending ? <div className="space-y-4"><Skeleton className="h-10 w-96" /><Skeleton className="h-72" /></div> : q.isError ? <ErrorState message={apiError(q.error)} onRetry={() => q.refetch()} /> : (
        <Tabs defaultValue="zone">
          <TabsList className="h-auto flex-wrap">
            <TabsTrigger value="zone"><BrainCircuit /> Zone classifier</TabsTrigger>
            <TabsTrigger value="estimate"><FlaskConical /> Radio estimate</TabsTrigger>
            <TabsTrigger value="gp"><Navigation /> Better-signal predictor</TabsTrigger>
            <TabsTrigger value="field"><CircleCheck /> Field validation</TabsTrigger>
          </TabsList>
          <div className="mt-2 flex flex-wrap gap-2">
            {Object.entries(q.data.loaded as Record<string, { loaded: boolean; version: string | null }>).map(([k, v]) => (
              <Badge key={k} variant={v.loaded ? "success" : "destructive"}>{k.replace(/_/g, " ")}: {v.loaded ? v.version : "not loaded"}</Badge>
            ))}
          </div>
          <TabsContent value="zone">{q.data.models.zone_classifier ? <ZoneClassifier m={q.data.models.zone_classifier} /> : <p>Not trained yet.</p>}</TabsContent>
          <TabsContent value="estimate">{q.data.models.radio_estimate ? <RadioEstimate m={q.data.models.radio_estimate} /> : <p>Not trained yet.</p>}</TabsContent>
          <TabsContent value="gp">{q.data.models.gp_signal ? <BetterSignal m={q.data.models.gp_signal} /> : <p>Not trained yet.</p>}</TabsContent>
          <TabsContent value="field"><FieldValidation /></TabsContent>
        </Tabs>
      )}
    </>
  );
}
