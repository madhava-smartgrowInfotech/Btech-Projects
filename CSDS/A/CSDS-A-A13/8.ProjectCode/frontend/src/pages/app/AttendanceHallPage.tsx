import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "motion/react";
import {
  Accessibility, ArrowLeft, Check, CheckCircle2, LayoutGrid, List, Lock, ScanLine, Search, Unlock, UserX, X, XCircle,
} from "lucide-react";
import { toast } from "sonner";
import { CameraScanner } from "@/components/attendance/CameraScanner";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState } from "@/components/common/States";
import { SeatGrid } from "@/components/seatmap/SeatGrid";
import {
  AlertDialog, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { api, errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatDateTime } from "@/lib/format";
import { paperColor } from "@/lib/papers";
import { storage } from "@/lib/storage";
import type { HallMap, MapSeat, ScanResult } from "@/lib/types";
import { cn } from "@/lib/utils";

type Status = "present" | "absent" | null;
type Filter = "all" | "unmarked" | "present" | "absent";
const next: Record<string, Status> = { null: "present", present: "absent", absent: null };

export default function AttendanceHallPage() {
  const { planId, hallId } = useParams();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [view, setView] = useState<"grid" | "list">(() => (storage.get("seatwise.attendance.view") as "grid" | "list") || "list");
  const [filter, setFilter] = useState<Filter>("all");
  const [q, setQ] = useState("");
  const [code, setCode] = useState("");
  const [last, setLast] = useState<{ tone: "ok" | "warn" | "error"; text: string } | null>(null);
  const [confirm, setConfirm] = useState<"absent" | "submit" | null>(null);
  const scanInput = useRef<HTMLInputElement>(null);

  const key = ["hallmap", Number(planId), Number(hallId)];
  const map = useQuery({
    queryKey: key,
    queryFn: async () => (await api.get<HallMap>(`/plans/${planId}/halls/${hallId}`)).data,
    refetchInterval: 5000,
  });
  const data = map.data;
  const base = `/plans/${planId}/halls/${hallId}/attendance`;
  const canMark = Boolean(data?.attendance.can_mark);

  useEffect(() => storage.set("seatwise.attendance.view", view), [view]);

  const counts = useMemo(() => {
    const seats = data?.seats ?? [];
    const present = seats.filter((s) => s.attendance === "present").length;
    const absent = seats.filter((s) => s.attendance === "absent").length;
    return { total: seats.length, present, absent, unmarked: seats.length - present - absent };
  }, [data]);

  const setLocal = useCallback(
    (candidateId: number, status: Status) =>
      queryClient.setQueryData<HallMap>(key, (old) =>
        old ? { ...old, seats: old.seats.map((s) => (s.candidate.id === candidateId ? { ...s, attendance: status } : s)) } : old,
      ),
    [queryClient, planId, hallId], // `key` is derived from planId and hallId
  );

  const mark = useMutation({
    mutationFn: async ({ seat, status }: { seat: MapSeat; status: Status }) =>
      (await api.put(`${base}/${seat.candidate.id}`, { status })).data,
    onMutate: ({ seat, status }) => {
      const previous = seat.attendance;
      setLocal(seat.candidate.id, status);
      return { previous };
    },
    onError: (err, { seat }, ctx) => {
      setLocal(seat.candidate.id, ctx?.previous ?? null);
      toast.error(errorMessage(err));
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: key }),
  });

  const scan = useMutation({
    mutationFn: async (value: string) => (await api.post<ScanResult>(`${base}/scan`, { code: value })).data,
    onSuccess: (res) => {
      setLocal(res.candidate.id, "present");
      setLast({
        tone: res.already_present ? "warn" : "ok",
        text: res.already_present
          ? `${res.candidate.full_name} (${res.candidate.roll_no}) was already marked present - seat ${res.seat}`
          : `${res.candidate.full_name} (${res.candidate.roll_no}) is present - seat ${res.seat}`,
      });
      queryClient.invalidateQueries({ queryKey: key });
    },
    onError: (err) => setLast({ tone: "error", text: errorMessage(err) }),
    onSettled: () => {
      setCode("");
      scanInput.current?.focus();
    },
  });

  const bulk = useMutation({
    mutationFn: async (action: "mark-remaining-absent" | "submit" | "reopen") => (await api.post(`${base}/${action}`)).data,
    onSuccess: (_, action) => {
      toast.success(action === "submit" ? "Attendance submitted" : action === "reopen" ? "Register reopened" : "Remaining candidates marked absent");
      setConfirm(null);
      queryClient.invalidateQueries({ queryKey: key });
      queryClient.invalidateQueries({ queryKey: ["attendance"] });
    },
    onError: (err) => toast.error(errorMessage(err)),
  });

  const handleCode = useCallback((value: string) => {
    if (value.trim()) scan.mutate(value.trim());
  }, [scan]);

  function onScan(event: FormEvent) {
    event.preventDefault();
    handleCode(code);
  }

  if (map.isError) return <ErrorState error={map.error} onRetry={() => map.refetch()} />;

  const needle = q.trim().toLowerCase();
  const visible = (data?.seats ?? []).filter(
    (s) =>
      (filter === "all" || (filter === "unmarked" ? !s.attendance : s.attendance === filter)) &&
      (!needle || s.candidate.roll_no.toLowerCase().includes(needle) || s.candidate.full_name.toLowerCase().includes(needle) || s.label.toLowerCase() === needle),
  );
  const seats = new Map((data?.seats ?? []).map((s) => [s.label, s]));

  return (
    <div className="pb-28">
      <Link to="/app/attendance" className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="size-4" /> {user?.role === "admin" ? "Attendance" : "My halls"}
      </Link>
      <PageHeader
        title={data ? `${data.hall.code} · ${data.hall.name}` : "Loading..."}
        description={data ? `${data.plan.session.label} · ${data.plan.session.start_time}-${data.plan.session.end_time}` : undefined}
      />

      {map.isPending && <Skeleton className="h-96 w-full rounded-xl" />}

      {data && (
        <div className="space-y-4">
          {data.attendance.submitted_at && (
            <div className="flex flex-col gap-3 rounded-xl border border-success/40 bg-success/5 p-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2 text-sm">
                <Lock className="size-4 text-success" /> Submitted {formatDateTime(data.attendance.submitted_at)}. The register is locked.
              </div>
              {user?.role === "admin" && (
                <Button variant="outline" size="sm" loading={bulk.isPending} onClick={() => bulk.mutate("reopen")}>
                  <Unlock /> Reopen
                </Button>
              )}
            </div>
          )}

          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Present", value: counts.present, cls: "text-success" },
              { label: "Absent", value: counts.absent, cls: "text-destructive" },
              { label: "To mark", value: counts.unmarked, cls: "" },
            ].map((k) => (
              <Card key={k.label}>
                <CardContent className="p-4 text-center">
                  <div className={cn("font-display text-3xl font-semibold tabular", k.cls)}>{k.value}</div>
                  <div className="text-xs text-muted-foreground">{k.label} of {counts.total}</div>
                </CardContent>
              </Card>
            ))}
          </div>

          {canMark && (
            <Card>
              <CardContent className="space-y-3 p-4">
                <form onSubmit={onScan} className="flex gap-2">
                  <div className="relative flex-1">
                    <ScanLine className="pointer-events-none absolute left-3 top-1/2 size-5 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      ref={scanInput}
                      autoFocus
                      value={code}
                      onChange={(e) => setCode(e.target.value)}
                      placeholder="Scan a seat slip or type a roll number"
                      className="h-12 pl-11 text-base"
                      aria-label="Scan a seat slip or type a roll number"
                      autoComplete="off"
                    />
                  </div>
                  <Button type="submit" size="lg" loading={scan.isPending} disabled={!code.trim()}>
                    Mark present
                  </Button>
                  <CameraScanner onCode={handleCode} disabled={scan.isPending} />
                </form>
                <AnimatePresence mode="wait">
                  {last && (
                    <motion.div
                      key={last.text}
                      initial={{ opacity: 0, y: -4 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      role="status"
                      className={cn(
                        "flex items-start gap-2 rounded-lg px-3 py-2 text-sm",
                        last.tone === "ok" && "bg-success/10 text-success",
                        last.tone === "warn" && "bg-warning/15 text-warning",
                        last.tone === "error" && "bg-destructive/10 text-destructive",
                      )}
                    >
                      {last.tone === "error" ? <XCircle className="mt-0.5 size-4 shrink-0" /> : <CheckCircle2 className="mt-0.5 size-4 shrink-0" />}
                      {last.text}
                    </motion.div>
                  )}
                </AnimatePresence>
              </CardContent>
            </Card>
          )}

          <div className="flex flex-wrap items-center gap-2">
            <div className="flex rounded-lg border p-0.5">
              {(["all", "unmarked", "present", "absent"] as Filter[]).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={cn("rounded-md px-3 py-1.5 text-sm capitalize", filter === f ? "bg-secondary font-medium" : "text-muted-foreground")}
                >
                  {f === "unmarked" ? "To mark" : f}
                </button>
              ))}
            </div>
            <div className="relative min-w-40 flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Find" className="pl-9" aria-label="Find a candidate" />
            </div>
            <div className="flex rounded-lg border p-0.5">
              <Button size="icon-sm" variant={view === "list" ? "secondary" : "ghost"} onClick={() => setView("list")} aria-label="List view">
                <List />
              </Button>
              <Button size="icon-sm" variant={view === "grid" ? "secondary" : "ghost"} onClick={() => setView("grid")} aria-label="Seat map view">
                <LayoutGrid />
              </Button>
            </div>
          </div>

          {view === "list" ? (
            <Card>
              <CardContent className="divide-y p-0">
                {visible.length === 0 && <p className="p-6 text-center text-sm text-muted-foreground">Nobody matches this filter.</p>}
                {visible.map((s) => (
                  <div key={s.label} className="flex items-center gap-3 px-3 py-2.5 sm:px-4">
                    <span className="w-10 shrink-0 text-center font-mono text-sm font-semibold" style={{ borderLeft: `3px solid ${paperColor(s.colour)}` }}>
                      {s.label}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-1.5 truncate font-medium">
                        {s.candidate.full_name}
                        {s.needs_accessible && <Accessibility className="size-4 shrink-0 text-success" aria-label="Needs an accessible seat" />}
                      </div>
                      <div className="truncate font-mono text-xs text-muted-foreground">
                        {s.candidate.roll_no} · {s.course_code}
                      </div>
                    </div>
                    <div className="flex shrink-0 gap-1.5">
                      <Button
                        size="lg"
                        variant={s.attendance === "present" ? "success" : "outline"}
                        className="h-11 px-3 sm:px-4"
                        disabled={!canMark}
                        aria-pressed={s.attendance === "present"}
                        onClick={() => mark.mutate({ seat: s, status: s.attendance === "present" ? null : "present" })}
                      >
                        <Check /> <span className="hidden sm:inline">Present</span>
                      </Button>
                      <Button
                        size="lg"
                        variant={s.attendance === "absent" ? "destructive" : "outline"}
                        className="h-11 px-3 sm:px-4"
                        disabled={!canMark}
                        aria-pressed={s.attendance === "absent"}
                        onClick={() => mark.mutate({ seat: s, status: s.attendance === "absent" ? null : "absent" })}
                      >
                        <X /> <span className="hidden sm:inline">Absent</span>
                      </Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="overflow-auto p-4 scrollbar-thin">
                <p className="mb-3 text-xs text-muted-foreground">Tap a seat: present, then absent, then clear.</p>
                <SeatGrid
                  hall={data.hall}
                  seatSize={60}
                  renderSeat={(label) => {
                    const s = seats.get(label);
                    if (!s) return <span className="block size-[var(--seat)] rounded-lg border border-dashed" aria-label={`${label} empty`} />;
                    const hidden = !visible.includes(s);
                    return (
                      <button
                        type="button"
                        disabled={!canMark}
                        onClick={() => mark.mutate({ seat: s, status: next[String(s.attendance)] })}
                        aria-label={`${label}: ${s.candidate.roll_no} ${s.candidate.full_name}, ${s.attendance ?? "not marked"}`}
                        className={cn(
                          "flex size-[var(--seat)] touch-manipulation flex-col justify-between rounded-lg border-t-[3px] p-1 text-left transition-colors",
                          s.attendance === "present" && "bg-success text-success-foreground",
                          s.attendance === "absent" && "bg-destructive text-destructive-foreground",
                          !s.attendance && "bg-card shadow-sm ring-1 ring-border",
                          hidden && "opacity-25",
                        )}
                        style={{ borderTopColor: paperColor(s.colour) }}
                      >
                        <span className="flex items-center justify-between text-2xs font-semibold">
                          {label}
                          {s.attendance === "present" ? <Check className="size-3" /> : s.attendance === "absent" ? <UserX className="size-3" /> : null}
                        </span>
                        <span className="truncate font-mono text-[10px]">{s.candidate.roll_no}</span>
                      </button>
                    );
                  }}
                />
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {data && canMark && (
        <div className="fixed inset-x-0 bottom-0 z-20 border-t bg-background/90 p-3 backdrop-blur lg:left-64">
          <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-1 sm:px-4">
            <div className="text-sm tabular text-muted-foreground">
              <span className="font-semibold text-foreground">{counts.present + counts.absent}</span> of {counts.total} marked
            </div>
            <div className="flex gap-2">
              <Button variant="outline" disabled={counts.unmarked === 0} onClick={() => setConfirm("absent")}>
                <UserX /> <span className="hidden sm:inline">Mark remaining absent</span><span className="sm:hidden">Rest absent</span>
              </Button>
              <Button disabled={counts.unmarked > 0} onClick={() => setConfirm("submit")}>
                <Lock /> Submit
              </Button>
            </div>
          </div>
        </div>
      )}

      <AlertDialog open={confirm !== null} onOpenChange={(o) => !o && setConfirm(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirm === "submit" ? "Submit the register?" : `Mark ${counts.unmarked} candidates absent?`}</AlertDialogTitle>
            <AlertDialogDescription>
              {confirm === "submit"
                ? `${counts.present} present and ${counts.absent} absent. Once submitted the register is locked; only an administrator can reopen it.`
                : "Everyone not marked yet is recorded as absent. You can still change individual marks before submitting."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <Button
              variant={confirm === "submit" ? "default" : "destructive"}
              loading={bulk.isPending}
              onClick={() => bulk.mutate(confirm === "submit" ? "submit" : "mark-remaining-absent")}
            >
              {confirm === "submit" ? "Submit" : "Mark absent"}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
