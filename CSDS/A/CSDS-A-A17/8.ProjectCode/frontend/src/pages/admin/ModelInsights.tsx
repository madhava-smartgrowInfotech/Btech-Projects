import { useEffect, useState } from "react";
import { Loader2, ShieldCheck } from "lucide-react";
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import type { ModelInsights as ModelInsightsType } from "@/types";

function ImportanceChart({ data }: { data: { feature: string; importance: number }[] }) {
  const chartData = data.map((d) => ({ ...d, label: d.feature.replaceAll("_", " ") }));
  return (
    <ResponsiveContainer width="100%" height={Math.max(160, chartData.length * 34)}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 24 }}>
        <XAxis type="number" hide />
        <YAxis type="category" dataKey="label" width={140} tick={{ fontSize: 12, fill: "#44403c" }} axisLine={false} tickLine={false} />
        <Bar dataKey="importance" fill="#166534" radius={4} barSize={14} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ModelInsights() {
  const [data, setData] = useState<ModelInsightsType | null>(null);

  useEffect(() => {
    api.get<ModelInsightsType>("/admin/model-insights").then(({ data }) => setData(data));
  }, []);

  if (!data) {
    return (
      <div className="flex items-center gap-2 text-ink-500 text-sm">
        <Loader2 size={16} className="animate-spin" /> Loading…
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold text-ink-900">Model insights</h1>
        <p className="text-sm text-ink-500 mt-1">Transparency on how each model works and what it was trained on.</p>
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>Quality grading model</CardTitle>
            <CardDescription>{data.quality_model.algorithm}</CardDescription>
          </div>
          <Badge tone="brand">{(data.quality_model.test_accuracy * 100).toFixed(1)}% test accuracy</Badge>
        </CardHeader>
        <CardContent className="space-y-4">
          <ImportanceChart data={data.quality_model.feature_importance} />
          <div className="flex items-start gap-2 rounded-xl bg-sand-100 p-3 text-xs text-ink-600">
            <ShieldCheck size={15} className="text-brand-600 shrink-0 mt-0.5" />
            <p>{data.quality_model.training_data}</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>Price forecasting model</CardTitle>
            <CardDescription>{data.price_model.algorithm}</CardDescription>
          </div>
          <Badge tone="sky">R² {data.price_model.test_r2.toFixed(3)}</Badge>
        </CardHeader>
        <CardContent className="space-y-4">
          <ImportanceChart data={data.price_model.feature_importance} />
          <div className="flex items-start gap-2 rounded-xl bg-sand-100 p-3 text-xs text-ink-600">
            <ShieldCheck size={15} className="text-brand-600 shrink-0 mt-0.5" />
            <p>{data.price_model.training_data}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
