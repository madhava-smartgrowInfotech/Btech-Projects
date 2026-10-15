import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, ShieldCheck } from "lucide-react";
import { Link, useParams } from "react-router";

import { SeverityBadge, humanize } from "@/components/app/RiskBadges.jsx";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { Tabs, TabPanel } from "@/components/ui/Navigation";
import { useBreadcrumb } from "@/components/ui/AppShell";
import { contractsApi } from "@/lib/api.js";
import { keys } from "@/lib/queries.js";

export default function ClauseDetail() {
  const { id, clauseId } = useParams();
  const [tab, setTab] = useState("flags");

  const query = useQuery({
    queryKey: keys.clause(id, clauseId),
    queryFn: async () => (await contractsApi.getClause(id, clauseId)).data,
  });
  const clause = query.data;

  useBreadcrumb(clause ? `Clause ${clause.index_in_doc + 1}` : null);

  const back = (
    <Button asChild variant="ghost" size="sm" className="-ml-3">
      <Link to={`/app/contracts/${id}`}>
        <ArrowLeft /> Back to report
      </Link>
    </Button>
  );

  if (query.isPending) {
    return (
      <div className="space-y-6" role="status" aria-label="Loading clause">
        {back}
        <Skeleton className="h-10 w-1/2" />
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-48 rounded-2xl" />
      </div>
    );
  }

  if (query.isError) {
    const notFound = query.error?.response?.status === 404;
    return (
      <div className="space-y-6">
        {back}
        <ErrorState
          error={query.error}
          title={notFound ? "This clause isn't in this contract" : "Couldn't load this clause"}
          hint={notFound ? "Go back to the report and pick a clause from the list." : "Check that the backend is running, then try again."}
          onRetry={notFound ? undefined : () => query.refetch()}
        />
      </div>
    );
  }

  const flags = clause.flags ?? [];
  const confidence = Math.round((clause.classification_confidence ?? 0) * 100);

  return (
    <div className="space-y-8">
      {back}
      <PageHeader
        eyebrow={`Clause ${clause.index_in_doc + 1} · page ${clause.page_number}`}
        title={`${humanize(clause.clause_type)} clause`}
        description={`Classified as ${humanize(clause.clause_type)} with ${confidence}% confidence (${clause.classification_method}).`}
      />

      <Tabs
        value={tab}
        onValueChange={setTab}
        tabs={[
          { value: "flags", label: "Flags", count: flags.length },
          { value: "text", label: "Clause text" },
        ]}
      >
        <TabPanel value="flags" className="mt-6">
          {flags.length === 0 ? (
            <EmptyState
              icon={<ShieldCheck />}
              title="No predatory-clause flags"
              description="None of ClauseGuard's predatory-clause rules matched this clause."
              action={
                <Button variant="outline" onClick={() => setTab("text")}>
                  Read the clause text
                </Button>
              }
            />
          ) : (
            <ul className="space-y-5">
              {flags.map((flag) => (
                <li key={flag.id}>
                  <Card className="space-y-5 p-5 sm:p-6">
                    <div className="flex flex-wrap items-center gap-3">
                      <SeverityBadge severity={flag.severity} />
                      <h2 className="font-display text-lg font-semibold">{flag.rule_label}</h2>
                    </div>

                    <section aria-labelledby={`reason-${flag.id}`} className="space-y-1.5">
                      <h3 id={`reason-${flag.id}`} className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        Why it is flagged
                      </h3>
                      <p className="leading-relaxed">{flag.reason}</p>
                    </section>

                    <section aria-labelledby={`prov-${flag.id}`} className="space-y-1.5">
                      <h3 id={`prov-${flag.id}`} className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        Provision
                      </h3>
                      <blockquote className="border-l-2 border-violet/60 pl-4 text-sm italic text-muted-foreground">{flag.provision}</blockquote>
                    </section>

                    <section aria-labelledby={`safer-${flag.id}`} className="rounded-xl border border-success/30 bg-success/10 p-4">
                      <h3 id={`safer-${flag.id}`} className="text-xs font-semibold uppercase tracking-wide text-success">
                        Safer wording
                      </h3>
                      <p className="mt-1.5 text-sm leading-relaxed">{flag.safer_wording}</p>
                    </section>
                  </Card>
                </li>
              ))}
            </ul>
          )}
        </TabPanel>

        <TabPanel value="text" className="mt-6">
          <Card>
            <CardBody>
              <p className="whitespace-pre-wrap leading-relaxed">{clause.text}</p>
            </CardBody>
          </Card>
        </TabPanel>
      </Tabs>
    </div>
  );
}
