import { useState } from "react";
import { Link } from "react-router-dom";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { FileWarning, Megaphone, Smartphone } from "lucide-react";
import { ComplaintList } from "@/components/complaints/ComplaintList";
import { ReportDialog } from "@/components/complaints/ReportDialog";
import { EmptyState, ErrorState, PageHeader } from "@/components/common/states";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api, apiError } from "@/lib/api";
import { OPEN, type ComplaintPage } from "@/lib/complaints";

export default function MyComplaints() {
  const [tab, setTab] = useState<"open" | "closed" | "all">("open");
  const [reporting, setReporting] = useState(false);
  const status = tab === "open" ? OPEN.join(",") : tab === "closed" ? "verified,dismissed" : undefined;
  const q = useQuery({
    queryKey: ["complaints", "mine", tab],
    queryFn: async () => (await api.get<ComplaintPage>("/api/complaints", { params: { status, limit: 200 } })).data,
    placeholderData: keepPreviousData,
    refetchInterval: 30_000,
  });
  const counts = q.data?.counts;
  const openCount = counts ? OPEN.reduce((s, k) => s + (counts[k] ?? 0), 0) : 0;
  const closedCount = counts ? (counts.verified ?? 0) + (counts.dismissed ?? 0) : 0;

  return (
    <>
      <PageHeader
        title="My complaints"
        description="Complaints raised automatically where your phone measured weak or dead service, and problems you reported. Each one carries its evidence and shows where it stands."
        actions={<Button onClick={() => setReporting(true)}><Megaphone /> Report a problem</Button>}
      />
      <Tabs value={tab} onValueChange={(v) => setTab(v as typeof tab)} className="mb-4">
        <TabsList>
          <TabsTrigger value="open">Open ({openCount})</TabsTrigger>
          <TabsTrigger value="closed">Closed ({closedCount})</TabsTrigger>
          <TabsTrigger value="all">All</TabsTrigger>
        </TabsList>
      </Tabs>
      {q.isPending ? (
        <div className="space-y-2">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-16" />)}</div>
      ) : q.isError ? (
        <ErrorState message={apiError(q.error)} onRetry={() => q.refetch()} />
      ) : q.data.items.length === 0 ? (
        <EmptyState
          icon={FileWarning}
          title={tab === "closed" ? "No closed complaints yet" : "No complaints"}
          description="When your phone measures a zone that stays weak or dead, SignalScout files the complaint for you. You can also report a problem yourself."
          action={<Button asChild variant="outline"><Link to="/probe"><Smartphone /> Open the field probe</Link></Button>}
        />
      ) : (
        <ComplaintList items={q.data.items} />
      )}
      <ReportDialog open={reporting} onOpenChange={setReporting} />
    </>
  );
}
