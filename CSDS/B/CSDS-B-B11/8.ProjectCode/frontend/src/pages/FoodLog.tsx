import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Camera, Database, Globe2, NotebookPen, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ConfirmModal } from "@/components/ui/Overlay";
import { EmptyState, ErrorState, InlineLoader, ProgressBar, Skeleton } from "@/components/ui/Feedback";
import { FileDrop } from "@/components/ui/FileDrop";
import { Input, SearchField, Label } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { Segmented } from "@/components/ui/Toggles";
import { Tabs, TabPanel } from "@/components/ui/Navigation";
import api, { errorMessage, today } from "@/lib/api";
import { fmt, label } from "@/lib/evaluation";
import { keys } from "@/lib/queries";
import {
  MEALS,
  type FoodResult,
  type LogDay,
  type LogEntry,
  type Meal,
  type PhotoResponse,
  type UsdaResult,
} from "@/lib/types";
import { useDebouncedValue } from "@/lib/useDebouncedValue";

const MAX_PHOTO_BYTES = 8 * 1024 * 1024;

interface LogBody {
  date: string;
  meal: Meal;
  grams: number;
  food_id?: number;
  fdc_id?: number;
  source?: "database" | "photo" | "usda";
}

export default function FoodLog() {
  const qc = useQueryClient();
  const [date, setDate] = useState(today());
  const [meal, setMeal] = useState<Meal>(defaultMeal());
  const [tab, setTab] = useState("database");

  const day = useQuery({
    queryKey: keys.logs(date),
    queryFn: async () => (await api.get<LogDay>("/logs", { params: { date } })).data,
  });

  const addLog = useMutation({
    mutationFn: async (body: LogBody) => (await api.post<LogEntry>("/logs", body)).data,
    onSuccess: (entry) => {
      qc.invalidateQueries({ queryKey: ["logs"] });
      qc.invalidateQueries({ queryKey: ["progress"] });
      toast.success(`Added ${entry.name} to ${MEALS.find((m) => m.value === entry.meal)?.label.toLowerCase()}.`);
    },
    onError: (err) => toast.error(errorMessage(err)),
  });

  const removeLog = useMutation({
    mutationFn: async (id: number) => (await api.delete(`/logs/${id}`)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["logs"] });
      qc.invalidateQueries({ queryKey: ["progress"] });
      toast.success("Entry removed.");
    },
    onError: (err) => toast.error(errorMessage(err)),
  });

  const busyFor = (source: LogBody["source"], id: number) =>
    addLog.isPending && addLog.variables?.source === source && (addLog.variables.food_id === id || addLog.variables.fdc_id === id);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Food log"
        description="Add what you ate. Totals update against today's target."
        actions={
          <div className="flex flex-wrap items-end gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="log-date">Day</Label>
              <Input id="log-date" type="date" value={date} max={today()} onChange={(e) => e.target.value && setDate(e.target.value)} className="w-auto" />
            </div>
          </div>
        }
      />

      <div className="space-y-2">
        <Label>Meal</Label>
        <Segmented label="Meal" value={meal} onChange={setMeal} options={MEALS.map((m) => ({ value: m.value, label: m.label }))} />
      </div>

      <Tabs
        value={tab}
        onValueChange={setTab}
        tabs={[
          { value: "database", label: "Dish database", icon: <Database /> },
          { value: "usda", label: "Ingredient (USDA)", icon: <Globe2 /> },
          { value: "photo", label: "From a photo", icon: <Camera /> },
        ]}
      >
        <TabPanel value="database">
          <DatabaseSearch
            busyFor={(id) => busyFor("database", id)}
            onLog={(f, grams) => addLog.mutate({ date, meal, grams, food_id: f.food_id, source: "database" })}
          />
        </TabPanel>
        <TabPanel value="usda">
          <UsdaSearch busyFor={(id) => busyFor("usda", id)} onLog={(u, grams) => addLog.mutate({ date, meal, grams, fdc_id: u.fdc_id, source: "usda" })} />
        </TabPanel>
        <TabPanel value="photo">
          <PhotoLogger busyFor={(id) => busyFor("photo", id)} onLog={(f, grams) => addLog.mutate({ date, meal, grams, food_id: f.food_id, source: "photo" })} />
        </TabPanel>
      </Tabs>

      <DayEntries
        date={date}
        data={day.data}
        pending={day.isPending}
        error={day.error}
        onRetry={() => day.refetch()}
        onDelete={(id) => removeLog.mutateAsync(id)}
        onAddFirst={() => setTab("database")}
      />
    </div>
  );
}

function defaultMeal(): Meal {
  const h = new Date().getHours();
  if (h < 11) return "breakfast";
  if (h < 16) return "lunch";
  if (h < 19) return "snack";
  return "dinner";
}

/* ---------- one result row: grams input + Log button ---------- */

function ResultRow({
  name,
  meta,
  badges,
  defaultGrams,
  kcalPer100,
  busy,
  onLog,
}: {
  name: string;
  meta: string;
  badges?: string[];
  defaultGrams: number;
  kcalPer100?: number;
  busy: boolean;
  onLog: (grams: number) => void;
}) {
  const [grams, setGrams] = useState(String(Math.round(defaultGrams)));
  const g = Number(grams);
  const valid = Number.isFinite(g) && g > 0 && g <= 3000;
  const id = `grams-${name.replace(/\W/g, "")}`;
  return (
    <li className="flex flex-col gap-3 py-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0 space-y-1">
        <div className="truncate text-sm font-medium">{name}</div>
        <div className="text-xs text-muted-foreground">
          {meta}
          {kcalPer100 !== undefined && valid ? ` · about ${fmt((kcalPer100 * g) / 100)} kcal` : ""}
        </div>
        {badges && badges.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {badges.map((b) => (
              <Badge key={b} tone="warning">
                {b}
              </Badge>
            ))}
          </div>
        )}
      </div>
      <div className="flex shrink-0 items-end gap-2">
        <div className="space-y-1">
          <Label htmlFor={id} className="text-xs text-muted-foreground">
            Grams
          </Label>
          <Input
            id={id}
            type="number"
            inputMode="decimal"
            min={1}
            max={3000}
            value={grams}
            onChange={(e) => setGrams(e.target.value)}
            aria-invalid={!valid || undefined}
            className="w-24"
          />
        </div>
        <Button size="md" disabled={!valid || busy} loading={busy} onClick={() => onLog(g)}>
          Log
        </Button>
      </div>
    </li>
  );
}

/* ---------- database ---------- */

function DatabaseSearch({ busyFor, onLog }: { busyFor: (id: number) => boolean; onLog: (f: FoodResult, grams: number) => void }) {
  const [q, setQ] = useState("");
  const query = useDebouncedValue(q.trim(), 300);
  const search = useQuery({
    queryKey: keys.search(query),
    enabled: query.length >= 2,
    queryFn: async () => (await api.get<{ results: FoodResult[] }>("/foods/search", { params: { q: query, limit: 15 } })).data.results,
  });

  return (
    <Card>
      <CardHeader title="Search the dish database" description="Indian dishes with nutrients per serving. Type at least 2 letters." />
      <CardBody className="space-y-4">
        <SearchField value={q} onChange={setQ} label="Search dishes" placeholder="e.g. dal, idli, paneer" />
        {query.length < 2 && <p className="text-sm text-muted-foreground">Start typing a dish name to see matches.</p>}
        {query.length >= 2 && search.isPending && (
          <div className="space-y-2" role="status" aria-label="Searching">
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </div>
        )}
        {search.isError && <ErrorState error={search.error} title="Search didn't work" onRetry={() => search.refetch()} />}
        {search.data && search.data.length === 0 && (
          <EmptyState icon={<Database />} title="No dish matches that" description="Try a shorter name, or use the USDA tab for a single ingredient." />
        )}
        {search.data && search.data.length > 0 && (
          <ul className="divide-y divide-[var(--glass-border)]">
            {search.data.map((f) => (
              <ResultRow
                key={f.food_id}
                name={f.name}
                meta={`${label(f.role)} · ${label(f.cuisine)} · ${Math.round(f.serving_g)} g serving`}
                badges={f.warnings}
                defaultGrams={f.serving_g}
                kcalPer100={f.per_100g.kcal}
                busy={busyFor(f.food_id)}
                onLog={(grams) => onLog(f, grams)}
              />
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}

/* ---------- USDA ---------- */

function UsdaSearch({ busyFor, onLog }: { busyFor: (id: number) => boolean; onLog: (u: UsdaResult, grams: number) => void }) {
  const [q, setQ] = useState("");
  const query = useDebouncedValue(q.trim(), 400);
  const search = useQuery({
    queryKey: keys.usda(query),
    enabled: query.length >= 2,
    retry: false,
    queryFn: async () => (await api.get<{ results: UsdaResult[] }>("/foods/usda", { params: { q: query } })).data.results,
  });

  return (
    <Card>
      <CardHeader title="Look up an ingredient" description="USDA FoodData Central, for single ingredients like 'paneer' or 'oats'." />
      <CardBody className="space-y-4">
        <SearchField value={q} onChange={setQ} label="Search ingredients" placeholder="e.g. paneer, chickpeas" />
        {query.length < 2 && <p className="text-sm text-muted-foreground">Type at least 2 letters.</p>}
        {query.length >= 2 && search.isPending && <InlineLoader label="Searching USDA" />}
        {search.isError && <ErrorState error={search.error} title="Ingredient lookup is unavailable" hint="Try the dish database instead." onRetry={() => search.refetch()} />}
        {search.data && search.data.length === 0 && <EmptyState icon={<Globe2 />} title="No ingredient matches" description="Try a more general word." />}
        {search.data && search.data.length > 0 && (
          <ul className="divide-y divide-[var(--glass-border)]">
            {search.data.map((u) => (
              <ResultRow
                key={u.fdc_id}
                name={u.name}
                meta={u.data_type ? `USDA · ${u.data_type}` : "USDA"}
                defaultGrams={100}
                busy={busyFor(u.fdc_id)}
                onLog={(grams) => onLog(u, grams)}
              />
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  );
}

/* ---------- photo ---------- */

function PhotoLogger({ busyFor, onLog }: { busyFor: (id: number) => boolean; onLog: (f: FoodResult, grams: number) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<PhotoResponse | null>(null);

  const recognise = useMutation({
    mutationFn: async (f: File) => {
      const fd = new FormData();
      fd.append("file", f);
      return (await api.post<PhotoResponse>("/logs/photo", fd)).data;
    },
    onSuccess: (data) => setResult(data),
    onError: () => setResult(null),
  });

  // A new photo clears the previous result.
  useEffect(() => {
    setResult(null);
    recognise.reset();
  }, [file]);

  return (
    <Card>
      <CardHeader title="Log from a photo" description="We recognise the dishes, then you pick the right match and portion." />
      <CardBody className="space-y-5">
        <FileDrop
          file={file}
          onFile={setFile}
          accept="image/jpeg,image/png,image/webp,image/heic,image/heif"
          title="Drop a meal photo here, or click to browse"
          hint="JPG, PNG, WEBP or HEIC, up to 8 MB"
          validate={(f) => {
            if (!f.type.startsWith("image/")) return "Upload a JPG, PNG or WEBP photo.";
            if (f.size > MAX_PHOTO_BYTES) return "That photo is larger than 8 MB. Try a smaller one.";
            return null;
          }}
        >
          <Button onClick={() => file && recognise.mutate(file)} loading={recognise.isPending} disabled={!file}>
            <Camera /> Recognise dish
          </Button>
        </FileDrop>

        {recognise.isPending && <InlineLoader label="Looking at your photo. This takes a few seconds." />}
        {recognise.isError && (
          <ErrorState error={recognise.error} title="Couldn't read this photo" hint="Log from the dish database instead, or try another photo." onRetry={() => file && recognise.mutate(file)} />
        )}

        {result && result.items.length === 0 && (
          <EmptyState icon={<Camera />} title="No food found" description="Try a clearer photo of the plate, taken from above." />
        )}

        {result && result.items.length > 0 && (
          <div className="space-y-5">
            {result.items.map((item, i) => (
              <section key={`${item.detected}-${i}`} aria-label={`Detected ${item.detected}`} className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-display font-semibold">{item.detected}</h3>
                  {item.confidence !== null && <Badge tone="violet">{Math.round(item.confidence * 100)}% sure</Badge>}
                  {!!item.estimated_grams && <Badge tone="neutral">about {Math.round(item.estimated_grams)} g</Badge>}
                </div>
                {item.description && <p className="text-sm text-muted-foreground">{item.description}</p>}
                {item.matches.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No dish in our database matches "{item.detected}". Use the dish search instead.</p>
                ) : (
                  <ul className="divide-y divide-[var(--glass-border)] rounded-2xl border border-[var(--glass-border)] px-4">
                    {item.matches.map((m) => (
                      <ResultRow
                        key={m.food_id}
                        name={m.name}
                        meta={`${label(m.role)} · ${label(m.cuisine)}`}
                        badges={m.warnings}
                        defaultGrams={m.grams}
                        kcalPer100={m.per_100g.kcal}
                        busy={busyFor(m.food_id)}
                        onLog={(grams) => onLog(m, grams)}
                      />
                    ))}
                  </ul>
                )}
              </section>
            ))}
          </div>
        )}
      </CardBody>
    </Card>
  );
}

/* ---------- entries for the chosen day ---------- */

function DayEntries({
  date,
  data,
  pending,
  error,
  onRetry,
  onDelete,
  onAddFirst,
}: {
  date: string;
  data: LogDay | undefined;
  pending: boolean;
  error: unknown;
  onRetry: () => void;
  onDelete: (id: number) => Promise<unknown>;
  onAddFirst: () => void;
}) {
  if (pending) {
    return <Skeleton className="h-64 w-full rounded-2xl" />;
  }
  if (!data) {
    return <ErrorState error={error} title="Couldn't load this day" onRetry={onRetry} />;
  }

  const rows: { key: string; label: string; value: number; target: number; unit: string }[] = [
    { key: "kcal", label: "Calories", value: data.totals.kcal, target: data.targets.kcal, unit: "kcal" },
    { key: "protein", label: "Protein", value: data.totals.protein, target: data.targets.protein, unit: "g" },
    { key: "carbs", label: "Carbs", value: data.totals.carbs, target: data.targets.carbs, unit: "g" },
    { key: "fat", label: "Fat", value: data.totals.fat, target: data.targets.fat, unit: "g" },
  ];

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <Card className="lg:col-span-2">
        <CardHeader title={`Logged on ${new Date(`${date}T00:00:00`).toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "short" })}`} />
        <CardBody>
          {data.entries.length === 0 ? (
            <EmptyState
              icon={<NotebookPen />}
              title="Nothing logged for this day"
              description="Pick a meal above, then add a dish, ingredient or photo."
              action={
                <Button size="sm" onClick={onAddFirst}>
                  Add a dish
                </Button>
              }
            />
          ) : (
            <div className="space-y-5">
              {MEALS.map((m) => {
                const items = data.entries.filter((e) => e.meal === m.value);
                if (!items.length) return null;
                return (
                  <section key={m.value} aria-labelledby={`entries-${m.value}`}>
                    <h3 id={`entries-${m.value}`} className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      {m.label}
                    </h3>
                    <ul className="divide-y divide-[var(--glass-border)]">
                      {items.map((e) => (
                        <li key={e.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                          <div className="min-w-0">
                            <div className="truncate">{e.name}</div>
                            <div className="text-xs text-muted-foreground tabular-nums">
                              {Math.round(e.grams)} g · {fmt(e.kcal)} kcal · P {fmt(e.protein)} g · {e.source === "photo" ? "from photo" : e.source === "usda" ? "USDA" : "database"}
                            </div>
                          </div>
                          <ConfirmModal
                            title={`Remove ${e.name}?`}
                            description="This entry will be removed from your log. You can add it again."
                            confirmLabel="Remove"
                            onConfirm={() => onDelete(e.id)}
                            trigger={
                              <Button variant="ghost" size="icon-sm" aria-label={`Remove ${e.name}`} className="text-muted-foreground hover:text-danger">
                                <Trash2 />
                              </Button>
                            }
                          />
                        </li>
                      ))}
                    </ul>
                  </section>
                );
              })}
            </div>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Day totals" description="Against your daily targets" />
        <CardBody className="space-y-4">
          {rows.map((r) => {
            const pct = r.target ? (r.value / r.target) * 100 : 0;
            return (
              <div key={r.key} className="space-y-1.5">
                <div className="flex items-center justify-between text-sm">
                  <span>{r.label}</span>
                  <span className="tabular-nums text-muted-foreground">
                    {fmt(r.value)} / {fmt(r.target)} {r.unit}
                  </span>
                </div>
                <ProgressBar value={pct} label={`${r.label}: ${Math.round(pct)} percent of target`} />
              </div>
            );
          })}
          <p className="text-xs text-muted-foreground">Fibre {fmt(data.totals.fibre)} g of {fmt(data.targets.fibre)} g · sodium {fmt(data.totals.sodium)} mg of {fmt(data.targets.sodium)} mg</p>
        </CardBody>
      </Card>
    </div>
  );
}
