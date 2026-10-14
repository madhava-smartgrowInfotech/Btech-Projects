import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Check } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";

import { PageHeader } from "@/components/ui/Layout";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Checkbox, Segmented, Switch } from "@/components/ui/Toggles";
import { Select } from "@/components/ui/Select";
import { CardsSkeleton, ErrorState } from "@/components/ui/Feedback";
import { FormField, Input, Label } from "@/components/ui/Field";
import { Stepper } from "@/components/ui/Navigation";
import api, { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { label } from "@/lib/evaluation";
import { keys } from "@/lib/queries";
import type { Profile, ProfileOptions, ProfileResponse, SaveProfileResponse } from "@/lib/types";

const STEPS = [
  { label: "Body", description: "Basics" },
  { label: "Goal", description: "Activity and target" },
  { label: "Diet", description: "Food and allergies" },
  { label: "Health", description: "Conditions" },
];

const ACTIVITY_TEXT: Record<string, string> = {
  sedentary: "Desk job, little exercise",
  light: "Light exercise 1-3 days a week",
  moderate: "Moderate exercise 3-5 days a week",
  active: "Hard exercise 6-7 days a week",
  very_active: "Very hard exercise or physical job",
};

interface Form {
  age: string;
  gender: "male" | "female" | "other";
  height_cm: string;
  weight_kg: string;
  activity: string;
  goal: string;
  diet_type: string;
  cuisine: string;
  allergies: string[];
  conditions: string[];
}

const EMPTY: Form = {
  age: "",
  gender: "female",
  height_cm: "",
  weight_kg: "",
  activity: "moderate",
  goal: "lose",
  diet_type: "vegetarian",
  cuisine: "both",
  allergies: [],
  conditions: [],
};

function fromProfile(p: Profile): Form {
  return {
    age: String(p.age),
    gender: p.gender,
    height_cm: String(p.height_cm),
    weight_kg: String(p.weight_kg),
    activity: p.activity,
    goal: p.goal,
    diet_type: p.diet_type,
    cuisine: p.cuisine,
    allergies: [...p.allergies],
    conditions: [...p.conditions],
  };
}

/** Returns a message for the first invalid field of a step, or null. */
function checkStep(step: number, f: Form): string | null {
  if (step === 0) {
    const age = Number(f.age);
    const h = Number(f.height_cm);
    const w = Number(f.weight_kg);
    if (!f.age || !Number.isInteger(age) || age < 18 || age > 90) return "Age must be a whole number from 18 to 90.";
    if (!f.height_cm || Number.isNaN(h) || h < 120 || h > 230) return "Height must be between 120 and 230 cm.";
    if (!f.weight_kg || Number.isNaN(w) || w < 30 || w > 250) return "Weight must be between 30 and 250 kg.";
  }
  return null;
}

export default function ProfileWizard() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { user, markProfile } = useAuth();
  const options = useQuery({
    queryKey: keys.profileOptions,
    queryFn: async () => (await api.get<ProfileOptions>("/profile/options")).data,
    staleTime: 60 * 60_000,
  });
  const existing = useQuery({
    queryKey: keys.profile,
    queryFn: async () => (await api.get<ProfileResponse>("/profile")).data,
  });

  const [step, setStep] = useState(0);
  const [form, setForm] = useState<Form>(EMPTY);
  const [stepError, setStepError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const prefilled = useRef(false);

  // Editing an existing profile: fill the form once, from the saved values.
  useEffect(() => {
    if (prefilled.current || !existing.data?.profile) return;
    prefilled.current = true;
    setForm(fromProfile(existing.data.profile));
  }, [existing.data]);

  const save = useMutation({
    mutationFn: async (body: Form) =>
      (
        await api.put<SaveProfileResponse>("/profile", {
          age: Number(body.age),
          gender: body.gender,
          height_cm: Number(body.height_cm),
          weight_kg: Number(body.weight_kg),
          activity: body.activity,
          goal: body.goal,
          diet_type: body.diet_type,
          cuisine: body.cuisine,
          allergies: body.allergies,
          conditions: body.conditions,
        })
      ).data,
    onSuccess: (data) => {
      qc.setQueryData(keys.profile, { profile: data.profile });
      qc.invalidateQueries({ queryKey: keys.targets });
      markProfile();
      toast.success(`Saved. Your daily target is ${Math.round(data.targets.kcal)} kcal.`);
      navigate("/dashboard");
    },
    onError: (err) => setSaveError(errorMessage(err)),
  });

  const set = <K extends keyof Form>(key: K, value: Form[K]) => setForm((f) => ({ ...f, [key]: value }));
  const toggleIn = (key: "allergies" | "conditions", value: string, on: boolean) =>
    setForm((f) => ({ ...f, [key]: on ? [...f[key], value] : f[key].filter((x) => x !== value) }));

  function next() {
    const problem = checkStep(step, form);
    setStepError(problem);
    if (problem) return;
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  }

  if (options.isError || existing.isError) {
    return (
      <ErrorState
        error={options.error ?? existing.error}
        title="Couldn't load your profile form"
        onRetry={() => {
          options.refetch();
          existing.refetch();
        }}
      />
    );
  }

  if (options.isPending || existing.isPending || !options.data) {
    return (
      <div className="space-y-6">
        <PageHeader title="Your profile" description="Loading your saved details." />
        <CardsSkeleton count={2} />
      </div>
    );
  }

  const opts = options.data;
  const editing = Boolean(existing.data?.profile);

  return (
    <div className="space-y-6">
      <PageHeader
        title={editing ? "Edit your profile" : `Welcome${user ? `, ${user.name.split(" ")[0]}` : ""}`}
        description={editing ? "Changing any detail recalculates your daily target." : "Four short steps. We use these details to size your calorie target."}
      />

      <Stepper
        steps={STEPS}
        current={step}
        onStepClick={(i) => {
          setStepError(null);
          setStep(i);
        }}
      />

      <Card>
        <CardHeader title={STEPS[step].label} description={STEPS[step].description} icon={<span className="text-sm font-semibold">{step + 1}</span>} />
        <CardBody className="space-y-5">
          {step === 0 && (
            <div className="grid gap-5 sm:grid-cols-2">
              <FormField label="Age (years)" hint="18 to 90">
                {(p) => <Input {...p} type="number" inputMode="numeric" min={18} max={90} value={form.age} onChange={(e) => set("age", e.target.value)} />}
              </FormField>
              <div className="space-y-1.5">
                <Label>Gender</Label>
                <Segmented
                  label="Gender"
                  value={form.gender}
                  onChange={(v) => set("gender", v)}
                  options={[
                    { value: "female", label: "Female" },
                    { value: "male", label: "Male" },
                    { value: "other", label: "Other" },
                  ]}
                />
              </div>
              <FormField label="Height (cm)" hint="120 to 230">
                {(p) => (
                  <Input {...p} type="number" inputMode="decimal" min={120} max={230} step="0.1" value={form.height_cm} onChange={(e) => set("height_cm", e.target.value)} />
                )}
              </FormField>
              <FormField label="Weight (kg)" hint="30 to 250. This is your starting weight.">
                {(p) => (
                  <Input {...p} type="number" inputMode="decimal" min={30} max={250} step="0.1" value={form.weight_kg} onChange={(e) => set("weight_kg", e.target.value)} />
                )}
              </FormField>
            </div>
          )}

          {step === 1 && (
            <div className="grid gap-5 sm:grid-cols-2">
              <FormField label="Activity level">
                {(p) => (
                  <Select
                    id={p.id}
                    aria-describedby={p["aria-describedby"]}
                    value={form.activity}
                    onValueChange={(v) => set("activity", v)}
                    options={opts.activity.map((a) => ({ value: a, label: label(a), description: ACTIVITY_TEXT[a] }))}
                  />
                )}
              </FormField>
              <div className="space-y-1.5">
                <Label>Goal</Label>
                <Segmented
                  label="Goal"
                  value={form.goal as "lose" | "maintain" | "gain"}
                  onChange={(v) => set("goal", v)}
                  options={opts.goal.map((g) => ({ value: g as "lose" | "maintain" | "gain", label: label(g) }))}
                />
                <p className="text-xs text-muted-foreground">Weight loss sets a deficit of about 500 kcal a day; gain sets a surplus.</p>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="grid gap-5 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Diet</Label>
                <Select
                  value={form.diet_type}
                  onValueChange={(v) => set("diet_type", v)}
                  aria-label="Diet type"
                  options={opts.diet_type.map((d) => ({ value: d, label: label(d).replace("Non vegetarian", "Non-vegetarian") }))}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Cuisine</Label>
                <Segmented
                  label="Cuisine"
                  value={form.cuisine as "north" | "south" | "both"}
                  onChange={(v) => set("cuisine", v)}
                  options={opts.cuisine.map((c) => ({ value: c as "north" | "south" | "both", label: label(c) }))}
                />
              </div>
              <fieldset className="space-y-3 sm:col-span-2">
                <legend className="text-sm font-medium">Allergies (these dishes are never suggested)</legend>
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                  {opts.allergies.map((a) => {
                    const id = `allergy-${a}`;
                    const on = form.allergies.includes(a);
                    return (
                      <label key={a} htmlFor={id} className="glass-flat flex cursor-pointer items-center gap-3 rounded-xl px-3 py-2.5 text-sm">
                        <Checkbox id={id} aria-label={label(a)} checked={on} onCheckedChange={(v) => toggleIn("allergies", a, v)} />
                        {label(a)}
                      </label>
                    );
                  })}
                </div>
              </fieldset>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">Tick any that apply. They tighten sodium, sugar, glycaemic load and fat limits.</p>
              <div className="grid gap-3 sm:grid-cols-3">
                {opts.conditions.map((c) => {
                  const id = `condition-${c}`;
                  const on = form.conditions.includes(c);
                  return (
                    <label key={c} htmlFor={id} className="glass-flat flex cursor-pointer items-center justify-between gap-3 rounded-xl px-4 py-3 text-sm">
                      {label(c)}
                      <Switch id={id} aria-label={label(c)} checked={on} onCheckedChange={(v) => toggleIn("conditions", c, v)} />
                    </label>
                  );
                })}
              </div>
              <p className="text-xs text-muted-foreground">
                NutriSense gives general nutrition guidance, not medical advice. If you have a condition or take medication, check your plan with a
                doctor or dietitian.
              </p>
            </div>
          )}

          {stepError && (
            <p role="alert" className="text-sm text-danger">
              {stepError}
            </p>
          )}
          {saveError && (
            <p role="alert" className="rounded-xl border border-danger/30 bg-danger/[0.06] px-3 py-2 text-sm text-danger">
              {saveError}
            </p>
          )}

          <div className="flex items-center justify-between gap-3 pt-2">
            <Button variant="ghost" onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0 || save.isPending}>
              <ArrowLeft /> Back
            </Button>
            {step < STEPS.length - 1 ? (
              <Button onClick={next}>
                Next <ArrowRight />
              </Button>
            ) : (
              <Button
                loading={save.isPending}
                onClick={() => {
                  const problem = checkStep(0, form);
                  if (problem) {
                    setStep(0);
                    setStepError(problem);
                    return;
                  }
                  setSaveError(null);
                  save.mutate(form);
                }}
              >
                {save.isPending ? "Saving…" : (
                  <>
                    <Check /> {editing ? "Save and recalculate" : "Save and see my target"}
                  </>
                )}
              </Button>
            )}
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
