import { ArrowLeft, Camera, ShieldCheck, Stethoscope } from "lucide-react";
import axios from "axios";
import { Link, useParams } from "react-router";

import { SeverityBadge } from "@/components/agri/bits";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { useBreadcrumb } from "@/components/ui/AppShell";
import { Search } from "lucide-react";
import { TREATMENT_TONE, cropKey } from "@/lib/disease";
import { useLang } from "@/lib/i18n";
import { useDisease } from "@/lib/queries";

export default function DiseaseDetail() {
  const { cls } = useParams();
  const { t } = useLang();
  const q = useDisease(cls);
  useBreadcrumb(q.data?.name);

  if (q.isError) {
    const missing = axios.isAxiosError(q.error) && q.error.response?.status === 404;
    return missing ? (
      <EmptyState
        icon={<Search />}
        title="Disease not found"
        description="That entry isn't in the 38-class knowledge base."
        action={
          <Button asChild>
            <Link to="/encyclopedia">Browse the disease guide</Link>
          </Button>
        }
      />
    ) : (
      <ErrorState error={q.error} title="Couldn't load this disease" onRetry={() => q.refetch()} />
    );
  }
  if (q.isPending) return <Skeleton className="h-[28rem] rounded-2xl" />;

  const d = q.data;
  return (
    <div className="space-y-5">
      <Button asChild variant="ghost" size="sm" magnetic={false} className="-ml-2">
        <Link to="/encyclopedia">
          <ArrowLeft /> Disease guide
        </Link>
      </Button>
      <Card className="space-y-6 p-6 md:p-8">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <SeverityBadge severity={d.severity} />
            <Badge>{d.crop}</Badge>
          </div>
          <h1 className="font-display text-3xl font-semibold tracking-tight text-balance">{d.name}</h1>
          <p className="max-w-3xl text-muted-foreground">{d.description}</p>
        </div>
        <div className="grid gap-5 md:grid-cols-2">
          <Card strong className="shadow-none">
            <CardHeader title={t("result.symptoms", "Symptoms")} icon={<Stethoscope />} />
            <CardBody className="space-y-4 text-sm">
              <p>{d.symptoms}</p>
              <div>
                <h2 className="font-display font-semibold">{t("result.lifecycle", "Lifecycle")}</h2>
                <p className="mt-1 text-muted-foreground">{d.lifecycle}</p>
              </div>
              <div>
                <h2 className="font-display font-semibold">{t("result.prevention", "Prevention")}</h2>
                <p className="mt-1">{d.prevention}</p>
              </div>
            </CardBody>
          </Card>
          <Card strong className="shadow-none">
            <CardHeader title="Treatments" icon={<ShieldCheck />} />
            <CardBody className="space-y-3">
              {d.treatments.map((tr) => (
                <div key={tr.type} className="rounded-xl border border-[var(--glass-border)] p-4">
                  <div className="flex items-center gap-2">
                    <Badge tone={TREATMENT_TONE[tr.type]} className="uppercase">
                      {tr.type}
                    </Badge>
                    <b className="text-sm">{tr.name}</b>
                  </div>
                  <p className="mt-1.5 text-sm">{tr.detail}</p>
                  <p className="mt-1 text-xs text-muted-foreground">Cost: {tr.cost}</p>
                </div>
              ))}
            </CardBody>
          </Card>
        </div>
        <Button asChild size="lg">
          <Link to={`/detect?crop=${cropKey(d.crop)}`}>
            <Camera /> Scan for this disease
          </Link>
        </Button>
      </Card>
    </div>
  );
}
