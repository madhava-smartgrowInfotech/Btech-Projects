export interface Device {
  id: number;
  owner_id: number;
  owner_name: string | null;
  kind: "phone" | "esp32" | "simulator" | "replay";
  name: string;
  api_key_prefix: string;
  hardware: string | null;
  firmware: string | null;
  fixed_lat: number | null;
  fixed_lon: number | null;
  config: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  last_seen_at: string | null;
  last_sync_at: string | null;
  readings_count: number;
  online: boolean;
}

export interface DeviceWithKey {
  device: Device;
  api_key: string;
}

export interface SyncBatch {
  id: number;
  ts: string;
  received: number;
  accepted: number;
  duplicates: number;
  rejected: number;
  oldest_reading: string | null;
}

export const KIND_LABEL: Record<Device["kind"], string> = {
  phone: "Phone probe",
  esp32: "ESP32 node",
  simulator: "Simulated node",
  replay: "Sample replay",
};
