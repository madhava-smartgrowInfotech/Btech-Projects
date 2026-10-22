import { useMutation } from "@tanstack/react-query";
import { AtSign, IndianRupee, Mail, Save, Sparkles, User as UserIcon } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { FormField, Input } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { ConfirmModal } from "@/components/ui/Overlay";
import { Select } from "@/components/ui/Select";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage, type User } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useMeta, useRefreshData } from "@/lib/queries";
import { formatDate } from "@/lib/utils";

export default function Profile() {
  const { user, setUser } = useAuth();
  const meta = useMeta();
  const refresh = useRefreshData();
  const [f, setF] = useState({
    name: user?.name ?? "",
    email: user?.email ?? "",
    monthly_income: String(user?.monthly_income ?? 0),
    currency: user?.currency ?? "INR",
    risk_profile: user?.risk_profile ?? "Moderate",
    savings_target: String(user?.savings_target ?? 0),
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [confirmDemo, setConfirmDemo] = useState(false);

  useEffect(() => {
    if (user)
      setF({
        name: user.name,
        email: user.email,
        monthly_income: String(user.monthly_income),
        currency: user.currency,
        risk_profile: user.risk_profile,
        savings_target: String(user.savings_target),
      });
  }, [user]);

  const save = useMutation({
    mutationFn: async () =>
      (await api.put<User>("/profile", { ...f, monthly_income: Number(f.monthly_income || 0), savings_target: Number(f.savings_target || 0) })).data,
    onSuccess: async (u) => {
      setUser(u);
      toast.success("Profile updated");
      await refresh();
    },
    onError: (e) => toast.error("Could not save your profile", { description: errorMessage(e) }),
  });

  const demo = useMutation({
    mutationFn: async () => (await api.post<{ transactions: number }>("/profile/demo-data")).data,
    onSuccess: async (r) => {
      toast.success("Demo data loaded", { description: `${r.transactions} sample transactions plus budgets, goals and investments. Visit the dashboard to see it.` });
      await refresh();
    },
    onError: (e) => toast.error("Could not load demo data", { description: errorMessage(e) }),
  });

  function submit(e: FormEvent) {
    e.preventDefault();
    const next: Record<string, string> = {};
    if (!f.name.trim()) next.name = "Name is required.";
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(f.email.trim())) next.email = "Please enter a valid email address.";
    if (Number(f.monthly_income) < 0) next.monthly_income = "Cannot be negative.";
    if (Number(f.savings_target) < 0) next.savings_target = "Cannot be negative.";
    setErrors(next);
    if (!Object.keys(next).length) save.mutate();
  }

  if (!user) return null;
  const opts = (xs: string[] | undefined, fallback: string[]) => (xs ?? fallback).map((x) => ({ value: x, label: x }));

  return (
    <>
      <PageHeader title="Profile" description="Your details and preferences. Monthly income is used when you have not recorded income for the month yet." />
      <div className="grid gap-6 lg:grid-cols-[1fr_22rem]">
        <Card>
          <CardHeader title="Your details" description={`Member since ${formatDate(user.created_at)}`} icon={<UserIcon />} />
          <CardBody>
            <form onSubmit={submit} className="space-y-5" noValidate>
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField label="Name" error={errors.name}>
                  {(p) => <Input {...p} icon={<UserIcon />} value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} autoComplete="name" />}
                </FormField>
                <FormField label="Email" error={errors.email}>
                  {(p) => <Input {...p} type="email" icon={<Mail />} value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} autoComplete="email" />}
                </FormField>
                <FormField label="Username" hint="Usernames cannot be changed.">
                  {(p) => <Input {...p} icon={<AtSign />} value={user.username} readOnly disabled />}
                </FormField>
                <FormField label="Preferred currency">
                  {(p) => <Select {...p} value={f.currency} onValueChange={(v) => setF({ ...f, currency: v })} options={opts(meta.data?.currencies, ["INR", "USD", "EUR", "GBP"])} />}
                </FormField>
                <FormField label="Monthly income" error={errors.monthly_income}>
                  {(p) => <Input {...p} type="number" min="0" step="500" icon={<IndianRupee />} value={f.monthly_income} onChange={(e) => setF({ ...f, monthly_income: e.target.value })} />}
                </FormField>
                <FormField label="Savings target" error={errors.savings_target}>
                  {(p) => <Input {...p} type="number" min="0" step="500" icon={<IndianRupee />} value={f.savings_target} onChange={(e) => setF({ ...f, savings_target: e.target.value })} />}
                </FormField>
                <FormField label="Risk preference" className="sm:col-span-2">
                  {(p) => <Select {...p} value={f.risk_profile} onValueChange={(v) => setF({ ...f, risk_profile: v })} options={opts(meta.data?.risk_profiles, ["Conservative", "Moderate", "Aggressive"])} />}
                </FormField>
              </div>
              <div className="flex justify-end">
                <Button type="submit" size="lg" loading={save.isPending}>
                  <Save /> Save changes
                </Button>
              </div>
            </form>
          </CardBody>
        </Card>

        <Card className="h-fit">
          <CardHeader title="Demo data" description="Fictional sample data" icon={<Sparkles />} />
          <CardBody className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Load a few months of fictional transactions, budgets, goals and investments to explore FINJARVIS right away. It is added to what you already have.
            </p>
            <Button variant="secondary" className="w-full" onClick={() => setConfirmDemo(true)} loading={demo.isPending}>
              <Sparkles /> Load demo data
            </Button>
          </CardBody>
        </Card>
      </div>
      <ConfirmModal
        open={confirmDemo}
        onOpenChange={setConfirmDemo}
        title="Add demo data to your account?"
        description="This adds about 35 fictional transactions, 5 budgets, 3 goals and 4 investments next to your own records. Loading it twice duplicates it."
        confirmLabel="Add demo data"
        onConfirm={async () => {
          await demo.mutateAsync();
        }}
      />
    </>
  );
}
