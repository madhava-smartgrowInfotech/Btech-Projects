import { useEffect, useState } from "react";
import { Loader2, Package, ShoppingBag, TrendingUp, Users } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/Card";
import { AnimatedCounter } from "@/components/motion/AnimatedCounter";
import { formatCurrency } from "@/lib/format";
import type { AdminOverview } from "@/types";

function Stat({ icon: Icon, label, value, sub }: { icon: typeof Users; label: string; value: number; sub?: string }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4">
        <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
          <Icon size={20} />
        </span>
        <div>
          <p className="text-xs text-ink-500">{label}</p>
          <p className="text-xl font-semibold text-ink-900">
            <AnimatedCounter value={value} />
          </p>
          {sub && <p className="text-xs text-ink-400">{sub}</p>}
        </div>
      </CardContent>
    </Card>
  );
}

export function Overview() {
  const [data, setData] = useState<AdminOverview | null>(null);

  useEffect(() => {
    api.get<AdminOverview>("/admin/overview").then(({ data }) => setData(data));
  }, []);

  if (!data) {
    return (
      <div className="flex items-center gap-2 text-ink-500 text-sm">
        <Loader2 size={16} className="animate-spin" /> Loading…
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-2xl font-semibold text-ink-900">Platform overview</h1>
        <p className="text-sm text-ink-500 mt-1">Live snapshot of marketplace activity.</p>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat icon={Package} label="Total listings" value={data.total_listings} sub={`${data.listed} live · ${data.sold} sold`} />
        <Stat icon={ShoppingBag} label="Orders" value={data.orders} />
        <Stat icon={Users} label="Farmers" value={data.users_by_role.farmer ?? 0} />
        <Stat icon={Users} label="Buyers" value={data.users_by_role.buyer ?? 0} />
      </div>

      <Card>
        <CardContent className="flex items-center gap-4">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-amber-50 text-amber-700">
            <TrendingUp size={20} />
          </span>
          <div>
            <p className="text-xs text-ink-500">Gross transaction volume</p>
            <p className="text-2xl font-semibold text-ink-900">{formatCurrency(data.gross_volume)}</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <p className="text-sm font-semibold text-ink-900 mb-3">Users by role</p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {Object.entries(data.users_by_role).map(([role, count]) => (
              <div key={role} className="rounded-xl bg-sand-100 p-3 text-center">
                <p className="text-lg font-semibold text-ink-900">{count}</p>
                <p className="text-xs text-ink-500 capitalize">{role}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
