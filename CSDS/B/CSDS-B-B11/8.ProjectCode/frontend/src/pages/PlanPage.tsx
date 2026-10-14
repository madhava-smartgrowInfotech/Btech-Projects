import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarDays, ChefHat, Repeat2, Sparkles } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Drawer } from "@/components/ui/Overlay";
import { CardsSkeleton, EmptyState, ErrorState, InlineLoader, ProgressBar, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { Tabs, TabPanel } from "@/components/ui/Navigation";
import api, { errorMessage, today } from "@/lib/api";
import { fmt, label } from "@/lib/evaluation";
import { keys } from "@/lib/queries";
import {
  MEALS,
  type Meal,
  type Plan,
  type PlanDay,
  type PlanDish,
  type PlanLatestResponse,
  type Recipe,
  type SwapOption,
  type SwapOptionsResponse,
} from "@/lib/types";

type SwapTarget = { day: number; meal: Meal; index: number; dish: PlanDish };
type RecipeTarget = { food_id: number; name: string; grams: number };

const dayMonth = (iso: string) => new Date(`${iso}T00:00:00`).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
const shortDay = (iso: string) => new Date(`${iso}T00:00:00`).toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" });

function dayTotals(day: PlanDay) {
  const dishes = MEALS.flatMap((m) => day.meals[m.value]);
  return dishes.reduce(
    (t, d) => ({ kcal: t.kcal + d.kcal, protein: t.protein + d.protein, carbs: t.carbs + d.carbs, fat: t.fat + d.fat, fibre: t.fibre + d.fibre }),
    { kcal: 0, protein: 0, carbs: 0, fat: 0, fibre: 0 },
  );
}

export default function PlanPage() {
  const qc = useQueryClient();
  const plan = useQuery({
    queryKey: keys.plan,
    queryFn: async () => (await api.get<PlanLatestResponse>("/plans/latest")).data,
  });
  const [tab, setTab] = useState<string | null>(null);
  const [swap, setSwap] = useState<SwapTarget | null>(null);
  const [recipe, setRecipe] = useState<RecipeTarget | null>(null);

  const generate = useMutation({
    mutationFn: async () => (await api.post<Plan>("/plans", {})).data,
    onSuccess: (p) => {
      qc.setQueryData<PlanLatestResponse>(keys.plan, { plan: p });
      setTab(null);
      toast.success("Your new 7-day plan is ready.");
    },
    onError: (err) => toast.error(errorMessage(err)),
  });

  if (plan.isPending) {
    return (
      <div className="space-y-6">
        <PageHeader title="Weekly plan" description="Loading your plan." />
        <Skeleton className="h-12 w-full max-w-md rounded-2xl" />
        <CardsSkeleton count={3} />
      </div>
    );
  }

  if (plan.isError) {
    return <ErrorState error={plan.error} title="Couldn't load your plan" onRetry={() => plan.refetch()} />;
  }

  const current = plan.data.plan;
  const generateButton = (
    <Button onClick={() => generate.mutate()} loading={generate.isPending} variant={current ? "secondary" : "primary"}>
      <Sparkles /> {current ? "Generate a new week" : "Generate my weekly plan"}
    </Button>
  );

  if (!current) {
    return (
      <div className="space-y-6">
        <PageHeader title="Weekly plan" description="A seven-day menu sized to your calorie target, with your allergies removed." />
        <EmptyState
          icon={<CalendarDays />}
          title="No plan yet"
          description="Planning takes a few seconds. Every day is checked against your calorie target and allergy list."
          action={generateButton}
        />
        {generate.isPending && (
          <InlineLoader label="Building your week. This can take a few seconds." className="justify-center" />
        )}
      </div>
    );
  }

  const defaultDay = Math.max(1, current.days.findIndex((d) => d.date === today()) + 1);
  const active = tab ?? String(defaultDay);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Weekly plan"
        description={`Target ${fmt(current.target_kcal)} kcal a day. Every day is planned within ±5 % of it.`}
        actions={generateButton}
      />

      <Tabs
        value={active}
        onValueChange={setTab}
        tabs={current.days.map((d) => ({ value: String(d.day), label: shortDay(d.date) }))}
        className="w-full"
        listClassName="overflow-x-auto"
      >
        {current.days.map((d) => {
          const totals = dayTotals(d);
          const diffPct = current.target_kcal ? ((totals.kcal - current.target_kcal) / current.target_kcal) * 100 : 0;
          const onTarget = Math.abs(diffPct) <= 5;
          return (
            <TabPanel key={d.day} value={String(d.day)}>
              <div className="space-y-6">
                <Card>
                  <CardBody className="grid gap-4 sm:grid-cols-[1fr_auto] sm:items-center">
                    <div className="space-y-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <h2 className="font-display text-lg font-semibold">
                          {d.weekday}, {dayMonth(d.date)}
                        </h2>
                        <Badge tone={onTarget ? "success" : "warning"}>{onTarget ? "On target" : `${diffPct > 0 ? "+" : ""}${diffPct.toFixed(1)}% vs target`}</Badge>
                      </div>
                      <ProgressBar value={current.target_kcal ? (totals.kcal / current.target_kcal) * 100 : 0} label={`${d.weekday} calories against target`} />
                      <p className="text-sm text-muted-foreground tabular-nums">
                        {fmt(totals.kcal)} of {fmt(current.target_kcal)} kcal · protein {fmt(totals.protein)} g · carbs {fmt(totals.carbs)} g · fat{" "}
                        {fmt(totals.fat)} g · fibre {fmt(totals.fibre)} g
                      </p>
                    </div>
                  </CardBody>
                </Card>

                <div className="grid gap-4 md:grid-cols-2">
                  {MEALS.map((m) => {
                    const dishes = d.meals[m.value];
                    return (
                      <Card key={m.value}>
                        <CardHeader title={m.label} description={`${fmt(dishes.reduce((s, x) => s + x.kcal, 0))} kcal`} />
                        <CardBody className="pt-4">
                          {dishes.length === 0 ? (
                            <p className="text-sm text-muted-foreground">Nothing planned for this meal.</p>
                          ) : (
                            <ul className="divide-y divide-[var(--glass-border)]">
                              {dishes.map((dish, index) => (
                                <li key={`${dish.food_id}-${index}`} className="flex flex-col gap-2 py-3 sm:flex-row sm:items-center sm:justify-between">
                                  <div className="min-w-0">
                                    <div className="truncate text-sm font-medium">{dish.name}</div>
                                    <div className="text-xs text-muted-foreground tabular-nums">
                                      {Math.round(dish.grams)} g · {fmt(dish.kcal)} kcal · P {fmt(dish.protein)} g · C {fmt(dish.carbs)} g · F {fmt(dish.fat)} g
                                    </div>
                                  </div>
                                  <div className="flex shrink-0 gap-1">
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => setSwap({ day: d.day, meal: m.value, index, dish })}
                                      aria-label={`Swap ${dish.name}`}
                                    >
                                      <Repeat2 /> Swap
                                    </Button>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => setRecipe({ food_id: dish.food_id, name: dish.name, grams: dish.grams })}
                                      aria-label={`Recipe for ${dish.name}`}
                                    >
                                      <ChefHat /> Recipe
                                    </Button>
                                  </div>
                                </li>
                              ))}
                            </ul>
                          )}
                        </CardBody>
                      </Card>
                    );
                  })}
                </div>
              </div>
            </TabPanel>
          );
        })}
      </Tabs>

      <SwapDrawer
        target={swap}
        planId={current.id}
        onClose={() => setSwap(null)}
        onSwapped={(p) => {
          qc.setQueryData<PlanLatestResponse>(keys.plan, { plan: p });
          setSwap(null);
          toast.success("Dish swapped. Your day totals are updated.");
        }}
      />

      <RecipeDrawer target={recipe} onClose={() => setRecipe(null)} />
    </div>
  );
}

function SwapDrawer({
  target,
  planId,
  onClose,
  onSwapped,
}: {
  target: SwapTarget | null;
  planId: number;
  onClose: () => void;
  onSwapped: (plan: Plan) => void;
}) {
  const options = useQuery({
    queryKey: ["swap-options", planId, target?.day, target?.meal, target?.index],
    enabled: target !== null,
    queryFn: async () =>
      (
        await api.get<SwapOptionsResponse>(`/plans/${planId}/swap-options`, {
          params: { day: target?.day, meal: target?.meal, index: target?.index },
        })
      ).data,
  });

  const swapTo = useMutation({
    mutationFn: async (o: SwapOption) =>
      (
        await api.post<Plan>(`/plans/${planId}/swap`, {
          day: target?.day,
          meal: target?.meal,
          index: target?.index,
          food_id: o.food_id,
          grams: o.grams,
        })
      ).data,
    onSuccess: onSwapped,
    onError: (err) => toast.error(errorMessage(err)),
  });

  return (
    <Drawer
      open={target !== null}
      onOpenChange={(v) => !v && onClose()}
      side="right"
      title={target ? `Swap ${target.dish.name}` : "Swap a dish"}
      description="Alternatives keep your allergy and diet rules and are portioned to a similar calorie count."
    >
      {options.isPending && target && (
        <div className="space-y-3" role="status" aria-label="Loading alternatives">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-2xl" />
          ))}
        </div>
      )}
      {options.isError && <ErrorState error={options.error} title="Couldn't load alternatives" onRetry={() => options.refetch()} />}
      {options.data && options.data.options.length === 0 && (
        <EmptyState icon={<Repeat2 />} title="No safe alternatives here" description="Every dish that fits this slot is already on your week. Try another day." />
      )}
      {options.data && options.data.options.length > 0 && (
        <ul className="space-y-3">
          {options.data.options.map((o) => (
            <li key={o.food_id}>
              <Card className="flex flex-col gap-3 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="font-medium">{o.name}</div>
                    <div className="text-xs text-muted-foreground tabular-nums">
                      {label(o.cuisine)} · {Math.round(o.grams)} g · {fmt(o.kcal)} kcal · P {fmt(o.protein)} g
                    </div>
                  </div>
                  {o.same_cluster && <Badge tone="cyan">Similar dish</Badge>}
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs text-muted-foreground tabular-nums">
                    {o.kcal_diff > 0 ? "+" : ""}
                    {o.kcal_diff.toFixed(1)}% calories vs original
                  </span>
                  <Button size="sm" loading={swapTo.isPending && swapTo.variables?.food_id === o.food_id} disabled={swapTo.isPending} onClick={() => swapTo.mutate(o)}>
                    Use this
                  </Button>
                </div>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </Drawer>
  );
}

function RecipeDrawer({ target, onClose }: { target: RecipeTarget | null; onClose: () => void }) {
  const recipe = useQuery({
    queryKey: ["recipe", target?.food_id, target?.grams],
    enabled: target !== null,
    staleTime: Infinity,
    retry: false,
    queryFn: async () => (await api.get<Recipe>(`/recipes/${target?.food_id}`, { params: { grams: target?.grams } })).data,
  });

  return (
    <Drawer
      open={target !== null}
      onOpenChange={(v) => !v && onClose()}
      side="right"
      title={target ? `Recipe: ${target.name}` : "Recipe"}
      description={target ? `One portion, about ${Math.round(target.grams)} g, written for your allergies and conditions.` : undefined}
    >
      {recipe.isPending && target && (
        <div className="space-y-4" role="status">
          <InlineLoader label="Writing the recipe. The first one for a dish can take a little while." />
          <Skeleton className="h-6 w-2/3" />
          <Skeleton className="h-32 w-full" />
        </div>
      )}
      {recipe.isError && (
        <ErrorState error={recipe.error} title="Couldn't write this recipe" hint="Recipes need the Gemini key in .env. Check docs/03_HOW_TO_RUN.md." onRetry={() => recipe.refetch()} />
      )}
      {recipe.data && recipe.data.ingredients.length === 0 && recipe.data.steps.length === 0 && (
        <EmptyState
          icon={<ChefHat />}
          title="The recipe came back empty"
          description="No ingredients or steps were returned for this dish. Try again, or use a different portion."
          action={
            <Button size="sm" variant="secondary" onClick={() => recipe.refetch()}>
              Try again
            </Button>
          }
        />
      )}
      {recipe.data && (recipe.data.ingredients.length > 0 || recipe.data.steps.length > 0) && (
        <article className="space-y-6">
          <div className="flex flex-wrap gap-2">
            <Badge tone="violet">{fmt(recipe.data.nutrients.kcal)} kcal</Badge>
            <Badge tone="neutral">P {fmt(recipe.data.nutrients.protein)} g</Badge>
            <Badge tone="neutral">C {fmt(recipe.data.nutrients.carbs)} g</Badge>
            <Badge tone="neutral">F {fmt(recipe.data.nutrients.fat)} g</Badge>
            {recipe.data.cached && <Badge tone="cyan">Saved recipe</Badge>}
          </div>

          {recipe.data.warnings.length > 0 && (
            <div role="alert" className="space-y-1 rounded-xl border border-warning/35 bg-warning/10 p-3 text-sm">
              {recipe.data.warnings.map((w) => (
                <p key={w}>{w}</p>
              ))}
            </div>
          )}

          <section aria-labelledby="ingredients-h" className="space-y-2">
            <h3 id="ingredients-h" className="font-display font-semibold">
              Ingredients
            </h3>
            <ul className="divide-y divide-[var(--glass-border)] text-sm">
              {recipe.data.ingredients.map((i, idx) => (
                <li key={`${i.item}-${idx}`} className="flex justify-between gap-3 py-2">
                  <span>{i.item}</span>
                  <span className="shrink-0 text-muted-foreground">{i.quantity}</span>
                </li>
              ))}
            </ul>
          </section>

          <section aria-labelledby="steps-h" className="space-y-2">
            <h3 id="steps-h" className="font-display font-semibold">
              Steps
            </h3>
            <ol className="list-decimal space-y-2 pl-5 text-sm">
              {recipe.data.steps.map((s, idx) => (
                <li key={idx}>{s}</li>
              ))}
            </ol>
            <p className="text-xs text-muted-foreground">
              {recipe.data.prep_minutes != null && `Prep ${recipe.data.prep_minutes} min`}
              {recipe.data.prep_minutes != null && recipe.data.cook_minutes != null && " · "}
              {recipe.data.cook_minutes != null && `Cook ${recipe.data.cook_minutes} min`}
            </p>
          </section>

          {recipe.data.health_tips.length > 0 && (
            <section aria-labelledby="tips-h" className="space-y-2">
              <h3 id="tips-h" className="font-display font-semibold">
                Health tips
              </h3>
              <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                {recipe.data.health_tips.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
            </section>
          )}
        </article>
      )}
    </Drawer>
  );
}
