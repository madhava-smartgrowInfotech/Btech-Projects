import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BarChart3, CheckCircle2, Cpu, ScanSearch, Sparkles } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router";

import { Button } from "@/components/ui/Button";
import { Card, CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/Display";
import { ErrorState, ProgressBar } from "@/components/ui/Feedback";
import { FileDrop } from "@/components/ui/FileDrop";
import { PageHeader } from "@/components/ui/Layout";
import { ConfirmModal } from "@/components/ui/Overlay";
import { Slider } from "@/components/ui/Slider";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage, type RetrainStatus } from "@/lib/api";
import { keys } from "@/lib/queries";
import { pct } from "@/lib/verdict";
import { formatBytes } from "@/lib/utils";

const JOB_KEY = "truthglow-retrain-job";
const MAX_BYTES = 25 * 1024 * 1024;

const readJob = () => {
  try {
    return localStorage.getItem(JOB_KEY);
  } catch {
    return null;
  }
};
const writeJob = (id: string | null) => {
  try {
    if (id) localStorage.setItem(JOB_KEY, id);
    else localStorage.removeItem(JOB_KEY);
  } catch {
    /* storage unavailable: the job still runs, it just isn't remembered across reloads */
  }
};

function validateCsv(f: File) {
  if (!f.name.toLowerCase().endsWith(".csv")) return `"${f.name}" is not a .csv file.`;
  if (f.size > MAX_BYTES) return `"${f.name}" is ${formatBytes(f.size)}; the limit is ${formatBytes(MAX_BYTES)}.`;
  return null;
}

export default function Retrain() {
  const qc = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [fireflies, setFireflies] = useState(10);
  const [generations, setGenerations] = useState(12);
  const [maxTfidf, setMaxTfidf] = useState(4000);
  const [confirm, setConfirm] = useState(false);
  const [jobId, setJobId] = useState<string | null>(readJob);
  const announced = useRef<string | null>(null);

  const start = useMutation({
    mutationFn: async () => {
      const fd = new FormData();
      if (file) fd.append("file", file);
      fd.append("fireflies", String(fireflies));
      fd.append("generations", String(generations));
      fd.append("max_tfidf", String(maxTfidf));
      return (await api.post<{ job_id: string }>("/retrain", fd)).data.job_id;
    },
    onSuccess: (id) => {
      writeJob(id);
      setJobId(id);
      toast.info("Training started", { description: "This can take a minute or two. You can leave this page open." });
    },
    onError: (e) => toast.error("Couldn't start training", { description: errorMessage(e) }),
  });

  const status = useQuery({
    queryKey: ["retrain", jobId],
    enabled: Boolean(jobId),
    queryFn: async () => (await api.get<RetrainStatus>(`/retrain/${jobId}`)).data,
    refetchInterval: (q) => (q.state.data?.status === "running" || !q.state.data ? 2000 : false),
    retry: false,
  });

  const s = status.data;
  const running = start.isPending || s?.status === "running";

  // a remembered job the server no longer knows about (server restarted)
  useEffect(() => {
    if (status.isError && jobId) {
      writeJob(null);
      setJobId(null);
    }
  }, [status.isError, jobId]);

  // announce a finished job once, and refresh everything that reads the model
  useEffect(() => {
    if (!s || !jobId || announced.current === jobId || s.status === "running") return;
    announced.current = jobId;
    qc.invalidateQueries({ queryKey: keys.model });
    if (s.status === "done" && s.result) toast.success("Model retrained", { description: `Accuracy ${pct(s.result.accuracy, 2)} · Macro-F1 ${s.result.f1_macro.toFixed(4)}` });
    if (s.status === "error") toast.error("Training failed", { description: s.error });
  }, [s, jobId, qc]);

  function reset() {
    writeJob(null);
    setJobId(null);
    start.reset();
  }

  return (
    <>
      <PageHeader
        eyebrow="Retrain"
        title="Retrain on your data"
        description="Upload a labelled CSV, or retrain on the built-in demo corpus, with your own Firefly budget. The new model replaces the current one as soon as it finishes."
      />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
        <Card strong className="min-w-0 space-y-6 p-5 sm:p-6">
          <div className="space-y-2">
            <h2 className="font-display text-base font-semibold">Training data</h2>
            <FileDrop
              file={file}
              onFile={setFile}
              accept=".csv,text/csv"
              validate={validateCsv}
              title="Drop a labelled CSV here, or click to browse (optional)"
              hint="Columns: text (+ optional title) and label = REAL, PARTIALLY TRUE, FAKE or 0, 1, 2. Without a file the demo corpus (300 per class) is used."
              disabled={running}
            />
          </div>
          <div className="space-y-5">
            <h2 className="font-display text-base font-semibold">Firefly budget</h2>
            <div className="grid gap-6 sm:grid-cols-2">
              <Slider label="Fireflies" min={4} max={20} value={fireflies} onChange={setFireflies} disabled={running} hint="Candidate solutions searched in parallel" />
              <Slider label="Generations" min={3} max={30} value={generations} onChange={setGenerations} disabled={running} hint="Rounds of improvement" />
            </div>
            <Slider label="Max TF-IDF features" min={1000} max={8000} step={500} value={maxTfidf} onChange={setMaxTfidf} disabled={running} hint="Vocabulary size before PCA" />
          </div>
          <ConfirmModal
            open={confirm}
            onOpenChange={setConfirm}
            title="Replace the current model?"
            description={`Training saves over models/msvm_model.pkl and the detector starts using the new model immediately. Source: ${file ? file.name : "built-in demo corpus"}.`}
            confirmLabel="Retrain and replace"
            onConfirm={async () => {
              await start.mutateAsync().catch(() => undefined);
            }}
          />
          <Button size="lg" loading={running} onClick={() => setConfirm(true)} className="w-full sm:w-auto">
            <Sparkles /> {running ? "Training…" : "Retrain model"}
          </Button>
        </Card>

        <div className="min-w-0 space-y-4">
          {running && (
            <Card className="space-y-4 p-5" role="status" aria-live="polite">
              <CardHeader className="px-0 pt-0" icon={<Cpu />} title="Training PCA + Firefly + MSVM" description={s?.source ?? "Starting…"} />
              <ProgressBar value={0} indeterminate label="Training in progress" />
              <p className="text-sm tabular-nums text-muted-foreground">{s ? `${s.elapsed_s.toFixed(0)} s elapsed` : "Starting…"}</p>
              <p className="text-xs text-muted-foreground">
                The Firefly search runs {fireflies} × {generations} evaluations. Larger budgets give a better search but take longer.
              </p>
            </Card>
          )}

          {!running && s?.status === "done" && s.result && (
            <Card className="space-y-4 p-5">
              <CardHeader className="px-0 pt-0" icon={<CheckCircle2 />} title="Retrained successfully" description={`${s.source} · ${s.elapsed_s.toFixed(0)} s`} />
              <div className="grid gap-3 sm:grid-cols-2">
                <StatCard label="Accuracy" value={s.result.accuracy * 100} format={(n) => `${n.toFixed(2)}%`} className="min-h-0" />
                <StatCard label="Macro F1" value={s.result.f1_macro} format={(n) => n.toFixed(4)} accent="cyan" className="min-h-0" />
              </div>
              <p className="text-sm text-muted-foreground">
                {s.result.n_docs.toLocaleString("en-US")} documents · PCA {s.result.n_pca} → Firefly kept {s.result.n_selected} components.
              </p>
              <div className="flex flex-wrap gap-2">
                <Button asChild variant="secondary" size="sm">
                  <Link to="/app/analytics">
                    <BarChart3 /> See analytics
                  </Link>
                </Button>
                <Button asChild size="sm">
                  <Link to="/app">
                    <ScanSearch /> Try the detector
                  </Link>
                </Button>
              </div>
            </Card>
          )}

          {!running && s?.status === "error" && (
            <ErrorState error={new Error(s.error ?? "Training failed.")} title="Training failed" hint="The previous model is still in use. Check your CSV's label column, then try again." onRetry={reset} />
          )}

          {!running && !s && (
            <Card className="space-y-3 p-5">
              <CardHeader className="px-0 pt-0" title="What happens when you retrain" />
              <ol className="list-decimal space-y-2 pl-5 text-sm text-muted-foreground">
                <li>Your texts are cleaned and turned into TF-IDF and 25 stylometric features.</li>
                <li>PCA keeps 95% of the variance; Firefly picks the best components and tunes C and γ.</li>
                <li>A new MSVM is fitted, scored on a 20% test split and saved.</li>
                <li>The detector and the analytics pages switch to the new model without a reload.</li>
              </ol>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}
