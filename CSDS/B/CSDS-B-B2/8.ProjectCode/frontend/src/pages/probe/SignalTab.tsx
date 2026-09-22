import { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "motion/react";
import { CircleCheck, Compass, ExternalLink, Navigation, RefreshCw, SearchX, WifiOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api, apiError } from "@/lib/api";
import { bearing, compass, nearestStrong, refreshPack } from "@/lib/probe/spots";
import { probeStore, type StrongSpotPack } from "@/lib/probe/store";
import type { ProbeController } from "@/lib/probe/useProbe";
import { timeAgo } from "@/lib/utils";

interface Suggestion {
  found: boolean;
  status: string;
  message: string;
  target: string;
  method: string;
  lat: number | null;
  lon: number | null;
  distance_m: number | null;
  bearing_deg: number | null;
  direction: string | null;
  predicted: number | null;
  predicted_mbps?: number;
  probability: number | null;
  supporting_readings: number;
  operator: string | null;
}

/** Phone heading from the compass (Chrome on Android); null when unavailable. */
function useHeading() {
  const [heading, setHeading] = useState<number | null>(null);
  useEffect(() => {
    const on = (e: DeviceOrientationEvent & { webkitCompassHeading?: number }) => {
      if (e.webkitCompassHeading != null) setHeading(e.webkitCompassHeading);
      else if (e.absolute && e.alpha != null) setHeading((360 - e.alpha) % 360);
    };
    window.addEventListener("deviceorientationabsolute" as "deviceorientation", on as EventListener);
    return () => window.removeEventListener("deviceorientationabsolute" as "deviceorientation", on as EventListener);
  }, []);
  return heading;
}

export function SignalTab({ probe }: { probe: ProbeController }) {
  const heading = useHeading();
  const [pos, setPos] = useState<[number, number] | null>(() => (probe.position ? [probe.position.coords.latitude, probe.position.coords.longitude] : null));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [online, setOnline] = useState<Suggestion | null>(null);
  const [pack, setPack] = useState<StrongSpotPack | null>(null);
  const operator = probe.settings.operator ?? probe.sync?.operator ?? probe.whoami?.carrier.operator ?? null;

  useEffect(() => {
    if (probe.position) setPos([probe.position.coords.latitude, probe.position.coords.longitude]);
  }, [probe.position]);
  useEffect(() => {
    if (pos || !navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((p) => setPos([p.coords.latitude, p.coords.longitude]), () => setError("Allow location to find better signal nearby."), { enableHighAccuracy: true, timeout: 15000 });
  }, [pos]);
  useEffect(() => {
    void probeStore.getPack().then((p) => setPack(p ?? null));
  }, []);

  const lookup = useCallback(async () => {
    if (!pos || !navigator.onLine) return;
    setLoading(true);
    setError(null);
    try {
      const params = { lat: pos[0], lon: pos[1], ...(operator ? { operator } : {}) };
      setOnline((await api.get<Suggestion>("/api/suggest", { params })).data);
      const next = await refreshPack(pos, operator, pack);
      if (next !== pack) setPack(next);
    } catch (e) {
      setError(apiError(e));
    } finally {
      setLoading(false);
    }
  }, [pos, operator, pack]);

  useEffect(() => {
    if (pos && probe.online) void lookup();
    // re-run when the phone moves roughly 100 m or comes back online
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pos ? Math.round(pos[0] * 1000) : null, pos ? Math.round(pos[1] * 1000) : null, probe.online]);

  // Offline: nearest predicted strong spot from the downloaded pack, or the nearest of this phone's own strong readings.
  const offline = useMemo(() => (pos ? nearestStrong(pos, pack, probe.records) : null), [pos, pack, probe.records]);

  const useOnline = probe.online && online;
  const target = useOnline && online.found && online.lat != null ? { lat: online.lat, lon: online.lon!, d: online.distance_m ?? 0 } : !probe.online && offline ? offline : null;
  const b = target && pos ? bearing(pos, [target.lat, target.lon]) : null;
  const arrow = b != null ? (heading != null ? b - heading : b) : 0;
  const osm = pos && target ? `https://www.openstreetmap.org/directions?engine=fossgis_osrm_foot&route=${pos[0]}%2C${pos[1]}%3B${target.lat}%2C${target.lon}` : null;

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border bg-card p-5 text-center">
        {!pos ? (
          <p className="py-10 text-sm text-muted-foreground">{error ?? "Getting your location…"}</p>
        ) : useOnline && online.status === "already_strong" ? (
          <div className="py-6">
            <CircleCheck className="mx-auto h-14 w-14 text-zone-strong" aria-hidden />
            <p className="mt-3 text-lg font-semibold">You're in a strong area</p>
            <p className="mt-1 text-sm text-muted-foreground">{online.message}</p>
          </div>
        ) : target && b != null ? (
          <>
            <div className="relative mx-auto h-48 w-48">
              <div className="absolute inset-0 rounded-full border-2 border-dashed border-border" aria-hidden />
              <span className="absolute left-1/2 top-1 -translate-x-1/2 text-xs font-semibold text-muted-foreground">{heading != null ? "ahead" : "N"}</span>
              <motion.div className="absolute inset-0 flex items-center justify-center" animate={{ rotate: arrow }} transition={{ type: "spring", stiffness: 60, damping: 14 }}>
                <Navigation className="h-24 w-24 fill-zone-strong text-zone-strong" style={{ transform: "rotate(-45deg)" }} aria-hidden />
              </motion.div>
            </div>
            <p className="mt-4 text-2xl font-bold tabular">{Math.round(target.d)} m <span className="text-primary">{compass(b)}</span></p>
            <p className="mt-1 text-sm text-muted-foreground">
              {useOnline
                ? online.message
                : `Offline: nearest ${offline?.kind} (from ${pack ? `the pack downloaded ${timeAgo(new Date(pack.fetched_at).toISOString())}` : "your readings"}).`}
            </p>
            {heading == null && <p className="mt-2 text-xs text-muted-foreground"><Compass className="mr-1 inline h-3.5 w-3.5" />Arrow points relative to north - face north to follow it.</p>}
            {osm && (
              <Button asChild variant="outline" size="sm" className="mt-4">
                <a href={osm} target="_blank" rel="noreferrer">Walking directions <ExternalLink /></a>
              </Button>
            )}
          </>
        ) : (
          <div className="py-8">
            {probe.online ? <SearchX className="mx-auto h-12 w-12 text-muted-foreground" aria-hidden /> : <WifiOff className="mx-auto h-12 w-12 text-muted-foreground" aria-hidden />}
            <p className="mt-3 font-semibold">{probe.online ? "No better spot found yet" : "Offline and no saved spots"}</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {probe.online ? online?.message ?? (loading ? "Looking…" : error ?? "") : "Open this tab once while online to save strong spots for offline use."}
            </p>
          </div>
        )}
      </div>

      {useOnline && online.found && online.status === "found" && (
        <div className="grid grid-cols-2 gap-2.5 text-sm">
          <div className="rounded-xl border bg-card p-3">
            <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Predicted there</p>
            <p className="mt-1 font-mono font-semibold">{online.target === "log_dl" ? `${online.predicted_mbps?.toFixed(1)} Mbps` : `${Math.round(online.predicted ?? 0)} dBm`}</p>
          </div>
          <div className="rounded-xl border bg-card p-3">
            <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Chance it's strong</p>
            <p className="mt-1 font-mono font-semibold">{Math.round((online.probability ?? 0) * 100)}%</p>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between gap-3 text-xs text-muted-foreground">
        <span>
          {operator ? `Operator: ${operator}` : "Operator detected after the first sync"}
          {pack && ` · ${pack.spots.length} strong spots saved for offline`}
        </span>
        <Button size="sm" variant="ghost" onClick={lookup} disabled={!probe.online || !pos} loading={loading}>
          <RefreshCw /> Update
        </Button>
      </div>
      <p className="text-center text-xs text-muted-foreground">Predicted by a Gaussian Process model from nearby readings of the same operator.</p>
    </div>
  );
}
