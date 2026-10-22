import { useMutation } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Download, FileSpreadsheet } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ErrorState, InlineLoader } from "@/components/ui/Feedback";
import { FileDrop } from "@/components/ui/FileDrop";
import { Table, type Column } from "@/components/ui/Table";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage, type ImportPreview } from "@/lib/api";
import { useMoney } from "@/lib/format";
import { useRefreshData } from "@/lib/queries";
import { cn } from "@/lib/utils";

type Row = ImportPreview["rows"][number] & { _i: number };

function downloadTemplate() {
  const blob = new Blob(["date,description,amount,category,type\n"], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "finjarvis_import_template.csv";
  a.click();
  URL.revokeObjectURL(url);
}

/** CSV / Excel import: pick a file, review what will be imported and what was skipped, then confirm. */
export function ImportPanel() {
  const money = useMoney();
  const refresh = useRefreshData();
  const [file, setFile] = useState<File | null>(null);
  const [done, setDone] = useState<number | null>(null);

  const preview = useMutation({
    mutationFn: async (f: File) => {
      const body = new FormData();
      body.append("file", f);
      return (await api.post<ImportPreview>("/transactions/import/preview", body)).data;
    },
  });

  const commit = useMutation({
    mutationFn: async (f: File) => {
      const body = new FormData();
      body.append("file", f);
      return (await api.post<{ imported: number }>("/transactions/import/commit", body)).data;
    },
    onSuccess: async (r) => {
      setDone(r.imported);
      toast.success(`Imported ${r.imported} transactions`);
      setFile(null);
      preview.reset();
      await refresh();
    },
    onError: (e) => toast.error("Import failed", { description: errorMessage(e) }),
  });

  useEffect(() => {
    if (file) {
      setDone(null);
      preview.mutate(file);
    } else {
      preview.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file]);

  const columns: Column<Row>[] = [
    { key: "date", header: "Date", cell: (r) => <span className="tabular-nums">{r.date}</span> },
    { key: "description", header: "Description", cell: (r) => <span className="font-medium">{r.description}</span> },
    { key: "category", header: "Category", cell: (r) => <Badge tone="violet">{r.category}</Badge> },
    {
      key: "amount",
      header: "Amount",
      align: "right",
      cell: (r) => (
        <span className={cn("tabular-nums", r.transaction_type === "income" && "text-success")}>
          {r.transaction_type === "income" ? "+" : "-"}
          {money.exact(r.amount)}
        </span>
      ),
    },
    { key: "type", header: "Type", hideOnCard: true, cell: (r) => <span className="capitalize text-muted-foreground">{r.transaction_type}</span> },
  ];

  const data = preview.data;
  return (
    <Card>
      <CardHeader
        title="Import from CSV or Excel"
        description="Columns needed: date, description, amount, category, type. A blank category is filled in by the AI."
        icon={<FileSpreadsheet />}
        action={
          <Button variant="ghost" size="sm" onClick={downloadTemplate}>
            <Download /> Template
          </Button>
        }
      />
      <CardBody className="space-y-4">
        <FileDrop
          file={file}
          onFile={setFile}
          accept=".csv,.xlsx,.xls"
          title="Drop a CSV or Excel file here, or click to browse"
          hint="Nothing is saved until you confirm the preview."
          validate={(f) => (/\.(csv|xlsx|xls)$/i.test(f.name) ? null : "Please choose a .csv, .xlsx or .xls file.")}
          disabled={commit.isPending}
        />

        {done !== null && !file && (
          <p role="status" className="flex items-center gap-2 rounded-xl border border-success/30 bg-success/10 px-3 py-2 text-sm text-success">
            <CheckCircle2 className="size-4" /> Imported {done} transactions. They now appear in View / Manage and on your dashboard.
          </p>
        )}

        {preview.isPending && file && <InlineLoader label="Reading and cleaning your file…" />}
        {preview.isError && <ErrorState error={preview.error} title="Couldn't read that file" hint="Check the column names and that it is a CSV or Excel file." />}

        {data && file && (
          <div className="space-y-3">
            {data.warnings.length > 0 && (
              <details className="rounded-xl border border-warning/35 bg-warning/10 px-3 py-2 text-sm text-warning" open={data.warnings.length <= 5}>
                <summary className="flex cursor-pointer items-center gap-2 font-medium">
                  <AlertTriangle className="size-4" /> {data.warnings.length} row{data.warnings.length > 1 ? "s" : ""} will be skipped
                </summary>
                <ul className="mt-2 list-disc space-y-0.5 pl-6">
                  {data.warnings.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </details>
            )}
            {data.valid === 0 ? (
              <ErrorState error={new Error("No valid rows found to import.")} title="Nothing to import" hint="Fix the problems above and choose the file again." />
            ) : (
              <>
                <p className="text-sm font-medium">Preview: {data.valid} valid rows ready to import</p>
                <Table columns={columns} rows={data.rows.map((r, i) => ({ ...r, _i: i }))} rowKey={(r) => r._i} pageSize={8} caption="Import preview" />
                <div className="flex justify-end">
                  <Button size="lg" loading={commit.isPending} onClick={() => commit.mutate(file)}>
                    <CheckCircle2 /> Confirm import of {data.valid}
                  </Button>
                </div>
              </>
            )}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
