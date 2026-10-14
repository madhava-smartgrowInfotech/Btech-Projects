import { Activity, FileText, Search } from "lucide-react";
import { useMemo, useState } from "react";

import { SearchField } from "@/components/ui/Field";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/Feedback";
import { Select } from "@/components/ui/Select";
import { Timeline } from "@/components/ui/Display";
import { CATEGORY_LABEL, CATEGORY_TONE } from "@/lib/constants";
import type { TimelineItem } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const PAGE = 60;

/** One merged timeline across hospitals, filterable by category, hospital and text. */
export function RecordTimeline({ items, onExplain }: { items: TimelineItem[]; onExplain?: (item: TimelineItem) => void }) {
  const [category, setCategory] = useState("all");
  const [hospital, setHospital] = useState("all");
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(PAGE);

  const categories = useMemo(() => [...new Set(items.map((i) => i.category))].sort(), [items]);
  const hospitals = useMemo(() => {
    const map = new Map<string, string>();
    items.forEach((i) => map.set(i.hospital, i.hospital_name));
    return [...map.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [items]);

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    return items.filter(
      (i) =>
        (category === "all" || i.category === category) &&
        (hospital === "all" || i.hospital === hospital) &&
        (!q || `${i.title} ${i.value}`.toLowerCase().includes(q)),
    );
  }, [items, category, hospital, query]);

  const clear = () => {
    setCategory("all");
    setHospital("all");
    setQuery("");
    setLimit(PAGE);
  };

  return (
    <Card>
      <CardHeader
        icon={<Activity />}
        title="Unified timeline"
        description={`${items.length} entries from ${hospitals.length} hospital${hospitals.length === 1 ? "" : "s"}`}
      />
      <CardBody className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-[1fr_1fr_1.5fr]">
          <Select
            aria-label="Filter by category"
            value={category}
            onValueChange={(v) => {
              setCategory(v);
              setLimit(PAGE);
            }}
            options={[{ value: "all", label: "All categories" }, ...categories.map((c) => ({ value: c, label: CATEGORY_LABEL[c] ?? c }))]}
          />
          <Select
            aria-label="Filter by hospital"
            value={hospital}
            onValueChange={(v) => {
              setHospital(v);
              setLimit(PAGE);
            }}
            options={[{ value: "all", label: "All hospitals" }, ...hospitals.map(([k, n]) => ({ value: k, label: n }))]}
          />
          <SearchField
            value={query}
            onChange={(v) => {
              setQuery(v);
              setLimit(PAGE);
            }}
            placeholder="Search titles and values"
            label="Search timeline"
          />
        </div>

        {shown.length === 0 ? (
          <EmptyState
            icon={<Search />}
            title="No entries match"
            description="Nothing in this record fits these filters."
            action={
              <Button variant="secondary" size="sm" onClick={clear}>
                Clear filters
              </Button>
            }
          />
        ) : (
          <Timeline
            items={shown.slice(0, limit).map((i) => ({
              icon: i.type === "DiagnosticReport" ? <FileText /> : <Activity />,
              title: i.title || i.type,
              meta: [formatDate(i.date), i.hospital_name, i.status].filter(Boolean).join(" · "),
              body: (
                <>
                  {i.value && <span className="block">{i.value}</span>}
                  {onExplain && i.type === "DiagnosticReport" && <span className="mt-1 block text-xs text-violet-ink">Ask the assistant to explain this report</span>}
                </>
              ),
              trailing: <Badge tone={CATEGORY_TONE[i.category] ?? "neutral"}>{CATEGORY_LABEL[i.category] ?? i.category}</Badge>,
              onClick: onExplain && i.type === "DiagnosticReport" ? () => onExplain(i) : undefined,
            }))}
          />
        )}

        {shown.length > limit && (
          <div className="text-center">
            <Button variant="ghost" onClick={() => setLimit(limit + PAGE)}>
              Show more ({shown.length - limit} left)
            </Button>
          </div>
        )}
      </CardBody>
    </Card>
  );
}
