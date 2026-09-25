import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, Radio, Truck } from "lucide-react";
import { api, apiErrorMessage } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { toast } from "@/components/ui/Toast";
import { formatCurrency } from "@/lib/format";
import type { Order, Shipment } from "@/types";

export function ActiveDeliveries() {
  const navigate = useNavigate();
  const [orders, setOrders] = useState<Order[]>([]);
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);

  async function load() {
    setLoading(true);
    try {
      const [ordersRes, shipmentsRes] = await Promise.all([
        api.get<Order[]>("/marketplace/orders/mine"),
        api.get<Shipment[]>("/iot/shipments"),
      ]);
      setOrders(ordersRes.data);
      setShipments(shipmentsRes.data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function startTransit(orderId: number) {
    setBusyId(orderId);
    try {
      await api.patch(`/marketplace/orders/${orderId}/status`, { status: "in_transit" });
      toast.success("Shipment started — live monitoring is now active");
      load();
    } catch (err) {
      toast.error("Couldn't start transit", apiErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  async function markDelivered(orderId: number) {
    setBusyId(orderId);
    try {
      await api.patch(`/marketplace/orders/${orderId}/status`, { status: "delivered" });
      toast.success("Order marked delivered");
      load();
    } catch (err) {
      toast.error("Couldn't update order", apiErrorMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-ink-900">Active deliveries</h1>
        <p className="text-sm text-ink-500 mt-1">Claim confirmed orders and monitor shipments in transit.</p>
      </div>

      {loading ? (
        <p className="text-sm text-ink-500 flex items-center gap-2">
          <Loader2 size={15} className="animate-spin" /> Loading…
        </p>
      ) : orders.length === 0 ? (
        <p className="text-sm text-ink-500">No orders ready for delivery right now.</p>
      ) : (
        <div className="space-y-3">
          {orders.map((o) => {
            const shipment = shipments.find((s) => s.order_id === o.id);
            return (
              <Card key={o.id}>
                <CardContent className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-50 text-brand-700">
                      <Truck size={16} />
                    </span>
                    <div>
                      <p className="font-semibold text-ink-900">Order #{o.id}</p>
                      <p className="text-xs text-ink-500">
                        {o.quantity_kg} kg · {formatCurrency(o.agreed_price)} / quintal
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge tone={o.status === "in_transit" ? "sky" : "amber"}>{o.status.replace("_", " ")}</Badge>
                    {o.status === "confirmed" && (
                      <Button size="sm" onClick={() => startTransit(o.id)} disabled={busyId === o.id}>
                        Start transit
                      </Button>
                    )}
                    {o.status === "in_transit" && shipment && (
                      <>
                        <Button size="sm" variant="outline" onClick={() => navigate(`/distributor/shipments/${shipment.id}`)}>
                          <Radio size={14} /> Live monitor
                        </Button>
                        <Button size="sm" onClick={() => markDelivered(o.id)} disabled={busyId === o.id}>
                          Mark delivered
                        </Button>
                      </>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
