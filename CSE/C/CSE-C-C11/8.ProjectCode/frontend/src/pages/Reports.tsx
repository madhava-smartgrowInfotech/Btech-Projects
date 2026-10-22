import { CalendarDays, Download, FileSpreadsheet, FileText, FileType2 } from "lucide-react";
import { useState } from "react";

import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { FormField, Input } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { Select } from "@/components/ui/Select";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage } from "@/lib/api";
import { MONTHS } from "@/lib/format";

type Kind = "pdf" | "excel" | "csv";

const KINDS: { kind: Kind; title: string; text: string; icon: typeof FileText; label: string }[] = [
  { kind: "pdf", title: "PDF report", text: "A printable monthly summary: income, expenses, savings, category breakdown, budgets, health score, investments and observations.", icon: FileText, label: "Generate PDF" },
  { kind: "excel", title: "Excel workbook", text: "The same summary plus every transaction, budget and holding on separate sheets, ready for your own analysis.", icon: FileSpreadsheet, label: "Generate Excel" },
  { kind: "csv", title: "Transactions CSV", text: "Every transaction you have recorded, as a plain CSV file you can open anywhere. Not limited to the month above.", icon: FileType2, label: "Export CSV" },
];

/** The API returns JSON errors even for file endpoints; read them out of the blob. */
async function blobError(e: unknown): Promise<string> {
  const data = (e as { response?: { data?: unknown } })?.response?.data;
  if (data instanceof Blob) {
    try {
      const detail = JSON.parse(await data.text())?.detail;
      if (typeof detail === "string") return detail;
    } catch {
      /* fall through */
    }
  }
  return errorMessage(e);
}

export default function Reports() {
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [busy, setBusy] = useState<Kind | null>(null);
  const yearOk = year >= 2000 && year <= 2100;

  async function download(kind: Kind) {
    setBusy(kind);
    try {
      const res = await api.get<Blob>(`/reports/${kind}`, { params: { month, year }, responseType: "blob" });
      const disposition = String(res.headers["content-disposition"] ?? "");
      const name = /filename="?([^";]+)"?/i.exec(disposition)?.[1] ?? `finjarvis_${kind}`;
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast.success(`${name} downloaded`);
    } catch (e) {
      toast.error(`Could not generate the ${kind.toUpperCase()} report`, { description: await blobError(e) });
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <PageHeader title="Financial reports" description="Download your month as a PDF or Excel workbook, or export every transaction as CSV." />
      <Card className="mb-6">
        <CardBody className="flex flex-wrap items-end gap-4">
          <FormField label="Month">
            {(p) => <Select {...p} icon={<CalendarDays />} value={String(month)} onValueChange={(v) => setMonth(Number(v))} options={MONTHS.map((m, i) => ({ value: String(i + 1), label: m }))} className="w-48" />}
          </FormField>
          <FormField label="Year" error={yearOk ? undefined : "Enter a year between 2000 and 2100."}>
            {(p) => <Input {...p} type="number" min={2000} max={2100} value={year} onChange={(e) => setYear(Number(e.target.value))} wrapperClassName="w-32" />}
          </FormField>
        </CardBody>
      </Card>
      <Stagger className="grid gap-4 md:grid-cols-3">
        {KINDS.map(({ kind, title, text, icon: Icon, label }) => (
          <StaggerItem key={kind}>
            <Card className="flex h-full flex-col gap-4 p-6">
              <span className="grid size-11 place-items-center rounded-2xl bg-grad-primary text-white shadow-[0_10px_30px_-10px_rgba(124,92,255,0.8)]">
                <Icon className="size-5" />
              </span>
              <div className="space-y-1.5">
                <h2 className="font-display text-lg font-semibold">{title}</h2>
                <p className="text-sm text-muted-foreground">{text}</p>
              </div>
              <Button className="mt-auto w-full" variant={kind === "pdf" ? "primary" : "secondary"} loading={busy === kind} disabled={busy !== null || (kind !== "csv" && !yearOk)} onClick={() => void download(kind)}>
                <Download /> {label}
              </Button>
            </Card>
          </StaggerItem>
        ))}
      </Stagger>
    </>
  );
}
