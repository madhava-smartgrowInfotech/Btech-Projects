import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  DndContext, DragOverlay, PointerSensor, TouchSensor, useDraggable, useDroppable, useSensor, useSensors,
  type DragEndEvent, type DragOverEvent, type DragStartEvent,
} from "@dnd-kit/core";
import { motion } from "motion/react";
import {
  Accessibility, AlertTriangle, ArrowLeft, Check, CheckCircle2, Download, Hand, Info, Lock, Minus, Plus, Search, X,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState } from "@/components/common/States";
import { PlanStatusBadge } from "@/components/plans/PlanStatusBadge";
import { SeatGrid } from "@/components/seatmap/SeatGrid";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { api, downloadFile, errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { paperColor } from "@/lib/papers";
import type { HallMap, MapSeat, SwapOptions, SwapTarget } from "@/lib/types";
import { cn } from "@/lib/utils";

const SIZES = [40, 48, 58, 68];

function seatStyle(seat: MapSeat): CSSProperties {
  const colour = paperColor(seat.colour);
  return {
    backgroundColor: `color-mix(in srgb, ${colour} 20%, hsl(var(--card)))`,
    borderTopColor: colour,
  };
}

function SeatCell({
  label, seat, accessible, canEdit, active, target, focused, dimmed, flagged, compact, onPick, onHover,
}: {
  label: string;
  seat?: MapSeat;
  accessible: boolean;
  canEdit: boolean;
  active: boolean;
  target?: SwapTarget;
  focused: boolean;
  dimmed: boolean;
  flagged: boolean;
  compact: boolean;
  onPick: (label: string) => void;
  onHover: (label: string | null) => void;
}) {
  const drag = useDraggable({ id: label, disabled: !canEdit || !seat });
  const drop = useDroppable({ id: label, disabled: !canEdit });
  const setRef = (node: HTMLElement | null) => {
    drag.setNodeRef(node);
    drop.setNodeRef(node);
  };
  const describe = seat
    ? `${label}: ${seat.candidate.roll_no} ${seat.candidate.full_name}, ${seat.course_code}${seat.attendance ? `, ${seat.attendance}` : ""}`
    : `${label}: empty${accessible ? ", accessible seat" : ""}`;

  return (
    <button
      ref={setRef}
      type="button"
      {...drag.listeners}
      {...drag.attributes}
      onClick={() => onPick(label)}
      onPointerEnter={() => onHover(label)}
      onPointerLeave={() => onHover(null)}
      onFocus={() => onHover(label)}
      onBlur={() => onHover(null)}
      aria-label={describe}
      aria-pressed={active}
      title={describe}
      style={seat ? seatStyle(seat) : undefined}
      className={cn(
        "relative flex size-[var(--seat)] touch-manipulation select-none flex-col items-start justify-between overflow-hidden rounded-lg p-1 text-left outline-none transition-[opacity,box-shadow,transform] duration-150",
        seat ? "border-t-[3px] shadow-sm" : "border border-dashed bg-transparent",
        canEdit && seat && "cursor-grab active:cursor-grabbing",
        drag.isDragging && "opacity-30",
        dimmed && "opacity-25",
        active && "z-10 scale-105 ring-2 ring-primary ring-offset-2 ring-offset-background",
        target?.ok && "ring-2 ring-success",
        target && !target.ok && "opacity-40 ring-1 ring-destructive/60",
        drop.isOver && target?.ok && "scale-105 ring-4",
        drop.isOver && target && !target.ok && "ring-2 ring-destructive opacity-80",
        focused && "z-10 ring-2 ring-warning ring-offset-2 ring-offset-background",
        flagged && "ring-2 ring-destructive",
        "focus-visible:ring-2 focus-visible:ring-ring",
      )}
    >
      <span className="flex w-full items-center justify-between gap-0.5 text-2xs font-semibold leading-none">
        <span className="truncate text-muted-foreground">{label}</span>
        {accessible && <Accessibility className={cn("size-3 shrink-0", seat?.needs_accessible ? "text-success" : "text-muted-foreground")} aria-hidden />}
      </span>
      {seat && !compact && (
        <span className="w-full truncate font-mono text-[10px] font-medium leading-tight text-foreground">{seat.candidate.roll_no}</span>
      )}
      {seat && (
        <span className="w-full truncate font-mono text-[9px] leading-none text-muted-foreground">{seat.course_code}</span>
      )}
      {seat?.attendance && (
        <span
          className={cn(
            "absolute bottom-0.5 right-0.5 flex size-3 items-center justify-center rounded-full text-white",
            seat.attendance === "present" ? "bg-success" : "bg-destructive",
          )}
          aria-hidden
        >
          {seat.attendance === "present" ? <Check className="size-2" strokeWidth={4} /> : <X className="size-2" strokeWidth={4} />}
        </span>
      )}
    </button>
  );
}

export default function HallMapPage() {
  const { planId, hallId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [active, setActive] = useState<string | null>(null);
  const [hover, setHover] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [focusPaper, setFocusPaper] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [size, setSize] = useState(() => (window.innerWidth < 640 ? 1 : 2));
  const [dragging, setDragging] = useState<string | null>(null);
  const scroller = useRef<HTMLDivElement>(null);

  const key = ["hallmap", Number(planId), Number(hallId)];
  const map = useQuery({ queryKey: key, queryFn: async () => (await api.get<HallMap>(`/plans/${planId}/halls/${hallId}`)).data });
  const data = map.data;
  const canEdit = Boolean(data?.can_edit);

  const options = useQuery({
    queryKey: ["swapcheck", Number(planId), Number(hallId), active],
    queryFn: async () => (await api.get<SwapOptions>(`/plans/${planId}/halls/${hallId}/swap-check`, { params: { seat: active } })).data,
    enabled: Boolean(active) && canEdit,
    staleTime: 0,
  });
  const targets = useMemo(() => new Map((options.data?.targets ?? []).map((t) => [t.seat, t])), [options.data]);
  const seats = useMemo(() => new Map((data?.seats ?? []).map((s) => [s.label, s])), [data]);
  const accessible = useMemo(() => new Set(data?.hall.accessible ?? []), [data]);
  const flagged = useMemo(() => new Set((data?.violations ?? []).flatMap((v) => v.seats)), [data]);

  const needle = search.trim().toLowerCase();
  const found = useMemo(() => {
    if (!needle || !data) return null;
    return data.seats.find((s) => s.candidate.roll_no.toLowerCase().includes(needle) || s.candidate.full_name.toLowerCase().includes(needle))?.label ?? null;
  }, [needle, data]);

  useEffect(() => {
    if (!found) return;
    document.querySelector(`[aria-label^="${found}:"]`)?.scrollIntoView({ block: "center", inline: "center", behavior: "smooth" });
  }, [found]);

  useEffect(() => {
    setActive(null);
    setSelected(null);
    setFocusPaper(null);
  }, [hallId, planId]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setActive(null);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const swap = useMutation({
    mutationFn: async ({ from, to }: { from: string; to: string }) =>
      (await api.post<{ message: string; notes: string[] }>(`/plans/${planId}/swap`, { hall_id: Number(hallId), from_seat: from, to_seat: to })).data,
    onSuccess: (res, vars) => {
      toast.success(res.message, { description: res.notes[0] });
      setActive(null);
      setSelected(vars.to);
      queryClient.invalidateQueries({ queryKey: key });
      queryClient.invalidateQueries({ queryKey: ["plan", Number(planId)] });
    },
    onError: (err) => toast.error(errorMessage(err)),
  });

  function attempt(from: string, to: string) {
    if (from === to) return;
    const verdict = targets.get(to);
    if (verdict && !verdict.ok) {
      toast.error("That move is not allowed", { description: verdict.reasons[0] });
      return;
    }
    swap.mutate({ from, to });
  }

  function onPick(label: string) {
    setSelected(label);
    if (!canEdit) return;
    if (active === null) {
      if (seats.has(label)) setActive(label);
      return;
    }
    if (active === label) {
      setActive(null);
      return;
    }
    attempt(active, label);
  }

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 180, tolerance: 6 } }),
  );

  function onDragStart(e: DragStartEvent) {
    const label = String(e.active.id);
    setDragging(label);
    setActive(label);
    setSelected(label);
  }
  function onDragOver(e: DragOverEvent) {
    setHover(e.over ? String(e.over.id) : null);
  }
  function onDragEnd(e: DragEndEvent) {
    setDragging(null);
    setHover(null);
    const from = String(e.active.id);
    if (e.over && String(e.over.id) !== from) attempt(from, String(e.over.id));
  }

  if (map.isError) return <ErrorState error={map.error} onRetry={() => map.refetch()} />;

  const seatSize = SIZES[size];
  const inspect = hover ?? selected;
  const inspectSeat = inspect ? seats.get(inspect) : undefined;
  const inspectTarget = active && inspect && inspect !== active ? targets.get(inspect) : undefined;
  const moving = active ? seats.get(active) : undefined;
  const backTo = user?.role === "admin" && data ? `/app/sessions/${data.plan.session.id}?plan=${data.plan.id}` : "/app/attendance";

  return (
    <>
      <Link to={backTo} className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="size-4" /> {user?.role === "admin" ? "Plan" : "My halls"}
      </Link>
      <PageHeader
        title={data ? `${data.hall.code} · ${data.hall.name}` : "Loading..."}
        description={
          data
            ? `${data.plan.session.label} · ${data.plan.session.start_time}-${data.plan.session.end_time} · ${[data.hall.building, data.hall.floor && (/^\d+$/.test(data.hall.floor) ? `floor ${data.hall.floor}` : `${data.hall.floor.toLowerCase()} floor`)].filter(Boolean).join(", ")}`
            : undefined
        }
        actions={
          data && (
            <>
              <PlanStatusBadge status={data.plan.status} version={data.plan.version} />
              {user?.role === "admin" && (
                <Button
                  variant="outline"
                  onClick={() =>
                    downloadFile(`/plans/${data.plan.id}/exports/seating-charts.pdf`, `seating-chart-${data.hall.code}.pdf`, {
                      hall_id: data.hall.id,
                    }).catch((err) => toast.error(errorMessage(err)))
                  }
                >
                  <Download /> Chart PDF
                </Button>
              )}
            </>
          )
        }
      />

      {data && data.halls.length > 1 && (
        <div className="-mt-2 mb-5 flex gap-1.5 overflow-x-auto pb-1 scrollbar-thin">
          {data.halls.map((h) => (
            <Button
              key={h.hall_id}
              size="sm"
              variant={h.hall_id === data.hall.id ? "default" : "outline"}
              onClick={() => navigate(`/app/plans/${planId}/halls/${h.hall_id}`)}
              className="shrink-0 font-mono"
            >
              {h.code} <span className="opacity-70">{h.placed}</span>
            </Button>
          ))}
        </div>
      )}

      {map.isPending && <Skeleton className="h-[480px] w-full rounded-xl" />}

      {data && (
        <div className="grid gap-5 xl:grid-cols-[1fr_20rem]">
          <Card className="min-w-0">
            <CardHeader className="flex-row flex-wrap items-center gap-2 space-y-0 border-b p-3 sm:p-4">
              <div className="flex flex-wrap gap-1.5">
                {data.legend.map((p) => (
                  <button
                    key={p.paper}
                    onClick={() => setFocusPaper((f) => (f === p.paper ? null : p.paper))}
                    aria-pressed={focusPaper === p.paper}
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-md border px-2 py-1 font-mono text-xs transition-colors hover:bg-accent",
                      focusPaper === p.paper && "border-primary bg-primary/10",
                    )}
                    title={p.courses.join(", ")}
                  >
                    <span className="size-2.5 rounded-sm" style={{ background: paperColor(p.colour) }} />
                    {p.paper} <span className="text-muted-foreground">{p.count}</span>
                  </button>
                ))}
              </div>
              <div className="ml-auto flex items-center gap-1">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
                  <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Find a candidate" className="h-8 w-44 pl-8 text-xs" aria-label="Find a candidate" />
                </div>
                <Button size="icon-sm" variant="ghost" aria-label="Smaller seats" disabled={size === 0} onClick={() => setSize((s) => s - 1)}>
                  <Minus />
                </Button>
                <Button size="icon-sm" variant="ghost" aria-label="Larger seats" disabled={size === SIZES.length - 1} onClick={() => setSize((s) => s + 1)}>
                  <Plus />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div ref={scroller} className="overflow-auto p-4 scrollbar-thin sm:p-6">
                <DndContext sensors={sensors} onDragStart={onDragStart} onDragOver={onDragOver} onDragEnd={onDragEnd} onDragCancel={() => setDragging(null)}>
                  <SeatGrid
                    hall={data.hall}
                    seatSize={seatSize}
                    renderSeat={(label) => {
                      const seat = seats.get(label);
                      return (
                        <SeatCell
                          label={label}
                          seat={seat}
                          accessible={accessible.has(label)}
                          canEdit={canEdit}
                          active={active === label}
                          target={active && active !== label ? targets.get(label) : undefined}
                          focused={found === label}
                          dimmed={Boolean(focusPaper && seat?.paper !== focusPaper)}
                          flagged={flagged.has(label)}
                          compact={seatSize < 48}
                          onPick={onPick}
                          onHover={(l) => !dragging && setHover(active ? l : null)}
                        />
                      );
                    }}
                  />
                  <DragOverlay dropAnimation={null}>
                    {dragging && seats.get(dragging) && (
                      <div
                        className="flex size-[var(--seat)] flex-col justify-between rounded-lg border-t-[3px] p-1 shadow-lift"
                        style={{ ...seatStyle(seats.get(dragging)!), ["--seat" as string]: `${seatSize}px` }}
                      >
                        <span className="text-2xs font-semibold">{dragging}</span>
                        <span className="truncate font-mono text-[10px]">{seats.get(dragging)!.candidate.roll_no}</span>
                      </div>
                    )}
                  </DragOverlay>
                </DndContext>
              </div>
            </CardContent>
          </Card>

          <div className="space-y-4">
            <Card>
              <CardContent className="space-y-3 p-4 text-sm">
                {canEdit ? (
                  <div className="flex items-start gap-2 text-muted-foreground">
                    <Hand className="mt-0.5 size-4 shrink-0" />
                    <span>
                      Drag a candidate to another seat, or tap one and then the destination. Green seats keep every rule; point at
                      a red one to see why not. Esc cancels.
                    </span>
                  </div>
                ) : (
                  <div className="flex items-start gap-2 text-muted-foreground">
                    <Lock className="mt-0.5 size-4 shrink-0" />
                    <span>{data.plan.status === "archived" ? "This version was replaced, so it is read-only." : "View only."}</span>
                  </div>
                )}
                {moving && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="rounded-lg border border-primary/40 bg-primary/5 p-3">
                    <div className="text-xs text-muted-foreground">Moving</div>
                    <div className="font-medium">
                      {moving.candidate.full_name} <span className="font-mono text-xs">({moving.candidate.roll_no})</span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {options.isFetching ? "Checking every seat..." : `${[...targets.values()].filter((t) => t.ok).length} seats keep every rule`}
                    </div>
                  </motion.div>
                )}
                {inspectTarget && (
                  <div className={cn("rounded-lg border p-3", inspectTarget.ok ? "border-success/40 bg-success/5" : "border-destructive/40 bg-destructive/5")}>
                    <div className="flex items-center gap-1.5 font-medium">
                      {inspectTarget.ok ? <CheckCircle2 className="size-4 text-success" /> : <XCircle className="size-4 text-destructive" />}
                      {inspect}: {inspectTarget.ok ? (inspectTarget.occupied ? "swap allowed" : "move allowed") : "not allowed"}
                    </div>
                    <ul className="mt-1.5 space-y-1 text-xs text-muted-foreground">
                      {inspectTarget.reasons.map((r) => (
                        <li key={r}>{r}</li>
                      ))}
                      {inspectTarget.ok &&
                        inspectTarget.notes.map((n) => (
                          <li key={n} className="flex gap-1">
                            <Info className="mt-px size-3 shrink-0" /> {n}
                          </li>
                        ))}
                    </ul>
                  </div>
                )}
                {!inspectTarget && inspectSeat && (
                  <div className="rounded-lg bg-muted/60 p-3">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs text-muted-foreground">Seat {inspectSeat.label}</span>
                      {inspectSeat.attendance && (
                        <Badge variant={inspectSeat.attendance === "present" ? "success" : "destructive"}>{inspectSeat.attendance}</Badge>
                      )}
                    </div>
                    <div className="mt-1 font-medium">{inspectSeat.candidate.full_name}</div>
                    <div className="font-mono text-xs">{inspectSeat.candidate.roll_no} · {inspectSeat.candidate.department}</div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      {inspectSeat.course_code} {inspectSeat.course_name}
                      {inspectSeat.paper !== inspectSeat.course_code && ` (shared paper ${inspectSeat.paper})`}
                    </div>
                    {inspectSeat.needs_accessible && (
                      <div className="mt-1 flex items-center gap-1 text-xs text-success">
                        <Accessibility className="size-3.5" /> Needs an accessible seat
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">This hall</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-muted-foreground">Seated</span><span className="tabular">{data.seats.length} / {data.hall.capacity}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Papers</span><span className="tabular">{data.legend.length}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Same-department neighbours</span><span className="tabular">{data.stats.same_department_pairs ?? 0}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Invigilator</span><span>{data.invigilators.map((i) => i.full_name).join(", ") || "Unassigned"}</span></div>
                {(data.attendance.present > 0 || data.attendance.absent > 0) && (
                  <div className="flex justify-between"><span className="text-muted-foreground">Attendance</span><span className="tabular">{data.attendance.present} present · {data.attendance.absent} absent</span></div>
                )}
                {data.violations.length === 0 ? (
                  <div className="flex items-center gap-1.5 pt-1 text-success">
                    <CheckCircle2 className="size-4" /> Every rule is met in this hall
                  </div>
                ) : (
                  <div className="space-y-1 pt-1">
                    {data.violations.map((v, i) => (
                      <div key={i} className="flex items-start gap-1.5 text-xs text-destructive">
                        <AlertTriangle className="mt-0.5 size-3.5 shrink-0" /> {v.seats.join(" & ")}: {v.detail}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </>
  );
}
