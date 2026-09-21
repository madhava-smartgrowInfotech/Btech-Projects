import {
  ArrowLeft,
  ClipboardCheck,
  ExternalLink,
  FileText,
  Loader2,
  MessageSquareText,
  RefreshCw,
  Search,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import { useMemo } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router";
import { toast } from "sonner";

import { DocStatusBadge } from "@/components/common/Badges";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { LanguageSelect } from "@/components/common/LanguageSelect";
import { EmptyState, ErrorState } from "@/components/common/States";
import { ClauseSearch } from "@/components/policy/ClauseSearch";
import { openOriginalPdf, PdfPageViewer } from "@/components/policy/PdfPageViewer";
import { PolicyCardView } from "@/components/policy/PolicyCardView";
import { ProcessingSteps } from "@/components/policy/ProcessingSteps";
import { RiskList } from "@/components/policy/RiskList";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { errorCode, errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useCreateConversation, usePolicy, usePolicyCard, useReextract, useRisks } from "@/lib/queries";
import type { Language } from "@/lib/types";

export default function PolicyView() {
  const { policyId } = useParams();
  const id = Number(policyId);
  const navigate = useNavigate();
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const tab = params.get("tab") ?? "card";
  const page = Number(params.get("page") ?? 1) || 1;
  const clause = params.get("clause") ? Number(params.get("clause")) : null;
  const lang = (params.get("lang") as Language) || user?.language || "en";

  const policy = usePolicy(id);
  const ready = policy.data?.document.status === "ready";
  const card = usePolicyCard(id, lang, ready && Boolean(policy.data?.has_card));
  const risks = useRisks(id, lang, ready);
  const createConv = useCreateConversation();
  const reextract = useReextract(id);

  const setView = (patch: Record<string, string | number | null>) => {
    const next = new URLSearchParams(params);
    Object.entries(patch).forEach(([k, v]) => (v === null ? next.delete(k) : next.set(k, String(v))));
    setParams(next, { replace: true });
  };
  const openSource = (p: number, ordinal: number | null) => setView({ tab: "document", page: p, clause: ordinal });

  const riskCount = risks.data?.length ?? 0;
  const highCount = useMemo(() => risks.data?.filter((r) => r.severity === "high").length ?? 0, [risks.data]);

  async function ask() {
    try {
      const conv = await createConv.mutateAsync(id);
      navigate(`/app/chat/${conv.id}`);
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }

  if (policy.isError) {
    return <ErrorState error={policy.error} title="Couldn't open this policy" onRetry={() => policy.refetch()} />;
  }
  if (policy.isLoading || !policy.data) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-1/2" />
        <Skeleton className="h-24" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  const p = policy.data;
  const doc = p.document;
  const processing = !["ready", "failed"].includes(doc.status);

  return (
    <div>
      <Link to="/app/policies" className="mb-3 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="size-4" /> My policies
      </Link>
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <DocStatusBadge status={doc.status} />
            {p.is_sample && <Badge variant="secondary">Sample policy</Badge>}
            {doc.uin && (
              <Badge variant="outline" className="font-mono text-[11px]">
                {doc.uin}
              </Badge>
            )}
          </div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{p.display_name}</h1>
          <p className="text-sm text-muted-foreground">
            {doc.insurer ?? "Insurer not detected yet"} · {doc.page_count} pages · {p.clause_count} clauses
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => openOriginalPdf(id)}>
            <ExternalLink /> Original PDF
          </Button>
          <Button variant="outline" asChild disabled={!ready}>
            <Link to={`/app/claims?policy=${id}`}>
              <ClipboardCheck /> Check a claim
            </Link>
          </Button>
          <Button onClick={ask} disabled={!ready || createConv.isPending}>
            {createConv.isPending ? <Loader2 className="animate-spin" /> : <MessageSquareText />} Ask this policy
          </Button>
        </div>
      </div>

      {processing && (
        <Card className="mb-6">
          <CardContent className="space-y-2 pt-6">
            <div className="text-sm font-medium">Analysing your policy - this usually takes under two minutes.</div>
            <ProcessingSteps status={doc.status} progress={doc.progress} detail={doc.status_detail} />
          </CardContent>
        </Card>
      )}
      {doc.status === "failed" && (
        <ErrorState error={new Error(doc.error ?? "Processing failed.")} title="We couldn't read this PDF" className="mb-6" />
      )}

      {!processing && doc.status !== "failed" && (
        <Tabs value={tab} onValueChange={(v) => setView({ tab: v })}>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <TabsList className="h-auto flex-wrap">
              <TabsTrigger value="card">
                <Sparkles /> Policy Card
              </TabsTrigger>
              <TabsTrigger value="risks">
                <ShieldAlert /> Risks
                {riskCount > 0 && (
                  <Badge variant={highCount ? "destructive" : "secondary"} className="ml-1 h-5 px-1.5 text-[10px]">
                    {riskCount}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="document">
                <FileText /> Document
              </TabsTrigger>
              <TabsTrigger value="search">
                <Search /> Clause search
              </TabsTrigger>
            </TabsList>
            {(tab === "card" || tab === "risks") && (
              <LanguageSelect value={lang} onChange={(l) => setView({ lang: l })} label="Display language" />
            )}
          </div>

          <TabsContent value="card">
            {!p.has_card ? (
              <EmptyState
                icon={<Sparkles />}
                title="Policy Card not available yet"
                description={doc.extraction_error ?? "The AI extraction has not finished for this policy."}
                action={
                  <Button onClick={() => reextract.mutate(undefined, { onError: (e) => toast.error(errorMessage(e)) })} disabled={reextract.isPending}>
                    {reextract.isPending ? <Loader2 className="animate-spin" /> : <RefreshCw />} Build Policy Card
                  </Button>
                }
              />
            ) : card.isError ? (
              <ErrorState
                error={card.error}
                title={errorCode(card.error) === "ai_quota" ? "Translation limit reached" : "Couldn't load the Policy Card"}
                onRetry={() => card.refetch()}
              />
            ) : card.isLoading || !card.data ? (
              <div className="space-y-4">
                {lang !== "en" && <p className="text-sm text-muted-foreground">Translating the Policy Card…</p>}
                <Skeleton className="h-40" />
                <div className="grid gap-3 sm:grid-cols-4">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <Skeleton key={i} className="h-24" />
                  ))}
                </div>
              </div>
            ) : (
              <>
                <PolicyCardView card={card.data} onOpenSource={openSource} />
                <div className="mt-4">
                  <ConfirmDialog
                    trigger={
                      <Button variant="ghost" size="sm" disabled={reextract.isPending}>
                        <RefreshCw /> Re-run AI extraction
                      </Button>
                    }
                    title="Re-run the Policy Card extraction?"
                    description="PolicyLens will read the whole policy again with Gemini and rebuild the card and risk highlights. This uses one AI request."
                    confirmLabel="Re-run"
                    onConfirm={() =>
                      reextract.mutate(undefined, {
                        onSuccess: () => toast.success("Extraction started - the card refreshes when it's done."),
                        onError: (e) => toast.error(errorMessage(e)),
                      })
                    }
                  />
                </div>
              </>
            )}
          </TabsContent>

          <TabsContent value="risks">
            {risks.isError ? (
              <ErrorState error={risks.error} onRetry={() => risks.refetch()} />
            ) : risks.isLoading || !risks.data ? (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-24" />
                ))}
              </div>
            ) : (
              <RiskList risks={risks.data} onOpenSource={openSource} />
            )}
          </TabsContent>

          <TabsContent value="document">
            <PdfPageViewer
              policyId={id}
              page={page}
              onPageChange={(n) => setView({ page: n })}
              selectedOrdinal={clause}
              onSelectClause={(c) => setView({ clause: c ? c.ordinal : null })}
            />
          </TabsContent>

          <TabsContent value="search">
            <ClauseSearch policyId={id} onOpenSource={openSource} />
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
