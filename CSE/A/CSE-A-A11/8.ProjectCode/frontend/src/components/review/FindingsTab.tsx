import { PartyPopper, SearchX } from "lucide-react";
import { useMemo, useState } from "react";

import { FindingCard } from "@/components/app/FindingCard";
import { DonutChart, HBarChart } from "@/components/app/Charts";
import { ChartCard } from "@/components/charts/Chart";
import { EmptyState } from "@/components/ui/Feedback";
import { SearchField } from "@/components/ui/Field";
import { Segmented, Switch } from "@/components/ui/Toggles";
import { Button } from "@/components/ui/Button";
import { SEV_COLOR, SEV_ORDER, SEV_RANK, SEV_TONE } from "@/lib/domain";
import type { Review, Severity } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";

const CAP = 50;

export function FindingsTab({ review }: { review: Review }) {
  const s = review.stats;
  const [sev, setSev] = useState<Severity[]>(["critical", "high", "medium", "low"]);
  const [cat, setCat] = useState<"all" | "security" | "quality">("all");
  const [onlyDiff, setOnlyDiff] = useState(true);
  const [q, setQ] = useState("");

  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return review.findings
      .filter(
        (f) =>
          sev.includes(f.severity) &&
          (cat === "all" || f.category === cat) &&
          (f.in_diff || !onlyDiff) &&
          (!needle || (f.title + f.file + f.cwe + f.rule_id + f.function).toLowerCase().includes(needle)),
      )
      .sort((a, b) => SEV_RANK[b.severity] - SEV_RANK[a.severity] || a.file.localeCompare(b.file) || a.line - b.line);
  }, [review.findings, sev, cat, onlyDiff, q]);

  const donut = SEV_ORDER.filter((k) => s.by_severity[k]).map((k) => ({ name: k, value: s.by_severity[k], color: SEV_COLOR[k] }));
  const cwe = Object.entries(s.by_cwe).map(([name, value]) => ({ name, value }));
  const perFile = Object.entries(s.by_file).map(([name, value]) => ({ name, value }));

  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_20rem]">
      <div className="min-w-0 space-y-4">
        <div className="glass space-y-3 rounded-2xl p-4">
          <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label="Severity filter">
            {SEV_ORDER.map((k) => {
              const on = sev.includes(k);
              return (
                <button
                  key={k}
                  type="button"
                  aria-pressed={on}
                  onClick={() => setSev((cur) => (on ? cur.filter((x) => x !== k) : [...cur, k]))}
                  className={cn("rounded-full transition-opacity", !on && "opacity-45 hover:opacity-80")}
                >
                  <Badge tone={on ? SEV_TONE[k] : "neutral"} className="cursor-pointer px-2.5 py-1 uppercase tracking-wide">{k}</Badge>
                </button>
              );
            })}
          </div>
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
            <Segmented
              label="Category"
              value={cat}
              onChange={setCat}
              size="sm"
              options={[
                { value: "all", label: "All" },
                { value: "security", label: "Security" },
                { value: "quality", label: "Quality" },
              ]}
            />
            <label className="flex items-center gap-2 text-sm">
              <Switch checked={onlyDiff} onCheckedChange={setOnlyDiff} aria-label="Only changed lines" />
              Only changed lines
            </label>
            <SearchField value={q} onChange={setQ} label="Search findings" placeholder="sql, CWE-78, users.py…" className="lg:ml-auto lg:w-72" />
          </div>
        </div>

        <p className="text-sm text-muted-foreground" aria-live="polite">
          Showing {shown.length} of {review.findings.length} findings · {s.preexisting} pre-existing outside the diff
        </p>

        {review.findings.length === 0 ? (
          <EmptyState icon={<PartyPopper />} title="No findings at all" description="The agents found nothing to report in this change." />
        ) : shown.length === 0 ? (
          <EmptyState
            icon={<SearchX />}
            title="Nothing matches these filters"
            description="Widen the severity selection, include pre-existing issues, or clear the search."
            action={
              <Button
                variant="secondary"
                onClick={() => {
                  setSev([...SEV_ORDER]);
                  setCat("all");
                  setOnlyDiff(false);
                  setQ("");
                }}
              >
                Reset filters
              </Button>
            }
          />
        ) : (
          <div className="space-y-3">
            {shown.slice(0, CAP).map((f, i) => (
              <FindingCard key={f.id + i} f={f} defaultOpen={i === 0 && shown.length <= 3} />
            ))}
            {shown.length > CAP && (
              <p className="rounded-xl border border-info/30 bg-info/10 px-4 py-3 text-sm">
                {shown.length - CAP} more findings hidden. Narrow the filters or download the full report from the Export tab.
              </p>
            )}
          </div>
        )}
      </div>

      <aside className="space-y-4" aria-label="Finding charts">
        <ChartCard
          title="By severity"
          description="Findings in the changed lines"
          empty={donut.length === 0 ? "No findings in the changed lines" : undefined}
          legend={donut.map((d) => ({ label: d.name, color: d.color }))}
          table={{ columns: ["Severity", "Findings"], rows: donut.map((d) => [d.name, d.value]) }}
        >
          <DonutChart data={donut} centerLabel="findings" />
        </ChartCard>
        {cwe.length > 0 && (
          <ChartCard title="Weakness types (CWE)" table={{ columns: ["CWE", "Findings"], rows: cwe.map((d) => [d.name, d.value]) }}>
            <HBarChart data={cwe} color="#7C5CFF" top={6} valueLabel="Findings" labelWidth={80} />
          </ChartCard>
        )}
        {perFile.length > 1 && (
          <ChartCard title="Findings per file" table={{ columns: ["File", "Findings"], rows: perFile.map((d) => [d.name, d.value]) }}>
            <HBarChart data={perFile} color="#22D3EE" top={6} valueLabel="Findings" labelWidth={110} />
          </ChartCard>
        )}
      </aside>
    </div>
  );
}
