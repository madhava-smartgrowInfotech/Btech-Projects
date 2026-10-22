import { useMutation } from "@tanstack/react-query";
import { BarChart3, Coins, IndianRupee, LineChart, PieChart as PieIcon, Plus, RefreshCw, Trash2, TrendingUp, Wallet } from "lucide-react";
import { useState } from "react";

import { ChartCard } from "@/components/charts/Chart";
import { ColorBars, Donut } from "@/components/charts/FinanceCharts";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { Badge } from "@/components/ui/Badge";
import { Button, IconButton } from "@/components/ui/Button";
import { StatCard } from "@/components/ui/Display";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { FormField, Input } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { ConfirmModal, Modal } from "@/components/ui/Overlay";
import { Select } from "@/components/ui/Select";
import { Table, type Column } from "@/components/ui/Table";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage, type Holding } from "@/lib/api";
import { pct, todayISO, useMoney } from "@/lib/format";
import { useInvestments, useMeta, useRefreshData } from "@/lib/queries";
import { cn, formatDate } from "@/lib/utils";

function AddInvestmentModal({ open, onOpenChange, types }: { open: boolean; onOpenChange: (o: boolean) => void; types: string[] }) {
  const refresh = useRefreshData();
  const blank = () => ({ name: "", symbol: "", type: types[0] ?? "Stock", qty: "", buy: "", now: "", date: todayISO() });
  const [f, setF] = useState(blank);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const add = useMutation({
    mutationFn: async () =>
      api.post("/investments", {
        asset_name: f.name,
        symbol: f.symbol,
        asset_type: f.type,
        quantity: Number(f.qty),
        purchase_price: Number(f.buy),
        current_price: Number(f.now || 0),
        purchase_date: f.date,
      }),
    onSuccess: async () => {
      toast.success(`Added ${f.name} to your portfolio`);
      setF(blank());
      onOpenChange(false);
      await refresh();
    },
    onError: (e) => toast.error("Could not add the investment", { description: errorMessage(e) }),
  });

  function submit() {
    const next: Record<string, string> = {};
    if (!f.name.trim()) next.name = "Please enter an asset name.";
    if (!(Number(f.qty) > 0)) next.qty = "Quantity must be greater than zero.";
    if (!(Number(f.buy) > 0)) next.buy = "Purchase price must be greater than zero.";
    if (Number(f.now) < 0) next.now = "Price cannot be negative.";
    setErrors(next);
    if (!Object.keys(next).length) add.mutate();
  }

  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title="Add an investment"
      description="Add a ticker symbol (like NIFTYBEES.NS) to enable live price refresh."
      footer={
        <>
          <Button variant="secondary" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={submit} loading={add.isPending}>
            <Plus /> Add investment
          </Button>
        </>
      }
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label="Asset name" error={errors.name} className="sm:col-span-2">
          {(p) => <Input {...p} placeholder="e.g. Nifty 50 Index Fund" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} autoFocus />}
        </FormField>
        <FormField label="Ticker symbol (optional)">
          {(p) => <Input {...p} placeholder="e.g. NIFTYBEES.NS" value={f.symbol} onChange={(e) => setF({ ...f, symbol: e.target.value })} />}
        </FormField>
        <FormField label="Asset type">
          {(p) => <Select {...p} value={f.type} onValueChange={(v) => setF({ ...f, type: v })} options={types.map((t) => ({ value: t, label: t }))} />}
        </FormField>
        <FormField label="Quantity" error={errors.qty}>
          {(p) => <Input {...p} type="number" min="0" step="any" value={f.qty} onChange={(e) => setF({ ...f, qty: e.target.value })} />}
        </FormField>
        <FormField label="Purchase price (per unit)" error={errors.buy}>
          {(p) => <Input {...p} type="number" min="0" step="any" icon={<IndianRupee />} value={f.buy} onChange={(e) => setF({ ...f, buy: e.target.value })} />}
        </FormField>
        <FormField label="Current price (blank = purchase price)" error={errors.now}>
          {(p) => <Input {...p} type="number" min="0" step="any" icon={<IndianRupee />} value={f.now} onChange={(e) => setF({ ...f, now: e.target.value })} />}
        </FormField>
        <FormField label="Purchase date">
          {(p) => <Input {...p} type="date" value={f.date} max={todayISO()} onChange={(e) => setF({ ...f, date: e.target.value })} />}
        </FormField>
      </div>
    </Modal>
  );
}

export default function Investments() {
  const money = useMoney();
  const refresh = useRefreshData();
  const meta = useMeta();
  const q = useInvestments();
  const [open, setOpen] = useState(false);
  const [deleting, setDeleting] = useState<Holding | null>(null);
  const [refreshing, setRefreshing] = useState<number | null>(null);

  const remove = useMutation({
    mutationFn: async (id: number) => api.delete(`/investments/${id}`),
    onSuccess: async () => {
      toast.success("Investment removed");
      await refresh();
    },
    onError: (e) => toast.error("Could not remove it", { description: errorMessage(e) }),
  });

  async function refreshPrice(h: Holding) {
    setRefreshing(h.id);
    try {
      const { data } = await api.post<{ success: boolean; message: string }>(`/investments/${h.id}/refresh`);
      if (data.success) {
        toast.success(`${h.asset_name}: ${data.message}`);
        await refresh();
      } else {
        toast.warning(`${h.asset_name}: ${data.message}`, { description: "Your last known price is still being used." });
      }
    } catch (e) {
      toast.error("Could not refresh the price", { description: errorMessage(e) });
    } finally {
      setRefreshing(null);
    }
  }

  const columns: Column<Holding>[] = [
    {
      key: "asset",
      header: "Asset",
      cell: (h) => (
        <span className="block">
          <span className="font-medium">{h.asset_name}</span>
          <span className="block text-xs text-muted-foreground">
            {h.asset_type}
            {h.symbol ? ` · ${h.symbol}` : ""}
          </span>
        </span>
      ),
    },
    { key: "qty", header: "Qty", align: "right", cell: (h) => <span className="tabular-nums">{h.quantity}</span> },
    { key: "invested", header: "Invested", align: "right", cell: (h) => <span className="tabular-nums">{money(h.invested_amount)}</span> },
    { key: "value", header: "Value", align: "right", cell: (h) => <span className="tabular-nums">{money(h.current_value)}</span> },
    {
      key: "pl",
      header: "P/L",
      align: "right",
      cell: (h) => (
        <span className={cn("tabular-nums", h.profit_loss >= 0 ? "text-success" : "text-danger")}>
          {h.profit_loss >= 0 ? "+" : "-"}
          {money(Math.abs(h.profit_loss))} <span className="text-xs">({pct(h.return_percent, 1)})</span>
        </span>
      ),
    },
    { key: "date", header: "Bought", hideOnCard: true, cell: (h) => <span className="whitespace-nowrap text-muted-foreground">{formatDate(`${h.purchase_date}T00:00:00Z`)}</span> },
    {
      key: "actions",
      header: <span className="sr-only">Actions</span>,
      align: "right",
      cell: (h) => (
        <span className="inline-flex gap-1">
          {h.symbol && (
            <Button variant="secondary" size="sm" loading={refreshing === h.id} onClick={() => void refreshPrice(h)} aria-label={`Refresh price of ${h.asset_name}`}>
              <RefreshCw /> Price
            </Button>
          )}
          <IconButton label={`Delete ${h.asset_name}`} size="icon-sm" onClick={() => setDeleting(h)}>
            <Trash2 className="text-danger" />
          </IconButton>
        </span>
      ),
    },
  ];

  const addButton = (
    <Button onClick={() => setOpen(true)}>
      <Plus /> Add investment
    </Button>
  );

  return (
    <>
      <PageHeader title="Investments" description="Track what you own. Live prices need a ticker and an internet connection; otherwise your own price is used." actions={addButton} />

      {q.isPending ? (
        <div className="space-y-4" role="status" aria-label="Loading investments">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-[132px] rounded-2xl" />
            ))}
          </div>
          <Skeleton className="h-64 rounded-2xl" />
        </div>
      ) : q.isError ? (
        <ErrorState error={q.error} title="Couldn't load your portfolio" onRetry={() => void q.refetch()} />
      ) : q.data.holdings.length === 0 ? (
        <EmptyState icon={<LineChart />} title="No investments yet" description="Add a stock, fund, ETF, gold or fixed deposit to see allocation and returns." action={addButton} />
      ) : (
        <div className="space-y-6">
          <Stagger className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StaggerItem>
              <StatCard label="Total invested" value={q.data.total_invested} format={(n) => money(n)} icon={<Wallet />} />
            </StaggerItem>
            <StaggerItem>
              <StatCard label="Current value" value={q.data.total_current_value} format={(n) => money(n)} icon={<Coins />} accent="cyan" />
            </StaggerItem>
            <StaggerItem>
              <StatCard
                label="Profit / loss"
                value={q.data.total_profit_loss}
                format={(n) => `${n < 0 ? "-" : ""}${money(Math.abs(n))}`}
                icon={<TrendingUp />}
                accent="magenta"
                delta={{ value: pct(q.data.total_return_percent, 2), positive: q.data.total_profit_loss >= 0 }}
              />
            </StaggerItem>
            <StaggerItem>
              <StatCard label="Holdings" value={q.data.holdings.length} format={(n) => String(Math.round(n))} icon={<BarChart3 />} hint={`${new Set(q.data.holdings.map((h) => h.asset_type)).size} asset types`} />
            </StaggerItem>
          </Stagger>

          <div className="grid gap-4 lg:grid-cols-2">
            <ChartCard
              title="Portfolio allocation"
              description="By current value"
              icon={<PieIcon />}
              table={{ columns: ["Asset", "Value"], rows: q.data.holdings.map((h) => [h.asset_name, money(h.current_value)]) }}
            >
              <Donut data={q.data.holdings.map((h) => ({ name: h.asset_name, value: h.current_value }))} />
            </ChartCard>
            <ChartCard
              title="Profit / loss by asset"
              icon={<BarChart3 />}
              table={{ columns: ["Asset", "P/L"], rows: q.data.holdings.map((h) => [h.asset_name, money(h.profit_loss)]) }}
            >
              <ColorBars data={q.data.holdings.map((h) => ({ name: h.asset_name, value: h.profit_loss }))} format={(v) => money.compact(v)} name="P/L" />
            </ChartCard>
          </div>

          <section aria-label="Holdings" className="space-y-3">
            <h2 className="font-display text-lg font-semibold">Holdings</h2>
            <Table columns={columns} rows={q.data.holdings} rowKey={(h) => h.id} caption="Holdings" pageSize={8} />
            <p className="text-xs text-muted-foreground">
              Predicted or historical returns are not guaranteed. Live prices depend on market-data availability and fall back to your manually entered price when offline.
            </p>
            <Badge>{q.data.holdings.filter((h) => h.symbol).length} of {q.data.holdings.length} holdings can refresh live prices</Badge>
          </section>
        </div>
      )}

      <AddInvestmentModal open={open} onOpenChange={setOpen} types={meta.data?.asset_types ?? ["Stock", "Mutual Fund", "ETF", "Gold", "Fixed Deposit", "Other"]} />
      {deleting && (
        <ConfirmModal
          open
          onOpenChange={(o) => !o && setDeleting(null)}
          title={`Remove ${deleting.asset_name}?`}
          description="It will disappear from your portfolio and net worth."
          confirmLabel="Remove"
          onConfirm={async () => {
            await remove.mutateAsync(deleting.id);
            setDeleting(null);
          }}
        />
      )}
    </>
  );
}
