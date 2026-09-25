import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { api, apiErrorMessage } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { toast } from "@/components/ui/Toast";
import { formatCurrency } from "@/lib/format";
import type { Order } from "@/types";

const STATUS_TONE: Record<string, "slate" | "amber" | "sky" | "brand" | "rose"> = {
  placed: "amber",
  confirmed: "sky",
  in_transit: "sky",
  delivered: "brand",
  cancelled: "rose",
};

export function FarmerOrders() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);

  async function load() {
    setLoading(true);
    try {
      const { data } = await api.get<Order[]>("/marketplace/orders/mine");
      setOrders(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function confirm(orderId: number) {
    setBusyId(orderId);
    try {
      await api.patch(`/marketplace/orders/${orderId}/status`, { status: "confirmed" });
      toast.success("Order confirmed");
      load();
    } catch (err) {
      toast.error("Couldn't confirm order", apiErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-ink-900">Orders</h1>
        <p className="text-sm text-ink-500 mt-1">Buyer orders placed against your listings.</p>
      </div>

      {loading ? (
        <p className="text-sm text-ink-500 flex items-center gap-2">
          <Loader2 size={15} className="animate-spin" /> Loading…
        </p>
      ) : orders.length === 0 ? (
        <p className="text-sm text-ink-500">No orders yet.</p>
      ) : (
        <div className="space-y-3">
          {orders.map((o) => (
            <Card key={o.id}>
              <CardContent className="flex items-center justify-between">
                <div>
                  <p className="font-semibold text-ink-900">Order #{o.id}</p>
                  <p className="text-xs text-ink-500">
                    {o.quantity_kg} kg · {formatCurrency(o.agreed_price)} / quintal
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge tone={STATUS_TONE[o.status] ?? "slate"}>{o.status.replace("_", " ")}</Badge>
                  {o.status === "placed" && (
                    <Button size="sm" onClick={() => confirm(o.id)} disabled={busyId === o.id}>
                      Confirm
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
