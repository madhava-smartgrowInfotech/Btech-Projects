import { useQuery } from "@tanstack/react-query";
import { Bot, Download, FileJson, FileSpreadsheet, FileText, ShieldCheck, Wrench } from "lucide-react";
import { lazy, Suspense, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { Table, type Column } from "@/components/ui/Table";
import { Timeline } from "@/components/ui/Display";
import { toast } from "@/components/ui/Toast";
import { api, download, errorMessage } from "@/lib/api";
import { keys } from "@/lib/queries";
import type { FuncRow, Review } from "@/lib/types";

const Markdown = lazy(() => import("@/components/app/Markdown"));

/* ------------------------------------------------------------------ files */
type FileRow = Review["files"][number] & { findings: number };

export function FilesTab({ review }: { review: Review }) {
  const byFile = review.stats.by_file;
  const files: FileRow[] = review.files.map((f) => ({ ...f, findings: byFile[f.path] ?? 0 }));
  const maxF = Math.max(1, ...files.map((f) => f.findings));
  const cols: Column<FileRow>[] = [
    { key: "path", header: "File", cell: (r) => <span className="font-mono text-xs">{r.path}</span>, sortValue: (r) => r.path },
    { key: "lang", header: "Language", cell: (r) => r.language, sortValue: (r) => r.language },
    { key: "status", header: "Status", cell: (r) => <Badge tone="neutral">{r.status}</Badge>, sortValue: (r) => r.status },
    { key: "added", header: "Added", align: "right", cell: (r) => <span className="text-success">+{r.added}</span>, sortValue: (r) => r.added },
    { key: "removed", header: "Removed", align: "right", cell: (r) => <span className="text-danger">-{r.removed}</span>, sortValue: (r) => r.removed },
    {
      key: "findings",
      header: "Findings in change",
      cell: (r) => (
        <div className="flex items-center gap-2">
          <div className="h-1.5 w-20 overflow-hidden rounded-full bg-muted">
            <div className="h-full rounded-full bg-grad-primary" style={{ width: `${(r.findings / maxF) * 100}%` }} />
          </div>
          <span className="w-5 text-xs tabular-nums">{r.findings}</span>
        </div>
      ),
      sortValue: (r) => r.findings,
    },
  ];
  const funcs = review.functions.filter((f) => f.name !== "<module>");
  const fcols: Column<FuncRow>[] = [
    { key: "name", header: "Function", cell: (r) => <span className="font-mono text-xs">{r.name}</span>, sortValue: (r) => r.name },
    { key: "file", header: "File", cell: (r) => <span className="font-mono text-xs">{r.file}:{r.line}</span>, sortValue: (r) => r.file },
    { key: "cc", header: "Cyclomatic", align: "right", cell: (r) => r.cyclomatic, sortValue: (r) => r.cyclomatic },
    { key: "nest", header: "Nesting", align: "right", cell: (r) => r.max_nesting, sortValue: (r) => r.max_nesting },
    { key: "params", header: "Params", align: "right", cell: (r) => r.n_params, sortValue: (r) => r.n_params },
    { key: "loc", header: "LOC", align: "right", cell: (r) => r.loc, sortValue: (r) => r.loc },
    { key: "changed", header: "Changed", cell: (r) => (r.in_diff === false ? <Badge tone="neutral">no</Badge> : <Badge tone="violet">yes</Badge>), sortValue: (r) => (r.in_diff === false ? 0 : 1) },
  ];
  return (
    <div className="space-y-6">
      <Table columns={cols} rows={files} rowKey={(r) => r.path} initialSort={{ key: "findings", dir: "desc" }} caption="Files in the change" pageSize={8} />
      {funcs.length > 0 && (
        <div className="space-y-3">
          <h3 className="font-display text-lg font-semibold">Function complexity in changed files</h3>
          <Table
            columns={fcols}
            rows={[...funcs].sort((a, b) => b.cyclomatic - a.cyclomatic).slice(0, 15)}
            rowKey={(r) => `${r.file}:${r.name}:${r.line}`}
            initialSort={{ key: "cc", dir: "desc" }}
            caption="Most complex functions"
            pageSize={8}
          />
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ trace */
export function TraceTab({ review }: { review: Review }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">What each agent did, in order. This is the audit trail behind the verdict.</p>
      <Card>
        <CardBody>
          <Timeline
            items={review.trace.map((t) => ({
              icon: <Bot />,
              title: t.agent,
              meta: `${t.role} · ${t.seconds}s`,
              body: (
                <>
                  <span className="block text-foreground">{t.summary}</span>
                  {t.details.slice(0, 6).map((d) => (
                    <span key={d} className="block text-xs">• {d}</span>
                  ))}
                </>
              ),
            }))}
          />
        </CardBody>
      </Card>
    </div>
  );
}

/* ------------------------------------------------------------------ export */
const FORMATS = [
  { fmt: "md", label: "PR comment (.md)", icon: FileText },
  { fmt: "sarif", label: "SARIF 2.1 (GitHub code scanning)", icon: ShieldCheck },
  { fmt: "json", label: "Full JSON", icon: FileJson },
  { fmt: "csv", label: "Findings CSV", icon: FileSpreadsheet },
] as const;

export function ExportTab({ review }: { review: Review }) {
  const [busy, setBusy] = useState<string | null>(null);
  const md = useQuery({
    queryKey: keys.markdown(review.id),
    queryFn: async () => (await api.get<string>(`/reviews/${review.id}/export/md`, { responseType: "text", transformResponse: (d) => d })).data,
    staleTime: 10 * 60_000,
  });

  async function get(path: string, name: string, key: string) {
    setBusy(key);
    try {
      const saved = await download(path, name);
      toast.success(`Downloaded ${saved}`);
    } catch (e) {
      toast.error(`Download failed: ${errorMessage(e)}`);
    } finally {
      setBusy(null);
    }
  }

  const patched = Object.keys(review.patched ?? {});
  return (
    <div className="grid gap-5 lg:grid-cols-[1.3fr_1fr]">
      <Card className="min-w-0">
        <CardHeader title="PR comment preview" description="Paste this into GitHub" />
        <CardBody>
          {md.isPending ? (
            <div className="space-y-2" role="status" aria-label="Loading preview">
              <Skeleton className="h-6 w-2/3" />
              <Skeleton className="h-40" />
            </div>
          ) : md.isError ? (
            <ErrorState error={md.error} title="Couldn't build the preview" onRetry={() => md.refetch()} />
          ) : (
            <div className="scrollbar-thin max-h-[28rem] overflow-auto rounded-xl border border-[var(--glass-border)] bg-muted/40 p-4">
              <Suspense fallback={<Skeleton className="h-40" />}>
                <Markdown>{md.data}</Markdown>
              </Suspense>
            </div>
          )}
        </CardBody>
      </Card>
      <div className="space-y-4">
        <Card>
          <CardHeader title="Download" icon={<Download />} />
          <CardBody className="space-y-2">
            {FORMATS.map(({ fmt, label, icon: Icon }) => (
              <Button
                key={fmt}
                variant="secondary"
                className="w-full justify-start"
                loading={busy === fmt}
                onClick={() => get(`/reviews/${review.id}/export/${fmt}`, `autosecai-${review.id}.${fmt}`, fmt)}
              >
                <Icon /> {label}
              </Button>
            ))}
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Auto-fixed files" icon={<Wrench />} description="Whole files with every verified patch applied" />
          <CardBody className="space-y-2">
            {patched.length === 0 ? (
              <EmptyState icon={<Wrench />} title="No whole-file fixes" description="Whole files are produced for full-file input (compare versions, upload). For a diff, copy each verified patch from its finding on the Findings tab." className="py-8" />
            ) : (
              patched.slice(0, 8).map((p) => (
                <Button
                  key={p}
                  variant="secondary"
                  className="w-full justify-start"
                  loading={busy === p}
                  onClick={() => get(`/reviews/${review.id}/patched?path=${encodeURIComponent(p)}`, p.split("/").pop() ?? "patched.txt", p)}
                >
                  <Download /> <span className="truncate">{p}</span>
                </Button>
              ))
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
