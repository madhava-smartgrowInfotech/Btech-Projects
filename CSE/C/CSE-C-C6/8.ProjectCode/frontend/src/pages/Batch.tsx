import { useMutation } from "@tanstack/react-query";
import { Download, FileSpreadsheet, PieChart as PieIcon, Play, Timer } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { ChartCard, ChartTooltip } from "@/components/charts/Chart";
import { VerdictBadge } from "@/components/detect/VerdictBadge";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/Display";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { FormField } from "@/components/ui/Field";
import { FileDrop } from "@/components/ui/FileDrop";
import { PageHeader } from "@/components/ui/Layout";
import { Select } from "@/components/ui/Select";
import { Table, type Column } from "@/components/ui/Table";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage, LABELS, type BatchPreview, type BatchResult, type BatchRow } from "@/lib/api";
import { useSamples } from "@/lib/queries";
import { pct, VERDICT } from "@/lib/verdict";
import { formatBytes, prefersReducedMotion } from "@/lib/utils";

const MAX_BYTES = 25 * 1024 * 1024;
const SHOWN_ROWS = 50;
const PREVIEW_COLUMNS = 6;

function validateCsv(f: File) {
  if (!f.name.toLowerCase().endsWith(".csv")) return `"${f.name}" is not a .csv file. Export your data as CSV and try again.`;
  if (f.size > MAX_BYTES) return `"${f.name}" is ${formatBytes(f.size)}; the limit is ${formatBytes(MAX_BYTES)}.`;
  return null;
}

function download(name: string, text: string) {
  const url = URL.createObjectURL(new Blob([text], { type: "text/csv;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

const resultColumns: Column<BatchRow>[] = [
  { key: "row", header: "#", cell: (r) => <span className="tabular-nums text-muted-foreground">{r.row}</span>, sortValue: (r) => r.row, className: "w-12" },
  {
    key: "text",
    header: "Article text",
    cell: (r) => (
      <span className="line-clamp-2 max-w-md break-words" title={r.text}>
        {r.text || <em className="text-muted-foreground">(empty)</em>}
      </span>
    ),
  },
  { key: "predicted", header: "Verdict", cell: (r) => <VerdictBadge label={r.predicted} />, sortValue: (r) => r.predicted },
  {
    key: "confidence",
    header: "Confidence",
    align: "right",
    cell: (r) => <span className="tabular-nums">{r.confidence === null ? "-" : pct(r.confidence)}</span>,
    sortValue: (r) => r.confidence,
  },
];

function Distribution({ result }: { result: BatchResult }) {
  const data = LABELS.map((l) => ({ name: l, value: result.distribution[l] ?? 0 }));
  const total = data.reduce((a, d) => a + d.value, 0);
  return (
    <ChartCard
      title="Batch verdict distribution"
      description={`${total.toLocaleString("en-US")} articles by predicted class`}
      icon={<PieIcon />}
      legend={LABELS.map((l) => ({ label: `${l} (${result.distribution[l] ?? 0})`, color: VERDICT[l].color }))}
      table={{ columns: ["Class", "Articles", "Share"], rows: data.map((d) => [d.name, d.value, total ? pct(d.value / total) : "-"]) }}
    >
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Tooltip content={<ChartTooltip formatter={(v) => `${v} articles`} />} />
            <Pie data={data.filter((d) => d.value > 0)} dataKey="value" nameKey="name" innerRadius="55%" outerRadius="85%" paddingAngle={3} stroke="none">
              {data
                .filter((d) => d.value > 0)
                .map((d) => (
                  <Cell key={d.name} fill={VERDICT[d.name].color} />
                ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}

export default function Batch() {
  const [file, setFile] = useState<File | null>(null);
  const [column, setColumn] = useState<string>("");
  const samples = useSamples();
  const resultRef = useRef<HTMLDivElement>(null);

  function downloadExample() {
    const esc = (t: string) => `"${t.replace(/"/g, '""')}"`;
    const rows = (samples.data ?? []).map((x) => `${esc(x.text)},${x.label}`);
    download("example_articles.csv", ["text,label", ...rows].join("\n"));
    toast.success("Example CSV downloaded", { description: "Drop it into the box above to try batch detection." });
  }

  const preview = useMutation({
    mutationFn: async (f: File) => {
      const fd = new FormData();
      fd.append("file", f);
      return (await api.post<BatchPreview>("/batch/preview", fd)).data;
    },
    onSuccess: (p) => setColumn(p.guessed_column),
    onError: (e) => toast.error("Couldn't read that CSV", { description: errorMessage(e) }),
  });

  const run = useMutation({
    mutationFn: async () => {
      const fd = new FormData();
      fd.append("file", file as File);
      fd.append("column", column);
      return (await api.post<BatchResult>("/batch/run", fd)).data;
    },
    onSuccess: (r) => toast.success(`Screened ${r.n_rows.toLocaleString("en-US")} articles`, { description: `Done in ${r.seconds} s` }),
    onError: (e) => toast.error("Batch detection failed", { description: errorMessage(e) }),
  });

  function onFile(f: File | null) {
    setFile(f);
    run.reset();
    preview.reset();
    setColumn("");
    if (f) preview.mutate(f);
  }

  const p = preview.data;
  const r = run.data;

  useEffect(() => {
    if (r) resultRef.current?.scrollIntoView({ behavior: prefersReducedMotion() ? "auto" : "smooth", block: "start" });
  }, [r]);
  const top = r ? LABELS.reduce((a, l) => (r.distribution[l] > r.distribution[a] ? l : a), LABELS[0]) : null;

  return (
    <>
      <PageHeader
        eyebrow="Batch check"
        title="Screen a whole CSV"
        description="Upload a CSV with one article per row. Pick the text column, run detection and download the results with a verdict and confidence for every row."
      />
      <div className="space-y-6">
        <FileDrop
          file={file}
          onFile={onFile}
          accept=".csv,text/csv"
          validate={validateCsv}
          title="Drop a CSV here, or click to browse"
          hint="A text column named text, news, content, statement or article is detected automatically · up to 25 MB"
          disabled={preview.isPending || run.isPending}
        />

        {file && preview.isPending && (
          <div className="space-y-3" role="status" aria-label="Reading file">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-40 w-full rounded-2xl" />
          </div>
        )}

        {file && preview.isError && (
          <ErrorState
            error={preview.error}
            title="This file can't be read"
            hint="Check that it is a comma-separated file with a header row, then choose it again."
            onRetry={() => preview.mutate(file)}
          />
        )}

        {p && (
          <Card className="space-y-4 p-5 sm:p-6">
            <CardHeader
              className="px-0 pt-0"
              icon={<FileSpreadsheet />}
              title={p.filename}
              description={`${p.n_rows.toLocaleString("en-US")} rows · ${p.columns.length} columns · first ${p.preview.length} shown`}
            />
            <Table
              caption="Preview of the uploaded file"
              columns={p.columns.slice(0, PREVIEW_COLUMNS).map<Column<Record<string, string>>>((c) => ({
                key: c,
                header: c,
                cell: (row) => (
                  <span className="line-clamp-2 max-w-xs break-words" title={row[c]}>
                    {row[c]}
                  </span>
                ),
              }))}
              rows={p.preview}
              rowKey={(row) => JSON.stringify(row)}
              pageSize={10}
            />
            {p.columns.length > PREVIEW_COLUMNS && (
              <p className="text-xs text-muted-foreground">Showing the first {PREVIEW_COLUMNS} of {p.columns.length} columns.</p>
            )}
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
              <FormField label="Text column" hint="The column that holds the article text" className="sm:w-72">
                {(f) => <Select {...f} value={column} onValueChange={setColumn} options={p.columns.map((c) => ({ value: c, label: c }))} placeholder="Choose a column" />}
              </FormField>
              <Button size="lg" loading={run.isPending} disabled={!column} onClick={() => run.mutate()} className="sm:mb-[1.4rem]">
                <Play /> Run batch detection
              </Button>
            </div>
          </Card>
        )}

        <div ref={resultRef} className="scroll-mt-24" />
        {run.isPending && (
          <div className="space-y-3" role="status" aria-label="Running detection">
            <div className="grid gap-4 sm:grid-cols-3">
              {[0, 1, 2].map((i) => (
                <Skeleton key={i} className="h-32 rounded-2xl" />
              ))}
            </div>
            <Skeleton className="h-64 w-full rounded-2xl" />
          </div>
        )}

        {run.isError && (
          <ErrorState error={run.error} title="Batch detection failed" hint="Your file is still loaded. Pick another column or try again." onRetry={() => run.mutate()} />
        )}

        {r && top && (
          <Stagger className="space-y-6">
            <StaggerItem className="grid gap-4 sm:grid-cols-3">
              <StatCard label="Articles screened" value={r.n_rows} icon={<FileSpreadsheet />} hint={`column "${r.column}"`} />
              <StatCard label="Most common verdict" display={<VerdictBadge label={top} size="lg" />} hint={`${r.distribution[top]} of ${r.n_rows}`} accent="magenta" />
              <StatCard label="Time taken" value={r.seconds} format={(n) => `${n.toFixed(2)} s`} icon={<Timer />} accent="cyan" />
            </StaggerItem>
            <StaggerItem className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)]">
              <Distribution result={r} />
              <Card className="min-w-0 space-y-4 p-5">
                <CardHeader
                  className="px-0 pt-0"
                  title="Results"
                  description={r.n_rows > SHOWN_ROWS ? `First ${SHOWN_ROWS} of ${r.n_rows.toLocaleString("en-US")} rows - download the CSV for all of them` : `All ${r.n_rows} rows`}
                  action={
                    <Button variant="secondary" size="sm" onClick={() => (download("fake_news_results.csv", r.csv), toast.success("Results downloaded"))}>
                      <Download /> Download CSV
                    </Button>
                  }
                />
                <Table caption="Detection results" columns={resultColumns} rows={r.rows.slice(0, SHOWN_ROWS)} rowKey={(row) => row.row} pageSize={10} />
              </Card>
            </StaggerItem>
          </Stagger>
        )}

        {!file && (
          <EmptyState
            icon={<FileSpreadsheet />}
            title="No file yet"
            description="Choose a CSV above to preview it. Rows are only read by your own local backend and never leave this computer."
            action={
              <Button variant="secondary" disabled={!samples.data} onClick={downloadExample}>
                <Download /> Download an example CSV
              </Button>
            }
          />
        )}
      </div>
    </>
  );
}
