import { CalendarDays, LineChart, NotebookPen, UserRound } from "lucide-react";

import { Reveal } from "@/components/motion/Reveal";
import { Card } from "@/components/ui/Card";

const STEPS = [
  {
    icon: <UserRound />,
    title: "Tell us about you",
    text: "Age, height, weight, activity, diet, cuisine, allergies and any diabetes, hypertension or high cholesterol.",
  },
  {
    icon: <CalendarDays />,
    title: "Get a 7-day plan",
    text: "Breakfast, lunch, snack and dinner from 890 Indian dishes, sized to your calorie and macro targets.",
  },
  {
    icon: <NotebookPen />,
    title: "Log what you eat",
    text: "Search the dish database, look up an ingredient in USDA FoodData Central, or photograph your plate.",
  },
  {
    icon: <LineChart />,
    title: "Track and adapt",
    text: "Log your weight. Once a week of readings shows a trend, your target is recalculated and the change is explained.",
  },
];

export function HowItWorks() {
  return (
    <section aria-labelledby="how-title" className="mx-auto max-w-6xl px-4 sm:px-6">
      <Reveal className="space-y-10">
        <div data-reveal className="mx-auto max-w-2xl space-y-3 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-ink">How it works</p>
          <h2 id="how-title" className="font-display text-2xl font-semibold tracking-tight sm:text-4xl">
            From your profile to a plan you can actually cook
          </h2>
        </div>
        <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step, i) => (
            <li key={step.title} data-reveal className="list-none">
              <Card interactive className="flex h-full flex-col gap-4 p-5">
                <div className="flex items-center justify-between">
                  <span className="grid size-11 place-items-center rounded-2xl bg-grad-primary text-white shadow-[0_10px_30px_-10px_rgba(124,92,255,0.8)] [&_svg]:size-5">
                    {step.icon}
                  </span>
                  <span className="font-display text-sm font-semibold text-muted-foreground">0{i + 1}</span>
                </div>
                <h3 className="font-display text-lg font-semibold">{step.title}</h3>
                <p className="text-sm text-muted-foreground">{step.text}</p>
              </Card>
            </li>
          ))}
        </ol>
      </Reveal>
    </section>
  );
}
