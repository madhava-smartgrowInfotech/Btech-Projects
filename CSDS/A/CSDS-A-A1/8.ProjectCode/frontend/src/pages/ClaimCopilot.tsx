import { ArrowLeft, ArrowRight, ClipboardCheck, FileText, Loader2, Stethoscope, Trash2 } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router";
import { toast } from "sonner";

import { ClaimResultView } from "@/components/claims/ClaimResult";
import { VerdictBadge } from "@/components/common/Badges";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { LanguageSelect } from "@/components/common/LanguageSelect";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorState } from "@/components/common/States";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useClaim, useClaims, useCreateClaim, useDeleteClaim, usePolicies } from "@/lib/queries";
import type { Language } from "@/lib/types";
import { cn, timeAgo } from "@/lib/utils";

const QUICK = ["Knee replacement", "Cataract surgery", "Dengue hospitalisation", "Appendix removal", "Kidney stone removal", "Normal delivery", "Chemotherapy"];
const STEPS = ["Policy", "Treatment", "Details", "Review"];

interface FormState {
  policy_id: number | null;
  treatment: string;
  hospitalization_type: string;
  claim_mode: string;
  policy_start_date: string;
  insured_age: string;
  pre_existing: string;
  estimated_cost: string;
  room_type: string;
  notes: string;
}

function Choice({ value, onChange, options, name }: { value: string; onChange: (v: string) => void; options: [string, string][]; name: string }) {
  return (
    <RadioGroup value={value} onValueChange={onChange} className="grid gap-2 sm:grid-cols-2" aria-label={name}>
      {options.map(([v, label]) => (
        <Label
          key={v}
          htmlFor={`${name}-${v}`}
          className={cn(
            "flex cursor-pointer items-center gap-2 rounded-lg border p-3 text-sm font-normal transition-colors hover:bg-accent",
            value === v && "border-primary bg-primary/5",
          )}
        >
          <RadioGroupItem id={`${name}-${v}`} value={v} /> {label}
        </Label>
      ))}
    </RadioGroup>
  );
}

function Wizard() {
  const { user } = useAuth();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const policies = usePolicies();
  const create = useCreateClaim();
  const ready = policies.data?.filter((p) => p.document.status === "ready") ?? [];
  const [step, setStep] = useState(0);
  const [language, setLanguage] = useState<Language>(user?.language ?? "en");
  const [form, setForm] = useState<FormState>({
    policy_id: params.get("policy") ? Number(params.get("policy")) : null,
    treatment: "",
    hospitalization_type: "planned",
    claim_mode: "cashless",
    policy_start_date: "",
    insured_age: "",
    pre_existing: "not_sure",
    estimated_cost: "",
    room_type: "not_sure",
    notes: "",
  });
  const set = (patch: Partial<FormState>) => setForm((f) => ({ ...f, ...patch }));

  useEffect(() => {
    if (!form.policy_id && ready.length === 1) set({ policy_id: ready[0].id });
  }, [ready.length]); // eslint-disable-line react-hooks/exhaustive-deps

  const canNext = [Boolean(form.policy_id), form.treatment.trim().length >= 2, true, true][step];
  const policy = ready.find((p) => p.id === form.policy_id);
  const today = new Date().toISOString().slice(0, 10);

  async function submit() {
    try {
      const body: Record<string, unknown> = {
        policy_id: form.policy_id,
        treatment: form.treatment.trim(),
        hospitalization_type: form.hospitalization_type,
        claim_mode: form.claim_mode,
        pre_existing: form.pre_existing,
        room_type: form.room_type,
        language,
      };
      if (form.policy_start_date) body.policy_start_date = form.policy_start_date;
      if (form.insured_age) body.insured_age = Number(form.insured_age);
      if (form.estimated_cost) body.estimated_cost = Number(form.estimated_cost);
      if (form.notes.trim()) body.notes = form.notes.trim();
      const result = await create.mutateAsync(body);
      navigate(`/app/claims/${result.id}`);
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }

  if (policies.isError) return <ErrorState error={policies.error} onRetry={() => policies.refetch()} />;
  if (policies.isLoading) return <Skeleton className="h-96" />;
  if (!ready.length) {
    return (
      <EmptyState
        icon={<FileText />}
        title="Add a policy first"
        description="Claim Copilot checks a treatment against your policy wording. Upload a policy or add the samples to begin."
        action={
          <Button asChild>
            <Link to="/app/policies">Go to My policies</Link>
          </Button>
        }
      />
    );
  }

  return (
    <Card className="gap-5">
      <CardHeader>
        <ol className="flex items-center gap-2" aria-label="Progress">
          {STEPS.map((label, i) => (
            <li key={label} className="flex flex-1 items-center gap-2">
              <span
                className={cn(
                  "grid size-7 shrink-0 place-items-center rounded-full border text-xs font-semibold transition-colors",
                  i < step && "border-primary bg-primary text-primary-foreground",
                  i === step && "border-primary text-primary",
                  i > step && "text-muted-foreground",
                )}
                aria-current={i === step ? "step" : undefined}
              >
                {i + 1}
              </span>
              <span className={cn("hidden text-sm sm:inline", i === step ? "font-medium" : "text-muted-foreground")}>{label}</span>
              {i < STEPS.length - 1 && <span className="h-px flex-1 bg-border" />}
            </li>
          ))}
        </ol>
      </CardHeader>
      <CardContent className="min-h-[280px]">
        <AnimatePresence mode="wait">
          <motion.div key={step} initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -16 }} transition={{ duration: 0.2 }}>
            {step === 0 && (
              <div className="space-y-3">
                <h2 className="font-semibold">Which policy will you claim under?</h2>
                <div className="grid gap-2 sm:grid-cols-2">
                  {ready.map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => set({ policy_id: p.id })}
                      className={cn(
                        "flex items-start gap-3 rounded-xl border p-4 text-left transition-colors hover:bg-accent",
                        form.policy_id === p.id && "border-primary bg-primary/5 ring-1 ring-primary",
                      )}
                      aria-pressed={form.policy_id === p.id}
                    >
                      <FileText className="mt-0.5 size-5 shrink-0 text-primary" />
                      <span className="min-w-0">
                        <span className="block font-medium">{p.display_name}</span>
                        <span className="block text-xs text-muted-foreground">{p.document.insurer}</span>
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
            {step === 1 && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="treatment" className="text-base font-semibold">
                    What treatment or hospitalisation is it for?
                  </Label>
                  <div className="relative">
                    <Stethoscope className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="treatment"
                      value={form.treatment}
                      onChange={(e) => set({ treatment: e.target.value })}
                      placeholder="e.g. Knee replacement surgery"
                      className="h-11 pl-9"
                      maxLength={200}
                      autoFocus
                    />
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {QUICK.map((q) => (
                    <Button key={q} type="button" variant={form.treatment === q ? "default" : "outline"} size="sm" onClick={() => set({ treatment: q })}>
                      {q}
                    </Button>
                  ))}
                </div>
                <div className="space-y-2">
                  <Label>Type of admission</Label>
                  <Choice
                    name="admission"
                    value={form.hospitalization_type}
                    onChange={(v) => set({ hospitalization_type: v })}
                    options={[
                      ["planned", "Planned hospitalisation"],
                      ["emergency", "Emergency"],
                      ["day_care", "Day-care procedure"],
                      ["not_sure", "Not sure"],
                    ]}
                  />
                </div>
              </div>
            )}
            {step === 2 && (
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2 sm:col-span-2">
                  <Label>How will you claim?</Label>
                  <Choice
                    name="mode"
                    value={form.claim_mode}
                    onChange={(v) => set({ claim_mode: v })}
                    options={[
                      ["cashless", "Cashless at a network hospital"],
                      ["reimbursement", "Pay first, get reimbursed"],
                    ]}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="start">Policy start date (first policy with this insurer)</Label>
                  <Input id="start" type="date" max={today} value={form.policy_start_date} onChange={(e) => set({ policy_start_date: e.target.value })} />
                  <p className="text-xs text-muted-foreground">Used to check waiting periods exactly.</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="age">Age of the patient</Label>
                  <Input id="age" type="number" min={0} max={120} value={form.insured_age} onChange={(e) => set({ insured_age: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cost">Estimated bill (₹)</Label>
                  <Input
                    id="cost"
                    type="number"
                    min={0}
                    step={1000}
                    placeholder="e.g. 250000"
                    value={form.estimated_cost}
                    onChange={(e) => set({ estimated_cost: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Room type</Label>
                  <Select value={form.room_type} onValueChange={(v) => set({ room_type: v })}>
                    <SelectTrigger className="w-full" aria-label="Room type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="not_sure">Not decided</SelectItem>
                      <SelectItem value="general_ward">General ward</SelectItem>
                      <SelectItem value="shared">Shared room</SelectItem>
                      <SelectItem value="single_private">Single private room</SelectItem>
                      <SelectItem value="deluxe">Deluxe / suite</SelectItem>
                      <SelectItem value="icu">ICU</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label>Was this condition present before the policy started?</Label>
                  <Choice
                    name="ped"
                    value={form.pre_existing}
                    onChange={(v) => set({ pre_existing: v })}
                    options={[
                      ["no", "No"],
                      ["yes", "Yes, it's pre-existing"],
                      ["not_sure", "Not sure"],
                    ]}
                  />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="notes">Anything else? (optional)</Label>
                  <Textarea id="notes" rows={2} maxLength={500} value={form.notes} onChange={(e) => set({ notes: e.target.value })} />
                </div>
              </div>
            )}
            {step === 3 && (
              <div className="space-y-4">
                <h2 className="font-semibold">Review</h2>
                <dl className="grid gap-2 text-sm sm:grid-cols-2">
                  {[
                    ["Policy", policy?.display_name],
                    ["Treatment", form.treatment],
                    ["Admission", form.hospitalization_type.replace("_", " ")],
                    ["Claim mode", form.claim_mode],
                    ["Policy start", form.policy_start_date || "Not given"],
                    ["Patient age", form.insured_age || "Not given"],
                    ["Estimated bill", form.estimated_cost ? `₹${Number(form.estimated_cost).toLocaleString("en-IN")}` : "Not given"],
                    ["Pre-existing", form.pre_existing.replace("_", " ")],
                  ].map(([k, v]) => (
                    <div key={k} className="rounded-lg bg-muted/50 px-3 py-2">
                      <dt className="text-xs text-muted-foreground">{k}</dt>
                      <dd className="font-medium capitalize">{v}</dd>
                    </div>
                  ))}
                </dl>
                <div className="flex flex-wrap items-center gap-3">
                  <Label>Answer language</Label>
                  <LanguageSelect value={language} onChange={setLanguage} />
                </div>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </CardContent>
      <div className="flex items-center justify-between gap-2 border-t px-6 pt-4">
        <Button variant="ghost" onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0 || create.isPending}>
          <ArrowLeft /> Back
        </Button>
        {step < STEPS.length - 1 ? (
          <Button onClick={() => setStep((s) => s + 1)} disabled={!canNext}>
            Next <ArrowRight />
          </Button>
        ) : (
          <Button onClick={submit} disabled={create.isPending}>
            {create.isPending ? <Loader2 className="animate-spin" /> : <ClipboardCheck />}
            {create.isPending ? "Reading your policy…" : "Check my claim"}
          </Button>
        )}
      </div>
    </Card>
  );
}

function History({ activeId }: { activeId: number | null }) {
  const { data, isLoading } = useClaims();
  const del = useDeleteClaim();
  const navigate = useNavigate();
  return (
    <Card className="gap-3">
      <CardHeader>
        <CardTitle className="text-base">Previous checks</CardTitle>
        <CardDescription>Saved with your checklist progress</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-24" />
        ) : !data?.length ? (
          <p className="text-sm text-muted-foreground">Your claim checks will appear here.</p>
        ) : (
          <ul className="space-y-1">
            {data.map((c) => (
              <li key={c.id} className="group relative">
                <Link
                  to={`/app/claims/${c.id}`}
                  className={cn("block rounded-lg px-3 py-2 pr-9 transition-colors hover:bg-accent", c.id === activeId && "bg-accent")}
                >
                  <div className="truncate text-sm font-medium">{c.treatment}</div>
                  <div className="mt-1 flex items-center gap-2">
                    <VerdictBadge verdict={c.verdict} />
                    <span className="truncate text-xs text-muted-foreground">{timeAgo(c.created_at)}</span>
                  </div>
                </Link>
                <ConfirmDialog
                  trigger={
                    <Button
                      variant="ghost"
                      size="icon-xs"
                      className="absolute right-1.5 top-2.5 opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
                      aria-label="Delete claim check"
                    >
                      <Trash2 />
                    </Button>
                  }
                  title="Delete this claim check?"
                  description="The verdict, checklist and steps will be removed."
                  confirmLabel="Delete"
                  destructive
                  onConfirm={() =>
                    del.mutate(c.id, {
                      onSuccess: () => c.id === activeId && navigate("/app/claims"),
                      onError: (e) => toast.error(errorMessage(e)),
                    })
                  }
                />
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

export default function ClaimCopilot() {
  const { caseId } = useParams();
  const id = caseId ? Number(caseId) : null;
  const claim = useClaim(id);

  return (
    <div>
      <PageHeader
        title="Claim Copilot"
        description="Describe a treatment - get a coverage verdict, eligibility pre-checks, a document checklist and the claim steps from your own policy."
        actions={
          id && (
            <Button asChild variant="outline">
              <Link to="/app/claims">
                <ClipboardCheck /> New claim check
              </Link>
            </Button>
          )
        }
      />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className="min-w-0">
          {!id ? (
            <Wizard />
          ) : claim.isError ? (
            <ErrorState error={claim.error} onRetry={() => claim.refetch()} />
          ) : claim.isLoading || !claim.data ? (
            <div className="space-y-4">
              <Skeleton className="h-40" />
              <Skeleton className="h-64" />
            </div>
          ) : (
            <ClaimResultView claim={claim.data} />
          )}
        </div>
        <aside className="lg:sticky lg:top-20 lg:self-start">
          <History activeId={id} />
        </aside>
      </div>
    </div>
  );
}
