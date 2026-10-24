import { useCallback, useEffect, useRef, useState } from "react";

import { endpoints, errorMessage } from "@/lib/api";
import { playAlert } from "@/lib/alertSound";
import { useCamera } from "@/lib/camera";
import type { SessionState } from "@/lib/types";

const FRAME_GAP_MS = 110; // the server rejects evidence if two frames are >0.5 s apart, so keep posting steadily
const SIM_TICK_MS = 200;
const TRACE_POINTS = 90;

export interface TracePoint {
  t: number;
  ear: number | null;
}

/**
 * One monitoring session on the server (the web equivalent of one desktop `Application`).
 * Owns the browser camera, the frame loop (camera) or tick loop (simulation) and the live EAR trace.
 */
export function useRiderSession(opts: { soundOn: boolean }) {
  const camera = useCamera();
  const [state, setState] = useState<SessionState | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [trace, setTrace] = useState<TracePoint[]>([]);
  const idRef = useRef<string | null>(null);
  const soundRef = useRef(opts.soundOn);
  const lastAlert = useRef(0);
  soundRef.current = opts.soundOn;

  const apply = useCallback((s: SessionState) => {
    if (s.alert_seq > lastAlert.current && soundRef.current) playAlert();
    lastAlert.current = s.alert_seq;
    const { preview: p, ...rest } = s;
    setState(rest as SessionState);
    if (p) setPreview(p);
    if (s.metrics) {
      const point = { t: Date.now(), ear: s.metrics.ear };
      setTrace((old) => [...old.slice(-(TRACE_POINTS - 1)), point]);
    }
  }, []);

  // create the server-side session on mount, close it on unmount
  useEffect(() => {
    let alive = true;
    endpoints
      .createSession()
      .then((s) => {
        if (!alive) {
          void endpoints.closeSession(s.session_id).catch(() => undefined);
          return;
        }
        idRef.current = s.session_id;
        lastAlert.current = s.alert_seq;
        setState(s);
      })
      .catch((e) => alive && setError(errorMessage(e)));
    return () => {
      alive = false;
      const id = idRef.current;
      idRef.current = null;
      if (id) void endpoints.closeSession(id).catch(() => undefined);
    };
  }, []);

  const source = state?.source ?? "none";
  const sessionId = state?.session_id;

  // camera frame loop
  useEffect(() => {
    if (source !== "camera" || !camera.running || !sessionId) return;
    let stop = false;
    let failures = 0;
    (async () => {
      while (!stop) {
        const began = performance.now();
        try {
          const blob = await camera.grab();
          if (blob && !stop) {
            apply(await endpoints.frame(sessionId, blob));
            failures = 0;
          }
        } catch (e) {
          failures += 1;
          if (failures >= 3 && !stop) {
            setError(errorMessage(e, "Lost contact with the server while sending camera frames."));
            return;
          }
        }
        const wait = FRAME_GAP_MS - (performance.now() - began);
        if (wait > 0) await new Promise((r) => setTimeout(r, wait));
      }
    })();
    return () => {
      stop = true;
    };
  }, [source, camera.running, camera.grab, sessionId, apply]);

  // simulation tick loop
  useEffect(() => {
    if (source !== "simulation" || !sessionId) return;
    let stop = false;
    let inflight = false;
    const timer = setInterval(async () => {
      if (inflight || stop) return;
      inflight = true;
      try {
        apply(await endpoints.tick(sessionId));
      } catch (e) {
        if (!stop) setError(errorMessage(e));
      } finally {
        inflight = false;
      }
    }, SIM_TICK_MS);
    return () => {
      stop = true;
      clearInterval(timer);
    };
  }, [source, sessionId, apply]);

  // a camera source with no frames arriving (permission pending, stalled) still needs the server watchdog to run
  useEffect(() => {
    if (source !== "camera" || !sessionId) return;
    const timer = setInterval(() => {
      if (!camera.running) endpoints.session(sessionId).then(apply).catch(() => undefined);
    }, 1000);
    return () => clearInterval(timer);
  }, [source, camera.running, sessionId, apply]);

  const run = useCallback(
    async (label: string, fn: (id: string) => Promise<SessionState>) => {
      const id = idRef.current;
      if (!id) {
        setError("The monitoring session is not ready yet. Wait a moment and try again.");
        return null;
      }
      setBusy(label);
      setError(null);
      try {
        const s = await fn(id);
        apply(s);
        return s;
      } catch (e) {
        setError(errorMessage(e));
        return null;
      } finally {
        setBusy(null);
      }
    },
    [apply],
  );

  const startCamera = useCallback(async () => {
    setError(null);
    setTrace([]);
    setPreview(null);
    const ok = await camera.start();
    if (!ok) return false;
    const s = await run("camera", (id) => endpoints.setSource(id, "camera"));
    if (!s) camera.stop();
    return s !== null;
  }, [camera, run]);

  const stopCamera = useCallback(async () => {
    camera.stop();
    setPreview(null);
    await run("camera", (id) => endpoints.setSource(id, "none"));
  }, [camera, run]);

  const setMonitoring = useCallback((active: boolean) => run("monitoring", (id) => endpoints.setMonitoring(id, active)), [run]);
  const setCalibration = useCallback((active: boolean) => run("calibration", (id) => endpoints.setCalibration(id, active)), [run]);

  /** Same as the desktop scenario dropdown: switching scenario keeps monitoring on if it was on. */
  const startSimulation = useCallback(
    async (scenario: string, keepMonitoring = false) => {
      camera.stop();
      setPreview(null);
      setTrace([]);
      const s = await run("simulation", (id) => endpoints.setSource(id, "simulation", scenario));
      if (s && keepMonitoring) return setMonitoring(true);
      return s;
    },
    [camera, run, setMonitoring],
  );

  return {
    camera,
    state,
    preview,
    trace,
    error,
    busy,
    clearError: () => setError(null),
    startCamera,
    stopCamera,
    startSimulation,
    setMonitoring,
    setCalibration,
  };
}
