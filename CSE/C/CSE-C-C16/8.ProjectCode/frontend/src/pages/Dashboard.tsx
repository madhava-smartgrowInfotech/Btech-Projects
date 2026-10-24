import { AlertTriangle, BookOpenText, Camera, CheckCircle2, History, Leaf, Percent, ScanSearch, Sprout } from "lucide-react";
import { Link } from "react-router";

import { ResultCard } from "@/components/agri/bits";
import { Stagger, StaggerItem } from "@/components/motion/Stagger";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/Display";
import { CardsSkeleton, EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { useLang } from "@/lib/i18n";
import { useDashboard } from "@/lib/queries";

// Static guidance carried over from the original dashboard template.
const QUICK = [
  { crop: "tomato", label: "Scan tomato" },
  { crop: "potato", label: "Scan potato" },
  { crop: "corn", label: "Scan maize" },
];
const TIPS = [
  "Water in the morning, never on the foliage.",
  "Mulch and stake tomatoes to stop soil splash.",
  "Spray early morning or late evening.",
  "Remove and burn severely infected leaves.",
];

export default function Dashboard() {
  const { t } = useLang();
  const q = useDashboard();

  if (q.isError) return <ErrorState error={q.error} title="Couldn't load your dashboard" onRetry={() => q.refetch()} />;

  const d = q.data;
  const name = d?.user.full_name || d?.user.email;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow={d ? `${d.user.region || "Your farm"} · ${d.user.role}` : undefined}
        title={d ? `${t("dash.hello", "Namaste")}, ${name}` : <Skeleton className="h-8 w-64" />}
        description="Ready to scout? Scan a leaf, read the diagnosis and keep a record of every field visit."
        actions={
          <>
            <Button asChild>
              <Link to="/detect">
                <Camera /> {t("common.newScan", "New scan")}
              </Link>
            </Button>
            <Button asChild variant="secondary">
              <Link to="/history">
                <History /> {t("nav.history", "History")}
              </Link>
            </Button>
          </>
        }
      />

      <Stagger className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {q.isPending
          ? Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-[132px] rounded-2xl" />)
          : d && (
              <>
                <StaggerItem>
                  <StatCard label={t("dash.total", "Total scans")} value={d.total} icon={<ScanSearch />} />
                </StaggerItem>
                <StaggerItem>
                  <StatCard label={t("dash.healthy", "Healthy")} value={d.healthy} icon={<CheckCircle2 />} accent="cyan" />
                </StaggerItem>
                <StaggerItem>
                  <StatCard label={t("dash.high", "High severity")} value={d.urgent} icon={<AlertTriangle />} accent="magenta" hint={d.urgent ? "Act soon" : undefined} />
                </StaggerItem>
                <StaggerItem>
                  <StatCard label={t("dash.rate", "Disease rate")} value={d.disease_rate} format={(n) => `${n.toFixed(1)}%`} icon={<Percent />} />
                </StaggerItem>
              </>
            )}
      </Stagger>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader title={t("dash.quick", "Quick actions")} icon={<Sprout />} description="Pick a crop so the diagnosis only considers its diseases." />
          <CardBody className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              {QUICK.map((qa) => (
                <Button key={qa.crop} asChild variant="outline" size="lg" className="justify-start" magnetic={false}>
                  <Link to={`/detect?crop=${qa.crop}`}>
                    <Leaf /> {qa.label}
                  </Link>
                </Button>
              ))}
              <Button asChild variant="outline" size="lg" className="justify-start" magnetic={false}>
                <Link to="/encyclopedia">
                  <BookOpenText /> {t("nav.guide", "Disease guide")}
                </Link>
              </Button>
            </div>
            <div className="flex items-start gap-3 rounded-xl border border-warning/30 bg-warning/[0.08] p-3 text-sm">
              <AlertTriangle className="mt-0.5 size-4 shrink-0 text-warning" aria-hidden />
              <p>
                <b>Season alert:</b> late blight pressure is high in humid weather. Scout lower leaves every 3 days.
              </p>
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardHeader title={t("dash.tips", "Field tips")} icon={<Leaf />} />
          <CardBody className="space-y-4">
            <ul className="space-y-2 text-sm text-muted-foreground">
              {TIPS.map((tip) => (
                <li key={tip} className="flex gap-2">
                  <span aria-hidden className="mt-2 size-1.5 shrink-0 rounded-full bg-grad-primary" />
                  {tip}
                </li>
              ))}
            </ul>
            <Button asChild variant="secondary" className="w-full" magnetic={false}>
              <Link to="/analytics">View analytics</Link>
            </Button>
          </CardBody>
        </Card>
      </div>

      <section aria-labelledby="recent-h" className="space-y-4">
        <h2 id="recent-h" className="font-display text-xl font-semibold">
          {t("dash.recent", "Recent detections")}
        </h2>
        {q.isPending ? (
          <CardsSkeleton />
        ) : d && d.recent.length === 0 ? (
          <EmptyState
            icon={<Camera />}
            title="No scans yet"
            description="Upload a clear photo of one leaf and your first diagnosis will show up here."
            action={
              <Button asChild>
                <Link to="/detect">Upload your first leaf</Link>
              </Button>
            }
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {d?.recent.map((r) => (
              <ResultCard key={r.result_id} r={r} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
