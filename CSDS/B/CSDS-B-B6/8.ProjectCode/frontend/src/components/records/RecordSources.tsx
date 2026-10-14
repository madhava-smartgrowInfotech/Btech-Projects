import { useMutation } from "@tanstack/react-query";
import { Building2, Download } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { toast } from "@/components/ui/Feedback";
import { downloadBundle, errorMessage } from "@/lib/api";
import { CATEGORY_LABEL, CATEGORY_TONE, HOSPITAL_TONE } from "@/lib/constants";
import type { RecordView } from "@/lib/types";
import { cn } from "@/lib/utils";

/** Which hospitals hold this person's records, how sure the MPI is, and the FHIR download. */
export function RecordSources({ record, personId }: { record: RecordView; personId: string }) {
  const download = useMutation({
    mutationFn: () => downloadBundle(personId),
    onSuccess: () => toast.success("FHIR bundle downloaded"),
    onError: (e) => toast.error(errorMessage(e)),
  });

  return (
    <Card>
      <CardHeader
        icon={<Building2 />}
        title="Record sources"
        description="Hospitals holding this person's records, matched by the Master Patient Index"
        action={
          <Button variant="secondary" size="sm" loading={download.isPending} onClick={() => download.mutate()}>
            <Download /> FHIR bundle
          </Button>
        }
      />
      <CardBody className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-3">
          {record.sources.map((s) => {
            const total = Object.values(s.counts).reduce((a, b) => a + b, 0);
            return (
              <div key={s.hospital} className="rounded-xl border border-[var(--glass-border)] bg-[var(--glass)] p-3">
                <div className="flex items-start justify-between gap-2">
                  <Badge tone={HOSPITAL_TONE[s.hospital] ?? "neutral"}>{s.name}</Badge>
                  <span className={cn("shrink-0 text-xs", s.status === "online" ? "text-success" : "text-warning")}>● {s.status}</span>
                </div>
                <dl className="mt-2 space-y-0.5 text-xs text-muted-foreground">
                  <div>
                    Local ID <span className="font-mono text-foreground">{s.local_id}</span>
                  </div>
                  <div>
                    Match confidence <span className="font-semibold text-foreground">{Math.round(s.confidence * 100)}%</span>
                  </div>
                  <div>{total} FHIR resources</div>
                </dl>
              </div>
            );
          })}
        </div>
        <div className="flex flex-wrap gap-2">
          {Object.entries(record.counts).map(([c, n]) => (
            <Badge key={c} tone={CATEGORY_TONE[c] ?? "neutral"}>
              {CATEGORY_LABEL[c] ?? c}: {n}
            </Badge>
          ))}
        </div>
      </CardBody>
    </Card>
  );
}
