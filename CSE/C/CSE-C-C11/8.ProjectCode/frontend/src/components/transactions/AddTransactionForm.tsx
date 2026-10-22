import { useMutation } from "@tanstack/react-query";
import { Bot, CalendarDays, IndianRupee, Plus, Tags, Type } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { FormField, Input, Textarea } from "@/components/ui/Field";
import { Select } from "@/components/ui/Select";
import { toast } from "@/components/ui/Toast";
import { Segmented } from "@/components/ui/Toggles";
import { api, errorMessage, type Meta } from "@/lib/api";
import { todayISO, useMoney } from "@/lib/format";
import { useRefreshData } from "@/lib/queries";

const AUTO = "__auto__";
const NEW = "__new__";

const blank = () => ({
  date: todayISO(),
  description: "",
  amount: "",
  type: "expense" as "expense" | "income",
  category: AUTO,
  newCategory: "",
  payment: "UPI",
  notes: "",
});

/** Add form. Leaving the category on Auto-detect lets the classifier choose, and shows its guess while you type. */
export function AddTransactionForm({ meta }: { meta: Meta }) {
  const money = useMoney();
  const refresh = useRefreshData();
  const [f, setF] = useState(blank);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [guess, setGuess] = useState<string | null>(null);

  // live AI suggestion, debounced so it does not fire on every keystroke
  useEffect(() => {
    const text = f.description.trim();
    if (text.length < 3) {
      setGuess(null);
      return;
    }
    const id = setTimeout(() => {
      api
        .post<{ category: string }>("/transactions/predict-category", { description: text })
        .then((r) => setGuess(r.data.category))
        .catch(() => setGuess(null));
    }, 350);
    return () => clearTimeout(id);
  }, [f.description]);

  const add = useMutation({
    mutationFn: async () => {
      const category = f.category === AUTO ? null : f.category === NEW ? f.newCategory.trim() : f.category;
      return (
        await api.post<{ id: number; category: string; auto_categorised: boolean }>("/transactions", {
          date: f.date,
          description: f.description,
          amount: Number(f.amount),
          transaction_type: f.type,
          category,
          payment_method: f.payment,
          notes: f.notes,
        })
      ).data;
    },
    onSuccess: async (res) => {
      toast.success(`${f.type === "income" ? "Income" : "Expense"} of ${money.exact(Number(f.amount))} added to ${res.category}`, {
        description: res.auto_categorised ? "FINJARVIS AI picked the category." : undefined,
      });
      setF(blank());
      setGuess(null);
      setErrors({});
      await refresh();
    },
    onError: (e) => toast.error("Could not add the transaction", { description: errorMessage(e) }),
  });

  function submit(e: FormEvent) {
    e.preventDefault();
    const next: Record<string, string> = {};
    if (!f.description.trim()) next.description = "Please enter a description.";
    if (!(Number(f.amount) > 0)) next.amount = "Enter an amount greater than zero.";
    if (!f.date) next.date = "Pick a date.";
    if (f.category === NEW && !f.newCategory.trim()) next.newCategory = "Please enter a name for the new category.";
    setErrors(next);
    if (Object.keys(next).length === 0) add.mutate();
  }

  const set = <K extends keyof ReturnType<typeof blank>>(k: K, v: ReturnType<typeof blank>[K]) => setF((s) => ({ ...s, [k]: v }));

  return (
    <Card>
      <CardHeader title="Add a transaction" description="Leave the category on Auto-detect and the AI will classify it." icon={<Plus />} />
      <CardBody>
        <form onSubmit={submit} className="space-y-5" noValidate>
          <Segmented
            label="Transaction type"
            value={f.type}
            onChange={(v) => set("type", v)}
            options={[
              { value: "expense", label: "Expense" },
              { value: "income", label: "Income" },
            ]}
          />
          <div className="grid gap-4 md:grid-cols-2">
            <FormField label="Date" error={errors.date}>
              {(p) => <Input {...p} type="date" icon={<CalendarDays />} value={f.date} max="2100-12-31" onChange={(e) => set("date", e.target.value)} />}
            </FormField>
            <FormField label="Amount" error={errors.amount}>
              {(p) => (
                <Input {...p} type="number" inputMode="decimal" min="0" step="0.01" icon={<IndianRupee />} placeholder="0.00" value={f.amount} onChange={(e) => set("amount", e.target.value)} />
              )}
            </FormField>
            <FormField label="Description" error={errors.description} className="md:col-span-2">
              {(p) => <Input {...p} icon={<Type />} placeholder="e.g. Swiggy order" value={f.description} onChange={(e) => set("description", e.target.value)} />}
            </FormField>
            <FormField
              label="Category"
              hint={
                f.category === AUTO && guess ? (
                  <span className="inline-flex items-center gap-1.5">
                    <Bot className="size-3.5 text-violet-ink" /> AI suggests <Badge tone="violet">{guess}</Badge>
                  </span>
                ) : (
                  "Pick one yourself to teach the AI when it disagrees."
                )
              }
            >
              {(p) => (
                <Select
                  {...p}
                  icon={<Tags />}
                  value={f.category}
                  onValueChange={(v) => set("category", v)}
                  options={[
                    { value: AUTO, label: "Auto-detect (AI)" },
                    ...meta.categories.map((c) => ({ value: c, label: c })),
                    { value: NEW, label: "+ New category" },
                  ]}
                />
              )}
            </FormField>
            <FormField label="Payment method">
              {(p) => <Select {...p} value={f.payment} onValueChange={(v) => set("payment", v)} options={meta.payment_methods.map((m) => ({ value: m, label: m }))} />}
            </FormField>
            {f.category === NEW && (
              <FormField label="New category name" error={errors.newCategory} className="md:col-span-2">
                {(p) => <Input {...p} placeholder="e.g. Pets" value={f.newCategory} onChange={(e) => set("newCategory", e.target.value)} autoFocus />}
              </FormField>
            )}
            <FormField label="Notes (optional)" className="md:col-span-2">
              {(p) => <Textarea {...p} rows={2} value={f.notes} onChange={(e) => set("notes", e.target.value)} />}
            </FormField>
          </div>
          <div className="flex justify-end">
            <Button type="submit" size="lg" loading={add.isPending}>
              <Plus /> Add transaction
            </Button>
          </div>
        </form>
      </CardBody>
    </Card>
  );
}
