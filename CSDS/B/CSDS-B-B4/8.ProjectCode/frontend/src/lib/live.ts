import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { storage } from "@/lib/storage";
import { TOKEN_KEY } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { notificationText } from "@/lib/notifications";

interface LiveMessage {
  type: string;
  kind?: string;
  payload?: Record<string, unknown>;
}

/** Keeps one WebSocket open while signed in; refreshes data and shows a toast on every event. */
export function useLiveUpdates(enabled: boolean) {
  const qc = useQueryClient();
  const { tx } = useI18n();

  useEffect(() => {
    if (!enabled) return;
    let ws: WebSocket | null = null;
    let retry = 0;
    let stopped = false;
    let timer: number | undefined;
    let ping: number | undefined;

    const connect = () => {
      const token = storage.get(TOKEN_KEY);
      if (!token || stopped) return;
      const proto = window.location.protocol === "https:" ? "wss" : "ws";
      ws = new WebSocket(`${proto}://${window.location.host}/api/ws?token=${encodeURIComponent(token)}`);
      ws.onopen = () => {
        retry = 0;
        ping = window.setInterval(() => ws?.readyState === WebSocket.OPEN && ws.send("ping"), 25000);
      };
      ws.onmessage = (event) => {
        let msg: LiveMessage;
        try {
          msg = JSON.parse(event.data);
        } catch {
          return;
        }
        if (msg.type !== "notification" || !msg.kind) return;
        for (const key of ["notifications", "badges", "me", "wallet", "payments", "payment", "holds", "approvals", "collect", "dashboard"]) {
          qc.invalidateQueries({ queryKey: [key] });
        }
        const text = notificationText(msg.kind, msg.payload ?? {}, tx);
        const tone = msg.kind.includes("rejected") || msg.kind.includes("expired") ? "warning" : "info";
        if (tone === "warning") toast.warning(text.title, { description: text.body });
        else toast(text.title, { description: text.body });
      };
      ws.onclose = () => {
        window.clearInterval(ping);
        if (stopped) return;
        retry = Math.min(retry + 1, 6);
        timer = window.setTimeout(connect, 1000 * 2 ** retry);
      };
    };

    connect();
    return () => {
      stopped = true;
      window.clearTimeout(timer);
      window.clearInterval(ping);
      ws?.close();
    };
  }, [enabled, qc, tx]);
}
