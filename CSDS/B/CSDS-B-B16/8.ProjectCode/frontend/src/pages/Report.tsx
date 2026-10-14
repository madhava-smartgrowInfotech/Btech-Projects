import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Download } from "lucide-react";

import { useBreadcrumb } from "@/components/ui/AppShell";
import { Button } from "@/components/ui/Button";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { api } from "@/lib/api";

export default function Report() {
  const { id = "" } = useParams();
  useBreadcrumb(`Report #${id}`);

  const query = useQuery({
    queryKey: ["report", id],
    queryFn: async () => (await api.get<Blob>(`/screenings/${id}/report`, { responseType: "blob" })).data,
    enabled: !!id,
    staleTime: 5 * 60_000,
  });

  // Object URL for the PDF. Created in an effect so React StrictMode's double mount gets a fresh URL.
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    if (!query.data) return;
    const next = URL.createObjectURL(new Blob([query.data], { type: "application/pdf" }));
    setUrl(next);
    return () => URL.revokeObjectURL(next);
  }, [query.data]);

  return (
    <div className="space-y-6">
      <Link to={`/screenings/${id}`} className="inline-flex items-center gap-1 text-sm text-violet-ink underline-offset-4 hover:underline">
        <ArrowLeft className="size-4" aria-hidden /> Back to result
      </Link>
      <PageHeader
        title="Screening report"
        description={`PDF report for screening #${id}: images, findings, risk stage and recommendations.`}
        actions={
          url ? (
            <Button asChild>
              <a href={url} download={`retinaguard_report_${id}.pdf`}>
                <Download /> Download PDF
              </a>
            </Button>
          ) : undefined
        }
      />

      {query.isPending && <Skeleton className="h-[70dvh] min-h-[420px] w-full rounded-2xl" />}
      {query.isError && (
        <ErrorState
          error={query.error}
          title="Couldn't generate the report"
          hint="Check that the screening still exists and the RetinaGuard API is running."
          onRetry={() => query.refetch()}
        />
      )}
      {url && (
        <div className="glass overflow-hidden rounded-2xl p-1">
          <iframe title={`Screening report #${id}`} src={url} className="h-[70dvh] min-h-[420px] w-full rounded-xl bg-white" />
        </div>
      )}
    </div>
  );
}
