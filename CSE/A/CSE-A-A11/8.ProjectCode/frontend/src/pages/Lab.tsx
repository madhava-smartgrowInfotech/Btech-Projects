import { useQuery, useQueryClient } from "@tanstack/react-query";
import { BarChart3, Boxes, Crosshair, Gauge, ListFilter, RefreshCw, Rocket, Sigma, Target, Workflow } from "lucide-react";
import { useState } from "react";

import { AgentProgress } from "@/components/app/Bits";
import { AblationTab, ModelsTab, PipelineTab, RocTab, SelectionTab, TryTab, TypesTab } from "@/components/lab/LabTabs";
import { StatCard } from "@/components/ui/Display";
import { Button } from "@/components/ui/Button";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { TabPanel, Tabs } from "@/components/ui/Navigation";
import { ConfirmModal } from "@/components/ui/Overlay";
import { toast } from "@/components/ui/Toast";
import { api } from "@/lib/api";
import { useMeta } from "@/lib/hooks";
import { useJob } from "@/lib/jobs";
import { keys } from "@/lib/queries";
import type { LabReport } from "@/lib/types";

export default function Lab() {
  const qc = useQueryClient();
  const meta = useMeta();
  const [tab, setTab] = useState("pipeline");
  const job = useJob();
  const q = useQuery({ queryKey: keys.lab, queryFn: async () => (await api.get<LabReport>("/lab/report")).data, staleTime: 5 * 60_000 });

  async function retrain() {
    const done = await job.run(async () => (await api.post<{ job_id: string }>("/lab/retrain")).data.job_id);
    if (!done) return;
    await qc.invalidateQueries({ queryKey: keys.lab });
    await qc.invalidateQueries({ queryKey: keys.meta });
    toast.success(`Models retrained in ${done.seconds?.toFixed(0)} s`);
  }

  if (q.isPending)
    return (
      <div className="space-y-5" role="status" aria-label="Loading model report">
        <Skeleton className="h-9 w-80" />
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-32" />)}</div>
        <Skeleton className="h-96" />
      </div>
    );
  if (q.isError) return <ErrorState error={q.error} title="Could not load the model report" hint="The trained models may be missing; retraining takes about 30 seconds once the API is up." onRetry={() => q.refetch()} />;

  const R = q.data;
  const best = R.results[R.best];
  const metrics = meta.data?.metrics ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Model lab"
        title="Base-paper reproduction"
        description="Leveraging Key Source Code Metrics for Predicting Software Vulnerabilities With Machine Learning · IEEE Access 2026 · DOI 10.1109/ACCESS.2026.3679930"
        actions={
          <ConfirmModal
            trigger={<Button variant="secondary" loading={job.running}><RefreshCw /> Retrain models</Button>}
            title="Retrain all models?"
            description="Regenerates the corpus, re-selects features, balances the data and trains the 9 models again (about 30 seconds). The saved model and report are replaced."
            confirmLabel="Retrain"
            onConfirm={retrain}
          />
        }
      />

      {job.running && <AgentProgress messages={job.messages} title="Retraining models…" />}
      {job.error && <ErrorState error={new Error(job.error)} title="Retraining failed" hint="The previous models are still in use." onRetry={retrain} className="py-6" />}

      <div className="grid grid-cols-2 gap-4 xl:grid-cols-5">
        <StatCard label="Functions" value={R.n_functions} icon={<Sigma />} />
        <StatCard label="Vulnerable" display={`${R.n_vulnerable} (${(R.class_ratio * 100).toFixed(1)}%)`} icon={<Crosshair />} accent="magenta" />
        <StatCard label={`${R.best} F1`} value={best.f1} format={(n) => n.toFixed(3)} icon={<Target />} accent="cyan" />
        <StatCard label={`${R.best} accuracy`} value={best.accuracy} format={(n) => n.toFixed(3)} icon={<Gauge />} />
        <StatCard label="Type-classifier acc." value={R.type_accuracy} format={(n) => n.toFixed(2)} icon={<Boxes />} accent="magenta" />
      </div>

      <p className="rounded-2xl border border-info/30 bg-info/10 px-4 py-3 text-sm">
        <strong>Data note:</strong> the paper trains on C functions from 10 open-source projects. This system runs on Python, so the model is trained on a generated corpus of
        Python functions (vulnerable + look-alike safe code + label noise) whose metrics come from real AST analysis. Numbers below are therefore <em>this system&apos;s</em>{" "}
        results, not the paper&apos;s (RF: acc 0.96, F1 0.961).
      </p>

      <Tabs
        value={tab}
        onValueChange={setTab}
        tabs={[
          { value: "pipeline", label: "Pipeline & data", icon: <Workflow /> },
          { value: "selection", label: "Feature selection", icon: <ListFilter /> },
          { value: "models", label: "Models", icon: <BarChart3 /> },
          { value: "roc", label: "ROC & confusion", icon: <Target /> },
          { value: "types", label: "Vulnerability types", icon: <Boxes /> },
          { value: "ablation", label: "Ablation", icon: <Sigma /> },
          { value: "try", label: "Try it", icon: <Rocket /> },
        ]}
      >
        <TabPanel value="pipeline"><PipelineTab R={R} metrics={metrics} /></TabPanel>
        <TabPanel value="selection"><SelectionTab R={R} metrics={metrics} /></TabPanel>
        <TabPanel value="models"><ModelsTab R={R} /></TabPanel>
        <TabPanel value="roc"><RocTab R={R} /></TabPanel>
        <TabPanel value="types"><TypesTab R={R} /></TabPanel>
        <TabPanel value="ablation"><AblationTab R={R} /></TabPanel>
        <TabPanel value="try"><TryTab /></TabPanel>
      </Tabs>
    </div>
  );
}
