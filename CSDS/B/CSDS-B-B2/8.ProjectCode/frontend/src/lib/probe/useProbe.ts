import { useCallback, useEffect, useRef, useState } from "react";
import { provisionalClass } from "./classify";
import { connectionHints, downloadTest, pingProbes, uploadTest } from "./measure";
import { probeStore, type ProbeMeta, type ProbeRecord, type SyncState } from "./store";
import { flushQueue } from "./sync-core";
import { safeStorage } from "@/lib/utils";

export interface ProbeSettings {
  operator: string | null;       // manual override; null = detect automatically
  intervalS: number;
  speedtestS: number;            // 0 = never
  dataSaver: boolean;
}

export interface WhoAmI {
  device: { id: number; name: string };
  carrier: { operator: string | null; network_name: string | null; asn: number | null; kind: string; ip: string | null };
  config: { interval_s: number; speedtest_interval_s: number; speedtest_max_bytes: number; weak_rtt_ms: number; weak_dl_mbps: number };
}

const SETTINGS_KEY = "signalscout-probe-settings";
export const DEFAULT_SETTINGS: ProbeSettings = { operator: null, intervalS: 10, speedtestS: 60, dataSaver: false };

export function loadSettings(): ProbeSettings {
  try {
    return { ...DEFAULT_SETTINGS, ...JSON.parse(safeStorage.get(SETTINGS_KEY) || "{}") };
  } catch {
    return DEFAULT_SETTINGS;
  }
}

async function registerBackgroundSync() {
  try {
    if (!("serviceWorker" in navigator)) return;
    const reg = await Promise.race([navigator.serviceWorker.ready, new Promise<null>((r) => setTimeout(() => r(null), 1500))]);
    const sync = (reg as unknown as { sync?: { register(tag: string): Promise<void> } } | null)?.sync;
    await sync?.register("probe-sync");
  } catch {
    /* Background Sync not supported - the page retries while it is open */
  }
}

export function useProbe(meta: ProbeMeta | null) {
  const [settings, setSettingsState] = useState<ProbeSettings>(loadSettings);
  const [running, setRunning] = useState(false);
  const [position, setPosition] = useState<GeolocationPosition | null>(null);
  const [gpsError, setGpsError] = useState<string | null>(null);
  const [awake, setAwake] = useState(false);
  const [online, setOnline] = useState(() => navigator.onLine);
  const [measuring, setMeasuring] = useState(false);
  const [phase, setPhase] = useState<string>("");
  const [last, setLast] = useState<ProbeRecord | null>(null);
  const [records, setRecords] = useState<ProbeRecord[]>([]);
  const [sync, setSync] = useState<SyncState | null>(null);
  const [nextAt, setNextAt] = useState<number | null>(null);
  const [whoami, setWhoami] = useState<WhoAmI | null>(null);
  const [needsPairing, setNeedsPairing] = useState(false);

  const posRef = useRef<GeolocationPosition | null>(null);
  const watchRef = useRef<number | null>(null);
  const wakeRef = useRef<WakeLockSentinel | null>(null);
  const timerRef = useRef<number | null>(null);
  const runningRef = useRef(false);
  const lastSpeedRef = useRef(0);
  const dlBytesRef = useRef(250_000);
  const settingsRef = useRef(settings);
  settingsRef.current = settings;
  const whoRef = useRef<WhoAmI | null>(null);
  whoRef.current = whoami;

  const refresh = useCallback(async () => {
    const all = await probeStore.all();
    setRecords(all);
    setSync(await probeStore.getSync());
    if (all.length) setLast((prev) => (prev ? all.find((r) => r.reading.client_uuid === prev.reading.client_uuid) ?? all[0]! : all[0]!));
  }, []);

  const doSync = useCallback(async () => {
    if (!navigator.onLine) return;
    const out = await flushQueue();
    if (out.unauthorized) setNeedsPairing(true);
    await refresh();
    return out;
  }, [refresh]);

  const loadWhoami = useCallback(async () => {
    if (!meta || !navigator.onLine) return;
    try {
      const res = await fetch("/api/probe/whoami", { headers: { "X-Device-Key": meta.deviceKey }, cache: "no-store" });
      if (res.status === 401) return setNeedsPairing(true);
      if (res.ok) setWhoami(await res.json());
    } catch {
      /* offline */
    }
  }, [meta]);

  const measure = useCallback(async () => {
    if (!meta || !runningRef.current) return;
    const s = settingsRef.current;
    const pos = posRef.current;
    if (!pos) {
      setPhase("Waiting for a GPS fix…");
      timerRef.current = window.setTimeout(measure, 3000);
      setNextAt(Date.now() + 3000);
      return;
    }
    setMeasuring(true);
    const isOnline = navigator.onLine;
    const hints = connectionHints();
    let ping = { sent: 0, ok: 0, rttMs: null as number | null, jitterMs: null as number | null };
    let dl: number | null = null;
    let ul: number | null = null;
    try {
      if (isOnline) {
        setPhase("Measuring latency…");
        ping = await pingProbes(3, 3000);
        const cfg = whoRef.current?.config;
        const due = s.speedtestS > 0 && !s.dataSaver && Date.now() - lastSpeedRef.current >= s.speedtestS * 1000;
        if (ping.ok > 0 && due) {
          setPhase("Testing download speed…");
          const r = await downloadTest(meta.deviceKey, dlBytesRef.current, ping.rttMs);
          if (r) {
            dl = Math.round(r.mbps * 100) / 100;
            const max = cfg?.speedtest_max_bytes ?? 1_000_000;
            dlBytesRef.current = r.ms < 1000 ? Math.min(dlBytesRef.current * 2, max) : r.ms > 4000 ? Math.max(Math.round(dlBytesRef.current / 2), 100_000) : dlBytesRef.current;
          }
          setPhase("Testing upload speed…");
          const u = await uploadTest(meta.deviceKey, 200_000, ping.rttMs);
          ul = u != null ? Math.round(u * 100) / 100 : null;
          lastSpeedRef.current = Date.now();
        }
      } else {
        ping = { sent: 3, ok: 0, rttMs: null, jitterMs: null };
      }
      const reading = {
        client_uuid: crypto.randomUUID(),
        ts: new Date().toISOString(),
        lat: pos.coords.latitude,
        lon: pos.coords.longitude,
        accuracy_m: pos.coords.accuracy != null ? Math.round(pos.coords.accuracy) : null,
        ...(s.operator ? { operator: s.operator } : {}),
        ...(hints.type ? { connection_type: hints.type } : {}),
        ...(hints.effectiveType ? { effective_type: hints.effectiveType } : {}),
        ...(hints.downlink != null ? { downlink_est: hints.downlink } : {}),
        ...(hints.rtt != null ? { rtt_est: hints.rtt } : {}),
        connected: isOnline,
        probes_sent: ping.sent,
        probes_ok: ping.ok,
        latency_ms: ping.rttMs,
        jitter_ms: ping.jitterMs,
        packet_loss: ping.sent ? Math.round(((ping.sent - ping.ok) / ping.sent) * 100) / 100 : null,
        dl_mbps: dl,
        ul_mbps: ul,
      };
      const cfg = whoRef.current?.config;
      const rec: ProbeRecord = { reading, status: "queued", provisional: provisionalClass(reading, cfg?.weak_rtt_ms, cfg?.weak_dl_mbps), created: Date.now() };
      await probeStore.put(rec);
      setLast(rec);
      await refresh();
      if (navigator.onLine) void doSync();
      else void registerBackgroundSync();
    } finally {
      setMeasuring(false);
      setPhase("");
      if (runningRef.current) {
        const wait = s.intervalS * 1000;
        timerRef.current = window.setTimeout(measure, wait);
        setNextAt(Date.now() + wait);
      }
    }
  }, [meta, refresh, doSync]);

  const acquireWake = useCallback(async () => {
    try {
      const wl = await (navigator as unknown as { wakeLock?: { request(t: "screen"): Promise<WakeLockSentinel> } }).wakeLock?.request("screen");
      if (wl) {
        wakeRef.current = wl;
        setAwake(true);
        wl.addEventListener("release", () => setAwake(false));
      }
    } catch {
      setAwake(false);
    }
  }, []);

  const start = useCallback(() => {
    if (!meta || runningRef.current) return;
    if (!navigator.geolocation) {
      setGpsError("This browser cannot provide location.");
      return;
    }
    setGpsError(null);
    watchRef.current = navigator.geolocation.watchPosition(
      (p) => {
        posRef.current = p;
        setPosition(p);
        setGpsError(null);
      },
      (err) => setGpsError(err.code === err.PERMISSION_DENIED ? "Location permission is blocked. Allow location for this site in Chrome settings." : "Waiting for a GPS signal - try near a window or outdoors."),
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 20000 },
    );
    runningRef.current = true;
    setRunning(true);
    lastSpeedRef.current = 0;
    void acquireWake();
    void loadWhoami();
    timerRef.current = window.setTimeout(measure, 800);
  }, [meta, measure, acquireWake, loadWhoami]);

  const stop = useCallback(() => {
    runningRef.current = false;
    setRunning(false);
    setNextAt(null);
    if (timerRef.current) window.clearTimeout(timerRef.current);
    if (watchRef.current != null) navigator.geolocation.clearWatch(watchRef.current);
    watchRef.current = null;
    void wakeRef.current?.release().catch(() => undefined);
    wakeRef.current = null;
    setAwake(false);
  }, []);

  const setSettings = useCallback((patch: Partial<ProbeSettings>) => {
    setSettingsState((s) => {
      const next = { ...s, ...patch };
      safeStorage.set(SETTINGS_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  useEffect(() => {
    void refresh();
    void loadWhoami();
    const onOnline = () => {
      setOnline(true);
      void doSync();
      void loadWhoami();
    };
    const onOffline = () => setOnline(false);
    const onVisible = () => {
      if (document.visibilityState === "visible") {
        if (runningRef.current && !wakeRef.current) void acquireWake();
        void refresh();
      }
    };
    const conn = (navigator as unknown as { connection?: EventTarget }).connection;
    const onConn = () => void loadWhoami();
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    document.addEventListener("visibilitychange", onVisible);
    conn?.addEventListener?.("change", onConn);
    const poll = window.setInterval(() => void doSync(), 30_000);
    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
      document.removeEventListener("visibilitychange", onVisible);
      conn?.removeEventListener?.("change", onConn);
      window.clearInterval(poll);
    };
  }, [refresh, doSync, loadWhoami, acquireWake]);

  useEffect(() => () => stop(), [stop]);

  const queued = records.filter((r) => r.status === "queued").length;
  return {
    settings, setSettings, running, start, stop, position, gpsError, awake, online, measuring, phase, last, records, queued,
    sync, doSync, nextAt, whoami, loadWhoami, needsPairing, refresh,
  };
}

export type ProbeController = ReturnType<typeof useProbe>;
