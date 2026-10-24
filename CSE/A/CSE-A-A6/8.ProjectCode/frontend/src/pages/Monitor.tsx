import {
  Camera,
  CameraOff,
  CircleHelp,
  Cpu,
  Crosshair,
  Play,
  ShieldAlert,
  ShieldCheck,
  Square,
  TriangleAlert,
  Volume2,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";

import { EarTrace } from "@/components/monitor/EarTrace";
import { PreviewPanel } from "@/components/monitor/PreviewPanel";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ErrorState, ProgressBar, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { Select } from "@/components/ui/Select";
import { toast } from "@/components/ui/Toast";
import { Switch } from "@/components/ui/Toggles";
import { primeAudio } from "@/lib/alertSound";
import { useConfig } from "@/lib/queries";
import { useRiderSession } from "@/lib/useRiderSession";
import { cn } from "@/lib/utils";
import { fixed, verdictTone } from "@/lib/verdict";

function MonitorSkeleton() {
  return (
    <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]" role="status" aria-label="Starting a monitoring session">
      <div className="space-y-4">
        <Skeleton className="aspect-[4/3] w-full rounded-2xl" />
        <Skeleton className="h-40 w-full rounded-2xl" />
      </div>
      <div className="space-y-4">
        <Skeleton className="h-48 w-full rounded-2xl" />
        <Skeleton className="h-56 w-full rounded-2xl" />
      </div>
    </div>
  );
}

function Metric({ label, value, unit, hint }: { label: string; value: string; unit?: string; hint?: string }) {
  return (
    <div className="rounded-xl border border-[var(--glass-border)] bg-[var(--glass)] p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 font-display text-xl font-semibold tabular-nums">
        {value}
        {unit && <span className="ml-1 text-xs font-normal text-muted-foreground">{unit}</span>}
      </div>
      {hint && <div className="mt-0.5 text-[11px] text-muted-foreground">{hint}</div>}
    </div>
  );
}

export default function Monitor() {
  const config = useConfig();
  const [sound, setSound] = useState(false);
  const [scenario, setScenario] = useState<string | null>(null);
  const session = useRiderSession({ soundOn: sound });
  const { state, camera } = session;

  // follow the server's scenario once the session exists
  useEffect(() => {
    if (state && scenario === null) setScenario(state.scenario);
  }, [state, scenario]);

  // surface successful calibration / failures as toasts
  const status = state?.status ?? "";
  useEffect(() => {
    if (status.startsWith("Calibration saved")) toast.success(status);
    else if (status.startsWith("Calibration failed") || status.startsWith("Calibration timed out")) toast.error(status);
  }, [status]);

  if (session.error && !state) {
    return (
      <>
        <PageHeader title="Live monitor" />
        <ErrorState error={session.error} title="Couldn't start a monitoring session" hint="Check that run.bat is still running, then reload." onRetry={() => window.location.reload()} />
      </>
    );
  }
  if (!state) {
    return (
      <>
        <PageHeader title="Live monitor" description="Starting a monitoring session…" />
        <MonitorSkeleton />
      </>
    );
  }

  const source = state.source;
  const cameraOn = source === "camera";
  const simOn = source === "simulation";
  const verdict = state.state;
  const tone = verdictTone(verdict);
  const warning = verdict === state.verdicts.warning;
  const normal = verdict === state.verdicts.normal;
  const VerdictIcon = warning ? ShieldAlert : normal ? ShieldCheck : CircleHelp;
  const scenarios = config.data?.scenarios ?? [state.scenario];
  const chosen = scenario ?? state.scenario;
  const busy = session.busy !== null;
  const m = state.metrics;

  const startMonitoringDisabled = busy || source === "none" || state.calibrating;

  return (
    <>
      <PageHeader
        title="Live monitor"
        eyebrow="Smart Rider"
        description="Eye and head cues from your webcam, judged by explainable rules. A possible-impairment warning is never an alcohol result."
        actions={
          <label className="glass flex h-10 items-center gap-3 rounded-xl px-3 text-sm" htmlFor="sound-switch">
            <Volume2 className="size-4 text-muted-foreground" />
            Alert sound
            <Switch
              id="sound-switch"
              checked={sound}
              onCheckedChange={(v) => {
                setSound(v);
                if (v) primeAudio();
              }}
            />
          </label>
        }
      />

      {session.error && (
        <div role="alert" className="mb-4 flex items-start gap-3 rounded-2xl border border-danger/30 bg-danger/[0.07] p-4 text-sm">
          <TriangleAlert className="mt-0.5 size-4 shrink-0 text-danger" />
          <p className="flex-1">{session.error}</p>
          <button type="button" onClick={session.clearError} className="rounded p-0.5 text-muted-foreground hover:text-foreground" aria-label="Dismiss message">
            <X className="size-4" />
          </button>
        </div>
      )}
      {camera.error && !cameraOn && (
        <div role="alert" className="mb-4 flex items-start gap-3 rounded-2xl border border-warning/35 bg-warning/[0.08] p-4 text-sm">
          <CameraOff className="mt-0.5 size-4 shrink-0 text-warning" />
          <p className="flex-1">{camera.error}</p>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        {/* ------------------------------ left column: preview + controls + trace */}
        <div className="min-w-0 space-y-4">
          <PreviewPanel state={state} preview={session.preview} videoRef={camera.videoRef} cameraRunning={camera.running} />

          <Card>
            <CardBody className="space-y-4">
              <div className="flex flex-wrap items-end gap-3">
                {cameraOn ? (
                  <Button variant="secondary" onClick={() => void session.stopCamera()} loading={session.busy === "camera"}>
                    <CameraOff /> Stop camera
                  </Button>
                ) : (
                  <Button onClick={() => void session.startCamera()} loading={session.busy === "camera" || camera.state === "starting"} disabled={busy}>
                    <Camera /> Start camera
                  </Button>
                )}
                <div className="flex w-full flex-wrap items-end gap-2 sm:w-auto">
                  <div className="w-full sm:w-52">
                    <label htmlFor="scenario" className="mb-1 block text-xs text-muted-foreground">
                      Simulation scenario
                    </label>
                    <Select
                      id="scenario"
                      value={chosen}
                      options={scenarios.map((s) => ({ value: s, label: s }))}
                      onValueChange={(v) => {
                        setScenario(v);
                        // same as the desktop dropdown: switching scenario restarts the simulation and keeps monitoring
                        if (simOn) void session.startSimulation(v, state.monitoring);
                      }}
                    />
                  </div>
                  <Button variant={simOn ? "outline" : "secondary"} onClick={() => void session.startSimulation(chosen)} disabled={busy} loading={session.busy === "simulation"}>
                    <Cpu /> {simOn ? "Restart simulation" : "Simulation mode"}
                  </Button>
                </div>
              </div>

              <div className="flex flex-wrap gap-3 border-t border-[var(--glass-border)] pt-4">
                {state.monitoring ? (
                  <Button variant="danger" onClick={() => void session.setMonitoring(false)} loading={session.busy === "monitoring"}>
                    <Square /> Stop monitoring
                  </Button>
                ) : (
                  <Button onClick={() => void session.setMonitoring(true)} disabled={startMonitoringDisabled} loading={session.busy === "monitoring"}>
                    <Play /> Start monitoring
                  </Button>
                )}
                {state.calibrating ? (
                  <Button variant="outline" onClick={() => void session.setCalibration(false)} disabled={busy}>
                    <X /> Cancel calibration
                  </Button>
                ) : (
                  <Button variant="secondary" onClick={() => void session.setCalibration(true)} disabled={busy || !cameraOn} title={cameraOn ? undefined : "Calibration needs the live camera"}>
                    <Crosshair /> Calibrate
                  </Button>
                )}
              </div>
              {source === "none" && <p className="text-xs text-muted-foreground">Start the camera or Simulation mode first, then Start monitoring.</p>}
              {simOn && <p className="text-xs text-muted-foreground">Calibration uses real rider measurements only, so it is disabled in simulation.</p>}
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Eye aspect ratio" description="Smoothed EAR from the last few seconds. Below the dashed line counts as a closed eye." />
            <CardBody className="pt-3">
              {session.trace.length > 2 ? (
                <EarTrace points={session.trace} threshold={state.threshold} />
              ) : (
                <div className="grid h-36 place-items-center rounded-xl border border-dashed border-[var(--glass-border)] px-4 text-center text-sm text-muted-foreground">
                  {source === "none" ? "Start a source to see live measurements." : "Waiting for measurements…"}
                </div>
              )}
            </CardBody>
          </Card>
        </div>

        {/* ------------------------------ right column: verdict, metrics, calibration */}
        <div className="min-w-0 space-y-4">
          <Card
            strong
            className={cn(
              "transition-shadow duration-500",
              warning && "border-danger/50 shadow-[0_0_44px_-12px_rgba(251,113,133,0.65)]",
              normal && state.monitoring && "border-success/35",
            )}
          >
            <CardBody className="space-y-4">
              <div className="flex items-center gap-4">
                <span
                  className={cn(
                    "grid size-14 shrink-0 place-items-center rounded-2xl ring-1 ring-[var(--glass-border)]",
                    tone === "danger" && "bg-danger/15 text-danger",
                    tone === "success" && "bg-success/15 text-success",
                    tone === "warning" && "bg-warning/15 text-warning",
                  )}
                >
                  <VerdictIcon className="size-7" />
                </span>
                <div className="min-w-0">
                  <div className="text-xs uppercase tracking-wide text-muted-foreground">Current state</div>
                  <div className="font-display text-xl font-semibold leading-tight text-balance" data-testid="verdict">
                    {verdict}
                  </div>
                </div>
              </div>
              <p className="text-sm text-muted-foreground" data-testid="reason">
                {state.reason}
              </p>
              <div
                role={warning ? "alert" : "status"}
                aria-live={warning ? "assertive" : "polite"}
                className={cn(
                  "whitespace-pre-line rounded-xl border p-3 text-sm font-medium",
                  warning ? "border-danger/40 bg-danger/10 text-danger" : "border-[var(--glass-border)] bg-[var(--glass)]",
                )}
                data-testid="alert"
              >
                {state.alert}
              </div>
              <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                <Badge tone={state.quality === "Good" ? "success" : "warning"}>Signal quality: {state.quality}</Badge>
                {source !== "none" && <span className="tabular-nums">Light {state.brightness.toFixed(0)}/255</span>}
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Measurements" description={state.monitoring ? "From the rule engine" : "Raw readings (monitoring stopped)"} />
            <CardBody className="pt-3">
              {m ? (
                <div className="grid grid-cols-2 gap-3">
                  <Metric label="EAR (smoothed)" value={fixed(m.ear)} />
                  <Metric label="Closure" value={m.closure === null ? "-" : fixed(m.closure, 1)} unit={m.closure === null ? undefined : "s"} />
                  <Metric label="Blink rate" value={m.blink_rate === null ? "-" : fixed(m.blink_rate, 1)} unit={m.blink_rate === null ? undefined : "/min*"} />
                  <Metric label="Closed fraction" value={m.closed_fraction === null ? "-" : `${Math.round(m.closed_fraction * 100)}%`} hint="last 10 s" />
                  <Metric label="Head roll" value={fixed(m.roll, 1)} unit="deg" />
                  <Metric label="EAR threshold" value={fixed(state.threshold)} hint={state.calibrated ? "calibrated" : "default"} />
                </div>
              ) : (
                <div className="grid h-28 place-items-center rounded-xl border border-dashed border-[var(--glass-border)] px-4 text-center text-sm text-muted-foreground">
                  No measurements yet.
                </div>
              )}
              {m && <p className="mt-3 text-[11px] text-muted-foreground">*Blink rate is unstable in short windows and never warns on its own.</p>}
            </CardBody>
          </Card>

          <Card>
            <CardHeader
              title="Calibration"
              description="Look forward with eyes naturally open for 8-15 seconds."
              action={<Badge tone={state.calibrated ? "success" : "neutral"}>{state.calibrated ? "Calibrated" : "Default threshold"}</Badge>}
            />
            <CardBody className="space-y-3 pt-3">
              {state.calibration ? (
                <>
                  <ProgressBar value={state.calibration.progress} label="Calibration progress" />
                  <p className="text-xs tabular-nums text-muted-foreground">
                    {state.calibration.usable} usable of {state.calibration.attempts} frames · {state.calibration.elapsed.toFixed(0)} s
                  </p>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Calibration sets your personal EAR threshold to 0.72 × your median open-eye EAR. It needs the live camera and a still, front-lit face.
                </p>
              )}
              <p className="text-xs text-muted-foreground" role="status" aria-live="polite" data-testid="status">
                {state.status}
              </p>
            </CardBody>
          </Card>
        </div>
      </div>

      <Card className="mt-6">
        <CardHeader title="Please read" icon={<TriangleAlert />} />
        <CardBody className="pt-3">
          <ul className="grid gap-x-8 gap-y-2 text-sm text-muted-foreground md:grid-cols-2">
            {(config.data?.disclaimers ?? []).map((d) => (
              <li key={d} className="flex gap-2">
                <span aria-hidden className="mt-2 size-1.5 shrink-0 rounded-full bg-grad-primary" />
                {d}
              </li>
            ))}
          </ul>
        </CardBody>
      </Card>
    </>
  );
}
