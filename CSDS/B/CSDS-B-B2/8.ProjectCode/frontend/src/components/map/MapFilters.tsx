import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import type { CoverageFilters, CoverageSummary } from "@/lib/coverage";
import { cn } from "@/lib/utils";
import { SOURCE_LABEL } from "@/lib/zones";

const PERIODS = [
  { value: "all", label: "All time", days: null },
  { value: "1", label: "Last 24 hours", days: 1 },
  { value: "7", label: "Last 7 days", days: 7 },
  { value: "30", label: "Last 30 days", days: 30 },
];
const HOURS: { label: string; value: [number, number] | null }[] = [
  { label: "All day", value: null },
  { label: "Morning", value: [6, 12] },
  { label: "Afternoon", value: [12, 18] },
  { label: "Evening", value: [18, 24] },
  { label: "Night", value: [0, 6] },
];

function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "rounded-full border px-3 py-1.5 text-xs font-medium transition-colors focus-visible:ring-2 focus-visible:ring-ring",
        active ? "border-primary bg-primary text-primary-foreground" : "bg-card hover:bg-accent",
      )}
    >
      {children}
    </button>
  );
}

export function MapFilters({ value, onChange, summary }: { value: CoverageFilters; onChange: (f: CoverageFilters) => void; summary?: CoverageSummary }) {
  const set = (patch: Partial<CoverageFilters>) => onChange({ ...value, ...patch });
  const sources = summary?.sources.map((s) => s.name) ?? [];
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground">Operator</Label>
          <Select value={value.operator ?? "all"} onValueChange={(v) => set({ operator: v === "all" ? null : v })}>
            <SelectTrigger className="h-9" aria-label="Operator">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="z-[1200]">
              <SelectItem value="all">All operators</SelectItem>
              {summary?.operators.map((o) => (
                <SelectItem key={o.name} value={o.name}>
                  {o.name} ({o.readings.toLocaleString()})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground">Period</Label>
          <Select value={value.days ? String(value.days) : "all"} onValueChange={(v) => set({ days: PERIODS.find((p) => p.value === v)?.days ?? null })}>
            <SelectTrigger className="h-9" aria-label="Period">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="z-[1200]">
              {PERIODS.map((p) => (
                <SelectItem key={p.value} value={p.value}>
                  {p.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-1.5">
        <Label className="text-xs text-muted-foreground">Time of day (your local time)</Label>
        <div className="flex flex-wrap gap-1.5">
          {HOURS.map((h) => (
            <Chip key={h.label} active={JSON.stringify(value.hours) === JSON.stringify(h.value)} onClick={() => set({ hours: h.value })}>
              {h.label}
              {h.value && <span className="ml-1 opacity-70 tabular">{String(h.value[0]).padStart(2, "0")}–{String(h.value[1] % 24).padStart(2, "0")}</span>}
            </Chip>
          ))}
        </div>
      </div>

      {sources.length > 1 && (
        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground">Data sources</Label>
          <div className="flex flex-wrap gap-1.5">
            {sources.map((s) => {
              const active = value.sources.length === 0 || value.sources.includes(s);
              return (
                <Chip
                  key={s}
                  active={active}
                  onClick={() => {
                    const current = value.sources.length ? value.sources : sources;
                    const next = active ? current.filter((x) => x !== s) : [...current, s];
                    set({ sources: next.length === sources.length || next.length === 0 ? [] : next });
                  }}
                >
                  {SOURCE_LABEL[s] ?? s}
                </Chip>
              );
            })}
          </div>
        </div>
      )}

      <label className="flex items-center justify-between gap-3 text-sm">
        <span>
          Include phone readings taken over Wi-Fi
          <span className="block text-xs text-muted-foreground">They describe the Wi-Fi line, not the mobile network.</span>
        </span>
        <Switch checked={value.includeWifi} onCheckedChange={(v) => set({ includeWifi: v })} />
      </label>
    </div>
  );
}
