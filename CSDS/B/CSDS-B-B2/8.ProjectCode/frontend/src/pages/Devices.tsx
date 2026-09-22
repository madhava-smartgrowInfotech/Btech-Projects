import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Copy, Cpu, History, KeyRound, MoreVertical, Pencil, Plus, Power, Smartphone, Trash2, Wifi } from "lucide-react";
import { toast } from "sonner";
import { EmptyState, ErrorState, PageHeader } from "@/components/common/states";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { api, apiError, hasRole, type ConnectInfo } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { KIND_LABEL, type Device, type DeviceWithKey, type SyncBatch } from "@/lib/devices";
import { formatDateTime, formatNumber, timeAgo } from "@/lib/utils";

const ICON = { phone: Smartphone, esp32: Cpu, simulator: Wifi, replay: History } as const;

function KeyReveal({ result, apiUrl, onClose }: { result: DeviceWithKey | null; apiUrl?: string; onClose: () => void }) {
  const [copied, setCopied] = useState<string | null>(null);
  const copy = async (text: string, what: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(what);
      setTimeout(() => setCopied(null), 1500);
    } catch {
      toast.error("Copy is not available - select the text instead");
    }
  };
  if (!result) return null;
  const isNode = result.device.kind === "esp32";
  const snippet = `#define SS_API_URL   "${apiUrl ?? "http://<this-pc-ip>:8202"}"\n#define SS_DEVICE_KEY "${result.api_key}"`;
  return (
    <Dialog open onOpenChange={(o) => !o && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Device key for {result.device.name}</DialogTitle>
          <DialogDescription>Copy it now - for security it is shown only once. You can create a new key at any time.</DialogDescription>
        </DialogHeader>
        <div className="flex items-center gap-2 rounded-lg border bg-muted/50 p-1 pl-3">
          <code className="min-w-0 flex-1 break-all font-mono text-xs">{result.api_key}</code>
          <Button size="sm" variant="ghost" onClick={() => copy(result.api_key, "key")} aria-label="Copy key">
            {copied === "key" ? <Check /> : <Copy />}
          </Button>
        </div>
        {isNode && (
          <div className="space-y-2">
            <p className="text-sm font-medium">For the firmware - paste into firmware/esp32_node/config.h</p>
            <pre className="overflow-x-auto rounded-lg border bg-muted/50 p-3 font-mono text-xs">{snippet}</pre>
            <Button size="sm" variant="outline" onClick={() => copy(snippet, "snippet")}>
              {copied === "snippet" ? <Check /> : <Copy />} Copy config lines
            </Button>
          </div>
        )}
        <DialogFooter>
          <Button onClick={onClose}>Done</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function AddNodeDialog({ open, onOpenChange, onCreated }: { open: boolean; onOpenChange: (o: boolean) => void; onCreated: (r: DeviceWithKey) => void }) {
  const [form, setForm] = useState({ name: "", network_name: "", lat: "", lon: "" });
  const create = useMutation({
    mutationFn: async () =>
      (await api.post<DeviceWithKey>("/api/devices", {
        kind: "esp32",
        name: form.name.trim(),
        network_name: form.network_name.trim() || null,
        fixed_lat: form.lat ? Number(form.lat) : null,
        fixed_lon: form.lon ? Number(form.lon) : null,
      })).data,
    onSuccess: (r) => {
      onCreated(r);
      onOpenChange(false);
      setForm({ name: "", network_name: "", lat: "", lon: "" });
    },
    onError: (e) => toast.error(apiError(e)),
  });
  const coordsBad = (form.lat === "") !== (form.lon === "") || (form.lat !== "" && (Math.abs(Number(form.lat)) > 90 || Math.abs(Number(form.lon)) > 180 || Number.isNaN(Number(form.lat)) || Number.isNaN(Number(form.lon))));
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add an ESP32 sensor node</DialogTitle>
          <DialogDescription>The node reports Wi-Fi and Bluetooth signal, latency and loss. Give it a fixed position if it has no GPS module.</DialogDescription>
        </DialogHeader>
        <form
          className="space-y-3"
          onSubmit={(e: FormEvent) => {
            e.preventDefault();
            create.mutate();
          }}
        >
          <div className="space-y-1.5">
            <Label htmlFor="n-name">Name</Label>
            <Input id="n-name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Market square node" required />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="n-net">Network it monitors</Label>
            <Input id="n-net" value={form.network_name} onChange={(e) => setForm({ ...form, network_name: e.target.value })} placeholder="Market square Wi-Fi" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="n-lat">Latitude</Label>
              <Input id="n-lat" inputMode="decimal" value={form.lat} onChange={(e) => setForm({ ...form, lat: e.target.value })} placeholder="17.4485" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="n-lon">Longitude</Label>
              <Input id="n-lon" inputMode="decimal" value={form.lon} onChange={(e) => setForm({ ...form, lon: e.target.value })} placeholder="78.3908" />
            </div>
          </div>
          {coordsBad && <p className="text-xs text-destructive">Enter both latitude and longitude, or leave both empty (GPS module).</p>}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" loading={create.isPending} disabled={form.name.trim().length < 2 || coordsBad}>Create node</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function SyncHistory({ device, onClose }: { device: Device | null; onClose: () => void }) {
  const q = useQuery({ queryKey: ["sync", device?.id], enabled: !!device, queryFn: async () => (await api.get<SyncBatch[]>(`/api/devices/${device!.id}/sync`)).data });
  return (
    <Dialog open={!!device} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>Sync history - {device?.name}</DialogTitle>
          <DialogDescription>Each upload from the device. Duplicates are readings re-sent after a lost reply; they are ignored safely.</DialogDescription>
        </DialogHeader>
        {q.isPending ? (
          <Skeleton className="h-40" />
        ) : q.isError ? (
          <ErrorState message={apiError(q.error)} onRetry={() => q.refetch()} />
        ) : q.data.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">No uploads yet.</p>
        ) : (
          <div className="max-h-80 overflow-y-auto rounded-lg border">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-muted text-xs text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 text-left font-medium">When</th>
                  <th className="px-3 py-2 text-right font-medium">Accepted</th>
                  <th className="px-3 py-2 text-right font-medium">Duplicates</th>
                  <th className="px-3 py-2 text-right font-medium">Rejected</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {q.data.map((b) => (
                  <tr key={b.id}>
                    <td className="px-3 py-2" title={formatDateTime(b.ts)}>
                      {timeAgo(b.ts)}
                      {b.oldest_reading && b.accepted > 1 && <span className="block text-xs text-muted-foreground">oldest reading {timeAgo(b.oldest_reading)}</span>}
                    </td>
                    <td className="px-3 py-2 text-right tabular">{b.accepted}</td>
                    <td className="px-3 py-2 text-right tabular">{b.duplicates}</td>
                    <td className="px-3 py-2 text-right tabular">{b.rejected}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default function Devices() {
  const qc = useQueryClient();
  const { user } = useAuth();
  const devices = useQuery({ queryKey: ["devices"], queryFn: async () => (await api.get<Device[]>("/api/devices")).data, refetchInterval: 20_000 });
  const connect = useQuery({ queryKey: ["connect"], queryFn: async () => (await api.get<ConnectInfo>("/api/system/connect")).data });
  const [adding, setAdding] = useState(false);
  const [revealed, setRevealed] = useState<DeviceWithKey | null>(null);
  const [renaming, setRenaming] = useState<Device | null>(null);
  const [newName, setNewName] = useState("");
  const [confirm, setConfirm] = useState<{ device: Device; action: "rotate" | "delete" } | null>(null);
  const [history, setHistory] = useState<Device | null>(null);

  const refresh = () => qc.invalidateQueries({ queryKey: ["devices"] });
  const patch = useMutation({
    mutationFn: async ({ id, body }: { id: number; body: Record<string, unknown> }) => (await api.patch<Device>(`/api/devices/${id}`, body)).data,
    onSuccess: () => refresh(),
    onError: (e) => toast.error(apiError(e)),
  });
  const rotate = useMutation({
    mutationFn: async (id: number) => (await api.post<DeviceWithKey>(`/api/devices/${id}/rotate-key`)).data,
    onSuccess: (r) => {
      setRevealed(r);
      refresh();
    },
    onError: (e) => toast.error(apiError(e)),
  });
  const remove = useMutation({
    mutationFn: async (id: number) => api.delete(`/api/devices/${id}`),
    onSuccess: () => {
      toast.success("Device removed");
      refresh();
    },
    onError: (e) => toast.error(apiError(e)),
  });

  const list = devices.data ?? [];
  const groups: { title: string; items: Device[] }[] = [
    { title: "Phones", items: list.filter((d) => d.kind === "phone") },
    { title: "Sensor nodes", items: list.filter((d) => d.kind === "esp32" || d.kind === "simulator") },
    { title: "Sample data", items: list.filter((d) => d.kind === "replay") },
  ].filter((g) => g.items.length);

  return (
    <>
      <PageHeader
        title="Devices"
        description={hasRole(user, "engineer") ? "Every phone probe and sensor node reporting to this installation." : "Your phones. Each phone probe registers itself when you sign in on it."}
        actions={
          <>
            <Button asChild variant="outline">
              <Link to="/app/connect">
                <Smartphone /> Connect a phone
              </Link>
            </Button>
            <Button onClick={() => setAdding(true)}>
              <Plus /> Add ESP32 node
            </Button>
          </>
        }
      />

      {devices.isPending ? (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-40" />
          ))}
        </div>
      ) : devices.isError ? (
        <ErrorState message={apiError(devices.error)} onRetry={() => devices.refetch()} />
      ) : list.length === 0 ? (
        <EmptyState
          icon={Smartphone}
          title="No devices yet"
          description="Open the phone probe on your phone to register it, or add an ESP32 sensor node."
          action={
            <Button asChild>
              <Link to="/app/connect">Connect a phone</Link>
            </Button>
          }
        />
      ) : (
        <div className="space-y-8">
          {groups.map((g) => (
            <section key={g.title}>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                {g.title} <span className="font-normal">({g.items.length})</span>
              </h2>
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {g.items.map((d) => {
                  const Icon = ICON[d.kind];
                  const network = typeof d.config?.network_name === "string" ? d.config.network_name : null;
                  return (
                    <Card key={d.id} className={d.is_active ? "p-4" : "p-4 opacity-60"}>
                      <div className="flex items-start gap-3">
                        <div className="relative rounded-lg bg-primary/10 p-2 text-primary">
                          <Icon className="h-5 w-5" aria-hidden />
                          {d.kind !== "replay" && (
                            <span className={`absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full ring-2 ring-card ${d.online ? "bg-zone-strong" : "bg-muted-foreground/50"}`} aria-hidden />
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="truncate font-medium">{d.name}</p>
                          <p className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
                            <Badge variant={d.kind === "replay" ? "secondary" : "outline"}>{KIND_LABEL[d.kind]}</Badge>
                            {d.kind !== "replay" && <span>{d.online ? "Online" : `Last seen ${timeAgo(d.last_seen_at)}`}</span>}
                            {!d.is_active && <Badge variant="destructive">Paused</Badge>}
                          </p>
                        </div>
                        {d.kind !== "replay" && (
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button size="icon" variant="ghost" className="h-8 w-8" aria-label={`Actions for ${d.name}`}>
                                <MoreVertical />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onSelect={() => setHistory(d)}>
                                <History /> Sync history
                              </DropdownMenuItem>
                              <DropdownMenuItem onSelect={() => { setRenaming(d); setNewName(d.name); }}>
                                <Pencil /> Rename
                              </DropdownMenuItem>
                              <DropdownMenuItem onSelect={() => setConfirm({ device: d, action: "rotate" })}>
                                <KeyRound /> New device key
                              </DropdownMenuItem>
                              <DropdownMenuItem onSelect={() => patch.mutate({ id: d.id, body: { is_active: !d.is_active } })}>
                                <Power /> {d.is_active ? "Pause uploads" : "Resume uploads"}
                              </DropdownMenuItem>
                              {d.kind !== "simulator" && (
                                <>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem className="text-destructive focus:text-destructive" onSelect={() => setConfirm({ device: d, action: "delete" })}>
                                    <Trash2 /> Remove device
                                  </DropdownMenuItem>
                                </>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        )}
                      </div>
                      <dl className="mt-4 grid grid-cols-2 gap-x-3 gap-y-2 text-xs">
                        <div>
                          <dt className="text-muted-foreground">Readings</dt>
                          <dd className="font-medium tabular">{formatNumber(d.readings_count)}</dd>
                        </div>
                        <div>
                          <dt className="text-muted-foreground">Last sync</dt>
                          <dd className="font-medium" title={formatDateTime(d.last_sync_at)}>{timeAgo(d.last_sync_at)}</dd>
                        </div>
                        {network && (
                          <div className="col-span-2">
                            <dt className="text-muted-foreground">Monitors</dt>
                            <dd className="font-medium">{network}</dd>
                          </div>
                        )}
                        {(d.hardware || d.firmware) && (
                          <div className="col-span-2">
                            <dt className="text-muted-foreground">Hardware</dt>
                            <dd className="truncate font-medium">{[d.hardware, d.firmware && `firmware ${d.firmware}`].filter(Boolean).join(" · ")}</dd>
                          </div>
                        )}
                        {d.fixed_lat != null && (
                          <div className="col-span-2">
                            <dt className="text-muted-foreground">Fixed position</dt>
                            <dd className="font-mono tabular">{d.fixed_lat.toFixed(5)}, {d.fixed_lon?.toFixed(5)}</dd>
                          </div>
                        )}
                        {hasRole(user, "engineer") && d.owner_name && (
                          <div className="col-span-2">
                            <dt className="text-muted-foreground">Owner</dt>
                            <dd className="font-medium">{d.owner_name}</dd>
                          </div>
                        )}
                      </dl>
                      {d.kind !== "replay" && <p className="mt-3 font-mono text-[11px] text-muted-foreground">key {d.api_key_prefix}…</p>}
                    </Card>
                  );
                })}
              </div>
            </section>
          ))}
        </div>
      )}

      <AddNodeDialog open={adding} onOpenChange={setAdding} onCreated={(r) => { setRevealed(r); refresh(); }} />
      <KeyReveal result={revealed} apiUrl={connect.data?.lan_api_urls[0]} onClose={() => setRevealed(null)} />
      <SyncHistory device={history} onClose={() => setHistory(null)} />

      <Dialog open={!!renaming} onOpenChange={(o) => !o && setRenaming(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename device</DialogTitle>
          </DialogHeader>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (renaming) patch.mutate({ id: renaming.id, body: { name: newName.trim() } }, { onSuccess: () => { toast.success("Renamed"); setRenaming(null); } });
            }}
            className="space-y-4"
          >
            <Input value={newName} onChange={(e) => setNewName(e.target.value)} aria-label="Device name" autoFocus />
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setRenaming(null)}>Cancel</Button>
              <Button type="submit" disabled={newName.trim().length < 2} loading={patch.isPending}>Save</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!confirm} onOpenChange={(o) => !o && setConfirm(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirm?.action === "rotate" ? `New key for ${confirm.device.name}?` : `Remove ${confirm?.device.name}?`}</AlertDialogTitle>
            <AlertDialogDescription>
              {confirm?.action === "rotate"
                ? "The old key stops working immediately. You will need to enter the new key on the device."
                : "The device and all of its readings are deleted. This cannot be undone."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              destructive={confirm?.action === "delete"}
              onClick={() => {
                if (!confirm) return;
                if (confirm.action === "rotate") rotate.mutate(confirm.device.id);
                else remove.mutate(confirm.device.id);
                setConfirm(null);
              }}
            >
              {confirm?.action === "rotate" ? "Create new key" : "Remove device"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
