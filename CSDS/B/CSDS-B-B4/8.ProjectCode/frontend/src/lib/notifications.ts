import { formatINR } from "@/lib/format";

type Tx = (key: string, fallback?: string, params?: Record<string, string | number>) => string;

/** Turns a stored notification into translated title + body text. */
export function notificationText(kind: string, payload: Record<string, unknown>, tx: Tx) {
  const params: Record<string, string | number> = {
    amount: formatINR(Number(payload.amount ?? 0)),
    payee: String(payload.payee_name ?? payload.payee_upi_id ?? ""),
    payer: String(payload.payer_name ?? ""),
    requester: String(payload.requested_by ?? payload.requester_name ?? ""),
    approver: String(payload.approver ?? ""),
    outcome: String(payload.outcome ?? ""),
  };
  return {
    title: tx(`notif.${kind}.title`, kind.replace(/_/g, " "), params),
    body: tx(`notif.${kind}.body`, "", params),
  };
}
