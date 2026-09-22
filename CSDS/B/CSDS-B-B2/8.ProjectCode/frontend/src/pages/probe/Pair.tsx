import { useState } from "react";
import { Smartphone } from "lucide-react";
import { toast } from "sonner";
import { LogoMark } from "@/components/brand/Logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, apiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { DeviceWithKey } from "@/lib/devices";
import { probeStore, type ProbeMeta } from "@/lib/probe/store";

function describeBrowser(): string {
  const ua = navigator.userAgent;
  const browser = /Edg\//.test(ua) ? "Edge" : /SamsungBrowser/.test(ua) ? "Samsung Internet" : /Chrome\//.test(ua) ? "Chrome" : /Firefox\//.test(ua) ? "Firefox" : /Safari\//.test(ua) ? "Safari" : "Browser";
  const os = /Android/.test(ua) ? "Android" : /iPhone|iPad/.test(ua) ? "iPhone" : /Windows/.test(ua) ? "Windows" : /Mac OS/.test(ua) ? "Mac" : "device";
  return `${browser} on ${os}`;
}

export function Pair({ onPaired }: { onPaired: (m: ProbeMeta) => void }) {
  const { user } = useAuth();
  const [name, setName] = useState(`${user?.name.split(" ")[0] ?? "My"}'s phone`);
  const [busy, setBusy] = useState(false);

  const pair = async () => {
    setBusy(true);
    try {
      const r = (await api.post<DeviceWithKey>("/api/devices/phone", { name: name.trim(), hardware: describeBrowser() })).data;
      const meta: ProbeMeta = { deviceKey: r.api_key, deviceId: r.device.id, deviceName: r.device.name, userId: user!.id };
      await probeStore.setMeta(meta);
      toast.success("Phone registered");
      onPaired(meta);
    } catch (e) {
      toast.error(apiError(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center px-6 py-10 text-center">
      <LogoMark className="h-14 w-14" />
      <h1 className="mt-5 text-2xl font-bold">Register this phone</h1>
      <p className="mt-2 max-w-sm text-sm text-muted-foreground">
        SignalScout will measure connectivity, latency and speed here and link the readings to your account. Readings are stored on the phone first, so nothing is lost without signal.
      </p>
      <div className="mt-8 w-full max-w-sm space-y-2 text-left">
        <Label htmlFor="phone-name">Phone name</Label>
        <Input id="phone-name" value={name} onChange={(e) => setName(e.target.value)} maxLength={120} />
        <p className="text-xs text-muted-foreground">Detected: {describeBrowser()}</p>
      </div>
      <Button size="lg" className="mt-6 w-full max-w-sm" onClick={pair} loading={busy} disabled={name.trim().length < 2}>
        <Smartphone /> Register and continue
      </Button>
    </div>
  );
}
