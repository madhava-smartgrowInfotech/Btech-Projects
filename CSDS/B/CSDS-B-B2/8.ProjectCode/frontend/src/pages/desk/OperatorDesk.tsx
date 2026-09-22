import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query";
import { CircleMarker, MapContainer, TileLayer, Tooltip } from "react-leaflet";
import { Headset, Inbox, Search } from "lucide-react";
import { toast } from "sonner";
import "@/components/map/leaflet-setup";
import { ComplaintList } from "@/components/complaints/ComplaintList";
import { EmptyState, ErrorState, PageHeader } from "@/components/common/states";
import { FitBounds } from "@/components/map/layers";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { api, apiError, hasRole } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { STATUS_LABEL, type ComplaintPage, type ComplaintStatus } from "@/lib/complaints";
import { useCoverageSummary, useLiveStream } from "@/lib/coverage";
import { cn } from "@/lib/utils";

const QUEUES: { id: string; label: string; statuses: ComplaintStatus[] }[] = [
  { id: "action", label: "Needs action", statuses: ["registered"] },
  { id: "working", label: "In progress", statuses: ["acknowledged", "in_progress"] },
  { id: "verify", label: "Awaiting verification", statuses: ["resolved"] },
  { id: "detected", label: "Detected", statuses: ["detected"] },
  { id: "closed", label: "Closed", statuses: ["verified", "dismissed"] },
];
const PIN: Record<ComplaintStatus, string> = {
  detected: "#7c5cff", registered: "#e11d48", acknowledged: "#0284c7", in_progress: "#d97706", resolved: "#0d9488", verified: "#16a34a", dismissed: "#8d8c87",
};

export default function OperatorDesk() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [queue, setQueue] = useState("action");
  const [operator, setOperator] = useState<string>("all");
  const [hideSample, setHideSample] = useState(false);
  const [search, setSearch] = useState("");
  const statuses = QUEUES.find((q) => q.id === queue)!.statuses;
  const summary = useCoverageSummary();
  const params = {
    status: statuses.join(","),
    ...(operator !== "all" ? { operator } : {}),
    ...(hideSample ? { source: "phone,esp32,simulator" } : {}),
    ...(search.trim() ? { q: search.trim() } : {}),
    limit: 200,
  };
  const q = useQuery({
    queryKey: ["complaints", "desk", params],
    queryFn: async () => (await api.get<ComplaintPage>("/api/complaints", { params })).data,
    placeholderData: keepPreviousData,
    refetchInterval: 30_000,
  });

  useLiveStream(true, {
    complaint: (c) => {
      qc.invalidateQueries({ queryKey: ["complaints"] });
      if (c.source === "sample_dataset") return;
      if (c.event === "registered") toast.error(`New complaint ${c.ref_code} - ${c.operator}`, { action: { label: "Open", onClick: () => navigate(`/app/complaints/${c.id}`) } });
      else if (c.event === "reopened") toast.warning(`${c.ref_code} reopened - the fix did not hold`, { action: { label: "Open", onClick: () => navigate(`/app/complaints/${c.id}`) } });
      else if (c.event === "verified") toast.success(`${c.ref_code} verified by new readings`);
    },
  });

  const counts = q.data?.counts;
  const bounds = useMemo<[[number, number], [number, number]] | null>(() => {
    const items = q.data?.items ?? [];
    if (!items.length) return null;
    const lats = items.map((c) => c.lat);
    const lons = items.map((c) => c.lon);
    return [[Math.min(...lats), Math.min(...lons)], [Math.max(...lats), Math.max(...lons)]];
  }, [q.data]);

  return (
    <>
      <PageHeader
        title="Operator desk"
        description="Complaints filed automatically from measured coverage, with the evidence to act on. New and reopened complaints appear here live."
      />
      <div className="mb-4 flex gap-1 overflow-x-auto rounded-lg bg-muted p-1" role="tablist" aria-label="Queues">
        {QUEUES.map((qq) => {
          const n = counts ? qq.statuses.reduce((s, k) => s + (counts[k] ?? 0), 0) : null;
          return (
            <button key={qq.id} role="tab" aria-selected={queue === qq.id} onClick={() => setQueue(qq.id)}
              className={cn("flex shrink-0 items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors", queue === qq.id ? "bg-card shadow-sm" : "text-muted-foreground hover:text-foreground")}>
              {qq.label}
              {n != null && <span className={cn("rounded-full px-1.5 text-xs tabular", qq.id === "action" && n > 0 ? "bg-rose-600 text-white" : "bg-background")}>{n}</span>}
            </button>
          );
        })}
      </div>

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search reference, zone or operator" className="pl-9" aria-label="Search complaints" />
        </div>
        <Select value={operator} onValueChange={setOperator}>
          <SelectTrigger className="sm:w-48" aria-label="Operator"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All operators</SelectItem>
            {summary.data?.operators.map((o) => <SelectItem key={o.name} value={o.name}>{o.name}</SelectItem>)}
          </SelectContent>
        </Select>
        <label className="flex items-center gap-2 text-sm">
          <Switch checked={hideSample} onCheckedChange={setHideSample} /> Hide sample data
        </label>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1fr)_380px]">
        <div>
          {q.isPending ? (
            <div className="space-y-2">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-16" />)}</div>
          ) : q.isError ? (
            <ErrorState message={apiError(q.error)} onRetry={() => q.refetch()} />
          ) : q.data.items.length === 0 ? (
            <EmptyState icon={queue === "action" ? Headset : Inbox} title={queue === "action" ? "Nothing waiting" : `No ${QUEUES.find((x) => x.id === queue)!.label.toLowerCase()} complaints`}
              description={queue === "action" ? "New complaints appear here the moment a zone stays weak or dead past the threshold." : "Try another queue or clear the filters."} />
          ) : (
            <ComplaintList items={q.data.items} showAssignee />
          )}
        </div>
        <Card className="hidden h-[520px] overflow-hidden xl:block">
          <div className="isolate h-full">
            <MapContainer center={[22.5, 79]} zoom={5} className="h-full w-full" zoomControl={false}>
              <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              <FitBounds bounds={bounds} fitKey={`${queue}-${q.data?.items.length ?? 0}`} />
              {q.data?.items.map((c) => (
                <CircleMarker key={c.id} center={[c.lat, c.lon]} radius={8} pathOptions={{ color: "#fff", weight: 2, fillColor: PIN[c.status], fillOpacity: 0.95 }}
                  eventHandlers={{ click: () => navigate(`/app/complaints/${c.id}`) }}>
                  <Tooltip direction="top">{c.ref_code} · {STATUS_LABEL[c.status]} · {c.operator}</Tooltip>
                </CircleMarker>
              ))}
            </MapContainer>
          </div>
        </Card>
      </div>
      {hasRole(user, "admin") && (
        <p className="mt-3 text-xs text-muted-foreground">
          Detection and verification thresholds are set on the <Link to="/app/settings" className="text-primary hover:underline">Settings</Link> page.
        </p>
      )}
    </>
  );
}
