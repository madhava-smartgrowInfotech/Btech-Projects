import { ArrowUpRight, FileText, Loader2, MessageSquareText, MoreVertical, Sparkles, Trash2, Upload } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { toast } from "sonner";

import { DocStatusBadge, SeverityBadge } from "@/components/common/Badges";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { PageHeader } from "@/components/common/PageHeader";
import { CardsSkeleton, EmptyState, ErrorState } from "@/components/common/States";
import { ProcessingSteps } from "@/components/policy/ProcessingSteps";
import { UploadDropzone } from "@/components/policy/UploadDropzone";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { errorMessage } from "@/lib/api";
import { useAddSamples, useCreateConversation, useDeletePolicy, usePolicies } from "@/lib/queries";
import type { Policy, Severity } from "@/lib/types";
import { formatBytes, timeAgo } from "@/lib/utils";

export default function Policies() {
  const { data, isLoading, error, refetch } = usePolicies();
  const addSamples = useAddSamples();
  const [showUpload, setShowUpload] = useState(false);

  async function onAddSamples() {
    try {
      const added = await addSamples.mutateAsync();
      toast.success(`Added ${added.length} sample ${added.length === 1 ? "policy" : "policies"}`);
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }

  const empty = !isLoading && !error && data?.length === 0;

  return (
    <div>
      <PageHeader
        title="My policies"
        description="Upload a health-insurance policy wording. PolicyLens splits it into clauses, builds its Policy Card and flags the fine print."
        actions={
          !empty && (
            <>
              <Button variant="outline" onClick={onAddSamples} disabled={addSamples.isPending}>
                {addSamples.isPending ? <Loader2 className="animate-spin" /> : <Sparkles />} Sample policies
              </Button>
              <Button onClick={() => setShowUpload((v) => !v)}>
                <Upload /> Upload policy
              </Button>
            </>
          )
        }
      />

      <AnimatePresence>
        {(showUpload || empty) && (
          <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="mb-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Upload a policy wording</CardTitle>
              </CardHeader>
              <CardContent>
                <UploadDropzone onUploaded={() => setShowUpload(false)} />
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {error ? (
        <ErrorState error={error} onRetry={() => refetch()} />
      ) : isLoading ? (
        <CardsSkeleton count={3} />
      ) : empty ? (
        <EmptyState
          icon={<FileText />}
          title="No policies yet"
          description="Upload your policy wording above, or add four real sample policies from Indian insurers to explore PolicyLens right away."
          action={
            <Button variant="outline" onClick={onAddSamples} disabled={addSamples.isPending}>
              {addSamples.isPending ? <Loader2 className="animate-spin" /> : <Sparkles />} Add sample policies
            </Button>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <AnimatePresence initial={false}>
            {data!.map((p, i) => (
              <motion.div
                key={p.id}
                layout
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.97 }}
                transition={{ delay: Math.min(i * 0.04, 0.3) }}
              >
                <PolicyTile policy={p} />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}

function PolicyTile({ policy }: { policy: Policy }) {
  const doc = policy.document;
  const navigate = useNavigate();
  const del = useDeletePolicy();
  const createConv = useCreateConversation();
  const processing = !["ready", "failed"].includes(doc.status);
  const severities: Severity[] = ["high", "medium", "low"];

  async function ask() {
    try {
      const conv = await createConv.mutateAsync(policy.id);
      navigate(`/app/chat/${conv.id}`);
    } catch (err) {
      toast.error(errorMessage(err));
    }
  }

  return (
    <motion.div whileHover={{ y: -3 }} transition={{ type: "spring", stiffness: 400, damping: 30 }} className="h-full">
      <Card className="h-full gap-4 transition-shadow hover:shadow-md">
        <CardHeader className="flex flex-row items-start gap-3 space-y-0">
          <div className="grid size-10 shrink-0 place-items-center rounded-lg bg-accent text-accent-foreground">
            <FileText className="size-5" />
          </div>
          <div className="min-w-0 flex-1">
            <Link to={`/app/policies/${policy.id}`} className="line-clamp-2 font-semibold leading-snug hover:text-primary">
              {policy.display_name}
            </Link>
            <div className="mt-1 truncate text-xs text-muted-foreground">
              {doc.insurer ?? doc.file_name} · {doc.page_count} pages · {formatBytes(doc.size_bytes)}
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon-sm" aria-label="Policy actions">
                <MoreVertical />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => navigate(`/app/policies/${policy.id}`)}>
                <ArrowUpRight /> Open
              </DropdownMenuItem>
              <ConfirmDialog
                trigger={
                  <DropdownMenuItem onSelect={(e) => e.preventDefault()} className="text-destructive focus:text-destructive">
                    <Trash2 /> Remove
                  </DropdownMenuItem>
                }
                title="Remove this policy?"
                description={`“${policy.display_name}” and its conversations, claim checks and comparisons will be removed from your library.`}
                confirmLabel="Remove"
                destructive
                onConfirm={() =>
                  del.mutate(policy.id, {
                    onSuccess: () => toast.success("Policy removed"),
                    onError: (err) => toast.error(errorMessage(err)),
                  })
                }
              />
            </DropdownMenuContent>
          </DropdownMenu>
        </CardHeader>
        <CardContent className="flex flex-1 flex-col gap-3">
          <div className="flex flex-wrap items-center gap-1.5">
            <DocStatusBadge status={doc.status} />
            {policy.is_sample && <Badge variant="secondary">Sample</Badge>}
            {doc.uin && <Badge variant="outline" className="font-mono text-[10px]">{doc.uin}</Badge>}
          </div>

          {processing ? (
            <ProcessingSteps status={doc.status} progress={doc.progress} detail={doc.status_detail} />
          ) : doc.status === "failed" ? (
            <p className="rounded-lg bg-destructive/5 p-3 text-sm text-destructive">{doc.error ?? "Processing failed."}</p>
          ) : (
            <>
              <dl className="grid grid-cols-2 gap-2 text-sm">
                {[
                  ["Sum insured", policy.highlights.sum_insured],
                  ["Pre-existing wait", policy.highlights.pre_existing_wait],
                  ["Co-payment", policy.highlights.co_payment],
                  ["Specific diseases wait", policy.highlights.specific_wait],
                ]
                  .filter(([, v]) => v)
                  .slice(0, 4)
                  .map(([k, v]) => (
                    <div key={k} className="min-w-0 rounded-lg bg-muted/50 px-2.5 py-2">
                      <dt className="text-[11px] text-muted-foreground">{k}</dt>
                      <dd className="line-clamp-2 text-xs font-medium">{v}</dd>
                    </div>
                  ))}
              </dl>
              {doc.extraction_error && !policy.has_card && (
                <p className="text-xs text-warning-foreground dark:text-warning">{doc.extraction_error}</p>
              )}
              <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
                {severities
                  .filter((s) => policy.risk_counts[s])
                  .map((s) => (
                    <span key={s} className="inline-flex items-center gap-1">
                      <SeverityBadge severity={s} /> {policy.risk_counts[s]}
                    </span>
                  ))}
                <span className="ml-auto">{policy.clause_count} clauses</span>
              </div>
            </>
          )}

          <div className="mt-auto flex items-center gap-2 pt-1">
            <Button asChild variant="outline" size="sm" className="flex-1">
              <Link to={`/app/policies/${policy.id}`}>View policy</Link>
            </Button>
            <Button size="sm" className="flex-1" onClick={ask} disabled={doc.status !== "ready" || createConv.isPending}>
              {createConv.isPending ? <Loader2 className="animate-spin" /> : <MessageSquareText />} Ask
            </Button>
          </div>
          <div className="text-[11px] text-muted-foreground">Added {timeAgo(policy.created_at)}</div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
