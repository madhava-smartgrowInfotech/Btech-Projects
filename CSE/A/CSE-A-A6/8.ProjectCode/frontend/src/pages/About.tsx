import { Calculator, Cpu, ExternalLink, Gauge, ListChecks, ShieldAlert, Terminal } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { CardsSkeleton, ErrorState } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { TabPanel, Tabs } from "@/components/ui/Navigation";
import { useAbout, useConfig } from "@/lib/queries";

export default function About() {
  const about = useAbout();
  const config = useConfig();
  const [tab, setTab] = useState("pipeline");

  if (about.isPending || config.isPending) {
    return (
      <>
        <PageHeader title="How it works" />
        <CardsSkeleton count={6} />
      </>
    );
  }
  if (about.isError || config.isError || !about.data || !config.data) {
    return (
      <>
        <PageHeader title="How it works" />
        <ErrorState error={about.error ?? config.error} onRetry={() => void about.refetch()} />
      </>
    );
  }
  const a = about.data;
  const c = config.data;

  return (
    <>
      <PageHeader title="How it works" eyebrow={a.title} description={a.summary} />
      <Tabs
        value={tab}
        onValueChange={setTab}
        tabs={[
          { value: "pipeline", label: "Pipeline", icon: <Cpu /> },
          { value: "formulas", label: "Formulas & rules", icon: <Calculator /> },
          { value: "gates", label: "Quality gates", icon: <Gauge /> },
          { value: "limits", label: "Limits & reference", icon: <ShieldAlert /> },
          { value: "tools", label: "Offline tools", icon: <Terminal /> },
        ]}
      >
        <TabPanel value="pipeline">
          <ol className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {a.pipeline.map((step, i) => (
              <li key={step.name}>
                <Card className="h-full">
                  <CardBody className="space-y-2">
                    <Badge tone="gradient">Step {i + 1}</Badge>
                    <h3 className="font-display text-lg font-semibold">{step.name}</h3>
                    <p className="text-sm text-muted-foreground">{step.text}</p>
                  </CardBody>
                </Card>
              </li>
            ))}
          </ol>
        </TabPanel>

        <TabPanel value="formulas" className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader title="Formulas" icon={<Calculator />} />
            <CardBody className="pt-2">
              <dl className="divide-y divide-[var(--glass-border)]">
                {a.formulas.map((f) => (
                  <div key={f.name} className="py-3">
                    <dt className="text-sm font-medium">{f.name}</dt>
                    <dd className="mt-1 text-sm text-muted-foreground">{f.text}</dd>
                  </div>
                ))}
              </dl>
            </CardBody>
          </Card>
          <div className="space-y-4">
            <Card>
              <CardHeader title="When a warning appears" icon={<ListChecks />} description="Quality failures always take precedence over a verdict." />
              <CardBody className="pt-2">
                <ul className="space-y-2 text-sm text-muted-foreground">
                  {a.rules.map((r) => (
                    <li key={r} className="flex gap-2">
                      <span aria-hidden className="mt-2 size-1.5 shrink-0 rounded-full bg-grad-primary" />
                      {r}
                    </li>
                  ))}
                </ul>
              </CardBody>
            </Card>
            <Card>
              <CardHeader title="Default values" description="Editable on the Thresholds screen within these bounds." />
              <CardBody className="pt-2">
                <table className="w-full text-sm">
                  <caption className="sr-only">Default thresholds and allowed ranges</caption>
                  <thead>
                    <tr className="text-left text-xs text-muted-foreground">
                      <th scope="col" className="py-1.5 font-medium">Setting</th>
                      <th scope="col" className="py-1.5 text-right font-medium">Default</th>
                      <th scope="col" className="py-1.5 text-right font-medium">Range</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(c.bounds).map(([key, b]) => (
                      <tr key={key} className="border-t border-[var(--glass-border)]">
                        <th scope="row" className="py-2 text-left font-normal">{b.label}</th>
                        <td className="py-2 text-right tabular-nums">{c.defaults[key]}</td>
                        <td className="py-2 text-right tabular-nums text-muted-foreground">{b.min} - {b.max}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardBody>
            </Card>
          </div>
        </TabPanel>

        <TabPanel value="gates">
          <Card>
            <CardHeader title="Signal quality gates" icon={<Gauge />} description="A frame that fails any gate produces Unable to assess, never a guess. These are heuristic reliability checks, not proven occlusion detection." />
            <CardBody className="pt-3">
              <ul className="grid gap-2 md:grid-cols-2">
                {c.quality_gates.map((g) => (
                  <li key={g} className="rounded-xl border border-[var(--glass-border)] bg-[var(--glass)] p-3 text-sm">
                    {g}
                  </li>
                ))}
              </ul>
              <p className="mt-4 text-xs text-muted-foreground">
                Detector, presence and tracking confidence thresholds are all 0.7. A gap of more than 0.5 s between samples, or one second with no output, also resets the evidence.
              </p>
            </CardBody>
          </Card>
        </TabPanel>

        <TabPanel value="limits" className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader title="Limitations" icon={<ShieldAlert />} />
            <CardBody className="pt-2">
              <ul className="space-y-2 text-sm text-muted-foreground">
                {[...c.disclaimers, ...a.limitations].map((l) => (
                  <li key={l} className="flex gap-2">
                    <span aria-hidden className="mt-2 size-1.5 shrink-0 rounded-full bg-warning" />
                    {l}
                  </li>
                ))}
              </ul>
            </CardBody>
          </Card>
          <Card>
            <CardHeader title="Research inspiration" />
            <CardBody className="space-y-3 pt-2 text-sm text-muted-foreground">
              <p>{a.reference.citation}</p>
              <p>{a.reference.note}</p>
              <a
                href={a.reference.doi}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 font-medium text-violet-ink underline-offset-4 hover:underline"
              >
                DOI 10.1109/ACCESS.2026.3670924 <ExternalLink className="size-3.5" />
              </a>
            </CardBody>
          </Card>
        </TabPanel>

        <TabPanel value="tools">
          <Card>
            <CardHeader title="Command-line tools" icon={<Terminal />} description="Kept from the desktop prototype. Run them from the project folder with the project's .venv." />
            <CardBody className="pt-2">
              <dl className="divide-y divide-[var(--glass-border)]">
                {a.cli_tools.map((t) => (
                  <div key={t.name} className="flex flex-col gap-1 py-3 sm:flex-row sm:gap-6">
                    <dt className="shrink-0 font-mono text-sm sm:w-44">{t.name}</dt>
                    <dd className="text-sm text-muted-foreground">{t.text}</dd>
                  </div>
                ))}
              </dl>
            </CardBody>
          </Card>
        </TabPanel>
      </Tabs>
    </>
  );
}
