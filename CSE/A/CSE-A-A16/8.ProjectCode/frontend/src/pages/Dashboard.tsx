import { Activity, ArrowRight, BarChart3, Camera, CheckCircle2, Database, Dumbbell, Hand, ImageIcon, Layers, Target } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Link } from "react-router";

import { axisProps, ChartCard, ChartGradients, ChartTooltip, gridProps } from "@/components/charts/Chart";
import { Stagger, StaggerItem } from "@/components/motion";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { KeyValueList, StatCard } from "@/components/ui/Display";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { classLabel, pct, whenTrained } from "@/lib/format";
import { useConfig, useDataset, useHealth, useModel } from "@/lib/queries";

export default function Dashboard() {
  const dataset = useDataset();
  const model = useModel();
  const health = useHealth();
  const config = useConfig();

  if (dataset.isError) {
    return (
      <div className="space-y-6">
        <PageHeader title="Dashboard" />
        <ErrorState error={dataset.error} title="Couldn't reach the SignSpeak server" hint="Start it with run.bat, then try again." onRetry={() => dataset.refetch()} />
      </div>
    );
  }

  const loading = dataset.isPending || model.isPending;
  const total = config.data?.classes.length ?? 29;
  const withData = dataset.data?.trainable_classes.length ?? 0;
  const counts = dataset.data?.counts ?? {};
  const chartData = (config.data?.classes ?? Object.keys(counts)).map((c) => ({ cls: c, label: classLabel(c), images: counts[c] ?? 0 }));
  const trained = model.data;
  const noImages = !loading && (dataset.data?.total ?? 0) === 0;

  const next = noImages
    ? { title: "Collect your first images", text: "Show a letter to the webcam and capture it, or drop an existing dataset into data/<class>/.", to: "/app/collect", label: "Collect data", icon: <Camera /> }
    : !trained
      ? { title: "Train the CNN", text: `${dataset.data?.total.toLocaleString("en-US")} images in ${withData} classes are ready. Train to get a model.`, to: "/app/train", label: "Train model", icon: <Dumbbell /> }
      : { title: "Sign something", text: "Your model is ready. Start the camera and spell a word.", to: "/app/recognize", label: "Recognize", icon: <Hand /> };

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Overview" title="Dashboard" description="Where your dataset and model stand right now." />

      <Stagger className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StaggerItem>
          <StatCard
            label="Model"
            icon={<Activity />}
            display={loading ? <Skeleton className="h-8 w-24" /> : <span className="text-2xl">{trained ? (health.data?.model_loaded ? "Ready" : "Trained") : "Not trained"}</span>}
            hint={trained ? whenTrained(trained.trained_at) : "Train to create one"}
          />
        </StaggerItem>
        <StaggerItem>
          <StatCard label="Images collected" icon={<ImageIcon />} accent="cyan" value={loading ? undefined : dataset.data?.total} display={<Skeleton className="h-8 w-20" />} hint="across all classes" />
        </StaggerItem>
        <StaggerItem>
          <StatCard
            label="Classes with data"
            icon={<Layers />}
            accent="magenta"
            value={loading ? undefined : withData}
            format={(n) => `${Math.round(n)} / ${total}`}
            display={<Skeleton className="h-8 w-20" />}
            hint={dataset.data && !dataset.data.ready_to_train ? "need 2+ to train" : "A-Z, space, del, nothing"}
          />
        </StaggerItem>
        <StaggerItem>
          <StatCard
            label="Test accuracy"
            icon={<Target />}
            value={loading ? undefined : trained?.test_accuracy != null ? trained.test_accuracy * 100 : null}
            format={(n) => `${n.toFixed(1)}%`}
            display={loading ? <Skeleton className="h-8 w-20" /> : "-"}
            hint={trained ? "on held-out images" : "after training"}
          />
        </StaggerItem>
      </Stagger>

      <Card strong className="overflow-hidden">
        <div className="flex flex-wrap items-center gap-4 p-5">
          <span className="grid size-12 place-items-center rounded-2xl bg-grad-primary text-white [&_svg]:size-6">{next.icon}</span>
          <div className="min-w-0 flex-1">
            <Badge tone="violet" className="mb-1">Next step</Badge>
            <h2 className="font-display text-lg font-semibold">{next.title}</h2>
            <p className="text-sm text-muted-foreground">{next.text}</p>
          </div>
          <Button asChild>
            <Link to={next.to}>
              {next.label} <ArrowRight />
            </Link>
          </Button>
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        <ChartCard
          className="lg:col-span-2"
          title="Images per class"
          description="Aim for roughly 150-250 per class"
          icon={<BarChart3 />}
          empty={
            loading ? (
              <Skeleton className="h-40 w-full" />
            ) : noImages ? (
              <EmptyState
                className="border-0 bg-transparent py-4"
                icon={<Database />}
                title="No images collected yet"
                description="The bars fill in as you collect."
                action={
                  <Button asChild size="sm">
                    <Link to="/app/collect">Collect data</Link>
                  </Button>
                }
              />
            ) : undefined
          }
          table={{ columns: ["Class", "Images"], rows: chartData.map((d) => [d.label, d.images]) }}
        >
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
                <ChartGradients />
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="cls" {...axisProps} interval={0} tickMargin={6} tickFormatter={(v: string) => (v.length > 1 ? v.slice(0, 3) : v)} />
                <YAxis {...axisProps} allowDecimals={false} width={40} />
                <Tooltip cursor={{ fill: "var(--muted)" }} content={<ChartTooltip labelFormatter={(l) => classLabel(String(l))} />} />
                <Bar dataKey="images" name="Images" fill="url(#bar-0)" radius={[6, 6, 0, 0]} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        <Card>
          <CardHeader title="Last training run" icon={<CheckCircle2 />} />
          <CardBody>
            {loading ? (
              <Skeleton className="h-40 w-full" />
            ) : trained ? (
              <div className="space-y-3">
                <KeyValueList
                  items={[
                    { label: "Trained", value: whenTrained(trained.trained_at) },
                    { label: "Classes", value: trained.labels.length },
                    { label: "Test accuracy", value: pct(trained.test_accuracy) },
                    { label: "Test loss", value: trained.test_loss != null ? trained.test_loss.toFixed(4) : "-" },
                  ]}
                />
                <Button asChild variant="secondary" size="sm" className="w-full">
                  <Link to="/app/model">Full report</Link>
                </Button>
              </div>
            ) : (
              <EmptyState
                className="border-0 bg-transparent px-0 py-4"
                icon={<Dumbbell />}
                title="Nothing trained yet"
                description="Results of your training runs show up here."
                action={
                  <Button asChild size="sm" variant="secondary">
                    <Link to="/app/train">Train model</Link>
                  </Button>
                }
              />
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
