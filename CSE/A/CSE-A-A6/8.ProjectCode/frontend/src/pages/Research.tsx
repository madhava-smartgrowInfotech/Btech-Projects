import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BarChart3, Beaker, Download, FlaskConical, ShieldCheck, Target, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatCard, KeyValueList } from "@/components/ui/Display";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { FormField, Input } from "@/components/ui/Field";
import { FileDrop } from "@/components/ui/FileDrop";
import { PageHeader } from "@/components/ui/Layout";
import { toast } from "@/components/ui/Toast";
import { downloadBlob, endpoints, errorMessage } from "@/lib/api";
import { keys, useResearch } from "@/lib/queries";
import type { ResearchReport } from "@/lib/types";

const CSV_COLUMNS = "subject_id,session_id,timestamp_s,ear,roll_deg,quality,label,consent";
const ratio = (v: number | null) => (v === null ? "n/a" : `${(v * 100).toFixed(1)}%`);

function ConfusionImage() {
  const image = useQuery({
    queryKey: ["confusion-image"],
    queryFn: async () => URL.createObjectURL(await endpoints.confusionImage()),
    staleTime: 0,
    gcTime: 0,
  });
  useEffect(() => () => void (image.data && URL.revokeObjectURL(image.data)), [image.data]);
  if (!image.data) return <Skeleton className="aspect-[5/4] w-full max-w-sm rounded-xl" />;
  return <img src={image.data} alt="Confusion matrix of the held-out evaluation" className="w-full max-w-sm rounded-xl bg-white" />;
}

function ReportView({ report, synthetic, hasImage }: { report: ResearchReport; synthetic: boolean; hasImage: boolean }) {
  const [[tn, fp], [fn, tp]] = report.confusion_matrix;
  return (
    <div className="space-y-6">
      {synthetic && (
        <div role="note" className="flex items-start gap-3 rounded-2xl border border-warning/40 bg-warning/[0.08] p-4 text-sm">
          <TriangleAlert className="mt-0.5 size-4 shrink-0 text-warning" />
          <p>
            <strong>Synthetic data.</strong> This report was built from the generated demonstration file, not from people. Its metrics only prove the
            pipeline runs; they say nothing about real-world performance or safety.
          </p>
        </div>
      )}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Precision" display={ratio(report.precision)} icon={<Target />} hint="TP / (TP + FP)" />
        <StatCard label="Recall" display={ratio(report.recall)} icon={<ShieldCheck />} accent="cyan" hint="TP / (TP + FN)" />
        <StatCard label="F1" display={ratio(report.f1)} icon={<BarChart3 />} accent="magenta" hint="2TP / (2TP + FP + FN)" />
        <StatCard label="False-alarm rate" display={ratio(report.false_alarm_rate)} icon={<TriangleAlert />} hint="per test window, not per hour" />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Confusion matrix" description="Rows are true labels, columns predicted (normal, possible impairment)." />
          <CardBody className="space-y-4">
            <table className="w-full max-w-sm text-center text-sm">
              <caption className="sr-only">Confusion matrix counts of held-out windows</caption>
              <thead>
                <tr className="text-xs text-muted-foreground">
                  <th scope="col" />
                  <th scope="col" className="p-2 font-medium">Pred. normal</th>
                  <th scope="col" className="p-2 font-medium">Pred. possible</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <th scope="row" className="p-2 text-left text-xs font-medium text-muted-foreground">True normal</th>
                  <td className="rounded-lg bg-success/12 p-3 font-display text-xl font-semibold tabular-nums">{tn}</td>
                  <td className="rounded-lg bg-danger/10 p-3 font-display text-xl font-semibold tabular-nums">{fp}</td>
                </tr>
                <tr>
                  <th scope="row" className="p-2 text-left text-xs font-medium text-muted-foreground">True possible</th>
                  <td className="rounded-lg bg-danger/10 p-3 font-display text-xl font-semibold tabular-nums">{fn}</td>
                  <td className="rounded-lg bg-success/12 p-3 font-display text-xl font-semibold tabular-nums">{tp}</td>
                </tr>
              </tbody>
            </table>
            {hasImage && <ConfusionImage />}
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Run details" />
          <CardBody>
            <KeyValueList
              items={[
                { label: "Status", value: report.status },
                { label: "Classifier", value: report.classifier },
                { label: "Training subjects", value: report.train_subjects.join(", ") },
                { label: "Held-out subjects", value: report.test_subjects.join(", ") },
                { label: "Training / test windows", value: `${report.train_windows} / ${report.test_windows}` },
                { label: "Rejected windows", value: report.rejected_windows },
                { label: "Features", value: report.features.join(", ") },
                { label: "Dataset SHA-256", value: <span className="break-all font-mono text-[11px]">{report.dataset_sha256}</span> },
              ]}
            />
            <p className="mt-3 text-xs text-muted-foreground">{report.limitation}</p>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

export default function Research() {
  const research = useResearch();
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [subjects, setSubjects] = useState("");
  const [serverError, setServerError] = useState<string | null>(null);

  const evaluate = useMutation({
    mutationFn: () => endpoints.evaluate(file as File, subjects),
    onSuccess: (data) => {
      setServerError(null);
      queryClient.setQueryData(keys.research, data);
      void queryClient.invalidateQueries({ queryKey: ["confusion-image"] });
      toast.success("Offline evaluation finished. The live app still uses rules only.");
    },
    onError: (e) => setServerError(errorMessage(e, "Evaluation failed.")),
  });

  const loadSample = useMutation({
    mutationFn: endpoints.sampleCsv,
    onSuccess: (text) => {
      setFile(new File([text], "synthetic_demo_measurements.csv", { type: "text/csv" }));
      setSubjects("S05, S06");
      setServerError(null);
      toast.message("Synthetic demonstration file loaded, with S05 and S06 held out.");
    },
    onError: (e) => toast.error(errorMessage(e, "Could not load the sample file.")),
  });

  async function downloadSample() {
    try {
      downloadBlob(new Blob([await endpoints.sampleCsv()], { type: "text/csv" }), "synthetic_demo_measurements.csv");
    } catch (e) {
      toast.error(errorMessage(e, "Could not download the sample file."));
    }
  }

  const data = research.data;
  return (
    <>
      <PageHeader
        title="Research and evaluation"
        eyebrow="Offline only"
        description="Train and test a simple nearest-centroid classifier on a consented, labelled measurement CSV. It never replaces the live rules."
        actions={
          data && (
            <Badge tone={data.trained ? "success" : "warning"} className="px-3 py-1 text-xs">
              {data.trained ? "Offline model trained" : "Model not trained"}
            </Badge>
          )
        }
      />

      <div className="space-y-6">
        <Card>
          <CardHeader title="Evaluate a dataset" icon={<FlaskConical />} description="Subject membership alone defines the split: no held-out subject appears in training." />
          <CardBody className="space-y-5">
            <div className="rounded-xl border border-[var(--glass-border)] bg-[var(--glass)] p-4 text-sm">
              <p className="mb-2 font-medium">CSV columns (UTF-8, one row per measured frame)</p>
              <code className="block overflow-x-auto whitespace-nowrap rounded-lg bg-muted px-3 py-2 font-mono text-xs">{CSV_COLUMNS}</code>
              <ul className="mt-3 grid gap-1 text-xs text-muted-foreground sm:grid-cols-2">
                <li>Labels: <code>normal</code> or <code>possible_impairment</code></li>
                <li>Consent: <code>yes</code> on every row; quality <code>Good</code> to count</li>
                <li>5-second windows with at least 20 samples and gaps of 0.5 s or less</li>
                <li>Both classes needed in the training and held-out groups</li>
              </ul>
              <p className="mt-3 text-xs text-muted-foreground">
                No real dataset is bundled. You can try the screen with a generated <strong>synthetic</strong> file; results from it are flagged and carry no research value.
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button size="sm" variant="secondary" onClick={() => void downloadSample()}>
                  <Download /> Download synthetic sample
                </Button>
                <Button size="sm" variant="outline" onClick={() => loadSample.mutate()} loading={loadSample.isPending}>
                  <Beaker /> Use synthetic sample
                </Button>
              </div>
            </div>

            <FileDrop
              file={file}
              onFile={setFile}
              onPick={() => setServerError(null)}
              accept=".csv,text/csv"
              validate={(f) => (f.name.toLowerCase().endsWith(".csv") ? null : "Choose a .csv file.")}
              title="Drop the measurements CSV here, or click to browse"
              hint="CSV only. The file is processed locally and not kept."
              disabled={evaluate.isPending}
            />

            <FormField label="Held-out subject IDs" hint="Comma-separated. Pick them before looking at outcomes, and leave at least one subject for training." error={undefined}>
              {(props) => (
                <Input {...props} value={subjects} onChange={(e) => setSubjects(e.target.value)} placeholder="S05, S06" autoComplete="off" />
              )}
            </FormField>

            {serverError && (
              <p role="alert" className="rounded-xl border border-danger/30 bg-danger/[0.07] p-3 text-sm text-danger">
                {serverError}
              </p>
            )}
            <Button onClick={() => evaluate.mutate()} loading={evaluate.isPending} disabled={!file || !subjects.trim()}>
              <FlaskConical /> Train and evaluate offline
            </Button>
          </CardBody>
        </Card>

        {research.isPending ? (
          <Skeleton className="h-64 w-full rounded-2xl" />
        ) : research.isError ? (
          <ErrorState error={research.error} title="Couldn't read the saved report" onRetry={() => void research.refetch()} />
        ) : data?.trained && data.report ? (
          <ReportView report={data.report} synthetic={data.synthetic} hasImage={!!data.confusion_matrix_image} />
        ) : (
          <Card>
            <CardBody className="flex flex-col items-center gap-3 py-10 text-center">
              <span className="grid size-14 place-items-center rounded-2xl bg-grad-soft text-violet-ink ring-1 ring-[var(--glass-border)]">
                <FlaskConical className="size-6" />
              </span>
              <h3 className="font-display text-lg font-semibold">Model not trained</h3>
              <p className="max-w-md text-sm text-muted-foreground">
                No report exists yet. Upload a consented, labelled CSV above, or try the synthetic sample to see how results are shown.
              </p>
            </CardBody>
          </Card>
        )}
      </div>
    </>
  );
}
