import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "motion/react";
import {
  AlertTriangle, ArrowRight, CheckCircle2, ChevronDown, Download, FileSpreadsheet, History, Info, RotateCcw, XCircle,
} from "lucide-react";
import { toast } from "sonner";
import { FileDrop } from "@/components/common/FileDrop";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState, TableSkeleton } from "@/components/common/States";
import {
  AlertDialog, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api, downloadFile, errorMessage } from "@/lib/api";
import { formatNumber, timeAgo } from "@/lib/format";
import type { DataKind, ImportBatch, ImportKind, ImportReport } from "@/lib/types";
import { cn } from "@/lib/utils";

const KINDS: { value: ImportKind; label: string; help: string }[] = [
  { value: "workbook", label: "Everything", help: "One Excel workbook with Courses, Halls, Candidates and Timetable sheets." },
  { value: "courses", label: "Courses", help: "Course codes, names and departments. Import these first." },
  { value: "halls", label: "Halls", help: "Rows x columns, blocked seats, accessible seats and aisles." },
  { value: "candidates", label: "Candidates", help: "Roll numbers, names, departments and the courses each person sits." },
  { value: "timetable", label: "Timetable", help: "Which course is examined in which sitting (date and time)." },
];
const TITLES: Record<DataKind, string> = { courses: "Courses", halls: "Halls", candidates: "Candidates", timetable: "Timetable" };
const ORDER: DataKind[] = ["courses", "halls", "candidates", "timetable"];

async function download(url: string, name: string) {
  try {
    await downloadFile(url, name);
  } catch (err) {
    toast.error(errorMessage(err));
  }
}

function DownloadMenu() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline">
          <Download /> Templates &amp; samples <ChevronDown className="opacity-60" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-72">
        <DropdownMenuLabel>Empty templates</DropdownMenuLabel>
        <DropdownMenuItem onSelect={() => download("/imports/templates/workbook", "seatwise_import_template.xlsx")}>
          <FileSpreadsheet /> Combined workbook (.xlsx)
        </DropdownMenuItem>
        {ORDER.map((kind) => (
          <DropdownMenuItem key={kind} onSelect={() => download(`/imports/templates/${kind}`, `${kind}_template.xlsx`)}>
            <FileSpreadsheet /> {TITLES[kind]} template (.xlsx)
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <DropdownMenuLabel>Sample data (fictional)</DropdownMenuLabel>
        <DropdownMenuItem onSelect={() => download("/imports/samples/workbook", "sample_seatwise_sample_workbook.xlsx")}>
          <FileSpreadsheet /> Sample workbook - 908 candidates, 14 halls
        </DropdownMenuItem>
        {ORDER.map((kind) => (
          <DropdownMenuItem key={kind} onSelect={() => download(`/imports/samples/${kind}`, `sample_${kind}.csv`)}>
            <FileSpreadsheet /> Sample {TITLES[kind].toLowerCase()} (.csv)
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function ReportView({ batch, onCommit, committing, onReset }: {
  batch: ImportBatch;
  onCommit: () => void;
  committing: boolean;
  onReset: () => void;
}) {
  const report = batch.report as ImportReport;
  const kinds = ORDER.filter((k) => report.kinds[k]);
  const [filter, setFilter] = useState<"all" | "error" | "warning">(report.errors ? "error" : "all");
  const issues = report.issues.filter((i) => filter === "all" || i.level === filter);
  const passed = report.errors === 0;
  const committed = batch.status === "committed";

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
      <div
        className={cn(
          "flex flex-col gap-4 rounded-xl border p-4 sm:flex-row sm:items-center sm:justify-between",
          committed ? "border-success/40 bg-success/5" : passed ? "border-success/40 bg-success/5" : "border-destructive/40 bg-destructive/5",
        )}
        role="status"
      >
        <div className="flex items-start gap-3">
          {passed ? <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-success" /> : <XCircle className="mt-0.5 size-5 shrink-0 text-destructive" />}
          <div>
            <div className="font-semibold">
              {committed ? "Imported" : passed ? "Validation passed" : `${report.errors} problem${report.errors === 1 ? "" : "s"} to fix`}
            </div>
            <div className="text-sm text-muted-foreground">
              {batch.filename} · {formatNumber(batch.rows_valid)} of {formatNumber(batch.rows_total)} rows valid
              {report.warnings > 0 && ` · ${report.warnings} warning${report.warnings === 1 ? "" : "s"}`}
              {report.mode === "replace" && " · replaces existing data"}
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={onReset}>
            <RotateCcw /> {committed ? "Import another file" : "Choose another file"}
          </Button>
          {!committed && (
            <Button onClick={onCommit} disabled={!passed} loading={committing}>
              Import {formatNumber(batch.rows_valid)} rows
            </Button>
          )}
          {committed && (
            <Button asChild>
              <Link to="/app/sessions">
                Generate plans <ArrowRight />
              </Link>
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {kinds.map((kind) => {
          const k = report.kinds[kind]!;
          return (
            <Card key={kind} className="shadow-none">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{TITLES[kind]}</span>
                  {k.errors ? (
                    <Badge variant="destructive">{k.errors} errors</Badge>
                  ) : k.warnings ? (
                    <Badge variant="warning">{k.warnings} warnings</Badge>
                  ) : (
                    <Badge variant="success">OK</Badge>
                  )}
                </div>
                <div className="mt-2 font-display text-2xl font-semibold tabular">{formatNumber(k.rows_total)}</div>
                <div className="text-xs text-muted-foreground">
                  {formatNumber(k.new)} new · {formatNumber(k.updated)} updated
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {report.issues.length > 0 && (
        <Card>
          <CardHeader className="flex-row flex-wrap items-center justify-between gap-2 space-y-0">
            <CardTitle className="text-sm">Problems found</CardTitle>
            <div className="flex gap-1">
              {(["all", "error", "warning"] as const).map((f) => (
                <Button key={f} size="sm" variant={filter === f ? "secondary" : "ghost"} onClick={() => setFilter(f)}>
                  {f === "all" ? "All" : f === "error" ? `Errors (${report.errors})` : `Warnings (${report.warnings})`}
                </Button>
              ))}
            </div>
          </CardHeader>
          <CardContent className="max-h-96 overflow-y-auto p-0 scrollbar-thin">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-24">Sheet</TableHead>
                  <TableHead className="w-16">Row</TableHead>
                  <TableHead className="w-40">Column</TableHead>
                  <TableHead>What to fix</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {issues.map((issue, i) => (
                  <TableRow key={i}>
                    <TableCell className="text-xs text-muted-foreground">{TITLES[issue.kind]}</TableCell>
                    <TableCell className="tabular">{issue.row ?? "-"}</TableCell>
                    <TableCell className="font-mono text-xs">{issue.column ?? "-"}</TableCell>
                    <TableCell>
                      <span className="flex items-start gap-2">
                        {issue.level === "error" ? (
                          <XCircle className="mt-0.5 size-4 shrink-0 text-destructive" aria-label="Error" />
                        ) : (
                          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-warning" aria-label="Warning" />
                        )}
                        {issue.message}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {report.issues_truncated && (
              <p className="p-3 text-xs text-muted-foreground">Only the first 500 problems are listed.</p>
            )}
          </CardContent>
        </Card>
      )}

      {kinds.some((k) => report.preview[k]?.length) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Preview</CardTitle>
            <CardDescription>The first rows of each sheet, as SeatWise read them.</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue={kinds[0]}>
              <TabsList>
                {kinds.map((k) => (
                  <TabsTrigger key={k} value={k}>
                    {TITLES[k]}
                  </TabsTrigger>
                ))}
              </TabsList>
              {kinds.map((k) => {
                const rows = report.preview[k] ?? [];
                const columns = rows[0] ? Object.keys(rows[0]) : [];
                return (
                  <TabsContent key={k} value={k}>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          {columns.map((c) => (
                            <TableHead key={c} className="normal-case">
                              {c}
                            </TableHead>
                          ))}
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {rows.map((row, i) => (
                          <TableRow key={i}>
                            {columns.map((c) => (
                              <TableCell key={c} className="max-w-56 truncate whitespace-nowrap text-xs">
                                {row[c] ?? <span className="text-muted-foreground">-</span>}
                              </TableCell>
                            ))}
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TabsContent>
                );
              })}
            </Tabs>
          </CardContent>
        </Card>
      )}
    </motion.div>
  );
}

function ImportHistory() {
  const history = useQuery({ queryKey: ["imports"], queryFn: async () => (await api.get<ImportBatch[]>("/imports")).data });
  const statusBadge = {
    committed: <Badge variant="success">Imported</Badge>,
    validated: <Badge variant="secondary">Checked, not imported</Badge>,
    failed: <Badge variant="destructive">Did not pass</Badge>,
  } as const;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <History className="size-4" /> Recent imports
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {history.isPending && <div className="p-5"><TableSkeleton rows={3} /></div>}
        {history.isError && <div className="p-5"><ErrorState error={history.error} onRetry={() => history.refetch()} /></div>}
        {history.data && history.data.length === 0 && (
          <p className="px-5 pb-5 text-sm text-muted-foreground">Nothing has been imported yet.</p>
        )}
        {history.data && history.data.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>File</TableHead>
                <TableHead className="hidden sm:table-cell">Type</TableHead>
                <TableHead>Rows</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="hidden md:table-cell">When</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {history.data.map((b) => (
                <TableRow key={b.id}>
                  <TableCell className="max-w-48 truncate font-medium">{b.filename}</TableCell>
                  <TableCell className="hidden capitalize sm:table-cell">{b.kind === "workbook" ? "Everything" : b.kind}</TableCell>
                  <TableCell className="tabular">{formatNumber(b.rows_total)}</TableCell>
                  <TableCell>{statusBadge[b.status]}</TableCell>
                  <TableCell className="hidden text-muted-foreground md:table-cell">
                    {timeAgo(b.committed_at ?? b.created_at)}
                    {b.created_by && ` · ${b.created_by}`}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

export default function ImportPage() {
  const queryClient = useQueryClient();
  const [kind, setKind] = useState<ImportKind>("workbook");
  const [mode, setMode] = useState<"update" | "replace">("update");
  const [batch, setBatch] = useState<ImportBatch | null>(null);
  const [confirmReplace, setConfirmReplace] = useState(false);

  const validate = useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      form.append("mode", mode);
      return (await api.post<ImportBatch>(`/imports/${kind}/validate`, form)).data;
    },
    onSuccess: (data) => {
      setBatch(data);
      queryClient.invalidateQueries({ queryKey: ["imports"] });
    },
    onError: (err) => toast.error(errorMessage(err)),
  });

  const commit = useMutation({
    mutationFn: async () => (await api.post<ImportBatch>(`/imports/${batch!.id}/commit`)).data,
    onSuccess: (data) => {
      setBatch(data);
      setConfirmReplace(false);
      toast.success(`Imported ${formatNumber(data.rows_valid)} rows from ${data.filename}`);
      for (const key of ["imports", "summary", "sessions", "halls", "courses", "candidates", "departments"]) {
        queryClient.invalidateQueries({ queryKey: [key] });
      }
    },
    onError: (err) => {
      toast.error(errorMessage(err));
      queryClient.invalidateQueries({ queryKey: ["imports"] });
    },
  });

  const current = KINDS.find((k) => k.value === kind)!;

  return (
    <>
      <PageHeader
        title="Import data"
        description="Upload courses, halls, candidates and the timetable. Every file is checked first; nothing changes until you confirm."
        actions={<DownloadMenu />}
      />

      <div className="grid gap-6">
        {!batch && (
          <Card>
            <CardHeader>
              <CardTitle>1. What are you importing?</CardTitle>
              <CardDescription>
                Import courses before candidates and the timetable - they refer to course codes. The combined workbook does it
                all in the right order.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Kind of data">
                {KINDS.map((k) => (
                  <button
                    key={k.value}
                    role="radio"
                    aria-checked={kind === k.value}
                    onClick={() => setKind(k.value)}
                    className={cn(
                      "rounded-full border px-4 py-1.5 text-sm font-medium transition-colors",
                      kind === k.value ? "border-primary bg-primary text-primary-foreground" : "hover:bg-accent",
                    )}
                  >
                    {k.label}
                  </button>
                ))}
              </div>
              <p className="flex items-start gap-2 text-sm text-muted-foreground">
                <Info className="mt-0.5 size-4 shrink-0" /> {current.help}
              </p>

              <div>
                <div className="mb-2 text-sm font-medium">2. How should it be applied?</div>
                <RadioGroup value={mode} onValueChange={(v) => setMode(v as "update" | "replace")} className="grid gap-2 sm:grid-cols-2">
                  <Label htmlFor="mode-update" className="flex cursor-pointer items-start gap-3 rounded-lg border p-3 font-normal has-[:checked]:border-primary">
                    <RadioGroupItem value="update" id="mode-update" className="mt-0.5" />
                    <span>
                      <span className="block text-sm font-medium">Add and update</span>
                      <span className="text-xs text-muted-foreground">New rows are added; rows with an existing code are updated.</span>
                    </span>
                  </Label>
                  <Label htmlFor="mode-replace" className="flex cursor-pointer items-start gap-3 rounded-lg border p-3 font-normal has-[:checked]:border-primary">
                    <RadioGroupItem value="replace" id="mode-replace" className="mt-0.5" />
                    <span>
                      <span className="block text-sm font-medium">Replace existing</span>
                      <span className="text-xs text-muted-foreground">Everything of this kind is replaced by the file.</span>
                    </span>
                  </Label>
                </RadioGroup>
              </div>

              <div>
                <div className="mb-2 text-sm font-medium">3. Upload the file</div>
                {validate.isPending ? (
                  <div className="flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed border-primary/40 bg-primary/5 px-6 py-10" aria-busy>
                    <div className="h-1.5 w-40 overflow-hidden rounded-full bg-primary/15">
                      <motion.div
                        className="h-full w-1/3 rounded-full bg-primary"
                        animate={{ x: ["-100%", "300%"] }}
                        transition={{ repeat: Infinity, duration: 1.1, ease: "easeInOut" }}
                      />
                    </div>
                    <span className="text-sm text-muted-foreground">Checking every row...</span>
                  </div>
                ) : (
                  <FileDrop
                    onFile={(file) => validate.mutate(file)}
                    accept={kind === "workbook" ? ".xlsx" : ".csv,.xlsx"}
                    hint={kind === "workbook" ? "Excel workbook (.xlsx), up to 15 MB" : undefined}
                  />
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {batch && (
          <ReportView
            batch={batch}
            committing={commit.isPending}
            onReset={() => setBatch(null)}
            onCommit={() => (batch.report?.mode === "replace" ? setConfirmReplace(true) : commit.mutate())}
          />
        )}

        <ImportHistory />
      </div>

      <AlertDialog open={confirmReplace} onOpenChange={setConfirmReplace}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Replace existing data?</AlertDialogTitle>
            <AlertDialogDescription>
              Everything of this kind that is not in {batch?.filename} will be removed. This cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <Button variant="destructive" loading={commit.isPending} onClick={() => commit.mutate()}>
              Replace
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
