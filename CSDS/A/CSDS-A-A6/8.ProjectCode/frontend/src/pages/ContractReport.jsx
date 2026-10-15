import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { ArrowRight, GitGraph, Gauge } from "lucide-react";
import { Bar, BarChart, Cell, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Link, useNavigate, useParams } from "react-router";

import { GradeBadge, SeverityBadge, humanize } from "@/components/app/RiskBadges.jsx";
import { ChartCard, ChartTooltip, STATUS, axisProps, gridProps } from "@/components/charts/Chart";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/Display";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { Table } from "@/components/ui/Table";
import { useBreadcrumb } from "@/components/ui/AppShell";
import { contractsApi } from "@/lib/api.js";
import { keys } from "@/lib/queries.js";
import { formatDate } from "@/lib/utils";

const SEVERITY_ORDER = [
  { key: "high", label: "High", color: STATUS.critical },
  { key: "medium", label: "Medium", color: STATUS.serious },
  { key: "low", label: "Low", color: STATUS.warning },
  { key: "none", label: "None", color: STATUS.neutral },
];

export default function ContractReport() {
  const { id } = useParams();
  const navigate = useNavigate();
  const query = useQuery({
    queryKey: keys.contract(id),
    queryFn: async () => (await contractsApi.get(id)).data,
  });
  const report = query.data;

  useBreadcrumb(report?.filename);

  const severityCounts = useMemo(() => {
    const counts = Object.fromEntries(SEVERITY_ORDER.map((s) => [s.key, 0]));
    (report?.clauses ?? []).forEach((c) => {
      counts[c.max_severity in counts ? c.max_severity : "none"] += 1;
    });
    return SEVERITY_ORDER.map((s) => ({ name: s.label, key: s.key, count: counts[s.key], color: s.color }));
  }, [report]);

  if (query.isPending) {
    return (
      <div className="space-y-6" role="status" aria-label="Loading report">
        <Skeleton className="h-10 w-2/3" />
        <Skeleton className="h-4 w-1/3" />
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-28 rounded-2xl" />
          ))}
        </div>
        <Skeleton className="h-64 rounded-2xl" />
      </div>
    );
  }

  if (query.isError) {
    const notFound = query.error?.response?.status === 404;
    return (
      <ErrorState
        error={query.error}
        title={notFound ? "This contract isn't available" : "Couldn't load this report"}
        hint={notFound ? "It may have been removed, or it belongs to a different account." : "Check that the backend is running, then try again."}
        onRetry={notFound ? undefined : () => query.refetch()}
      />
    );
  }

  const clauses = report.clauses ?? [];
  const combos = report.combo_flags ?? [];

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Contract report"
        title={<span className="[overflow-wrap:anywhere]">{report.filename}</span>}
        description={`Uploaded ${formatDate(report.uploaded_at, true)} · ${report.clauses.length} clauses`}
        actions={
          <>
            <GradeBadge grade={report.complexity_grade} />
            <Button asChild variant="outline">
              <Link to={`/app/contracts/${id}/graph`}>
                <GitGraph /> Clause graph
              </Link>
            </Button>
          </>
        }
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
        <StatCard label="Complexity grade" display={report.complexity_grade} hint={`Score ${report.complexity_score}`} icon={<Gauge />} />
        <StatCard label="Readability" value={report.readability_score} format={(n) => n.toFixed(1)} hint="Flesch reading ease (higher = easier)" accent="cyan" />
        <StatCard label="Legalese density" value={report.legalese_density} format={(n) => `${n.toFixed(1)}%`} hint="Legal jargon per 100 words" accent="magenta" />
        <StatCard label="Cross-references" value={report.cross_reference_count} format={(n) => String(n)} hint="Section and clause references" />
        <StatCard label="Avg sentence length" value={report.avg_sentence_length} format={(n) => `${n.toFixed(1)} words`} hint="Words per sentence" accent="cyan" />
        <StatCard label="Flagged clauses" value={clauses.filter((c) => c.flag_count > 0).length} format={(n) => String(n)} hint={`${clauses.length} clauses in total`} accent="magenta" />
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader title="Plain-language summary" />
          <CardBody className="space-y-5">
            <p className="whitespace-pre-line leading-relaxed text-muted-foreground">{report.plain_summary || "No summary was generated for this contract."}</p>
            <div>
              <h3 className="text-sm font-semibold">Key obligations</h3>
              {report.key_obligations.length ? (
                <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm text-muted-foreground">
                  {report.key_obligations.map((o, i) => (
                    <li key={i}>{o}</li>
                  ))}
                </ul>
              ) : (
                <p className="mt-2 text-sm text-muted-foreground">No key obligations were extracted.</p>
              )}
            </div>
          </CardBody>
        </Card>

        <div className="space-y-6 lg:col-span-2">
          <ChartCard
            title="Clauses by highest severity"
            description="Each clause counted once, at its worst flag."
            empty={clauses.length === 0 ? "No clauses were extracted from this contract." : undefined}
            table={{
              columns: ["Severity", "Clauses"],
              rows: severityCounts.map((s) => [s.name, s.count]),
            }}
          >
            <ResponsiveContainer width="100%" height={210}>
              <BarChart data={severityCounts} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="name" {...axisProps} />
                <YAxis allowDecimals={false} {...axisProps} />
                <Tooltip content={<ChartTooltip />} cursor={{ fill: "var(--chart-grid)" }} />
                <Bar dataKey="count" name="Clauses" radius={[8, 8, 0, 0]}>
                  {severityCounts.map((s) => (
                    <Cell key={s.key} fill={s.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <Card className="border-warning/35">
            <CardHeader title="Risky clause combinations" icon={<GitGraph />} />
            <CardBody>
              {combos.length === 0 ? (
                <p className="text-sm text-muted-foreground">None detected. No set of clauses in this contract combines into a known risky pattern.</p>
              ) : (
                <ul className="space-y-3">
                  {combos.map((combo, i) => (
                    <li key={combo.combo_id ?? i} className="rounded-xl border border-warning/30 bg-warning/10 p-3 text-sm">
                      {combo.reason || "Risky combination of clauses."}
                    </li>
                  ))}
                </ul>
              )}
            </CardBody>
          </Card>
        </div>
      </div>

      <Card>
        <CardHeader title={`Clauses (${clauses.length})`} description="Select a clause to see its flags and safer wording." />
        <CardBody>
          <Table
            caption="Clauses in this contract"
            rowKey={(c) => c.id}
            rows={clauses}
            pageSize={10}
            initialSort={{ key: "order", dir: "asc" }}
            onRowClick={(c) => navigate(`/app/contracts/${id}/clauses/${c.id}`)}
            columns={[
              {
                key: "order",
                header: "#",
                cell: (c) => (
                  <Link to={`/app/contracts/${id}/clauses/${c.id}`} className="font-medium text-foreground underline-offset-4 hover:underline">
                    {c.index_in_doc + 1}
                  </Link>
                ),
                sortValue: (c) => c.index_in_doc,
              },
              { key: "page", header: "Page", cell: (c) => c.page_number, sortValue: (c) => c.page_number, hideOnCard: true },
              { key: "type", header: "Type", cell: (c) => humanize(c.clause_type), sortValue: (c) => c.clause_type },
              {
                key: "preview",
                header: "Clause",
                cell: (c) => <span className="line-clamp-2 text-muted-foreground">{c.text_preview}</span>,
                hideOnCard: true,
              },
              { key: "flags", header: "Flags", cell: (c) => c.flag_count, align: "right", sortValue: (c) => c.flag_count },
              { key: "risk", header: "Risk", cell: (c) => <SeverityBadge severity={c.max_severity} />, sortValue: (c) => c.max_severity },
            ]}
          />
          <p className="mt-4 flex items-center gap-1.5 text-xs text-muted-foreground">
            <ArrowRight className="size-3.5" /> Select a row, or a clause number, to open its flags.
          </p>
        </CardBody>
      </Card>
    </div>
  );
}
