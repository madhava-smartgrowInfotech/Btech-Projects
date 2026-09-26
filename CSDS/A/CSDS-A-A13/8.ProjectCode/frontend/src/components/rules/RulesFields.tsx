import { Minus, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Switch } from "@/components/ui/switch";
import type { Rules } from "@/lib/types";
import { cn } from "@/lib/utils";

/** A 3x3 diagram of which seats count as neighbours. */
function NeighbourDiagram({ adjacency }: { adjacency: 4 | 8 }) {
  return (
    <div className="grid w-fit grid-cols-3 gap-1" aria-hidden>
      {Array.from({ length: 9 }, (_, i) => {
        const r = Math.floor(i / 3);
        const c = i % 3;
        const centre = i === 4;
        const diagonal = r !== 1 && c !== 1;
        const neighbour = !centre && (adjacency === 8 || !diagonal);
        return (
          <span
            key={i}
            className={cn(
              "size-4 rounded-[4px] border",
              centre && "border-primary bg-primary",
              neighbour && "border-destructive/50 bg-destructive/20",
              !centre && !neighbour && "bg-muted",
            )}
          />
        );
      })}
    </div>
  );
}

function OptionCard({ value, checked, title, description, children }: {
  value: string;
  checked: boolean;
  title: string;
  description: string;
  children?: React.ReactNode;
}) {
  return (
    <Label
      htmlFor={`opt-${value}`}
      className={cn(
        "flex cursor-pointer items-start gap-3 rounded-xl border p-4 font-normal transition-colors hover:bg-accent/60",
        checked && "border-primary bg-primary/5 hover:bg-primary/5",
      )}
    >
      <RadioGroupItem value={value} id={`opt-${value}`} className="mt-0.5" />
      <div className="min-w-0 flex-1">
        <div className="text-sm font-medium">{title}</div>
        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{description}</p>
      </div>
      {children}
    </Label>
  );
}

export function RulesFields({ value, onChange, showAccessibleDefault = false }: {
  value: Rules;
  onChange: (rules: Rules) => void;
  showAccessibleDefault?: boolean;
}) {
  const set = <K extends keyof Rules>(key: K, v: Rules[K]) => onChange({ ...value, [key]: v });
  const clampGap = (n: number) => Math.max(0, Math.min(100, Number.isFinite(n) ? Math.round(n) : 0));

  return (
    <div className="space-y-7">
      <fieldset>
        <legend className="mb-1 text-sm font-semibold">Neighbours</legend>
        <p className="mb-3 text-xs text-muted-foreground">Neighbours never write the same paper. Aisles always separate seats.</p>
        <RadioGroup
          value={String(value.adjacency)}
          onValueChange={(v) => set("adjacency", Number(v) as 4 | 8)}
          className="grid gap-3 sm:grid-cols-2"
        >
          <OptionCard value="8" checked={value.adjacency === 8} title="8 neighbours" description="Front, back, sides and the four diagonals. Strongest protection.">
            <NeighbourDiagram adjacency={8} />
          </OptionCard>
          <OptionCard value="4" checked={value.adjacency === 4} title="4 neighbours" description="Front, back and sides only. Fits more candidates of one paper in a hall.">
            <NeighbourDiagram adjacency={4} />
          </OptionCard>
        </RadioGroup>
      </fieldset>

      <fieldset>
        <legend className="mb-1 text-sm font-semibold">Roll-number gap</legend>
        <p className="mb-3 text-xs text-muted-foreground">
          Neighbours' roll numbers (with the same prefix) must differ by at least this much. 0 turns the rule off.
        </p>
        <div className="flex items-center gap-2">
          <Button type="button" variant="outline" size="icon" aria-label="Decrease gap" onClick={() => set("roll_gap", clampGap(value.roll_gap - 1))}>
            <Minus />
          </Button>
          <Input
            type="number"
            inputMode="numeric"
            min={0}
            max={100}
            className="w-20 text-center tabular"
            value={value.roll_gap}
            onChange={(e) => set("roll_gap", clampGap(Number(e.target.value)))}
            aria-label="Roll-number gap"
          />
          <Button type="button" variant="outline" size="icon" aria-label="Increase gap" onClick={() => set("roll_gap", clampGap(value.roll_gap + 1))}>
            <Plus />
          </Button>
          <span className="ml-2 text-xs text-muted-foreground">
            {value.roll_gap === 0 ? "Off" : `e.g. 017 may sit next to ${String(17 + value.roll_gap).padStart(3, "0")}, not ${String(17 + value.roll_gap - 1).padStart(3, "0")}`}
          </span>
        </div>
      </fieldset>

      <fieldset className="flex items-start justify-between gap-4 rounded-xl border p-4">
        <div>
          <legend className="text-sm font-semibold">Department mix</legend>
          <p className="mt-1 text-xs text-muted-foreground">
            Spread each department across halls and keep candidates from the same department apart where possible.
          </p>
        </div>
        <Switch checked={value.department_mix} onCheckedChange={(v) => set("department_mix", v)} aria-label="Department mix" />
      </fieldset>

      <fieldset>
        <legend className="mb-3 text-sm font-semibold">Hall usage</legend>
        <RadioGroup
          value={value.fill_strategy}
          onValueChange={(v) => set("fill_strategy", v as Rules["fill_strategy"])}
          className="grid gap-3 sm:grid-cols-2"
        >
          <OptionCard value="compact" checked={value.fill_strategy === "compact"} title="Compact" description="Use as few halls as possible, so fewer invigilators are needed." />
          <OptionCard value="balanced" checked={value.fill_strategy === "balanced"} title="Balanced" description="Use every selected hall and fill them evenly, leaving more space." />
        </RadioGroup>
      </fieldset>

      {showAccessibleDefault && (
        <fieldset>
          <legend className="mb-1 text-sm font-semibold">Accessible seats per hall</legend>
          <p className="mb-3 text-xs text-muted-foreground">
            Used when a hall file lists no accessible seats: the front-row seats nearest the door are reserved.
          </p>
          <Input
            type="number"
            inputMode="numeric"
            min={0}
            max={20}
            className="w-24 tabular"
            value={value.accessible_per_hall}
            onChange={(e) => set("accessible_per_hall", Math.max(0, Math.min(20, Math.round(Number(e.target.value) || 0))))}
            aria-label="Accessible seats per hall"
          />
        </fieldset>
      )}
    </div>
  );
}
