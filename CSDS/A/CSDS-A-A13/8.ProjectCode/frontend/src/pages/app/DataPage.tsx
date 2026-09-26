import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "motion/react";
import {
  Accessibility, BookOpen, Building2, CalendarClock, ChevronLeft, ChevronRight, Search, Upload, Users,
} from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/common/States";
import { HallLayoutPreview } from "@/components/halls/HallLayoutPreview";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api, errorMessage } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/format";
import type { CandidateDetail, CandidatePage, Course, DataSummary, Department, ExamSession, Hall } from "@/lib/types";
import { useDebounced } from "@/lib/useDebounced";

const noData = (
  <EmptyState
    icon={Upload}
    title="Nothing imported yet"
    description="Import your courses, halls, candidates and timetable to get started."
    action={
      <Button asChild>
        <Link to="/app/import">Go to import</Link>
      </Button>
    }
  />
);

function CandidateDialog({ id, onClose }: { id: number | null; onClose: () => void }) {
  const detail = useQuery({
    queryKey: ["candidate", id],
    queryFn: async () => (await api.get<CandidateDetail>(`/candidates/${id}`)).data,
    enabled: id !== null,
  });
  const c = detail.data;
  return (
    <Dialog open={id !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>{c ? c.full_name : "Candidate"}</DialogTitle>
          <DialogDescription>{c ? `${c.roll_no} · ${c.department_name}` : "Loading..."}</DialogDescription>
        </DialogHeader>
        {detail.isPending && <Skeleton className="h-40 w-full" />}
        {detail.isError && <ErrorState error={detail.error} onRetry={() => detail.refetch()} />}
        {c && (
          <div className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <div className="text-xs text-muted-foreground">Email</div>
                <div className="truncate">{c.email ?? "-"}</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Accessible seat</div>
                <div>{c.needs_accessible_seat ? "Needed" : "Not needed"}</div>
              </div>
            </div>
            <div>
              <div className="mb-1.5 text-xs text-muted-foreground">Courses</div>
              <div className="flex flex-wrap gap-1.5">
                {c.courses.map((code) => (
                  <Badge key={code} variant="secondary" className="font-mono">
                    {code}
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <div className="mb-1.5 text-xs text-muted-foreground">Published seats</div>
              {c.seats.length === 0 ? (
                <p className="text-muted-foreground">No published seating plan includes this candidate yet.</p>
              ) : (
                <ul className="divide-y rounded-lg border">
                  {c.seats.map((s) => (
                    <li key={s.plan_id} className="flex items-center justify-between gap-3 p-3">
                      <div>
                        <div className="font-medium">{s.course_code} · {s.session_label}</div>
                        <div className="text-xs text-muted-foreground">{s.hall_name}</div>
                      </div>
                      <Badge className="font-mono text-sm">{s.hall_code} · {s.seat_label}</Badge>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

function CandidatesTab() {
  const [q, setQ] = useState("");
  const [department, setDepartment] = useState("all");
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState<number | null>(null);
  const search = useDebounced(q);
  const departments = useQuery({ queryKey: ["departments"], queryFn: async () => (await api.get<Department[]>("/departments")).data });
  const list = useQuery({
    queryKey: ["candidates", search, department, page],
    queryFn: async () =>
      (await api.get<CandidatePage>("/candidates", {
        params: { q: search || undefined, department: department === "all" ? undefined : department, page, page_size: 25 },
      })).data,
    placeholderData: keepPreviousData,
  });
  const pages = list.data ? Math.max(1, Math.ceil(list.data.total / list.data.page_size)) : 1;

  return (
    <Card>
      <CardContent className="space-y-4 p-4 sm:p-5">
        <div className="flex flex-col gap-2 sm:flex-row">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={q}
              onChange={(e) => {
                setQ(e.target.value);
                setPage(1);
              }}
              placeholder="Search by roll number or name"
              className="pl-9"
              aria-label="Search candidates"
            />
          </div>
          <Select
            value={department}
            onValueChange={(v) => {
              setDepartment(v);
              setPage(1);
            }}
          >
            <SelectTrigger className="sm:w-56" aria-label="Department">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All departments</SelectItem>
              {departments.data?.map((d) => (
                <SelectItem key={d.code} value={d.code}>
                  {d.code} · {d.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {list.isPending && <TableSkeleton />}
        {list.isError && <ErrorState error={list.error} onRetry={() => list.refetch()} />}
        {list.data && list.data.total === 0 && !search && department === "all" && noData}
        {list.data && list.data.total === 0 && (search || department !== "all") && (
          <p className="py-8 text-center text-sm text-muted-foreground">No candidate matches this search.</p>
        )}
        {list.data && list.data.total > 0 && (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Roll number</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead className="hidden sm:table-cell">Department</TableHead>
                  <TableHead className="hidden md:table-cell">Courses</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {list.data.items.map((c) => (
                  <TableRow key={c.id} className="cursor-pointer" onClick={() => setOpen(c.id)}>
                    <TableCell className="font-mono text-xs font-medium">{c.roll_no}</TableCell>
                    <TableCell>
                      <span className="inline-flex items-center gap-1.5">
                        {c.full_name}
                        {c.needs_accessible_seat && <Accessibility className="size-4 text-success" aria-label="Needs an accessible seat" />}
                      </span>
                    </TableCell>
                    <TableCell className="hidden sm:table-cell">{c.department_code}</TableCell>
                    <TableCell className="hidden font-mono text-xs text-muted-foreground md:table-cell">{c.courses.join(", ")}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">
                {formatNumber(list.data.total)} candidates · page {page} of {pages}
              </span>
              <div className="flex gap-1">
                <Button size="icon-sm" variant="outline" aria-label="Previous page" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                  <ChevronLeft />
                </Button>
                <Button size="icon-sm" variant="outline" aria-label="Next page" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>
                  <ChevronRight />
                </Button>
              </div>
            </div>
          </>
        )}
      </CardContent>
      <CandidateDialog id={open} onClose={() => setOpen(null)} />
    </Card>
  );
}

function CoursesTab() {
  const [q, setQ] = useState("");
  const courses = useQuery({ queryKey: ["courses"], queryFn: async () => (await api.get<Course[]>("/courses")).data });
  const needle = q.trim().toLowerCase();
  const rows = courses.data?.filter((c) => !needle || `${c.code} ${c.name} ${c.department_code}`.toLowerCase().includes(needle));
  return (
    <Card>
      <CardContent className="space-y-4 p-4 sm:p-5">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter courses" className="pl-9" aria-label="Filter courses" />
        </div>
        {courses.isPending && <TableSkeleton />}
        {courses.isError && <ErrorState error={courses.error} onRetry={() => courses.refetch()} />}
        {courses.data?.length === 0 && noData}
        {rows && rows.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Course</TableHead>
                <TableHead className="hidden sm:table-cell">Department</TableHead>
                <TableHead>Candidates</TableHead>
                <TableHead className="hidden md:table-cell">Sitting</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((c) => (
                <TableRow key={c.id}>
                  <TableCell>
                    <div className="font-mono text-xs font-medium">{c.code}</div>
                    <div className="text-sm">{c.name}</div>
                  </TableCell>
                  <TableCell className="hidden sm:table-cell">{c.department_name}</TableCell>
                  <TableCell className="tabular">{formatNumber(c.candidates)}</TableCell>
                  <TableCell className="hidden text-sm md:table-cell">
                    {c.session_label ?? <span className="text-muted-foreground">Not scheduled</span>}
                    {c.paper_group && <Badge variant="outline" className="ml-2">Shared paper {c.paper_group}</Badge>}
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

function floorText(floor: string) {
  if (!floor) return "";
  return /^\d+$/.test(floor) ? `Floor ${floor}` : `${floor} floor`;
}

function HallsTab() {
  const queryClient = useQueryClient();
  const halls = useQuery({ queryKey: ["halls"], queryFn: async () => (await api.get<Hall[]>("/halls")).data });
  const toggle = useMutation({
    mutationFn: async ({ id, is_active }: { id: number; is_active: boolean }) =>
      (await api.patch<Hall>(`/halls/${id}`, { is_active })).data,
    onSuccess: (hall) => {
      queryClient.invalidateQueries({ queryKey: ["halls"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
      toast.success(`${hall.code} is now ${hall.is_active ? "available" : "unavailable"} for new plans`);
    },
    onError: (err) => toast.error(errorMessage(err)),
  });
  if (halls.isPending) return <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{Array.from({ length: 6 }, (_, i) => <Skeleton key={i} className="h-72 rounded-xl" />)}</div>;
  if (halls.isError) return <ErrorState error={halls.error} onRetry={() => halls.refetch()} />;
  if (!halls.data.length) return noData;
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {halls.data.map((h, i) => (
        <motion.div key={h.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: Math.min(i * 0.03, 0.3) }}>
          <Card className={h.is_active ? "" : "opacity-60"}>
            <CardContent className="space-y-4 p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="font-mono text-xs text-muted-foreground">{h.code}</div>
                  <div className="truncate font-semibold">{h.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {[h.building, floorText(h.floor)].filter(Boolean).join(" · ")}
                  </div>
                </div>
                <Switch
                  checked={h.is_active}
                  onCheckedChange={(v) => toggle.mutate({ id: h.id, is_active: v })}
                  aria-label={`${h.code} available for plans`}
                />
              </div>
              <HallLayoutPreview rows={h.rows} cols={h.cols} blocked={h.blocked_seats} accessible={h.accessible_seats} aisles={h.aisles_after_cols} />
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="rounded-md bg-muted/60 p-2">
                  <div className="font-semibold tabular">{h.capacity}</div>
                  <div className="text-muted-foreground">seats</div>
                </div>
                <div className="rounded-md bg-muted/60 p-2">
                  <div className="font-semibold tabular">{h.accessible_seats.length}</div>
                  <div className="text-muted-foreground">accessible</div>
                </div>
                <div className="rounded-md bg-muted/60 p-2" title="Most candidates of one paper this hall can take without neighbours sharing it">
                  <div className="font-semibold tabular">{h.paper_ceiling}</div>
                  <div className="text-muted-foreground">per paper</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}

function TimetableTab() {
  const sessions = useQuery({ queryKey: ["sessions"], queryFn: async () => (await api.get<ExamSession[]>("/sessions")).data });
  if (sessions.isPending) return <TableSkeleton />;
  if (sessions.isError) return <ErrorState error={sessions.error} onRetry={() => sessions.refetch()} />;
  if (!sessions.data.length) return noData;
  return (
    <div className="space-y-3">
      {sessions.data.map((s) => (
        <Card key={s.id}>
          <CardContent className="flex flex-col gap-3 p-4 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="font-semibold">{s.label}</div>
              <div className="text-sm text-muted-foreground">
                {formatDate(s.date)} · {s.start_time}-{s.end_time} · {formatNumber(s.candidates)} candidates
              </div>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {s.papers.map((p) => (
                  <Badge key={p.course_code} variant="secondary" className="font-mono" title={p.course_name}>
                    {p.course_code} · {p.candidates}
                  </Badge>
                ))}
              </div>
            </div>
            <Button asChild variant="outline" className="shrink-0">
              <Link to={`/app/sessions/${s.id}`}>
                <CalendarClock /> {s.plans.count ? "View plans" : "Plan seating"}
              </Link>
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

const TABS = [
  { value: "candidates", label: "Candidates", icon: Users },
  { value: "courses", label: "Courses", icon: BookOpen },
  { value: "halls", label: "Halls", icon: Building2 },
  { value: "timetable", label: "Timetable", icon: CalendarClock },
] as const;

export default function DataPage() {
  const [params, setParams] = useSearchParams();
  const tab = TABS.some((t) => t.value === params.get("tab")) ? params.get("tab")! : "candidates";
  const summary = useQuery({ queryKey: ["summary"], queryFn: async () => (await api.get<DataSummary>("/data/summary")).data });
  const counts: Record<string, number | undefined> = {
    candidates: summary.data?.candidates,
    courses: summary.data?.courses,
    halls: summary.data?.halls,
    timetable: summary.data?.sessions,
  };

  return (
    <>
      <PageHeader
        title="Data"
        description="Everything SeatWise knows about your candidates, courses, halls and timetable."
        actions={
          <Button asChild variant="outline">
            <Link to="/app/import">
              <Upload /> Import
            </Link>
          </Button>
        }
      />
      <Tabs value={tab} onValueChange={(v) => setParams({ tab: v }, { replace: true })}>
        <TabsList>
          {TABS.map((t) => (
            <TabsTrigger key={t.value} value={t.value}>
              <t.icon /> {t.label}
              {counts[t.value] !== undefined && <span className="ml-1 text-xs text-muted-foreground tabular">{formatNumber(counts[t.value]!)}</span>}
            </TabsTrigger>
          ))}
        </TabsList>
        <TabsContent value="candidates"><CandidatesTab /></TabsContent>
        <TabsContent value="courses"><CoursesTab /></TabsContent>
        <TabsContent value="halls"><HallsTab /></TabsContent>
        <TabsContent value="timetable"><TimetableTab /></TabsContent>
      </Tabs>
    </>
  );
}
