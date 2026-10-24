import { useMutation, useQueryClient } from "@tanstack/react-query";
import { RotateCcw, Save, SlidersHorizontal } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { FormField, Input } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { toast } from "@/components/ui/Toast";
import { endpoints, errorMessage } from "@/lib/api";
import { keys, useConfig, useSettings } from "@/lib/queries";

const ORDER = ["ear_threshold", "closure_seconds", "persistence_seconds", "closed_fraction", "tilt_degrees", "cooldown_seconds"];

export default function Thresholds() {
  const settings = useSettings();
  const config = useConfig();
  const queryClient = useQueryClient();
  const [form, setForm] = useState<Record<string, string>>({});
  const [serverError, setServerError] = useState<string | null>(null);

  // load the saved values into the form once
  useEffect(() => {
    if (settings.data && Object.keys(form).length === 0) {
      setForm(Object.fromEntries(Object.entries(settings.data.settings).map(([k, v]) => [k, String(v)])));
    }
  }, [settings.data, form]);

  const bounds = config.data?.bounds;
  const errors = useMemo(() => {
    const out: Record<string, string> = {};
    if (!bounds) return out;
    for (const key of ORDER) {
      const b = bounds[key];
      const raw = form[key];
      if (raw === undefined) continue;
      const value = Number(raw);
      if (raw.trim() === "" || !Number.isFinite(value)) out[key] = "Enter a number.";
      else if (value < b.min || value > b.max) out[key] = `Must be between ${b.min} and ${b.max}.`;
    }
    return out;
  }, [form, bounds]);

  const save = useMutation({
    mutationFn: () => endpoints.saveSettings(Object.fromEntries(ORDER.map((k) => [k, Number(form[k])]))),
    onSuccess: (data) => {
      setServerError(null);
      queryClient.setQueryData(keys.settings, data);
      toast.success("Thresholds saved. Monitoring was stopped; restart it to use the new settings.");
    },
    onError: (e) => setServerError(errorMessage(e, "Could not save the thresholds.")),
  });

  const dirty = settings.data ? ORDER.some((k) => Number(form[k]) !== settings.data.settings[k]) : false;
  const invalid = Object.keys(errors).length > 0;

  return (
    <>
      <PageHeader
        title="Rule thresholds"
        eyebrow="Experimental"
        description="Adjust the baseline rules. These are demonstration choices, not measured safety specifications. Saving stops monitoring and clears the calibrated status."
        actions={
          settings.data && (
            <Badge tone={settings.data.calibrated ? "success" : "neutral"}>{settings.data.calibrated ? "Personally calibrated" : "Not calibrated"}</Badge>
          )
        }
      />

      {settings.isPending || config.isPending ? (
        <Card>
          <CardBody className="grid gap-5 sm:grid-cols-2" role="status" aria-label="Loading thresholds">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-10 w-full" />
              </div>
            ))}
          </CardBody>
        </Card>
      ) : settings.isError || config.isError || !bounds ? (
        <ErrorState error={settings.error ?? config.error} title="Couldn't load the thresholds" onRetry={() => void settings.refetch()} />
      ) : (
        <form
          noValidate
          onSubmit={(e) => {
            e.preventDefault();
            if (!invalid) save.mutate();
          }}
        >
          <Card>
            <CardHeader icon={<SlidersHorizontal />} title="Detection rules" description={settings.data?.note} />
            <CardBody className="grid gap-5 sm:grid-cols-2">
              {ORDER.map((key) => {
                const b = bounds[key];
                return (
                  <FormField key={key} label={b.label} hint={`${b.help} Range ${b.min} - ${b.max}.`} error={errors[key]}>
                    {(props) => (
                      <Input
                        {...props}
                        type="number"
                        inputMode="decimal"
                        step={b.step}
                        min={b.min}
                        max={b.max}
                        value={form[key] ?? ""}
                        onChange={(e) => {
                          setServerError(null);
                          setForm((f) => ({ ...f, [key]: e.target.value }));
                        }}
                      />
                    )}
                  </FormField>
                );
              })}
            </CardBody>
            {serverError && (
              <p role="alert" className="mx-5 mb-2 rounded-xl border border-danger/30 bg-danger/[0.07] p-3 text-sm text-danger">
                {serverError}
              </p>
            )}
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--glass-border)] p-5">
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  if (config.data) setForm(Object.fromEntries(Object.entries(config.data.defaults).map(([k, v]) => [k, String(v)])));
                }}
              >
                <RotateCcw /> Reset to defaults
              </Button>
              <Button type="submit" loading={save.isPending} disabled={invalid || !dirty}>
                <Save /> Save thresholds
              </Button>
            </div>
          </Card>
        </form>
      )}
    </>
  );
}
