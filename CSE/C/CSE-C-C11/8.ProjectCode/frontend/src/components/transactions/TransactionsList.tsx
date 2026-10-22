import { useMutation } from "@tanstack/react-query";
import { ArrowDownUp, CalendarDays, Pencil, Receipt, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router";

import { Badge } from "@/components/ui/Badge";
import { Button, IconButton } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { FormField, Input, SearchField, Textarea } from "@/components/ui/Field";
import { ConfirmModal, Modal } from "@/components/ui/Overlay";
import { Select } from "@/components/ui/Select";
import { Table, type Column } from "@/components/ui/Table";
import { toast } from "@/components/ui/Toast";
import { Segmented, Checkbox } from "@/components/ui/Toggles";
import { api, errorMessage, type Meta, type Transaction } from "@/lib/api";
import { useMoney } from "@/lib/format";
import { useRefreshData, useTransactions, type TxnFilters } from "@/lib/queries";
import { formatDate, cn } from "@/lib/utils";

function EditModal({ txn, meta, onClose }: { txn: Transaction; meta: Meta; onClose: () => void }) {
  const refresh = useRefreshData();
  const [f, setF] = useState({
    description: txn.description,
    amount: String(txn.amount),
    category: txn.category,
    date: txn.date,
    transaction_type: txn.transaction_type,
    payment_method: txn.payment_method,
    notes: txn.notes ?? "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const save = useMutation({
    mutationFn: async () => api.put(`/transactions/${txn.id}`, { ...f, amount: Number(f.amount) }),
    onSuccess: async () => {
      toast.success("Transaction updated");
      await refresh();
      onClose();
    },
    onError: (e) => toast.error("Could not save the changes", { description: errorMessage(e) }),
  });
  const categories = Array.from(new Set([...meta.categories, f.category]));

  function submit() {
    const next: Record<string, string> = {};
    if (!f.description.trim()) next.description = "Description cannot be empty.";
    if (!(Number(f.amount) > 0)) next.amount = "Amount must be greater than zero.";
    if (!f.category.trim()) next.category = "Pick or type a category.";
    setErrors(next);
    if (!Object.keys(next).length) save.mutate();
  }

  return (
    <Modal
      open
      onOpenChange={(o) => !o && onClose()}
      title="Edit transaction"
      description={`#${txn.id}`}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={submit} loading={save.isPending}>
            Save changes
          </Button>
        </>
      }
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <FormField label="Description" error={errors.description} className="sm:col-span-2">
          {(p) => <Input {...p} value={f.description} onChange={(e) => setF({ ...f, description: e.target.value })} />}
        </FormField>
        <FormField label="Amount" error={errors.amount}>
          {(p) => <Input {...p} type="number" min="0" step="0.01" value={f.amount} onChange={(e) => setF({ ...f, amount: e.target.value })} />}
        </FormField>
        <FormField label="Date">
          {(p) => <Input {...p} type="date" value={f.date} onChange={(e) => setF({ ...f, date: e.target.value })} />}
        </FormField>
        <FormField label="Category" error={errors.category}>
          {(p) => <Select {...p} value={f.category} onValueChange={(v) => setF({ ...f, category: v })} options={categories.map((c) => ({ value: c, label: c }))} />}
        </FormField>
        <FormField label="Type">
          {(p) => (
            <Select
              {...p}
              value={f.transaction_type}
              onValueChange={(v) => setF({ ...f, transaction_type: v as "income" | "expense" })}
              options={[
                { value: "expense", label: "Expense" },
                { value: "income", label: "Income" },
              ]}
            />
          )}
        </FormField>
        <FormField label="Payment method">
          {(p) => (
            <Select
              {...p}
              value={f.payment_method}
              onValueChange={(v) => setF({ ...f, payment_method: v })}
              options={Array.from(new Set([...meta.payment_methods, f.payment_method])).map((m) => ({ value: m, label: m }))}
            />
          )}
        </FormField>
        <FormField label="Notes" className="sm:col-span-2">
          {(p) => <Textarea {...p} rows={2} value={f.notes} onChange={(e) => setF({ ...f, notes: e.target.value })} />}
        </FormField>
      </div>
    </Modal>
  );
}

export function TransactionsList({ meta }: { meta: Meta }) {
  const money = useMoney();
  const refresh = useRefreshData();
  const [filters, setFilters] = useState<TxnFilters>({ category: "All", type: "All", sort: "date", order: "desc" });
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<Transaction | null>(null);
  const [deleting, setDeleting] = useState<Transaction | null>(null);
  const q = useTransactions({ ...filters, q: search });

  const remove = useMutation({
    mutationFn: async (id: number) => api.delete(`/transactions/${id}`),
    onSuccess: async () => {
      toast.success("Transaction deleted");
      await refresh();
    },
    onError: (e) => toast.error("Could not delete it", { description: errorMessage(e) }),
  });

  const set = (patch: Partial<TxnFilters>) => setFilters((s) => ({ ...s, ...patch }));
  const filtered = !!(filters.start || filters.end || (filters.category && filters.category !== "All") || (filters.type && filters.type !== "All") || search);

  const columns: Column<Transaction>[] = [
    { key: "date", header: "Date", cell: (t) => <span className="whitespace-nowrap tabular-nums">{formatDate(`${t.date}T00:00:00Z`)}</span> },
    { key: "description", header: "Description", cell: (t) => <span className="font-medium">{t.description}</span> },
    { key: "category", header: "Category", cell: (t) => <Badge tone="violet">{t.category}</Badge> },
    {
      key: "amount",
      header: "Amount",
      align: "right",
      cell: (t) => (
        <span className={cn("whitespace-nowrap font-medium tabular-nums", t.transaction_type === "income" ? "text-success" : "text-foreground")}>
          {t.transaction_type === "income" ? "+" : "-"}
          {money.exact(t.amount)}
        </span>
      ),
    },
    { key: "payment", header: "Payment", hideOnCard: true, cell: (t) => <span className="text-muted-foreground">{t.payment_method}</span> },
    {
      key: "actions",
      header: <span className="sr-only">Actions</span>,
      align: "right",
      cell: (t) => (
        <span className="inline-flex gap-1">
          <IconButton label={`Edit ${t.description}`} size="icon-sm" onClick={() => setEditing(t)}>
            <Pencil />
          </IconButton>
          <IconButton label={`Delete ${t.description}`} size="icon-sm" onClick={() => setDeleting(t)}>
            <Trash2 className="text-danger" />
          </IconButton>
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <Card>
        <CardBody className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <FormField label="From">{(p) => <Input {...p} type="date" icon={<CalendarDays />} value={filters.start ?? ""} onChange={(e) => set({ start: e.target.value })} />}</FormField>
            <FormField label="To">{(p) => <Input {...p} type="date" icon={<CalendarDays />} value={filters.end ?? ""} onChange={(e) => set({ end: e.target.value })} />}</FormField>
            <FormField label="Category">
              {(p) => (
                <Select {...p} value={filters.category} onValueChange={(v) => set({ category: v })} options={[{ value: "All", label: "All categories" }, ...meta.categories.map((c) => ({ value: c, label: c }))]} />
              )}
            </FormField>
            <FormField label="Sort by">
              {(p) => (
                <Select
                  {...p}
                  icon={<ArrowDownUp />}
                  value={filters.sort}
                  onValueChange={(v) => set({ sort: v })}
                  options={[
                    { value: "date", label: "Date" },
                    { value: "amount", label: "Amount" },
                    { value: "category", label: "Category" },
                  ]}
                />
              )}
            </FormField>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Segmented
              label="Type filter"
              value={(filters.type ?? "All") as "All" | "income" | "expense"}
              onChange={(v) => set({ type: v })}
              options={[
                { value: "All", label: "All" },
                { value: "income", label: "Income" },
                { value: "expense", label: "Expenses" },
              ]}
            />
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <Checkbox checked={filters.order === "asc"} onCheckedChange={(c) => set({ order: c ? "asc" : "desc" })} aria-label="Ascending order" /> Ascending
            </label>
            <SearchField className="min-w-52 flex-1 sm:max-w-sm" value={search} onChange={setSearch} placeholder="Search description…" label="Search transactions" />
            {filtered && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setFilters({ category: "All", type: "All", sort: "date", order: "desc" });
                  setSearch("");
                }}
              >
                Clear filters
              </Button>
            )}
          </div>
        </CardBody>
      </Card>

      {q.isPending ? (
        <div className="space-y-2" role="status" aria-label="Loading transactions">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full rounded-xl" />
          ))}
        </div>
      ) : q.isError ? (
        <ErrorState error={q.error} title="Couldn't load transactions" onRetry={() => void q.refetch()} />
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground" aria-live="polite">
            <Badge>{q.data.total} transactions</Badge>
            <Badge tone="success">Income {money(q.data.income)}</Badge>
            <Badge tone="magenta">Expenses {money(q.data.expense)}</Badge>
          </div>
          <Table
            columns={columns}
            rows={q.data.items}
            rowKey={(t) => t.id}
            caption="Transactions"
            empty={
              <EmptyState
                icon={<Receipt />}
                title={filtered ? "No transactions match your filters" : "No transactions yet"}
                description={filtered ? "Try widening the date range or clearing a filter." : "Add your first transaction or import a CSV statement."}
                action={
                  filtered ? (
                    <Button
                      variant="secondary"
                      onClick={() => {
                        setFilters({ category: "All", type: "All", sort: "date", order: "desc" });
                        setSearch("");
                      }}
                    >
                      Clear filters
                    </Button>
                  ) : (
                    <Button asChild>
                      <Link to="/app/transactions?tab=add">Add a transaction</Link>
                    </Button>
                  )
                }
              />
            }
          />
        </>
      )}

      {editing && <EditModal key={editing.id} txn={editing} meta={meta} onClose={() => setEditing(null)} />}
      {deleting && (
        <ConfirmModal
          open
          onOpenChange={(o) => !o && setDeleting(null)}
          title="Delete this transaction?"
          description={`${deleting.description} (${money.exact(deleting.amount)}) will be removed permanently.`}
          onConfirm={async () => {
            await remove.mutateAsync(deleting.id);
            setDeleting(null);
          }}
        />
      )}
    </div>
  );
}
