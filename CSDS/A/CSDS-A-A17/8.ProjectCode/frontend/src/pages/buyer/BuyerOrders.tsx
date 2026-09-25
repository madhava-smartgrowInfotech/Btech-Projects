import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { formatCurrency } from "@/lib/format";
import type { Order } from "@/types";

const STATUS_TONE: Record<string, "slate" | "amber" | "sky" | "brand" | "rose"> = {
  placed: "amber",
  confirmed: "sky",
  in_transit: "sky",
  delivered: "brand",
  cancelled: "rose",
};

const STATUS_STEPS = ["placed", "confirmed", "in_transit", "delivered"];

export function BuyerOrders() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Order[]>("/marketplace/orders/mine")
      .then(({ data }) => setOrders(data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-ink-900">My orders</h1>
        <p className="text-sm text-ink-500 mt-1">Track every order from placed to delivered.</p>
      </div>

      {loading ? (
        <p className="text-sm text-ink-500 flex items-center gap-2">
          <Loader2 size={15} className="animate-spin" /> Loading…
        </p>
      ) : orders.length === 0 ? (
        <p className="text-sm text-ink-500">No orders yet — browse the marketplace to get started.</p>
      ) : (
        <div className="space-y-3">
          {orders.map((o) => {
            const stepIndex = STATUS_STEPS.indexOf(o.status);
            return (
              <Card key={o.id}>
                <CardContent>
                  <div className="flex items-center justify-between mb-3">
                    <p className="font-semibold text-ink-900">Order #{o.id}</p>
                    <Badge tone={STATUS_TONE[o.status] ?? "slate"}>{o.status.replace("_", " ")}</Badge>
                  </div>
                  <p className="text-xs text-ink-500 mb-3">
                    {o.quantity_kg} kg · {formatCurrency(o.agreed_price)} / quintal
                  </p>
                  {stepIndex >= 0 && (
                    <div className="flex items-center gap-1.5">
                      {STATUS_STEPS.map((s, i) => (
                        <div
                          key={s}
                          className={`h-1.5 flex-1 rounded-full ${i <= stepIndex ? "bg-brand-500" : "bg-ink-100"}`}
                          title={s}
                        />
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
