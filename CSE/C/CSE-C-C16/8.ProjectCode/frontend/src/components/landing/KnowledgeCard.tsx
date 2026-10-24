import { ArrowRight, FlaskConical, Leaf, ShieldCheck } from "lucide-react";
import { Link } from "react-router";

import { SeverityBadge } from "@/components/agri/bits";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Feedback";
import type { Disease } from "@/lib/api";
import { useDiseases } from "@/lib/queries";

const FEATURED = "Tomato___Late_blight";

/** A real entry from the disease knowledge base (not a mock-up): what the app tells you about a diagnosis. */
export function KnowledgeCard() {
  const q = useDiseases();
  const d: Disease | undefined = q.data?.find((x) => x.class === FEATURED) ?? q.data?.find((x) => !x.healthy);

  return (
    <div className="glass-strong relative overflow-hidden rounded-3xl">
      <div aria-hidden className="absolute -right-16 -top-16 size-56 rounded-full bg-grad-primary opacity-30 blur-3xl" />
      <div className="relative space-y-4 p-6">
        <div className="flex items-center justify-between gap-2">
          <Badge tone="violet">From the disease guide</Badge>
          {d && <SeverityBadge severity={d.severity} />}
        </div>
        {!d ? (
          q.isError ? (
            <p className="text-sm text-muted-foreground">The disease guide preview needs the API. Start it with run.bat.</p>
          ) : (
            <div className="space-y-3" role="status" aria-label="Loading disease guide preview">
              <Skeleton className="h-8 w-3/4" />
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-24 w-full" />
            </div>
          )
        ) : (
          <>
            <h2 className="font-display text-2xl font-semibold leading-tight">{d.name}</h2>
            <p className="text-sm text-muted-foreground">{d.symptoms}</p>
            <ul className="space-y-3 text-sm">
              {d.treatments.map((t) => (
                <li key={t.type} className="flex gap-3">
                  <span className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-lg bg-grad-soft text-violet-ink">
                    {t.type === "chemical" ? <FlaskConical className="size-4" /> : t.type === "organic" ? <Leaf className="size-4" /> : <ShieldCheck className="size-4" />}
                  </span>
                  <span>
                    <b className="capitalize">{t.type}:</b> <span className="text-muted-foreground">{t.detail}</span>
                  </span>
                </li>
              ))}
            </ul>
            <Link to={`/disease/${encodeURIComponent(d.class)}`} className="inline-flex items-center gap-1 text-sm font-medium text-violet-ink hover:underline">
              Read the full guide <ArrowRight className="size-4" aria-hidden />
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
