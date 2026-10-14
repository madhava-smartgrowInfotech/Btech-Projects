import { lazy, Suspense, useEffect, useState, type FormEvent } from "react";
import { Link, useLocation, useParams } from "react-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, FileText, HeartPulse, Image as ImageIcon, Layers, Pencil, ScanEye, TriangleAlert } from "lucide-react";
import { toast } from "sonner";

import { AlertBox } from "@/components/app/AlertBox";
import { ClinicalForm } from "@/components/app/ClinicalForm";
import { Disclaimer } from "@/components/app/Disclaimer";
import { Figure } from "@/components/app/Figure";
import { ProbBar } from "@/components/app/ProbBar";
import { StageBadge } from "@/components/app/StageBadge";
import { ChartCard } from "@/components/charts/Chart";
import { useBreadcrumb } from "@/components/ui/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { KeyValueList, StatCard } from "@/components/ui/Display";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { Tabs, TabPanel } from "@/components/ui/Navigation";
import { Segmented } from "@/components/ui/Toggles";
import { api, errorMessage, pct } from "@/lib/api";
import { clinicalFromStored, clinicalPayload, EMPTY_CLINICAL, type ClinicalValues } from "@/lib/clinical";
import { keys } from "@/lib/queries";
import type { ScreeningFull, Stage } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";

const ShapChart = lazy(() => import("@/components/app/ShapChart"));

const STEP_CAPTIONS: [string, string][] = [
  ["original", "1. Original (cropped)"],
  ["green", "2. Green channel"],
  ["clahe", "3. CLAHE enhanced"],
  ["resized", "4. Resized 256 + normalised"],
];
const BAND_CAPTIONS: Record<string, string> = {
  LL: "LL - approximation",
  LH: "LH - horizontal detail",
  HL: "HL - vertical detail",
  HH: "HH - diagonal detail",
};
const STAGE_BAR: Record<Stage, string> = {
  Low: "bg-success",
  Moderate: "bg-warning",
  High: "bg-magenta",
  "Very high": "bg-danger",
};

function WaveletView({ wavelet }: { wavelet: Record<string, string | null> }) {
  const [level, setLevel] = useState<"1" | "2">("2");
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Segmented<"1" | "2">
          label="Wavelet level"
          value={level}
          onChange={setLevel}
          size="sm"
          options={[
            { value: "1", label: "Level 1" },
            { value: "2", label: "Level 2" },
          ]}
        />
      </div>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {(["LL", "LH", "HL", "HH"] as const).map((b) => (
          <Figure key={b} src={wavelet[`${level}_${b}`]} caption={BAND_CAPTIONS[b]} />
        ))}
      </div>
      <p className="text-xs text-muted-foreground">
        Detail bands (LH, HL, HH) highlight vessel edges and small lesions. All 8 sub-bands from both levels are stacked as the LeNet input.
      </p>
    </div>
  );
}

function ResultSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-label="Loading screening">
      <Skeleton className="h-10 w-80" />
      <Skeleton className="h-40 w-full rounded-2xl" />
      <Skeleton className="h-24 w-full rounded-2xl" />
      <div className="grid gap-6 lg:grid-cols-2">
        <Skeleton className="h-96 w-full rounded-2xl" />
        <Skeleton className="h-96 w-full rounded-2xl" />
      </div>
    </div>
  );
}

export default function Result() {
  const { id = "" } = useParams();
  const location = useLocation();
  const queryClient = useQueryClient();
  useBreadcrumb(`Screening #${id}`);

  const query = useQuery({
    queryKey: keys.screening(id),
    queryFn: async () => (await api.get<ScreeningFull>(`/screenings/${id}`)).data,
    enabled: !!id,
  });
  const s = query.data;

  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [clinical, setClinical] = useState<ClinicalValues>(EMPTY_CLINICAL);
  const [formError, setFormError] = useState<string>((location.state as { clinicalError?: string } | null)?.clinicalError ?? "");
  const [tab, setTab] = useState("steps");

  // Keep the form in step with the saved values (on load and after each save).
  useEffect(() => {
    if (!s) return;
    setClinical(s.clinical ? clinicalFromStored(s.clinical) : { ...EMPTY_CLINICAL, age: s.patient.age, sex: s.patient.sex === "Female" ? 0 : 1 });
  }, [s]);

  async function saveClinical(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSaving(true);
    setFormError("");
    try {
      const payload = clinicalPayload(clinical);
      const { data } = await api.post<ScreeningFull>(`/screenings/${id}/clinical`, payload);
      queryClient.setQueryData(keys.screening(id), data);
      queryClient.invalidateQueries({ queryKey: ["screenings"] });
      queryClient.invalidateQueries({ queryKey: ["patients"] });
      queryClient.invalidateQueries({ queryKey: ["patient"] });
      setEditing(false);
      toast.success("Heart-disease risk and combined stage updated");
    } catch (err) {
      setFormError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  if (query.isPending) return <ResultSkeleton />;
  if (query.isError || !s) {
    return (
      <ErrorState
        error={query.error}
        title="Couldn't open this screening"
        hint={
          <Link to="/patients" className="underline underline-offset-4">
            Back to patients and history
          </Link>
        }
        onRetry={() => query.refetch()}
      />
    );
  }

  const r = s.retina;
  const st = s.stage_detail;
  const q = s.quality;
  const factors = s.heart?.factors ?? [];
  const showForm = !s.heart || editing;

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Screening #${s.id}`}
        description={
          <span>
            <Link className="font-medium text-violet-ink hover:underline" to={`/patients/${s.patient.id}`}>
              {s.patient.name}
            </Link>{" "}
            ({s.patient.code}, {s.patient.age}, {s.patient.sex}) · {s.eye} eye · {formatDate(s.created_at, true)} · by {s.screened_by}
          </span>
        }
        actions={
          st ? (
            <Button asChild>
              <Link to={`/screenings/${s.id}/report`}>
                <FileText /> Screening report
              </Link>
            </Button>
          ) : undefined
        }
      />

      {/* Combined stage */}
      {st ? (
        <Card strong className="relative overflow-hidden p-5 sm:p-6">
          <span aria-hidden className={cn("absolute inset-y-0 left-0 w-1.5", STAGE_BAR[st.stage])} />
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="space-y-2">
              <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">Overall risk stage</p>
              <div className="flex flex-wrap items-center gap-3">
                <span className="font-display text-3xl font-semibold">{st.stage}</span>
                <StageBadge stage={st.stage} />
              </div>
            </div>
            <p className="text-sm text-muted-foreground">Score {st.score}/6</p>
          </div>
          <div className="mt-5 grid gap-6 md:grid-cols-2">
            <div>
              <h3 className="text-sm font-semibold">Why this stage</h3>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                {st.reasons.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold">Recommendations</h3>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                {st.recommendations.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      ) : (
        <Card className="flex flex-wrap items-center justify-between gap-3 p-5">
          <div>
            <h2 className="font-display font-semibold">Combined stage pending</h2>
            <p className="text-sm text-muted-foreground">Add the clinical profile to score heart-disease risk and get the combined stage.</p>
          </div>
          <Button variant="secondary" asChild>
            <a href="#heart-risk">Add clinical data</a>
          </Button>
        </Card>
      )}

      {/* Image quality */}
      <Card className="space-y-4 p-5 sm:p-6">
        <div className="flex items-start gap-3">
          <span className={cn("grid size-9 shrink-0 place-items-center rounded-xl", q.passed ? "bg-success/12 text-success" : "bg-warning/12 text-warning")}>
            {q.passed ? <CheckCircle2 className="size-5" aria-hidden /> : <TriangleAlert className="size-5" aria-hidden />}
          </span>
          <div className="min-w-0">
            <h2 className="font-display font-semibold">Image quality {q.passed ? "passed" : "check failed"}</h2>
            <p className="text-sm text-muted-foreground">Sharpness, brightness and clipped pixels are checked before the models run.</p>
          </div>
        </div>
        <KeyValueList
          columns={2}
          items={[
            { label: "Sharpness", value: `${q.sharpness ?? "-"} (min ${q.thresholds?.sharpness_min ?? "-"})` },
            { label: "Brightness", value: `${q.brightness ?? "-"} (range ${q.thresholds?.brightness_range?.join("–") ?? "-"})` },
            { label: "Clipped pixels", value: `${((q.clipped_fraction ?? 0) * 100).toFixed(1)}%` },
          ]}
        />
        {!q.passed && (
          <AlertBox tone="warning">
            {q.issues?.length ? q.issues.join(" ") : "The image did not pass the quality check."} Results may be less reliable; consider retaking the photo.
          </AlertBox>
        )}
      </Card>

      {/* Image analysis */}
      <Card className="p-5 sm:p-6">
        <Tabs
          value={tab}
          onValueChange={setTab}
          tabs={[
            { value: "steps", label: "Preprocessing", icon: <ImageIcon /> },
            { value: "wavelet", label: "Wavelets", icon: <Layers /> },
          ]}
        >
          <TabPanel value="steps">
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {STEP_CAPTIONS.map(([k, caption]) => (
                <Figure key={k} src={s.images.steps[k]} caption={caption} />
              ))}
            </div>
          </TabPanel>
          <TabPanel value="wavelet">
            <WaveletView wavelet={s.images.wavelet} />
          </TabPanel>
        </Tabs>
      </Card>

      <div className="grid items-start gap-6 lg:grid-cols-2">
        {/* Retinopathy */}
        <Card className="space-y-5 p-5 sm:p-6">
          <div className="flex items-center gap-2">
            <ScanEye className="size-5 text-violet-ink" aria-hidden />
            <h2 className="font-display font-semibold">Hypertensive retinopathy</h2>
            <span className="text-xs text-muted-foreground">LeNet CNN</span>
          </div>
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className={cn("text-lg font-semibold", r.positive ? "text-danger" : "text-success")}>{r.label ?? "Result"}</p>
              <p className="text-xs text-muted-foreground">Probability of hypertensive retinopathy</p>
            </div>
            <p className="font-display text-3xl font-semibold tabular-nums">{pct(r.probability)}</p>
          </div>
          <ProbBar value={r.probability} threshold={r.threshold} label="Retinopathy probability" />
          <p className="text-xs text-muted-foreground">The marker shows the decision threshold ({pct(r.threshold)}).</p>
          <div className="grid grid-cols-2 gap-3">
            <Figure src={s.images.heatmap} caption="Grad-CAM heatmap" />
            <Figure src={s.images.vessels} caption="Frangi vessel map" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <StatCard label="Vessel density" display={r.vessels?.vessel_density != null ? `${(r.vessels.vessel_density * 100).toFixed(1)}%` : "-"} />
            <StatCard
              label="Mean vessel width"
              display={r.vessels?.mean_vessel_width_px != null ? `${r.vessels.mean_vessel_width_px.toFixed(1)} px` : "-"}
            />
          </div>
        </Card>

        {/* Heart risk */}
        <Card id="heart-risk" className="scroll-mt-24 space-y-5 p-5 sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <HeartPulse className="size-5 text-magenta-ink" aria-hidden />
              <h2 className="font-display font-semibold">Heart-disease risk</h2>
              <span className="text-xs text-muted-foreground">Random Forest</span>
            </div>
            {s.heart && !editing && (
              <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
                <Pencil /> Edit clinical data
              </Button>
            )}
          </div>

          {!showForm && s.heart ? (
            <>
              <div className="flex items-end justify-between gap-4">
                <p className="text-lg font-semibold">Heart-disease risk</p>
                <p className="font-display text-3xl font-semibold tabular-nums">{pct(s.heart.probability)}</p>
              </div>
              <ProbBar value={s.heart.probability} label="Heart-disease risk" />
              <ChartCard
                title="Top factors (SHAP)"
                description="Red raises the risk, green lowers it. Values are the SHAP contribution to the predicted probability."
                table={{
                  columns: ["Factor", "Value", "Impact"],
                  rows: factors.map((f) => [f.label, f.display ?? f.value, f.impact.toFixed(3)]),
                }}
              >
                <Suspense fallback={<Skeleton className="h-72 w-full" />}>
                  <ShapChart factors={factors} />
                </Suspense>
              </ChartCard>
            </>
          ) : (
            <form onSubmit={saveClinical} className="space-y-5">
              <p className="text-sm text-muted-foreground">Enter the clinical parameters to get the heart-disease risk and the combined stage.</p>
              <ClinicalForm value={clinical} onChange={setClinical} disabled={saving} idPrefix="result-clinical" />
              {formError && <AlertBox>{formError}</AlertBox>}
              <div className="flex flex-wrap gap-2">
                <Button type="submit" loading={saving}>
                  Score risk
                </Button>
                {editing && (
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => {
                      setEditing(false);
                      setFormError("");
                    }}
                  >
                    Cancel
                  </Button>
                )}
              </div>
            </form>
          )}
        </Card>
      </div>

      <Disclaimer />
    </div>
  );
}
