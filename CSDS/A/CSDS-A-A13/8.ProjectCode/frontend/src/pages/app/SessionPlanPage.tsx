import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "motion/react";
import {
  Accessibility, AlertTriangle, ArrowLeft, CheckCircle2, ChevronDown, Copy, Dices, Download, FileSearch, Fingerprint,
  Globe, Grid3x3, Hash, Plus, ShieldCheck, Sparkles, Timer, Trash2, XCircle,
} from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { CardsSkeleton, ErrorState } from "@/components/common/States";
import { GenerationProgress } from "@/components/plans/GenerationProgress";
import { PlanStatusBadge } from "@/components/plans/PlanStatusBadge";
import { RulesFields } from "@/components/rules/RulesFields";
import {
  AlertDialog, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api, errorDetails, errorMessage } from "@/lib/api";
import { formatDate, formatDuration, formatNumber, formatPercent, timeAgo } from "@/lib/format";
import { paperColor } from "@/lib/papers";
import type { ExamSession, Hall, PlanDetail, PlanSummary, Rules, User, VerifyResult } from "@/lib/types";
import { cn } from "@/lib/utils";

// ------------------------------------------------------------------ generate

function rulesSummary(r: Rules) {
  return [
    `${r.adjacency} neighbours`,
    r.roll_gap ? `roll gap ${r.roll_gap}` : "no roll gap",
    r.department_mix ? "department mix on" : "department mix off",
    r.fill_strategy === "compact" ? "fewest halls" : "balanced fill",
  ].join(" · ");
}

function GeneratePanel({ session, onDone }: { session: ExamSession; onDone: (plan: PlanDetail) => void }) {
  const queryClient = useQueryClient();
  const defaults = useQuery({ queryKey: ["rules"], queryFn: async () => (await api.get<Rules>("/settings/rules")).data });
  const halls = useQuery({ queryKey: ["halls"], queryFn: async () => (await api.get<Hall[]>("/halls")).data });
  const [rules, setRules] = useState<Rules | null>(null);
  const [showRules, setShowRules] = useState(false);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [seedMode, setSeedMode] = useState<"random" | "fixed">("random");
  const [seed, setSeed] = useState("");
  const [failure, setFailure] = useState<{ message: string; reasons: string[] } | null>(null);

  useEffect(() => {
    if (defaults.data && !rules) setRules(defaults.data);
  }, [defaults.data, rules]);
  useEffect(() => {
    if (halls.data) setSelected(new Set(halls.data.filter((h) => h.is_active).map((h) => h.id)));
  }, [halls.data]);

  const seats = useMemo(() => (halls.data ?? []).filter((h) => selected.has(h.id)).reduce((n, h) => n + h.capacity, 0), [halls.data, selected]);
  const enough = seats >= session.candidates;

  const generate = useMutation({
    mutationFn: async () =>
      (await api.post<PlanDetail>(`/sessions/${session.id}/plans`, {
        rules,
        hall_ids: [...selected],
        seed: seedMode === "fixed" && seed ? Number(seed) : null,
      })).data,
    onMutate: () => setFailure(null),
    onSuccess: (plan) => {
      toast.success(`Version ${plan.version} ready in ${formatDuration(plan.solve_ms)} - ${plan.same_paper_pairs} same-paper neighbours`);
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      queryClient.invalidateQueries({ queryKey: ["plans"] });
      onDone(plan);
    },
    onError: (err) => setFailure({ message: errorMessage(err), reasons: errorDetails<string[]>(err) ?? [] }),
  });

  if (defaults.isPending || halls.isPending || !rules) return <CardsSkeleton count={2} className="sm:grid-cols-1 xl:grid-cols-1" />;
  if (defaults.isError || halls.isError) return <ErrorState error={defaults.error ?? halls.error} />;

  const seedValid = seedMode === "random" || (/^\d+$/.test(seed) && Number(seed) >= 1 && Number(seed) < 2 ** 31);

  return (
    <div className="space-y-5">
      {generate.isPending ? (
        <GenerationProgress candidates={session.candidates} />
      ) : (
        <>
          <section>
            <div className="flex items-center justify-between gap-2">
              <div>
                <div className="text-sm font-semibold">Rules</div>
                <div className="text-xs text-muted-foreground">{rulesSummary(rules)}</div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setShowRules((v) => !v)} aria-expanded={showRules}>
                {showRules ? "Hide" : "Change"} <ChevronDown className={cn("transition-transform", showRules && "rotate-180")} />
              </Button>
            </div>
            <AnimatePresence initial={false}>
              {showRules && (
                <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                  <div className="pt-4">
                    <RulesFields value={rules} onChange={setRules} />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </section>

          <section>
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
              <div>
                <div className="text-sm font-semibold">Halls</div>
                <div className={cn("text-xs", enough ? "text-muted-foreground" : "text-destructive")}>
                  {selected.size} selected · {formatNumber(seats)} seats for {formatNumber(session.candidates)} candidates
                  {!enough && " - not enough seats"}
                </div>
              </div>
              <div className="flex gap-1">
                <Button variant="ghost" size="sm" onClick={() => setSelected(new Set(halls.data!.map((h) => h.id)))}>
                  All
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setSelected(new Set())}>
                  None
                </Button>
              </div>
            </div>
            <div className="grid max-h-64 gap-1.5 overflow-y-auto rounded-lg border p-2 scrollbar-thin sm:grid-cols-2">
              {halls.data!.map((h) => (
                <label key={h.id} className="flex cursor-pointer items-center gap-2.5 rounded-md px-2 py-1.5 text-sm hover:bg-accent">
                  <Checkbox
                    checked={selected.has(h.id)}
                    onCheckedChange={(v) =>
                      setSelected((prev) => {
                        const next = new Set(prev);
                        if (v) next.add(h.id);
                        else next.delete(h.id);
                        return next;
                      })
                    }
                  />
                  <span className="min-w-0 flex-1 truncate">
                    <span className="font-mono text-xs">{h.code}</span> <span className="text-muted-foreground">{h.name}</span>
                  </span>
                  <span className="text-xs tabular text-muted-foreground">{h.capacity}</span>
                </label>
              ))}
            </div>
            <p className="mt-1.5 text-xs text-muted-foreground">
              {rules.fill_strategy === "compact" ? "The engine uses as few of these halls as it can." : "Every selected hall is used and filled evenly."}
            </p>
          </section>

          <section>
            <div className="mb-2 text-sm font-semibold">Random seed</div>
            <RadioGroup value={seedMode} onValueChange={(v) => setSeedMode(v as "random" | "fixed")} className="gap-2">
              <Label htmlFor="seed-random" className="flex cursor-pointer items-center gap-2.5 font-normal">
                <RadioGroupItem value="random" id="seed-random" /> Draw a new random seed
              </Label>
              <div className="flex flex-wrap items-center gap-2.5">
                <Label htmlFor="seed-fixed" className="flex cursor-pointer items-center gap-2.5 font-normal">
                  <RadioGroupItem value="fixed" id="seed-fixed" /> Use this seed
                </Label>
                <Input
                  value={seed}
                  onChange={(e) => {
                    setSeed(e.target.value.replace(/\D/g, ""));
                    setSeedMode("fixed");
                  }}
                  inputMode="numeric"
                  placeholder="e.g. drawn in front of witnesses"
                  className="h-9 w-64 max-w-full"
                  aria-label="Seed"
                />
              </div>
            </RadioGroup>
            <p className="mt-1.5 text-xs text-muted-foreground">The seed is stored with the plan, so anyone can reproduce it exactly.</p>
          </section>

          {failure && (
            <div role="alert" className="rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm">
              <div className="flex items-center gap-2 font-medium text-destructive">
                <XCircle className="size-4" /> No plan could be made
              </div>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-muted-foreground">
                {(failure.reasons.length ? failure.reasons : [failure.message]).map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            </div>
          )}

          <Button size="lg" className="w-full" disabled={!selected.size || !seedValid || !session.candidates} onClick={() => generate.mutate()}>
            <Sparkles /> Generate plan
          </Button>
        </>
      )}
    </div>
  );
}

// ------------------------------------------------------------------ plan detail

function Kpi({ icon: Icon, label, value, good, hint }: {
  icon: typeof ShieldCheck;
  label: string;
  value: string;
  good?: boolean;
  hint?: string;
}) {
  return (
    <div className="rounded-xl border bg-card p-4">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        {label}
        <Icon className={cn("size-4", good === true && "text-success", good === false && "text-destructive")} aria-hidden />
      </div>
      <div className="mt-1.5 font-display text-2xl font-semibold">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-muted-foreground">{hint}</div>}
    </div>
  );
}

function InvigilatorPicker({ plan, hall, staff }: { plan: PlanDetail; hall: PlanDetail["halls"][number]; staff: User[] }) {
  const queryClient = useQueryClient();
  const update = useMutation({
    mutationFn: async (userId: string) =>
      (await api.put<PlanDetail>(`/plans/${plan.id}/invigilators`, {
        assignments: [{ hall_id: hall.hall_id, user_ids: userId === "none" ? [] : [Number(userId)] }],
      })).data,
    onSuccess: (data) => {
      queryClient.setQueryData(["plan", plan.id], data);
      toast.success(`Invigilator for ${hall.code} updated`);
    },
    onError: (err) => toast.error(errorMessage(err)),
  });
  const current = hall.invigilators[0]?.id;
  const busy = new Set(plan.halls.filter((h) => h.hall_id !== hall.hall_id).flatMap((h) => h.invigilators.map((i) => i.id)));
  return (
    <Select value={current ? String(current) : "none"} onValueChange={(v) => update.mutate(v)} disabled={plan.status === "archived" || update.isPending}>
      <SelectTrigger className="h-8 w-44 text-xs" aria-label={`Invigilator for ${hall.code}`}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="none">Unassigned</SelectItem>
        {staff.map((u) => (
          <SelectItem key={u.id} value={String(u.id)} disabled={busy.has(u.id)}>
            {u.full_name}
            {busy.has(u.id) ? " (other hall)" : ""}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function PlanDetailView({ planId, onDeleted }: { planId: number; onDeleted: () => void }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const plan = useQuery({ queryKey: ["plan", planId], queryFn: async () => (await api.get<PlanDetail>(`/plans/${planId}`)).data });
  const users = useQuery({ queryKey: ["users"], queryFn: async () => (await api.get<User[]>("/users")).data });
  const staff = (users.data ?? []).filter((u) => u.role === "invigilator" && u.status === "active");
  const [confirm, setConfirm] = useState<"publish" | "delete" | null>(null);
  const [verdict, setVerdict] = useState<VerifyResult | null>(null);

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["plan"] });
    queryClient.invalidateQueries({ queryKey: ["plans"] });
    queryClient.invalidateQueries({ queryKey: ["sessions"] });
  };
  const publish = useMutation({
    mutationFn: async () => (await api.post<PlanDetail>(`/plans/${planId}/publish`)).data,
    onSuccess: (p) => {
      toast.success(`Version ${p.version} is published. Candidates can now look up their seats.`);
      setConfirm(null);
      refresh();
    },
    onError: (err) => toast.error(errorMessage(err)),
  });
  const verify = useMutation({
    mutationFn: async () => (await api.post<VerifyResult>(`/plans/${planId}/verify`)).data,
    onSuccess: setVerdict,
    onError: (err) => toast.error(errorMessage(err)),
  });
  const remove = useMutation({
    mutationFn: async () => api.delete(`/plans/${planId}`),
    onSuccess: () => {
      toast.success("Plan deleted");
      setConfirm(null);
      refresh();
      onDeleted();
    },
    onError: (err) => toast.error(errorMessage(err)),
  });

  if (plan.isPending) return <CardsSkeleton count={4} />;
  if (plan.isError) return <ErrorState error={plan.error} onRetry={() => plan.refetch()} />;
  const p = plan.data;
  const card = p.scorecard;
  const firstHall = p.halls[0];

  return (
    <motion.div key={p.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
      <Card>
        <CardContent className="flex flex-col gap-4 p-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="font-display text-xl font-semibold">Version {p.version}</h2>
              <PlanStatusBadge status={p.status} />
              {p.swaps > 0 && <Badge variant="outline">{p.swaps} manual move{p.swaps === 1 ? "" : "s"}</Badge>}
            </div>
            <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
              <button
                className="inline-flex items-center gap-1 font-mono hover:text-foreground"
                onClick={() => {
                  void navigator.clipboard?.writeText(String(p.seed));
                  toast.success("Seed copied");
                }}
                title="Copy seed"
              >
                <Dices className="size-3.5" /> seed {p.seed} <Copy className="size-3" />
              </button>
              <span>
                {p.created_by ?? "Unknown"} · {timeAgo(p.created_at)}
              </span>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {firstHall && (
              <Button onClick={() => navigate(`/app/plans/${p.id}/halls/${firstHall.hall_id}`)}>
                <Grid3x3 /> Seat maps
              </Button>
            )}
            {p.status === "draft" && (
              <Button variant="success" onClick={() => setConfirm("publish")}>
                <Globe /> Publish
              </Button>
            )}
            <Button variant="outline" loading={verify.isPending} onClick={() => verify.mutate()}>
              <FileSearch /> Verify
            </Button>
            <Button asChild variant="outline">
              <Link to={`/app/exports?plan=${p.id}`}>
                <Download /> Exports
              </Link>
            </Button>
            {p.status !== "published" && (
              <Button variant="ghost" size="icon" aria-label="Delete this version" onClick={() => setConfirm("delete")}>
                <Trash2 />
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {!card.hard_ok && (
        <div role="alert" className="flex items-start gap-3 rounded-xl border border-destructive/40 bg-destructive/5 p-4 text-sm">
          <AlertTriangle className="mt-0.5 size-5 shrink-0 text-destructive" />
          <div>
            <div className="font-medium">This plan no longer meets every rule</div>
            <div className="text-muted-foreground">
              {card.unplaced > 0
                ? `${card.unplaced} registered candidates have no seat - the data changed after the plan was made. Generate a new version.`
                : "Open the seat maps to see the highlighted seats."}
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <Kpi icon={ShieldCheck} label="Same-paper neighbours" value={formatNumber(card.same_paper_pairs)} good={card.same_paper_pairs === 0}
          hint={`${p.rules.adjacency}-seat neighbourhood, checked independently`} />
        <Kpi icon={Hash} label="Roll-gap violations" value={formatNumber(card.roll_gap_violations)} good={card.roll_gap_violations === 0}
          hint={p.rules.roll_gap ? `neighbours at least ${p.rules.roll_gap} roll numbers apart` : "rule switched off"} />
        <Kpi icon={Sparkles} label="Conflicts avoided" value={formatNumber(p.conflicts_avoided ?? 0)} good
          hint={`same-paper neighbours roll-order seating would create`} />
        <Kpi icon={Accessibility} label="Accessible seating" value={card.accessible_violations === 0 ? "All honoured" : `${card.accessible_violations} missed`}
          good={card.accessible_violations === 0} hint="everyone who needs an accessible seat has one" />
        <Kpi icon={Timer} label="Solve time" value={formatDuration(p.solve_ms)}
          hint={`${formatNumber(card.placed)} candidates · ${p.stats.attempts ?? 1} attempt${(p.stats.attempts ?? 1) === 1 ? "" : "s"}`} />
        <Kpi icon={Grid3x3} label="Halls used" value={`${card.halls_used}`}
          hint={`${formatPercent(card.utilisation)} of their seats filled · ${formatNumber(card.same_department_pairs)} same-department neighbour pairs`} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Halls</CardTitle>
          <CardDescription>Open a hall to see its seat map, move candidates or print its chart.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Hall</TableHead>
                <TableHead className="w-40">Seats used</TableHead>
                <TableHead className="hidden lg:table-cell">Papers</TableHead>
                <TableHead className="hidden md:table-cell">Invigilator</TableHead>
                <TableHead className="w-24" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {p.halls.map((h) => (
                <TableRow key={h.hall_id}>
                  <TableCell>
                    <div className="font-mono text-xs font-medium">{h.code}</div>
                    <div className="text-xs text-muted-foreground">{h.name}</div>
                  </TableCell>
                  <TableCell>
                    <div className="text-xs tabular">{h.placed} / {h.capacity}</div>
                    <Progress value={h.utilisation * 100} className="mt-1 h-1.5" />
                  </TableCell>
                  <TableCell className="hidden lg:table-cell">
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(h.papers).map(([paper, n], i) => (
                        <span key={paper} className="inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 font-mono text-2xs">
                          <span className="size-2 rounded-sm" style={{ background: paperColor(i) }} />
                          {paper} · {n}
                        </span>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell className="hidden md:table-cell">
                    <InvigilatorPicker plan={p} hall={h} staff={staff} />
                  </TableCell>
                  <TableCell>
                    <Button asChild variant="ghost" size="sm">
                      <Link to={`/app/plans/${p.id}/halls/${h.hall_id}`}>Open</Link>
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Fingerprint className="size-4" /> Audit fingerprints
          </CardTitle>
          <CardDescription>
            The inputs and result are hashed when the plan is made. Verify re-runs the engine with the same seed and compares.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 text-xs sm:grid-cols-2">
          {[
            ["Input data", p.data_fingerprint],
            ["Engine result", p.solver_hash],
            ["Current seating", p.assignment_hash],
            ["Engine", `v${p.engine_version} · ${p.stats.hall_budget ?? "-"} per-hall budget`],
          ].map(([label, value]) => (
            <div key={label} className="min-w-0 rounded-lg bg-muted/60 p-3">
              <div className="text-muted-foreground">{label}</div>
              <div className="truncate font-mono" title={value}>{value}</div>
            </div>
          ))}
        </CardContent>
      </Card>

      <AlertDialog open={confirm === "publish"} onOpenChange={(o) => !o && setConfirm(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Publish version {p.version}?</AlertDialogTitle>
            <AlertDialogDescription>
              Candidates will see these seats in the public lookup and invigilators will see their halls. Any previously published
              version of this sitting is replaced.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <Button variant="success" loading={publish.isPending} onClick={() => publish.mutate()}>
              Publish
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={confirm === "delete"} onOpenChange={(o) => !o && setConfirm(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete version {p.version}?</AlertDialogTitle>
            <AlertDialogDescription>The seating and its invigilator list are removed. The audit trail keeps a record.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <Button variant="destructive" loading={remove.isPending} onClick={() => remove.mutate()}>
              Delete
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Dialog open={verdict !== null} onOpenChange={(o) => !o && setVerdict(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {verdict?.reproduced ? <CheckCircle2 className="size-5 text-success" /> : <XCircle className="size-5 text-destructive" />}
              {verdict?.reproduced ? "Reproduced exactly" : "Could not reproduce"}
            </DialogTitle>
            <DialogDescription>
              {verdict?.reproduced
                ? `Running the engine again with seed ${verdict.seed} on the same data gave an identical seating${verdict.solve_ms ? ` (${formatDuration(verdict.solve_ms)})` : ""}.`
                : verdict && !verdict.data_unchanged
                  ? "The candidates, halls or rules changed after this plan was made, so the same seed now gives a different result."
                  : "The engine returned a different seating. Check that this copy of SeatWise runs the same engine version."}
            </DialogDescription>
          </DialogHeader>
          {verdict && (
            <div className="space-y-2 text-xs">
              <div className="rounded-lg bg-muted/60 p-3">
                <div className="text-muted-foreground">Stored engine result</div>
                <div className="break-all font-mono">{verdict.stored_solver_hash}</div>
              </div>
              <div className="rounded-lg bg-muted/60 p-3">
                <div className="text-muted-foreground">Recomputed now</div>
                <div className="break-all font-mono">{verdict.recomputed_hash ?? "not recomputed"}</div>
              </div>
              {verdict.manual_moves > 0 && (
                <p className="text-muted-foreground">
                  {verdict.manual_moves} manual move{verdict.manual_moves === 1 ? " was" : "s were"} made after generation; each is listed in the audit trail.
                </p>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" asChild>
              <Link to={`/app/audit?plan=${p.id}`}>Open audit trail</Link>
            </Button>
            <Button onClick={() => setVerdict(null)}>Done</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}

// ------------------------------------------------------------------ page

export default function SessionPlanPage() {
  const { sessionId } = useParams();
  const [params, setParams] = useSearchParams();
  const [generating, setGenerating] = useState(false);
  const session = useQuery({
    queryKey: ["sessions", Number(sessionId)],
    queryFn: async () => (await api.get<ExamSession>(`/sessions/${sessionId}`)).data,
  });
  const plans = useQuery({
    queryKey: ["plans", "session", Number(sessionId)],
    queryFn: async () => (await api.get<PlanSummary[]>(`/sessions/${sessionId}/plans`)).data,
  });

  const list = plans.data ?? [];
  const requested = Number(params.get("plan"));
  const selected =
    list.find((p) => p.id === requested) ?? list.find((p) => p.status === "published") ?? list.find((p) => p.status === "draft") ?? list[0];
  const select = (id: number) => setParams({ plan: String(id) }, { replace: true });

  if (session.isError) return <ErrorState error={session.error} onRetry={() => session.refetch()} />;
  const s = session.data;

  return (
    <>
      <Link to="/app/sessions" className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="size-4" /> Sittings
      </Link>
      <PageHeader
        title={s ? s.label : "Loading..."}
        description={
          s ? `${formatDate(s.date)} · ${s.start_time}-${s.end_time} · ${formatNumber(s.candidates)} candidates in ${s.papers.length} papers` : undefined
        }
        actions={
          list.length > 0 && (
            <Button onClick={() => setGenerating(true)}>
              <Plus /> New version
            </Button>
          )
        }
      />
      {s && (
        <div className="-mt-3 mb-6 flex flex-wrap gap-1.5">
          {s.papers.map((p) => (
            <Badge key={p.course_code} variant="secondary" className="font-mono" title={p.course_name}>
              {p.course_code} · {p.candidates}
              {p.paper_group && <span className="ml-1 text-muted-foreground">({p.paper_group})</span>}
            </Badge>
          ))}
        </div>
      )}

      {(session.isPending || plans.isPending) && <CardsSkeleton count={3} />}

      {s && plans.data && list.length === 0 && (
        <Card className="mx-auto max-w-3xl">
          <CardHeader>
            <CardTitle>Generate the first plan</CardTitle>
            <CardDescription>The engine seats every candidate so that no two neighbours write the same paper.</CardDescription>
          </CardHeader>
          <CardContent>
            <GeneratePanel session={s} onDone={(p) => select(p.id)} />
          </CardContent>
        </Card>
      )}

      {s && list.length > 0 && selected && (
        <div className="grid gap-6 xl:grid-cols-[18rem_1fr]">
          <div className="space-y-2">
            <div className="px-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Versions</div>
            {list.map((p) => (
              <button
                key={p.id}
                onClick={() => select(p.id)}
                className={cn(
                  "w-full rounded-xl border bg-card p-3 text-left transition-colors hover:border-primary/50",
                  p.id === selected.id && "border-primary ring-1 ring-primary",
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium">Version {p.version}</span>
                  <PlanStatusBadge status={p.status} />
                </div>
                <div className="mt-1 text-xs text-muted-foreground">
                  seed {p.seed} · {formatDuration(p.solve_ms)} · {timeAgo(p.created_at)}
                </div>
                <div className="mt-1.5 flex items-center gap-1.5 text-xs">
                  {p.hard_ok ? <CheckCircle2 className="size-3.5 text-success" /> : <AlertTriangle className="size-3.5 text-destructive" />}
                  {p.same_paper_pairs} same-paper · {p.halls_used} halls
                </div>
              </button>
            ))}
          </div>
          <PlanDetailView planId={selected.id} onDeleted={() => setParams({}, { replace: true })} />
        </div>
      )}

      <Dialog open={generating} onOpenChange={setGenerating}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>New version</DialogTitle>
            <DialogDescription>Earlier versions stay available until you delete them.</DialogDescription>
          </DialogHeader>
          {s && (
            <GeneratePanel
              session={s}
              onDone={(p) => {
                setGenerating(false);
                select(p.id);
              }}
            />
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
