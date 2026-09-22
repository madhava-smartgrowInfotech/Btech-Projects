import { useQuery } from "@tanstack/react-query";
import { QRCodeSVG } from "qrcode.react";
import { Check, Copy, Globe, Laptop, Lock, RefreshCw, Router, Smartphone, WifiOff } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { EmptyState, ErrorState, PageHeader } from "@/components/common/states";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api, apiError, type ConnectInfo } from "@/lib/api";
import { timeAgo } from "@/lib/utils";

function CopyField({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="flex items-center gap-2 rounded-lg border bg-muted/50 p-1 pl-3">
      <code className="min-w-0 flex-1 truncate font-mono text-xs sm:text-sm">{value}</code>
      <Button
        size="sm"
        variant="ghost"
        aria-label="Copy link"
        onClick={async () => {
          try {
            await navigator.clipboard.writeText(value);
            setCopied(true);
            toast.success("Link copied");
            setTimeout(() => setCopied(false), 1500);
          } catch {
            toast.error("Copy is not available in this browser - select the link instead");
          }
        }}
      >
        {copied ? <Check /> : <Copy />}
      </Button>
    </div>
  );
}

export default function Connect() {
  const q = useQuery({
    queryKey: ["connect"],
    queryFn: async () => (await api.get<ConnectInfo>("/api/system/connect")).data,
    refetchInterval: (query) => (query.state.data?.tunnel_url ? 60_000 : 5_000),
  });
  const phoneUrl = q.data?.probe_url ?? null;

  return (
    <>
      <PageHeader
        title="Connect a phone"
        description="The field probe runs in the phone's browser. Phone browsers only allow GPS on secure (HTTPS) pages, so SignalScout opens a private HTTPS link to this computer."
        actions={
          <Button variant="outline" size="sm" onClick={() => q.refetch()} loading={q.isFetching}>
            <RefreshCw /> Refresh
          </Button>
        }
      />

      {q.isPending ? (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
          <Skeleton className="h-80" />
          <Skeleton className="h-80" />
        </div>
      ) : q.isError ? (
        <ErrorState message={apiError(q.error)} onRetry={() => q.refetch()} />
      ) : (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Smartphone className="h-4 w-4 text-primary" /> Scan with your phone
              </CardTitle>
              <CardDescription>Use the camera app on an Android phone, then open the link in Chrome.</CardDescription>
            </CardHeader>
            <CardContent>
              {phoneUrl ? (
                <div className="flex flex-col items-center gap-4">
                  <div className="rounded-2xl border bg-white p-4 shadow-sm">
                    <QRCodeSVG value={phoneUrl} size={208} level="M" marginSize={0} title="QR code with the HTTPS link to SignalScout" />
                  </div>
                  <div className="w-full">
                    <CopyField value={phoneUrl} />
                  </div>
                  <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <Lock className="h-3.5 w-3.5" aria-hidden /> Secure link, started {timeAgo(q.data.tunnel_started_at)}. It changes each time SignalScout restarts.
                  </p>
                </div>
              ) : (
                <EmptyState
                  icon={WifiOff}
                  title={q.data.tunnel_enabled ? "Waiting for the secure link…" : "Secure link is switched off"}
                  description={
                    q.data.tunnel_enabled
                      ? "run.bat opens it automatically a few seconds after start-up. This page checks every 5 seconds. If it never appears, see Troubleshooting in the documentation."
                      : "Set TUNNEL_ENABLED=true in .env and restart run.bat to use the phone probe."
                  }
                  className="border-0 bg-transparent py-6"
                />
              )}
            </CardContent>
          </Card>

          <div className="flex flex-col gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="h-4 w-4 text-primary" /> Before you start measuring
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ol className="space-y-3 text-sm">
                  {[
                    ["Turn on location", "Settings → Location on the phone, with high accuracy."],
                    ["Use mobile data, not Wi-Fi", "Switch Wi-Fi off so SignalScout measures your mobile network. Readings over Wi-Fi are tagged and kept separate."],
                    ["Keep the screen on", "Browsers pause pages when the screen is off; the probe keeps it awake while a session runs."],
                  ].map(([t, d], i) => (
                    <li key={t} className="flex gap-3">
                      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">{i + 1}</span>
                      <span>
                        <span className="font-medium">{t}</span>
                        <span className="block text-muted-foreground">{d}</span>
                      </span>
                    </li>
                  ))}
                </ol>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Router className="h-4 w-4 text-primary" /> On this network
                </CardTitle>
                <CardDescription>For ESP32 nodes and for opening the dashboard from another computer on the same Wi-Fi.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                {q.data.lan_api_urls.length ? (
                  <>
                    <div>
                      <p className="mb-1.5 flex items-center gap-2 font-medium">
                        API for ESP32 nodes <Badge variant="secondary">port {q.data.backend_port}</Badge>
                      </p>
                      {q.data.lan_api_urls.map((u) => (
                        <CopyField key={u} value={u} />
                      ))}
                    </div>
                    <div>
                      <p className="mb-1.5 flex items-center gap-2 font-medium">
                        <Laptop className="h-4 w-4" aria-hidden /> Dashboard <Badge variant="secondary">port {q.data.frontend_port}</Badge>
                      </p>
                      {q.data.lan_dashboard_urls.map((u) => (
                        <CopyField key={u} value={u} />
                      ))}
                    </div>
                  </>
                ) : (
                  <p className="text-muted-foreground">No network adapter found. Connect this computer to Wi-Fi or Ethernet.</p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </>
  );
}
