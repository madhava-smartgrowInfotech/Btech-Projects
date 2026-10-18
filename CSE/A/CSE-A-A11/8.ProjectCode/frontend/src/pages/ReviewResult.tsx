import { useQueryClient } from "@tanstack/react-query";
import { Bot, FolderTree, ListChecks, Plus, Search, ShieldAlert, ShieldCheck, Trash2, Wrench, Brain, Download } from "lucide-react";
import { useState } from "react";
import { useNavigate, useParams, Link } from "react-router";

import { VerdictBanner } from "@/components/app/Bits";
import { RiskGauge } from "@/components/app/RiskGauge";
import { FindingsTab } from "@/components/review/FindingsTab";
import { MlTab } from "@/components/review/MlTab";
import { ExportTab, FilesTab, TraceTab } from "@/components/review/MoreTabs";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/Display";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { useBreadcrumb } from "@/components/ui/AppShell";
import { TabPanel, Tabs } from "@/components/ui/Navigation";
import { ConfirmModal } from "@/components/ui/Overlay";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage } from "@/lib/api";
import { useReview } from "@/lib/hooks";
import { keys } from "@/lib/queries";
import { formatDate } from "@/lib/utils";

export default function ReviewResult() {
  const { id } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const q = useReview(id);
  const [tab, setTab] = useState("findings");
  useBreadcrumb(q.data?.title);

  if (q.isPending)
    return (
      <div className="space-y-5" role="status" aria-label="Loading review">
        <Skeleton className="h-9 w-72" />
        <Skeleton className="h-24" />
        <div className="grid gap-4 md:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-32" />)}
        </div>
        <Skeleton className="h-80" />
      </div>
    );

  if (q.isError)
    return (
      <div className="mx-auto max-w-lg space-y-4">
        <ErrorState
          error={q.error}
          title="Couldn't open this review"
          hint="It may have been deleted, or the API isn't running."
          onRetry={() => q.refetch()}
        />
        <Button asChild variant="secondary" className="w-full">
          <Link to="/app/history">Back to history</Link>
        </Button>
      </div>
    );

  const r = q.data;
  const s = r.stats;
  const blockers = s.by_severity.critical + s.by_severity.high;

  async function remove() {
    try {
      await api.delete(`/reviews/${r.id}`);
      await qc.invalidateQueries({ queryKey: keys.reviews });
      qc.removeQueries({ queryKey: keys.review(r.id) });
      toast.success("Review deleted.");
      navigate("/app/history");
    } catch (e) {
      toast.error(`Couldn't delete the review: ${errorMessage(e)}`);
      throw e;
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Review"
        title={r.title}
        description={`${r.source} · ${formatDate(r.created, true)} · ${s.files} file(s), +${s.lines_added}/-${s.lines_removed} lines · id ${r.id}`}
        actions={
          <>
            <Button asChild variant="secondary">
              <Link to="/app/review"><Plus /> New review</Link>
            </Button>
            <ConfirmModal
              trigger={<Button variant="outline"><Trash2 /> Delete</Button>}
              title="Delete this review?"
              description="It is removed from your history for good. Exports you already downloaded are not affected."
              onConfirm={remove}
            />
          </>
        }
      />

      <VerdictBanner verdict={r.verdict} summary={r.summary} />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-[1.15fr_1fr_1fr_1fr_1fr]">
        <Card className="flex items-center justify-center p-3 md:col-span-2 xl:col-span-1">
          <RiskGauge score={r.score} />
        </Card>
        <StatCard label="Security findings" value={s.by_category.security ?? 0} icon={<ShieldAlert />} accent={s.by_category.security ? "magenta" : "cyan"} hint="in changed lines" />
        <StatCard label="Critical + High" value={blockers} icon={<ShieldCheck />} accent={blockers ? "magenta" : "cyan"} hint="merge blockers" />
        <StatCard label="Quality issues" value={s.by_category.quality ?? 0} icon={<ListChecks />} accent="violet" hint="maintainability" />
        <StatCard
          label="Auto-fixes (verified)"
          display={`${s.autofix} (${s.autofix_verified})`}
          icon={<Wrench />}
          accent="cyan"
          hint="patches generated, then re-scanned"
        />
      </div>

      <Tabs
        value={tab}
        onValueChange={setTab}
        tabs={[
          { value: "findings", label: "Findings", icon: <Search />, count: r.findings.length },
          { value: "ml", label: "Function risk (ML)", icon: <Brain />, count: r.ml.length },
          { value: "files", label: "Files", icon: <FolderTree />, count: r.files.length },
          { value: "trace", label: "Agent trace", icon: <Bot /> },
          { value: "export", label: "Export", icon: <Download /> },
        ]}
      >
        <TabPanel value="findings"><FindingsTab review={r} /></TabPanel>
        <TabPanel value="ml"><MlTab review={r} /></TabPanel>
        <TabPanel value="files"><FilesTab review={r} /></TabPanel>
        <TabPanel value="trace"><TraceTab review={r} /></TabPanel>
        <TabPanel value="export"><ExportTab review={r} /></TabPanel>
      </Tabs>
    </div>
  );
}
