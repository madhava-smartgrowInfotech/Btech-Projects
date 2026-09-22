/** Provisional class shown on the phone before the server confirms it - the same bands the server uses. */
import type { ReadingPayload } from "./store";

export function provisionalClass(r: ReadingPayload, weakRttMs = 400, weakDlMbps = 2): { label: "Strong" | "Weak" | "Dead"; reasons: string[] } {
  const lost = r.probes_sent - r.probes_ok;
  if (!r.connected) return { label: "Dead", reasons: ["Phone reported no connection"] };
  if (r.probes_sent && (lost >= 2 || r.probes_ok === 0)) return { label: "Dead", reasons: [`${lost} of ${r.probes_sent} latency probes failed`] };
  const reasons: string[] = [];
  if (lost === 1) reasons.push(`1 of ${r.probes_sent} latency probes lost`);
  if (r.latency_ms != null && r.latency_ms > weakRttMs) reasons.push(`Round-trip ${Math.round(r.latency_ms)} ms is above ${weakRttMs} ms`);
  if (r.dl_mbps != null && r.dl_mbps < weakDlMbps) reasons.push(`Download ${r.dl_mbps.toFixed(2)} Mbps is below ${weakDlMbps} Mbps`);
  return reasons.length ? { label: "Weak", reasons } : { label: "Strong", reasons: ["Latency and speed within the Strong band"] };
}
