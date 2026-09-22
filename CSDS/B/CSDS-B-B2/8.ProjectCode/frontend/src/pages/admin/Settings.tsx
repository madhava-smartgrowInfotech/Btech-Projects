import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BellRing, CheckCircle2, Database, Link2, Send, SlidersHorizontal, Timer, XCircle } from "lucide-react";
import { toast } from "sonner";
import { ErrorState, PageHeader } from "@/components/common/states";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { api, apiError } from "@/lib/api";
import { formatDateTime, timeAgo } from "@/lib/utils";

interface SettingRow { key: string; value: number | boolean | string; default: number | boolean | string; type: string; min: number | null; max: number | null; description: string }
interface AdminSettings {
  settings: SettingRow[];
  channels: { telegram: { token: boolean; chat_id: string | null; ready: boolean }; email: { configured: boolean; from: string | null; desk_email: string | null; ready: boolean }; gemini: { configured: boolean; model: string }; opencellid: { configured: boolean } };
  sample_data: { state: string; readings: number };
  demo_preset: Record<string, number>;
}
interface NotificationRow { id: number; channel: string; recipient: string; subject: string; status: string; attempts: number; last_error: string | null; created_at: string; sent_at: string | null }

const GROUPS: { title: string; icon: typeof Timer; keys: string[] }[] = [
  { title: "Detection", icon: SlidersHorizontal, keys: ["detect_min_readings", "detect_window_min", "detect_bad_share", "detect_persist_min"] },
  { title: "Automatic verification", icon: Timer, keys: ["verify_min_readings", "verify_strong_share", "verify_reopen_share", "verify_timeout_days"] },
  { title: "Phone probe bands", icon: SlidersHorizontal, keys: ["probe_weak_rtt_ms", "probe_weak_dl_mbps"] },
];

function Channel({ ok, title, detail }: { ok: boolean; title: string; detail: string }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border p-3">
      {ok ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-zone-strong" /> : <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />}
      <div className="min-w-0">
        <p className="text-sm font-medium">{title}</p>
        <p className="break-words text-xs text-muted-foreground">{detail}</p>
      </div>
    </div>
  );
}

export default function AdminSettings() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["admin-settings"], queryFn: async () => (await api.get<AdminSettings>("/api/admin/settings")).data });
  const notes = useQuery({ queryKey: ["admin-notifications"], queryFn: async () => (await api.get<NotificationRow[]>("/api/admin/notifications")).data, refetchInterval: 15_000 });
  const [draft, setDraft] = useState<Record<string, string | boolean>>({});
  const [confirmRemove, setConfirmRemove] = useState(false);
  useEffect(() => {
    if (q.data) setDraft(Object.fromEntries(q.data.settings.map((s) => [s.key, typeof s.value === "boolean" ? s.value : String(s.value)])));
  }, [q.data]);

  const done = (d: AdminSettings, msg: string) => { qc.setQueryData(["admin-settings"], d); toast.success(msg); };
  const save = useMutation({
    mutationFn: async (changes: Record<string, unknown>) => (await api.put<AdminSettings>("/api/admin/settings", changes)).data,
    onSuccess: (d) => done(d, "Settings saved"),
    onError: (e) => toast.error(apiError(e)),
  });
  const preset = useMutation({
    mutationFn: async (name: string) => (await api.post<AdminSettings>(`/api/admin/settings/preset/${name}`)).data,
    onSuccess: (d, name) => done(d, name === "demo" ? "Demo thresholds applied - complaints register after about 2 minutes" : "Standard thresholds restored"),
    onError: (e) => toast.error(apiError(e)),
  });
  const test = useMutation({
    mutationFn: async () => (await api.post<{ channel: string; ok: boolean; detail: string }[]>("/api/admin/notifications/test")).data,
    onSuccess: (rows) => rows.forEach((r) => (r.ok ? toast.success(`${r.channel}: ${r.detail}`) : toast.error(`${r.channel}: ${r.detail}`))),
    onError: (e) => toast.error(apiError(e)),
  });
  const link = useMutation({
    mutationFn: async () => (await api.post<{ ok: boolean; detail: string }>("/api/admin/telegram/link")).data,
    onSuccess: (r) => { (r.ok ? toast.success : toast.error)(r.detail); qc.invalidateQueries({ queryKey: ["admin-settings"] }); },
    onError: (e) => toast.error(apiError(e)),
  });
  const sample = useMutation({
    mutationFn: async (remove: boolean) => (remove ? (await api.delete("/api/admin/sample-data")).data : (await api.post("/api/admin/sample-data")).data),
    onSuccess: (_, remove) => { toast.success(remove ? "Sample data removed" : "Loading sample data…"); qc.invalidateQueries(); },
    onError: (e) => toast.error(apiError(e)),
  });

  if (q.isPending) return <div className="space-y-4"><Skeleton className="h-10 w-60" /><Skeleton className="h-64" /></div>;
  if (q.isError) return <ErrorState message={apiError(q.error)} onRetry={() => q.refetch()} />;
  const byKey = Object.fromEntries(q.data.settings.map((s) => [s.key, s]));
  const changed = q.data.settings.filter((s) => s.type !== "bool" && s.type !== "str" && String(s.value) !== draft[s.key]);
  const ch = q.data.channels;

  return (
    <>
      <PageHeader title="Settings" description="How SignalScout judges zones, raises and verifies complaints, and who gets told."
        actions={<>
          <Button variant="outline" onClick={() => preset.mutate("standard")} loading={preset.isPending && preset.variables === "standard"}>Standard thresholds</Button>
          <Button onClick={() => preset.mutate("demo")} loading={preset.isPending && preset.variables === "demo"}>Demo thresholds</Button>
        </>} />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Zone and complaint rules</CardTitle>
            <CardDescription>Demo thresholds register a complaint after about 2 minutes in a dead zone, for live demonstrations. Standard thresholds suit day-to-day monitoring.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {GROUPS.map((g) => (
              <div key={g.title}>
                <p className="mb-3 flex items-center gap-2 text-sm font-semibold"><g.icon className="h-4 w-4 text-primary" /> {g.title}</p>
                <div className="grid gap-3 sm:grid-cols-2">
                  {g.keys.map((k) => {
                    const s = byKey[k]!;
                    return (
                      <div key={k} className="space-y-1.5">
                        <Label htmlFor={k} className="text-xs">{s.description}</Label>
                        <Input id={k} inputMode="decimal" value={String(draft[k] ?? "")} onChange={(e) => setDraft({ ...draft, [k]: e.target.value })} />
                        <p className="text-[11px] text-muted-foreground">Default {String(s.default)}{s.min != null ? ` · ${s.min}–${s.max}` : ""}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
            <div className="flex gap-2">
              <Button disabled={!changed.length} loading={save.isPending}
                onClick={() => save.mutate(Object.fromEntries(changed.map((s) => [s.key, Number(draft[s.key])])))}>
                Save {changed.length ? `(${changed.length})` : ""}
              </Button>
              {changed.length > 0 && <Button variant="ghost" onClick={() => setDraft(Object.fromEntries(q.data.settings.map((s) => [s.key, typeof s.value === "boolean" ? s.value : String(s.value)])))}>Undo</Button>}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><BellRing className="h-4 w-4 text-primary" /> Notifications</CardTitle>
              <CardDescription>New, reopened and verified complaints go to the desk. Reporters with email updates on hear about every change.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Channel ok={ch.telegram.ready} title="Telegram desk chat"
                detail={!ch.telegram.token ? "Add TELEGRAM_BOT_TOKEN to .env" : ch.telegram.chat_id ? `Chat ${ch.telegram.chat_id}` : "Bot ready - send it a message in Telegram, then link the chat"} />
              <Channel ok={ch.email.ready} title="Email (Gmail SMTP)"
                detail={ch.email.configured ? `From ${ch.email.from} to ${ch.email.desk_email ?? ch.email.from}` : "Add SMTP_USER and SMTP_PASSWORD (Gmail app password) to .env"} />
              <div className="flex items-center justify-between gap-3 text-sm">
                <span>Send to Telegram</span>
                <Switch aria-label="Send to Telegram" checked={Boolean(draft.notify_telegram)} onCheckedChange={(v) => { setDraft({ ...draft, notify_telegram: v }); save.mutate({ notify_telegram: v }); }} />
              </div>
              <div className="flex items-center justify-between gap-3 text-sm">
                <span>Send email</span>
                <Switch aria-label="Send email" checked={Boolean(draft.notify_email)} onCheckedChange={(v) => { setDraft({ ...draft, notify_email: v }); save.mutate({ notify_email: v }); }} />
              </div>
              <div className="flex flex-wrap gap-2 pt-1">
                <Button variant="outline" onClick={() => link.mutate()} loading={link.isPending} disabled={!ch.telegram.token}><Link2 /> Link Telegram chat</Button>
                <Button variant="outline" onClick={() => test.mutate()} loading={test.isPending}><Send /> Send test</Button>
              </div>
              <p className="text-xs text-muted-foreground">Optional services: complaint text by Gemini {ch.gemini.configured ? `on (${ch.gemini.model})` : "off - template text is used"} · OpenCelliD tower lookup {ch.opencellid.configured ? "on" : "off"}.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Database className="h-4 w-4 text-primary" /> Sample data</CardTitle>
              <CardDescription>Public drive-test traces replayed through the real pipeline on first start, tagged "Sample".</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap items-center gap-3 text-sm">
              <Badge variant="secondary">{q.data.sample_data.state === "done" ? `${q.data.sample_data.readings.toLocaleString()} readings loaded` : q.data.sample_data.state}</Badge>
              <Button variant="outline" size="sm" onClick={() => setConfirmRemove(true)}>Remove sample data</Button>
              <Button variant="ghost" size="sm" onClick={() => sample.mutate(false)}>Load again</Button>
            </CardContent>
          </Card>
        </div>
      </div>

      <Card className="mt-4">
        <CardHeader><CardTitle>Recent notifications</CardTitle></CardHeader>
        <CardContent>
          {!notes.data?.length ? (
            <p className="text-sm text-muted-foreground">None yet. They appear here when complaints are registered, reopened or verified.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-sm">
                <thead className="text-left text-xs text-muted-foreground">
                  <tr><th className="py-2 font-medium">When</th><th className="font-medium">Channel</th><th className="font-medium">To</th><th className="font-medium">Subject</th><th className="font-medium">Status</th></tr>
                </thead>
                <tbody className="divide-y">
                  {notes.data.map((n) => (
                    <tr key={n.id}>
                      <td className="py-2" title={formatDateTime(n.created_at)}>{timeAgo(n.created_at)}</td>
                      <td className="capitalize">{n.channel}</td>
                      <td className="max-w-[160px] truncate">{n.recipient}</td>
                      <td className="max-w-[260px] truncate">{n.subject}</td>
                      <td>
                        <Badge variant={n.status === "sent" ? "success" : n.status === "failed" ? "destructive" : "warning"} title={n.last_error ?? undefined}>
                          {n.status}{n.status === "pending" && n.attempts ? ` (retry ${n.attempts})` : ""}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <AlertDialog open={confirmRemove} onOpenChange={setConfirmRemove}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove the sample data?</AlertDialogTitle>
            <AlertDialogDescription>All replayed public-dataset readings and the complaints they produced are deleted. Your own readings are kept. You can load the sample again later.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction destructive onClick={() => sample.mutate(true)}>Remove</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
