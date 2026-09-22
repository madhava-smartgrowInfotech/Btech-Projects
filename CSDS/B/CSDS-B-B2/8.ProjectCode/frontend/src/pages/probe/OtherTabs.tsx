import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle, CheckCircle2, Clock3, CloudUpload, LogOut, RefreshCw, Smartphone, Unlink, XCircle } from "lucide-react";
import { toast } from "sonner";
import { ZoneBadge } from "@/components/common/zone";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { api } from "@/lib/api";
import type { SyncBatch } from "@/lib/devices";
import type { ProbeMeta } from "@/lib/probe/store";
import type { ProbeController } from "@/lib/probe/useProbe";
import { formatDateTime, timeAgo } from "@/lib/utils";
import type { ZoneLabel } from "@/lib/zones";

export function LogTab({ probe }: { probe: ProbeController }) {
  const items = probe.records.slice(0, 200);
  if (!items.length) return <p className="py-16 text-center text-sm text-muted-foreground">No readings yet. Start measuring on the Live tab.</p>;
  return (
    <ul className="divide-y rounded-2xl border bg-card">
      {items.map((r) => {
        const label = (r.server?.zone_label ?? r.provisional.label) as ZoneLabel;
        return (
          <li key={r.reading.client_uuid} className="flex items-center gap-3 px-3 py-2.5">
            <span className="shrink-0" aria-label={r.status}>
              {r.status === "synced" ? <CheckCircle2 className="h-4 w-4 text-zone-strong" /> : r.status === "rejected" ? <XCircle className="h-4 w-4 text-zone-dead" /> : <Clock3 className="h-4 w-4 text-muted-foreground" />}
            </span>
            <div className="min-w-0 flex-1">
              <p className="flex items-center gap-2 text-sm">
                <ZoneBadge label={label} confidence={r.server?.zone_confidence ?? null} />
                {!r.server && r.status !== "rejected" && <span className="text-[11px] text-muted-foreground">provisional</span>}
              </p>
              <p className="mt-0.5 truncate font-mono text-[11px] text-muted-foreground tabular">
                {r.reading.connected ? `${r.reading.latency_ms ?? "–"} ms` : "offline"}
                {r.reading.dl_mbps != null && ` · ${r.reading.dl_mbps.toFixed(1)}↓ ${r.reading.ul_mbps?.toFixed(1) ?? "–"}↑ Mbps`}
                {r.reading.accuracy_m != null && ` · ±${r.reading.accuracy_m} m`}
              </p>
              {r.error && <p className="text-[11px] text-destructive">{r.error}</p>}
            </div>
            <time className="shrink-0 text-[11px] text-muted-foreground" dateTime={r.reading.ts} title={formatDateTime(r.reading.ts)}>
              {new Date(r.reading.ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
            </time>
          </li>
        );
      })}
    </ul>
  );
}

export function SyncTab({ probe, meta }: { probe: ProbeController; meta: ProbeMeta }) {
  const [busy, setBusy] = useState(false);
  const history = useQuery({ queryKey: ["probe-sync", meta.deviceId], queryFn: async () => (await api.get<SyncBatch[]>(`/api/devices/${meta.deviceId}/sync`)).data, enabled: probe.online, refetchInterval: 20_000 });
  const synced = probe.records.filter((r) => r.status === "synced").length;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-2.5">
        <div className="rounded-xl border bg-card p-3">
          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Waiting on this phone</p>
          <p className="mt-1 font-mono text-2xl font-semibold tabular">{probe.queued}</p>
        </div>
        <div className="rounded-xl border bg-card p-3">
          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Uploaded (kept here)</p>
          <p className="mt-1 font-mono text-2xl font-semibold tabular">{synced}</p>
        </div>
      </div>
      <div className="rounded-2xl border bg-card p-4 text-sm">
        <p className="flex items-center gap-2 font-medium">
          <CloudUpload className="h-4 w-4 text-primary" /> Last upload {timeAgo(probe.sync?.lastSyncAt ? new Date(probe.sync.lastSyncAt).toISOString() : null)}
        </p>
        {probe.sync?.lastBatch && (
          <p className="mt-1 text-xs text-muted-foreground">
            {probe.sync.lastBatch.accepted} accepted · {probe.sync.lastBatch.duplicates} already uploaded · {probe.sync.lastBatch.rejected} rejected
          </p>
        )}
        {probe.sync?.lastError && probe.queued > 0 && (
          <p className="mt-2 flex items-start gap-1.5 rounded-lg bg-zone-weak/15 px-3 py-2 text-xs"><AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />{probe.sync.lastError}</p>
        )}
        <Button className="mt-3 w-full" variant="outline" disabled={!probe.online || probe.queued === 0} loading={busy}
          onClick={async () => {
            setBusy(true);
            const out = await probe.doSync();
            setBusy(false);
            if (out?.error) toast.error(out.error);
            else toast.success(`Uploaded ${out?.sent ?? 0} readings`);
            void history.refetch();
          }}>
          <RefreshCw /> {probe.online ? "Sync now" : "Offline - will sync automatically"}
        </Button>
        <p className="mt-2 text-xs text-muted-foreground">Readings are saved on the phone first. When the connection returns they upload automatically - even if this page is closed, on browsers that support background sync.</p>
      </div>
      <div className="rounded-2xl border bg-card p-4">
        <p className="mb-2 text-sm font-medium">Uploads received by SignalScout</p>
        {!probe.online ? (
          <p className="text-xs text-muted-foreground">Available when online.</p>
        ) : history.data?.length ? (
          <ul className="divide-y text-xs">
            {history.data.slice(0, 12).map((b) => (
              <li key={b.id} className="flex justify-between gap-2 py-1.5">
                <span title={formatDateTime(b.ts)}>{timeAgo(b.ts)}{b.oldest_reading && b.accepted > 1 ? ` · oldest reading ${timeAgo(b.oldest_reading)}` : ""}</span>
                <span className="tabular text-muted-foreground">{b.accepted} new{b.duplicates ? ` · ${b.duplicates} dup` : ""}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-muted-foreground">No uploads yet.</p>
        )}
      </div>
    </div>
  );
}

const OPERATORS = ["Jio", "Airtel", "Vi", "BSNL", "MTNL"];

export function SettingsTab({ probe, meta, onUnpair, onSignOut }: { probe: ProbeController; meta: ProbeMeta; onUnpair: () => void; onSignOut: () => void }) {
  const [confirm, setConfirm] = useState(false);
  const [custom, setCustom] = useState(probe.settings.operator && !OPERATORS.includes(probe.settings.operator) ? probe.settings.operator : "");
  const s = probe.settings;
  const detected = probe.whoami?.carrier.operator ?? probe.sync?.operator;
  const testsPerHour = s.dataSaver || !s.speedtestS ? 0 : Math.floor(3600 / Math.max(s.speedtestS, s.intervalS));
  const mbPerHour = Math.round(testsPerHour * 1.2 * 10) / 10;
  const opValue = s.operator == null ? "auto" : OPERATORS.includes(s.operator) ? s.operator : "other";
  return (
    <div className="space-y-4">
      <div className="space-y-4 rounded-2xl border bg-card p-4">
        <div className="space-y-1.5">
          <Label>Mobile operator</Label>
          <Select value={opValue} onValueChange={(v) => probe.setSettings({ operator: v === "auto" ? null : v === "other" ? custom || null : v })}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="auto">Detect automatically{detected ? ` (${detected})` : ""}</SelectItem>
              {OPERATORS.map((o) => <SelectItem key={o} value={o}>{o}</SelectItem>)}
              <SelectItem value="other">Other…</SelectItem>
            </SelectContent>
          </Select>
          {opValue === "other" && (
            <Input placeholder="Operator name" value={custom} onChange={(e) => { setCustom(e.target.value); probe.setSettings({ operator: e.target.value.trim() || null }); }} />
          )}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label>Reading every</Label>
            <Select value={String(s.intervalS)} onValueChange={(v) => probe.setSettings({ intervalS: Number(v) })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>{[5, 10, 20, 30, 60].map((n) => <SelectItem key={n} value={String(n)}>{n} seconds</SelectItem>)}</SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Speed test every</Label>
            <Select value={String(s.speedtestS)} onValueChange={(v) => probe.setSettings({ speedtestS: Number(v) })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {[30, 60, 120, 300].map((n) => <SelectItem key={n} value={String(n)}>{n < 60 ? `${n} s` : `${n / 60} min`}</SelectItem>)}
                <SelectItem value="0">Never</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <label className="flex items-center justify-between gap-3 text-sm">
          <span>Data saver<span className="block text-xs text-muted-foreground">Skip speed tests; latency and connectivity are still measured.</span></span>
          <Switch checked={s.dataSaver} onCheckedChange={(v) => probe.setSettings({ dataSaver: v })} />
        </label>
        <p className="rounded-lg bg-muted px-3 py-2 text-xs text-muted-foreground">Estimated mobile data use: about {mbPerHour} MB per hour of measuring.</p>
      </div>

      <div className="space-y-3 rounded-2xl border bg-card p-4 text-sm">
        <p className="flex items-center gap-2 font-medium"><Smartphone className="h-4 w-4 text-primary" /> {meta.deviceName}</p>
        <div className="flex flex-col gap-2">
          <Button asChild variant="outline"><Link to="/app">Open the dashboard</Link></Button>
          <Button variant="outline" onClick={() => setConfirm(true)}><Unlink /> Unregister this phone</Button>
          <Button variant="ghost" onClick={onSignOut}><LogOut /> Sign out</Button>
        </div>
      </div>

      <AlertDialog open={confirm} onOpenChange={setConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Unregister this phone?</AlertDialogTitle>
            <AlertDialogDescription>
              {probe.queued > 0 ? `${probe.queued} readings have not been uploaded yet and will be kept until you register again. ` : ""}
              You can register it again at any time.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={onUnpair}>Unregister</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
