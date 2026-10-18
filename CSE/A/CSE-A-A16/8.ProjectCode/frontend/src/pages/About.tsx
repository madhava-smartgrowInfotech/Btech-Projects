import { BookOpen, ExternalLink, Lightbulb, Workflow } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { KeyValueList } from "@/components/ui/Display";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { Stepper } from "@/components/ui/Navigation";
import { useAbout } from "@/lib/queries";

export default function About() {
  const { data, isPending, isError, error, refetch } = useAbout();

  if (isError) {
    return (
      <div className="space-y-6">
        <PageHeader title="About" />
        <ErrorState error={error} title="Couldn't load the project details" hint="Make sure the SignSpeak server is running (run.bat)." onRetry={() => refetch()} />
      </div>
    );
  }
  if (isPending) {
    return (
      <div className="space-y-6" role="status" aria-label="Loading">
        <PageHeader title="About" />
        <Skeleton className="h-56" />
        <Skeleton className="h-72" />
      </div>
    );
  }

  const doi = data.base_paper["DOI"];
  const entries = Object.entries(data.base_paper).map(([label, value]) => ({
    label,
    value:
      label === "DOI" ? (
        <a
          href={`https://doi.org/${doi}`}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 text-violet-ink underline-offset-4 hover:underline"
        >
          {value} <ExternalLink className="size-3" aria-hidden />
          <span className="sr-only">(opens in a new tab)</span>
        </a>
      ) : (
        value
      ),
  }));

  return (
    <div className="space-y-6">
      <PageHeader eyebrow={data.batch} title={data.title} description="Real-time American Sign Language alphabet recognition with a convolutional neural network." actions={<Badge tone="gradient">ASL · CNN</Badge>} />

      <Card>
        <CardHeader title="Abstract" icon={<BookOpen />} />
        <CardBody className="space-y-3 text-sm leading-relaxed text-muted-foreground sm:text-base">
          {data.abstract.split("\n\n").map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="End-to-end pipeline" icon={<Workflow />} description="What happens to every webcam frame." />
        <CardBody>
          <Stepper
            orientation="vertical"
            current={data.pipeline.length}
            steps={data.pipeline.map((label, i) => ({ label: <span className="font-medium">{label}</span>, description: `Step ${i + 1} of ${data.pipeline.length}` }))}
          />
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Base paper" icon={<Lightbulb />} />
        <CardBody className="space-y-4">
          <KeyValueList items={entries} />
          <div className="rounded-2xl border border-[var(--glass-border)] bg-grad-soft p-4">
            <h3 className="mb-1 font-display text-sm font-semibold">How this project adopts it</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">{data.adoption_note}</p>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
