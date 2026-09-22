import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CircleMarker, MapContainer, Polygon, Polyline, TileLayer, Tooltip } from "react-leaflet";
import { ArrowLeft, Check, Copy, Download, FileJson, FileSpreadsheet, MapPin, MessageSquarePlus, Navigation, Printer, RadioTower, ShieldCheck, UserRound } from "lucide-react";
import { toast } from "sonner";
import "@/components/map/leaflet-setup";
import { EvidenceChart } from "@/components/complaints/EvidenceChart";
import { SeverityBadge, StatusBadge, StatusStepper } from "@/components/complaints/parts";
import { ErrorState } from "@/components/common/states";
import { ZoneBar } from "@/components/common/zone";
import { FitBounds } from "@/components/map/layers";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Textarea } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { api, apiError, hasRole, TOKEN_KEY } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { NEXT_ACTIONS, STATUS_LABEL, type ComplaintDetail as Detail, type ComplaintStatus } from "@/lib/complaints";
import { cn, formatDateTime, safeStorage, timeAgo } from "@/lib/utils";
import { METHOD_LABEL, SOURCE_LABEL, ZONE_COLOR } from "@/lib/zones";

interface TowerInfo {
  enabled: boolean;
  error?: string;
  towers: { radio: string | null; mcc: number; mnc: number; area: number; cell: number; lat: number; lon: number; range_m: number | null; distance_m: number; serving: boolean }[];
}

function Metric({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-lg border bg-muted/30 p-3">
      <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-0.5 font-mono text-base font-semibold tabular">{value}</p>
      {hint && <p className="text-[11px] text-muted-foreground">{hint}</p>}
    </div>
  );
}

const pct = (v: number | null | undefined) => (v == null ? "–" : `${Math.round(v * 100)}%`);
const num = (v: number | null | undefined, unit: string, digits = 0) => (v == null ? "–" : `${v.toFixed(digits)} ${unit}`);

function span(minutes: number) {
  if (minutes < 90) return `${Math.round(minutes)} min`;
  if (minutes < 60 * 48) return `${(minutes / 60).toFixed(1)} hours`;
  return `${(minutes / 1440).toFixed(1)} days`;
}

async function download(path: string, filename: string) {
  const token = safeStorage.get(TOKEN_KEY);
  const res = await fetch(path, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
  if (!res.ok) throw new Error(`Download failed (HTTP ${res.status})`);
  const url = URL.createObjectURL(await res.blob());
  const a = Object.assign(document.createElement("a"), { href: url, download: filename });
  a.click();
  URL.revokeObjectURL(url);
}

export default function ComplaintDetail() {
  const { id } = useParams();
  const qc = useQueryClient();
  const { user } = useAuth();
  const isEngineer = hasRole(user, "engineer");
  const [action, setAction] = useState<{ to: ComplaintStatus; label: string } | null>(null);
  const [note, setNote] = useState("");
  const [comment, setComment] = useState("");
  const [copied, setCopied] = useState(false);

  const q = useQuery({ queryKey: ["complaint", id], queryFn: async () => (await api.get<Detail>(`/api/complaints/${id}`)).data, refetchInterval: 20_000 });
  const towers = useQuery({ queryKey: ["towers", id], staleTime: 3_600_000, queryFn: async () => (await api.get<TowerInfo>(`/api/complaints/${id}/towers`)).data });
  const engineers = useQuery({ queryKey: ["engineers"], enabled: isEngineer, queryFn: async () => (await api.get<{ id: number; name: string }[]>("/api/complaints/meta/engineers")).data });
  const onUpdated = (d: Detail) => {
    qc.setQueryData(["complaint", id], d);
    qc.invalidateQueries({ queryKey: ["complaints"] });
  };
  const transition = useMutation({
    mutationFn: async (body: { to: ComplaintStatus; note?: string }) => (await api.post<Detail>(`/api/complaints/${id}/transition`, body)).data,
    onSuccess: (d) => { onUpdated(d); toast.success(`Now ${STATUS_LABEL[d.status]}`); setAction(null); setNote(""); },
    onError: (e) => toast.error(apiError(e)),
  });
  const assign = useMutation({
    mutationFn: async (userId: number | null) => (await api.post<Detail>(`/api/complaints/${id}/assign`, { user_id: userId })).data,
    onSuccess: (d) => { onUpdated(d); toast.success(d.assigned_to_name ? `Assigned to ${d.assigned_to_name}` : "Unassigned"); },
    onError: (e) => toast.error(apiError(e)),
  });
  const addNote = useMutation({
    mutationFn: async () => (await api.post<Detail>(`/api/complaints/${id}/notes`, { note: comment.trim() })).data,
    onSuccess: (d) => { onUpdated(d); setComment(""); toast.success("Note added"); },
    onError: (e) => toast.error(apiError(e)),
  });

  if (q.isPending) return <div className="space-y-4"><Skeleton className="h-10 w-72" /><Skeleton className="h-28" /><Skeleton className="h-72" /></div>;
  if (q.isError) return <ErrorState message={apiError(q.error)} onRetry={() => q.refetch()} />;
  const c = q.data;
  const ev = c.evidence;
  const spot = c.suggestion;
  const center: [number, number] = [c.lat, c.lon];
  const bounds: [[number, number], [number, number]] = (() => {
    const pts = [...c.boundary, ...(spot?.lat != null && spot.lon != null ? [[spot.lat, spot.lon] as [number, number]] : [])];
    return [[Math.min(...pts.map((p) => p[0])), Math.min(...pts.map((p) => p[1]))], [Math.max(...pts.map((p) => p[0])), Math.max(...pts.map((p) => p[1]))]];
  })();

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <Link to={isEngineer ? "/app/desk" : "/app/complaints"} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground print:hidden">
            <ArrowLeft className="h-4 w-4" /> {isEngineer ? "Operator desk" : "My complaints"}
          </Link>
          <h1 className="mt-1 flex flex-wrap items-center gap-2 text-2xl font-bold">
            <span className="font-mono">{c.ref_code}</span>
            <StatusBadge status={c.status} className="text-sm" />
            <SeverityBadge severity={c.severity} />
            {c.source === "sample_dataset" && <Badge variant="secondary">Sample data</Badge>}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {c.operator} · zone {c.h3_cell} · {c.origin === "user" ? `reported by ${c.reporter_name ?? "a user"}` : "detected automatically"} · updated {timeAgo(c.updated_at)}
          </p>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="print:hidden"><Download /> Export evidence</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onSelect={() => download(`/api/complaints/${c.id}/evidence.json`, `${c.ref_code}-evidence.json`).catch((e) => toast.error(e.message))}><FileJson /> Evidence (JSON)</DropdownMenuItem>
            <DropdownMenuItem onSelect={() => download(`/api/complaints/${c.id}/evidence.csv`, `${c.ref_code}-readings.csv`).catch((e) => toast.error(e.message))}><FileSpreadsheet /> Readings (CSV)</DropdownMenuItem>
            <DropdownMenuItem onSelect={() => window.print()}><Printer /> Print or save as PDF</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <Card><CardContent className="pt-5"><StatusStepper c={c} /></CardContent></Card>

      {isEngineer && NEXT_ACTIONS[c.status].length > 0 && (
        <Card className="print:hidden">
          <CardContent className="flex flex-col gap-3 pt-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-wrap gap-2">
              {NEXT_ACTIONS[c.status].map((a) => (
                <Button key={a.to} variant={a.variant ?? "default"} onClick={() => setAction(a)} loading={transition.isPending && transition.variables?.to === a.to}>{a.label}</Button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <UserRound className="h-4 w-4 text-muted-foreground" aria-hidden />
              <Select value={c.assigned_to_id ? String(c.assigned_to_id) : "none"} onValueChange={(v) => assign.mutate(v === "none" ? null : Number(v))}>
                <SelectTrigger className="w-52" aria-label="Assigned engineer"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Unassigned</SelectItem>
                  {engineers.data?.map((e) => <SelectItem key={e.id} value={String(e.id)}>{e.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          {c.summary && (
            <Card>
              <CardHeader className="flex-row items-center justify-between pb-2">
                <CardTitle>Complaint text</CardTitle>
                <Button size="sm" variant="ghost" className="print:hidden" onClick={async () => {
                  try { await navigator.clipboard.writeText(c.summary ?? ""); setCopied(true); setTimeout(() => setCopied(false), 1500); } catch { toast.error("Copy is not available"); }
                }}>{copied ? <Check /> : <Copy />} Copy</Button>
              </CardHeader>
              <CardContent><p className="text-sm leading-relaxed">{c.summary}</p></CardContent>
            </Card>
          )}

          <Card>
            <CardHeader className="pb-3"><CardTitle>Evidence</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <ZoneBar strong={ev.classes.Strong} weak={ev.classes.Weak} dead={ev.classes.Dead} />
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                <Metric label="Readings" value={ev.readings.toLocaleString()} hint={`${ev.devices} device${ev.devices === 1 ? "" : "s"}`} />
                <Metric label="Weak or dead" value={pct(ev.bad_share)} hint={`${ev.classes.Dead} dead`} />
                <Metric label="Measured over" value={span(ev.window.minutes)} hint={ev.window.last ? `until ${formatDateTime(ev.window.last)}` : undefined} />
                <Metric label="Confidence" value={pct(ev.mean_confidence)} hint={Object.keys(ev.methods ?? {}).map((m) => METHOD_LABEL[m] ?? m).join(", ")} />
              </div>
              {ev.service && (
                <div>
                  <p className="mb-2 text-sm font-medium">Measured service (phone probe)</p>
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                    <Metric label="No connection" value={pct(ev.service.no_connectivity_share)} />
                    <Metric label="Latency median" value={num(ev.service.latency_median_ms, "ms")} hint={ev.service.latency_p90_ms != null ? `90th percentile ${ev.service.latency_p90_ms.toFixed(0)} ms` : undefined} />
                    <Metric label="Download median" value={num(ev.service.download_median_mbps, "Mbps", 1)} />
                    <Metric label="Upload median" value={num(ev.service.upload_median_mbps, "Mbps", 1)} />
                  </div>
                  {Object.keys(ev.service.radio_estimate).length > 0 && (
                    <p className="mt-2 text-xs text-muted-foreground">
                      Estimated radio condition from speed tests: {Object.entries(ev.service.radio_estimate).map(([k, v]) => `${k} ${v}`).join(" · ")} (an estimate, shown for context).
                    </p>
                  )}
                </div>
              )}
              {ev.radio && (
                <div>
                  <p className="mb-2 text-sm font-medium">Radio measurements</p>
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                    <Metric label="RSRP median" value={num(ev.radio.rsrp_median_dbm, "dBm")} hint={ev.radio.rsrp_min_dbm != null ? `minimum ${ev.radio.rsrp_min_dbm.toFixed(0)} dBm` : undefined} />
                    <Metric label="RSRQ median" value={num(ev.radio.rsrq_median_db, "dB")} />
                    <Metric label="SINR median" value={num(ev.radio.sinr_median_db, "dB")} />
                    <Metric label="Serving cells" value={ev.radio.cell_ids.length ? String(ev.radio.cell_ids.length) : "–"} hint={ev.radio.cell_ids.length ? `cell ID ${ev.radio.cell_ids.slice(0, 3).join(", ")}` : undefined} />
                  </div>
                </div>
              )}
              {ev.wifi && (
                <div>
                  <p className="mb-2 text-sm font-medium">Sensor node Wi-Fi link</p>
                  <div className="grid grid-cols-3 gap-2">
                    <Metric label="Wi-Fi RSSI" value={num(ev.wifi.rssi_median_dbm, "dBm")} />
                    <Metric label="Latency" value={num(ev.wifi.latency_median_ms, "ms")} />
                    <Metric label="Offline" value={pct(ev.wifi.offline_share)} />
                  </div>
                </div>
              )}
              {ev.top_reasons && ev.top_reasons.length > 0 && (
                <div>
                  <p className="mb-1.5 text-sm font-medium">Most common reasons</p>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    {ev.top_reasons.map((r) => <li key={r.reason} className="flex justify-between gap-3"><span>{r.reason}</span><span className="tabular">{r.count}×</span></li>)}
                  </ul>
                </div>
              )}
              <p className="text-xs text-muted-foreground">
                Sources: {Object.entries(ev.sources).map(([s, n]) => `${SOURCE_LABEL[s] ?? s} ${n}`).join(" · ")}
                {ev.model_versions?.length ? ` · model ${ev.model_versions.join(", ")}` : ""}
              </p>
            </CardContent>
          </Card>

          {ev.series && ev.series.length > 1 && (
            <Card>
              <CardHeader className="pb-2"><CardTitle>Readings over time</CardTitle></CardHeader>
              <CardContent><EvidenceChart series={ev.series} /></CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-4">
          <Card className="overflow-hidden">
            <div className="isolate h-64">
              <MapContainer center={center} zoom={16} className="h-full w-full" zoomControl={false} scrollWheelZoom={false}>
                <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                <FitBounds bounds={bounds} fitKey={c.ref_code} />
                <Polygon positions={c.boundary} pathOptions={{ color: c.severity === "dead" ? ZONE_COLOR.Dead : ZONE_COLOR.Weak, weight: 2, fillOpacity: 0.3 }}>
                  <Tooltip sticky>Complaint zone</Tooltip>
                </Polygon>
                {spot?.found && spot.lat != null && spot.lon != null && spot.status === "found" && (
                  <>
                    <Polyline positions={[center, [spot.lat, spot.lon]]} pathOptions={{ color: "var(--series-1)", weight: 2, dashArray: "6 6" }} />
                    <CircleMarker center={[spot.lat, spot.lon]} radius={8} pathOptions={{ color: "#fff", weight: 2, fillColor: ZONE_COLOR.Strong, fillOpacity: 1 }}>
                      <Tooltip>Nearest predicted strong signal</Tooltip>
                    </CircleMarker>
                  </>
                )}
                {towers.data?.towers.map((t) => (
                  <CircleMarker key={`${t.mcc}-${t.mnc}-${t.area}-${t.cell}`} center={[t.lat, t.lon]} radius={t.serving ? 7 : 5}
                    pathOptions={{ color: "#fff", weight: 1.5, fillColor: "var(--series-7)", fillOpacity: 1 }}>
                    <Tooltip>{t.radio ?? "Cell"} tower · cell {t.cell} · {t.distance_m} m away{t.serving ? " · served these readings" : ""}</Tooltip>
                  </CircleMarker>
                ))}
              </MapContainer>
            </div>
            <CardContent className="space-y-2 pt-4 text-sm">
              <p className="flex items-center gap-2"><MapPin className="h-4 w-4 text-muted-foreground" /> {c.lat.toFixed(5)}, {c.lon.toFixed(5)}</p>
              {spot && (
                <p className="flex items-start gap-2 text-muted-foreground">
                  <Navigation className="mt-0.5 h-4 w-4 shrink-0 text-zone-strong" />
                  {spot.message}
                </p>
              )}
              {towers.data?.enabled && (
                <div className="border-t pt-2">
                  <p className="flex items-center gap-2 font-medium"><RadioTower className="h-4 w-4 text-muted-foreground" /> Known towers within 1 km</p>
                  {towers.data.error ? <p className="mt-1 text-xs text-muted-foreground">{towers.data.error}</p> : towers.data.towers.length ? (
                    <ul className="mt-1 space-y-0.5 text-xs text-muted-foreground">
                      {towers.data.towers.slice(0, 5).map((t) => (
                        <li key={`${t.mcc}-${t.mnc}-${t.area}-${t.cell}`} className="flex justify-between gap-3">
                          <span>{t.radio ?? "Cell"} · cell {t.cell}{t.serving ? " · served these readings" : ""}</span>
                          <span className="tabular">{t.distance_m} m</span>
                        </li>
                      ))}
                    </ul>
                  ) : <p className="mt-1 text-xs text-muted-foreground">No towers listed near this zone.</p>}
                  <p className="mt-1 text-[11px] text-muted-foreground">Tower positions: OpenCelliD (CC BY-SA 4.0)</p>
                </div>
              )}
            </CardContent>
          </Card>

          {(c.status === "resolved" || c.status === "verified" || c.verification) && (
            <Card>
              <CardHeader className="pb-2"><CardTitle className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-primary" /> Automatic verification</CardTitle></CardHeader>
              <CardContent className="text-sm">
                {c.verification ? (
                  <>
                    <p className={cn("font-medium", c.verification.state === "verified" ? "text-ink-strong" : c.verification.state === "failed" ? "text-ink-dead" : "")}>
                      {{ waiting: "Waiting for new readings in this zone", verified: "Fix confirmed by new readings", failed: "New readings still weak or dead - reopened",
                         awaiting_data: "No new readings yet - verification is waiting for data", confirmed_by_engineer: "Confirmed by an engineer" }[c.verification.state] ?? c.verification.state}
                    </p>
                    {c.verification.readings != null && (
                      <p className="mt-1 text-muted-foreground">
                        {c.verification.readings} new reading{c.verification.readings === 1 ? "" : "s"}
                        {c.verification.needed ? ` of ${c.verification.needed} needed` : ""}
                        {c.verification.strong_share != null && c.verification.readings ? ` · ${pct(c.verification.strong_share)} strong` : ""}
                      </p>
                    )}
                  </>
                ) : (
                  <p className="text-muted-foreground">Starts when the complaint is marked resolved.</p>
                )}
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader className="pb-2"><CardTitle>History</CardTitle></CardHeader>
            <CardContent>
              <ol className="relative space-y-4 border-l pl-4">
                {c.events.map((e) => (
                  <li key={e.id} className="relative">
                    <span className={cn("absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full ring-4 ring-card", e.kind === "note" ? "bg-muted-foreground" : "bg-primary")} aria-hidden />
                    <p className="text-sm">
                      {e.kind === "status" && e.to_status ? <span className="font-medium">{STATUS_LABEL[e.to_status as ComplaintStatus] ?? e.to_status}</span> : e.kind === "assign" ? <span className="font-medium">Assignment</span> : <span className="font-medium">Note</span>}
                      <span className="text-muted-foreground"> · {e.actor_label}</span>
                    </p>
                    {e.note && <p className="mt-0.5 text-sm text-muted-foreground">{e.note}</p>}
                    <p className="text-[11px] text-muted-foreground">{formatDateTime(e.ts)}</p>
                  </li>
                ))}
              </ol>
              <div className="mt-4 space-y-2 print:hidden">
                <Textarea value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Add a note for the team" className="min-h-[70px]" maxLength={2000} />
                <Button size="sm" variant="outline" onClick={() => addNote.mutate()} disabled={!comment.trim()} loading={addNote.isPending}><MessageSquarePlus /> Add note</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Dialog open={!!action} onOpenChange={(o) => !o && setAction(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{action?.label} - {c.ref_code}</DialogTitle>
            <DialogDescription>
              {action?.to === "resolved" ? "SignalScout will verify the fix automatically from the next readings in this zone." :
               action?.to === "dismissed" ? "Dismissed complaints leave the queue. Add the reason for the record." : "Add a note for the record (optional)."}
            </DialogDescription>
          </DialogHeader>
          <Textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder={action?.to === "resolved" ? "What was done, e.g. antenna tilt corrected on sector 2" : "Note"} maxLength={2000} />
          <DialogFooter>
            <Button variant="outline" onClick={() => setAction(null)}>Cancel</Button>
            <Button variant={action?.to === "dismissed" ? "destructive" : "default"} disabled={action?.to === "dismissed" && note.trim().length < 3}
              loading={transition.isPending} onClick={() => action && transition.mutate({ to: action.to, note: note.trim() || undefined })}>
              {action?.label}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
