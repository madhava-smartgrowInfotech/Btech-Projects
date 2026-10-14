import { useQuery } from "@tanstack/react-query";
import { HeartPulse } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ChartCard, ChartGradients, ChartTooltip, axisProps, gridProps } from "@/components/charts/Chart";
import { Badge, type BadgeTone } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { CardsSkeleton, ErrorState, ProgressBar } from "@/components/ui/Feedback";
import { api } from "@/lib/api";
import { keys } from "@/lib/queries";
import type { RiskPanelData, RiskScore } from "@/lib/types";

const LEVEL_TONE: Record<RiskScore["level"], BadgeTone> = { high: "danger", moderate: "warning", low: "success" };

/**
 * Heart and diabetes risk for one person, with the factors behind each score. Loaded only when
 * the doctor asks for it (it pulls in the chart library, so this file is lazy-loaded).
 */
export default function RiskPanel({ personId }: { personId: string }) {
  const risk = useQuery({
    queryKey: keys.risk(personId),
    queryFn: async () => (await api.get<RiskPanelData>(`/risk/${personId}`)).data,
    enabled: false,
    retry: false,
  });

  return (
    <Card>
      <CardHeader
        icon={<HeartPulse />}
        title="Health-risk prediction"
        description="Random Forest models on blood pressure, cholesterol, glucose, BMI, age and sex from the record"
        action={
          <Button loading={risk.isFetching} onClick={() => risk.refetch()}>
            {risk.data ? "Re-run" : "Assess risk"}
          </Button>
        }
      />
      <CardBody className="space-y-4">
        {risk.isError && <ErrorState error={risk.error} title="Risk could not be scored" onRetry={() => risk.refetch()} />}
        {!risk.data && !risk.isFetching && !risk.isError && (
          <p className="text-sm text-muted-foreground">Press Assess risk to score heart disease and type 2 diabetes from the values in this record.</p>
        )}
        {risk.isFetching && <CardsSkeleton count={2} />}
        {risk.data && (
          <>
            <div className="grid gap-4 md:grid-cols-2">
              <RiskScoreCard title="Heart disease" score={risk.data.heart} />
              <RiskScoreCard title="Type 2 diabetes" score={risk.data.diabetes} />
            </div>
            <p className="text-xs text-muted-foreground">{risk.data.disclaimer}</p>
          </>
        )}
      </CardBody>
    </Card>
  );
}

function RiskScoreCard({ title, score }: { title: string; score: RiskScore }) {
  const pct = Math.round(score.probability * 100);
  const factors = score.top_factors.map((f) => ({ name: f.label, impact: Math.round(f.impact * 100) }));
  const id = title.replace(/\W/g, "");

  return (
    <ChartCard
      title={title}
      description={`${score.level[0].toUpperCase()}${score.level.slice(1)} estimated risk`}
      icon={<HeartPulse />}
      className="h-full"
      table={{
        columns: ["Factor", "Value", "Impact (pts)"],
        rows: score.top_factors.map((f) => [f.label, String(f.value), Math.round(f.impact * 100)]),
      }}
    >
      <div className="flex items-center gap-3">
        <ProgressBar value={pct} label={`${title} risk ${pct}%`} className="h-2.5" />
        <span className="w-14 text-right font-display text-xl font-semibold tabular-nums">{pct}%</span>
      </div>
      <Badge tone={LEVEL_TONE[score.level]}>{score.level} risk</Badge>

      {factors.length === 0 ? (
        <p className="text-sm text-muted-foreground">No usable values in the record, so population medians were used.</p>
      ) : (
        <div className="h-44 w-full" role="img" aria-label={`Top factors for ${title}`}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={factors} layout="vertical" margin={{ top: 4, right: 16, bottom: 4, left: 4 }}>
              <ChartGradients id={id} />
              <CartesianGrid {...gridProps} />
              <XAxis type="number" {...axisProps} />
              <YAxis type="category" dataKey="name" width={120} {...axisProps} />
              <Tooltip cursor={{ fill: "var(--muted)" }} content={<ChartTooltip formatter={(v) => `${v} pts`} />} />
              <Bar dataKey="impact" name="Impact" fill={`url(#bar${id}-0)`} radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      <p className="text-xs text-muted-foreground">
        {score.inputs.some((u) => !u.from_record)
          ? `Not in record (median used): ${score.inputs
              .filter((u) => !u.from_record)
              .map((u) => u.label)
              .join(", ")}`
          : "All inputs came from the record."}
      </p>
    </ChartCard>
  );
}
