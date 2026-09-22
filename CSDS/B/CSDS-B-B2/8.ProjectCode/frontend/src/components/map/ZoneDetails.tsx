import type { ReactNode } from "react";
import { Clock, Gauge, Radio, Wifi } from "lucide-react";
import { ZoneBadge, ZoneBar } from "@/components/common/zone";
import { Badge } from "@/components/ui/badge";
import type { HexProps } from "@/lib/coverage";
import { formatDateTime, timeAgo } from "@/lib/utils";
import { SOURCE_LABEL } from "@/lib/zones";

function Metric({ icon: Icon, label, value }: { icon: typeof Clock; label: string; value: string }) {
  return (
    <div className="rounded-lg border bg-muted/40 p-2.5">
      <p className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        <Icon className="h-3.5 w-3.5" aria-hidden /> {label}
      </p>
      <p className="mt-0.5 font-mono text-sm tabular">{value}</p>
    </div>
  );
}

export function ZoneDetails({ zone, actions }: { zone: HexProps; actions?: ReactNode }) {
  const metrics: [typeof Clock, string, string][] = [];
  if (zone.median_rsrp != null) metrics.push([Radio, "Median RSRP", `${Math.round(zone.median_rsrp)} dBm`]);
  if (zone.median_latency != null) metrics.push([Clock, "Median latency", `${Math.round(zone.median_latency)} ms`]);
  if (zone.median_dl != null) metrics.push([Gauge, "Median download", `${zone.median_dl.toFixed(1)} Mbps`]);
  if (zone.median_wifi_rssi != null) metrics.push([Wifi, "Median Wi-Fi", `${Math.round(zone.median_wifi_rssi)} dBm`]);

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs text-muted-foreground">Zone {zone.cell}</p>
          <p className="mt-1 text-sm">
            <span className="font-semibold tabular">{zone.n.toLocaleString()}</span> readings · last {timeAgo(zone.last_ts)}
          </p>
        </div>
        <ZoneBadge label={zone.label} className="text-sm" />
      </div>
      <ZoneBar strong={zone.strong} weak={zone.weak} dead={zone.dead} />
      {metrics.length > 0 && (
        <div className="grid grid-cols-2 gap-2">
          {metrics.map(([icon, label, value]) => (
            <Metric key={label} icon={icon} label={label} value={value} />
          ))}
        </div>
      )}
      <div>
        <p className="mb-1.5 text-xs font-medium text-muted-foreground">By operator</p>
        <ul className="divide-y rounded-lg border">
          {Object.entries(zone.operators)
            .sort((a, b) => b[1].n - a[1].n)
            .map(([op, v]) => (
              <li key={op} className="flex items-center justify-between gap-2 px-3 py-2 text-sm">
                <span className="truncate">{op}</span>
                <span className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground tabular">{v.n}</span>
                  <ZoneBadge label={v.label} />
                </span>
              </li>
            ))}
        </ul>
      </div>
      <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
        {zone.sources.map((s) => (
          <Badge key={s} variant={s === "sample_dataset" ? "secondary" : "outline"}>
            {SOURCE_LABEL[s] ?? s}
          </Badge>
        ))}
        <span title={formatDateTime(zone.last_ts)}>· median confidence {zone.confidence != null ? `${Math.round(zone.confidence * 100)}%` : "–"}</span>
      </div>
      {actions}
    </div>
  );
}
