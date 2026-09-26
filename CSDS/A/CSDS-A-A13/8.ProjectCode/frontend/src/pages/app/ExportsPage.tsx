import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import { ClipboardList, FileSpreadsheet, FileText, Grid3x3, QrCode, UserCheck } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { CardsSkeleton, EmptyState, ErrorState } from "@/components/common/States";
import { PlanStatusBadge } from "@/components/plans/PlanStatusBadge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { downloadFile, errorMessage, api } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import type { PlanDetail, PlanSummary } from "@/lib/types";

interface ExportKind {
  file: string;
  title: string;
  description: string;
  icon: LucideIcon;
  format: "PDF" | "Excel";
}

const EXPORTS: ExportKind[] = [
  { file: "seating-charts.pdf", title: "Seating charts", icon: Grid3x3, format: "PDF",
    description: "One landscape page per hall: the seat grid, colour-coded by paper, with roll numbers and a legend. Post it at the door." },
  { file: "hall-lists.xlsx", title: "Hall-wise lists", icon: FileSpreadsheet, format: "Excel",
    description: "A sheet per hall (seat, roll number, name, course) plus a summary and a roll-order door list." },
  { file: "invigilator-sheets.pdf", title: "Invigilator sheets", icon: ClipboardList, format: "PDF",
    description: "Instructions, paper counts and a seat-by-seat list with present and signature columns." },
  { file: "qr-slips.pdf", title: "Seat slips with QR codes", icon: QrCode, format: "PDF",
    description: "Six slips per page. Each QR code opens the candidate's seat in the public lookup." },
  { file: "attendance.xlsx", title: "Attendance report", icon: UserCheck, format: "Excel",
    description: "Present, absent and not-marked counts per hall and course, with who marked each candidate and when." },
];

export default function ExportsPage() {
  const [params, setParams] = useSearchParams();
  const plans = useQuery({ queryKey: ["plans", "all"], queryFn: async () => (await api.get<PlanSummary[]>("/plans")).data });
  const usable = (plans.data ?? []).filter((p) => p.status !== "archived");
  const planId = Number(params.get("plan")) || usable.find((p) => p.status === "published")?.id || usable[0]?.id;
  const [hallId, setHallId] = useState("all");
  const [busy, setBusy] = useState<string | null>(null);

  const detail = useQuery({
    queryKey: ["plan", planId],
    queryFn: async () => (await api.get<PlanDetail>(`/plans/${planId}`)).data,
    enabled: Boolean(planId),
  });

  useEffect(() => setHallId("all"), [planId]);

  async function download(kind: ExportKind) {
    if (!planId) return;
    setBusy(kind.file);
    try {
      const name = await downloadFile(`/plans/${planId}/exports/${kind.file}`, kind.file, hallId === "all" ? undefined : { hall_id: hallId });
      toast.success(`Downloaded ${name}`);
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <PageHeader title="Exports" description="Printable charts, lists, invigilator sheets, QR seat slips and attendance reports." />
      {plans.isPending && <CardsSkeleton count={3} />}
      {plans.isError && <ErrorState error={plans.error} onRetry={() => plans.refetch()} />}
      {plans.data && usable.length === 0 && (
        <EmptyState
          icon={FileText}
          title="No plans to export yet"
          description="Generate a seating plan for a sitting first."
          action={
            <Button asChild>
              <Link to="/app/sessions">Go to sittings</Link>
            </Button>
          }
        />
      )}
      {usable.length > 0 && (
        <div className="space-y-6">
          <Card>
            <CardContent className="grid gap-4 p-5 md:grid-cols-[1fr_16rem]">
              <div className="min-w-0 space-y-2">
                <Label>Plan</Label>
                <Select value={planId ? String(planId) : undefined} onValueChange={(v) => setParams({ plan: v }, { replace: true })}>
                  <SelectTrigger aria-label="Plan">
                    <SelectValue placeholder="Choose a plan" />
                  </SelectTrigger>
                  <SelectContent>
                    {usable.map((p) => (
                      <SelectItem key={p.id} value={String(p.id)}>
                        {p.session.label} · v{p.version} ({p.status})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="min-w-0 space-y-2">
                <Label>Halls</Label>
                <Select value={hallId} onValueChange={setHallId} disabled={!detail.data}>
                  <SelectTrigger aria-label="Halls">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All halls</SelectItem>
                    {detail.data?.halls.map((h) => (
                      <SelectItem key={h.hall_id} value={String(h.hall_id)}>
                        {h.code} · {h.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {detail.data && (
                <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground md:col-span-2">
                  <PlanStatusBadge status={detail.data.status} version={detail.data.version} />
                  {formatNumber(detail.data.candidates)} candidates in {detail.data.halls_used} halls · seed {detail.data.seed}
                  {detail.data.status === "draft" && " · this version is not published yet"}
                </div>
              )}
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {EXPORTS.map((kind, i) => (
              <motion.div
                key={kind.file}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                whileHover={{ y: -2 }}
              >
                <Card className="flex h-full flex-col">
                  <CardHeader>
                    <div className="mb-2 flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                      <kind.icon className="size-5" />
                    </div>
                    <CardTitle>{kind.title}</CardTitle>
                    <CardDescription>{kind.description}</CardDescription>
                  </CardHeader>
                  <CardContent className="mt-auto">
                    <Button className="w-full" variant="outline" loading={busy === kind.file} disabled={!planId || busy !== null} onClick={() => download(kind)}>
                      Download {kind.format}
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
