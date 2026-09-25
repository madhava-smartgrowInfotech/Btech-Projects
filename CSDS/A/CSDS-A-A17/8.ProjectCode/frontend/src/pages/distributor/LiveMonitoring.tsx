import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { AlertTriangle, Radio, Wifi, WifiOff } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { LiveSensorChart } from "@/components/charts/LiveSensorChart";
import { toast } from "@/components/ui/Toast";
import type { SensorReading } from "@/types";

const MAX_READINGS = 60;

export function LiveMonitoring() {
  const { id } = useParams();
  const [readings, setReadings] = useState<SensorReading[]>([]);
  const [connected, setConnected] = useState(false);
  const wasAnomaly = useRef(false);

  useEffect(() => {
    api.get<SensorReading[]>(`/iot/shipments/${id}/history`).then(({ data }) => setReadings(data));
  }, [id]);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const socket = new WebSocket(`${protocol}//${window.location.host}/ws/iot/${id}`);

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onmessage = (event) => {
      const reading: SensorReading = JSON.parse(event.data);
      setReadings((prev) => [reading, ...prev].slice(0, MAX_READINGS));

      if (reading.is_anomaly && !wasAnomaly.current) {
        toast.error("Cold-chain alert", "Sensor reading outside safe range — check the shipment.");
      }
      wasAnomaly.current = reading.is_anomaly;
    };

    return () => socket.close();
  }, [id]);

  const latest = readings[0];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink-900">Live shipment monitoring</h1>
          <p className="text-sm text-ink-500 mt-1">Shipment #{id} · storage &amp; transport telemetry</p>
        </div>
        <div className="flex items-center gap-1.5 text-xs font-medium">
          {connected ? (
            <span className="flex items-center gap-1 text-brand-700">
              <Wifi size={14} /> Live
            </span>
          ) : (
            <span className="flex items-center gap-1 text-ink-400">
              <WifiOff size={14} /> Connecting…
            </span>
          )}
        </div>
      </div>

      {latest?.is_anomaly && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 px-4 py-3 text-sm"
        >
          <AlertTriangle size={16} /> Sensor readings are currently outside the safe range for this shipment.
        </motion.div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Radio size={16} className="text-brand-600" /> Cold-chain telemetry
          </CardTitle>
          <CardDescription>Updates roughly every 1.5 seconds while this shipment is in transit.</CardDescription>
        </CardHeader>
        <CardContent>
          <LiveSensorChart readings={readings} />
        </CardContent>
      </Card>
    </div>
  );
}
