import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpenText, ChevronDown, History, Send, Sparkles, UploadCloud } from "lucide-react";
import { useState, type FormEvent, type KeyboardEvent } from "react";
import { Link } from "react-router";

import { LogoMark } from "@/components/brand/Logo";
import { FadeIn } from "@/components/motion";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { EmptyState, ErrorState, InlineLoader, Skeleton } from "@/components/ui/Feedback";
import { Textarea } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage, type AskResult, type Doc, type HistoryItem, type Source } from "@/lib/api";
import { keys } from "@/lib/queries";
import { timeAgo } from "@/lib/utils";

interface Shown {
  question: string;
  answer: string;
  created_at: string;
  docs: string[];
  passages?: Source[];
  llm?: boolean;
}

const unique = (names: string[]) => Array.from(new Set(names));

export default function Ask() {
  const qc = useQueryClient();
  const [question, setQuestion] = useState("");
  const [shown, setShown] = useState<Shown | null>(null);

  const docs = useQuery({ queryKey: keys.documents, queryFn: async () => (await api.get<Doc[]>("/documents")).data });
  const history = useQuery({ queryKey: keys.history, queryFn: async () => (await api.get<HistoryItem[]>("/ask/history")).data });

  const ask = useMutation({
    mutationFn: async (q: string) => (await api.post<AskResult>("/ask", { question: q })).data,
    onSuccess: (r) => {
      setShown({ question: r.question, answer: r.answer, created_at: r.created_at, docs: unique(r.sources.map((s) => s.doc_name)), passages: r.sources, llm: r.llm_enabled });
      void qc.invalidateQueries({ queryKey: keys.history });
      void qc.invalidateQueries({ queryKey: keys.dashboard });
    },
    onError: (e) => toast.error("Couldn't get an answer", { description: errorMessage(e) }),
  });

  function submit(e?: FormEvent) {
    e?.preventDefault();
    const q = question.trim();
    if (q && !ask.isPending) ask.mutate(q);
  }
  function onKeyDown(e: KeyboardEvent) {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) submit();
  }

  const noDocs = docs.isSuccess && docs.data.length === 0;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Ask"
        title="Ask your notes"
        description="Answers are built only from the documents you uploaded, and the source file is shown with each one."
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="min-w-0 space-y-6">
          {noDocs ? (
            <EmptyState
              icon={<UploadCloud />}
              title="Upload something to ask about"
              description="There is nothing to search yet. Add a PDF, DOCX or TXT and come back."
              action={
                <Button asChild>
                  <Link to="/app/upload">Upload material</Link>
                </Button>
              }
            />
          ) : (
            <Card>
              <CardBody>
                <form onSubmit={submit} className="space-y-3">
                  <label htmlFor="question" className="text-sm font-medium">
                    Your question
                  </label>
                  <Textarea
                    id="question"
                    name="question"
                    rows={3}
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={onKeyDown}
                    placeholder="e.g. What is the LIFO principle?"
                    disabled={ask.isPending}
                  />
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-xs text-muted-foreground">Press Ctrl+Enter to send</span>
                    <Button type="submit" loading={ask.isPending} disabled={!question.trim() || docs.isPending}>
                      <Send /> Ask
                    </Button>
                  </div>
                </form>
              </CardBody>
            </Card>
          )}

          {ask.isPending && (
            <Card role="status" aria-label="Searching your documents">
              <CardBody className="space-y-3">
                <InlineLoader label="Searching your documents…" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-11/12" />
                <Skeleton className="h-4 w-2/3" />
              </CardBody>
            </Card>
          )}

          {ask.isError && !ask.isPending && (
            <ErrorState error={ask.error} title="That question didn't go through" hint="Your question is still in the box. Try again." onRetry={() => submit()} />
          )}

          {shown && !ask.isPending && (
            <FadeIn>
              <Card strong>
                <CardBody className="space-y-4">
                  <div className="ml-auto w-fit max-w-full rounded-2xl rounded-br-md bg-grad-primary px-3.5 py-2 text-sm text-white">{shown.question}</div>
                  <div className="flex gap-3">
                    <LogoMark className="size-8" />
                    <div className="min-w-0 flex-1 space-y-3">
                      <p className="whitespace-pre-wrap break-words leading-relaxed" aria-live="polite">
                        {shown.answer}
                      </p>
                      {shown.llm !== undefined && (
                        <Badge tone={shown.llm ? "violet" : "neutral"}>
                          <Sparkles /> {shown.llm ? "Written by Claude from your notes" : "Offline mode: key sentences from your notes"}
                        </Badge>
                      )}
                    </div>
                  </div>
                  <div className="space-y-2 border-t border-[var(--glass-border)] pt-4">
                    <h3 className="flex items-center gap-2 text-sm font-medium">
                      <BookOpenText className="size-4 text-violet-ink" /> Sources
                    </h3>
                    {shown.docs.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No passage in your documents matched this question.</p>
                    ) : shown.passages ? (
                      <ul className="space-y-2">
                        {shown.passages.map((s) => (
                          <li key={`${s.doc_id}-${s.chunk_index}`}>
                            <details className="group glass-flat rounded-xl px-3 py-2 text-sm">
                              <summary className="flex cursor-pointer list-none items-center justify-between gap-2 rounded">
                                <span className="min-w-0 truncate font-medium">
                                  {s.doc_name} <span className="font-normal text-muted-foreground">- passage {s.chunk_index + 1}</span>
                                </span>
                                <span className="flex shrink-0 items-center gap-2">
                                  <Badge tone="cyan">match {s.score.toFixed(2)}</Badge>
                                  <ChevronDown className="size-4 text-muted-foreground transition-transform group-open:rotate-180" />
                                </span>
                              </summary>
                              <p className="mt-2 whitespace-pre-wrap break-words text-muted-foreground">{s.text}</p>
                            </details>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {shown.docs.map((n) => (
                          <Badge key={n} tone="cyan">
                            {n}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </CardBody>
              </Card>
            </FadeIn>
          )}
        </div>

        <aside aria-label="Recent questions">
          <Card className="lg:sticky lg:top-24">
            <CardHeader icon={<History />} title="Recent questions" description="Your last 10. Select one to reopen it." />
            <CardBody className="pt-3">
              {history.isPending ? (
                <div className="space-y-2" role="status" aria-label="Loading history">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                </div>
              ) : history.isError ? (
                <ErrorState error={history.error} title="History unavailable" onRetry={() => history.refetch()} className="py-6" />
              ) : history.data.length === 0 ? (
                <p className="rounded-xl border border-dashed border-[var(--glass-border)] p-4 text-center text-sm text-muted-foreground">
                  Questions you ask will be listed here.
                </p>
              ) : (
                <ul className="-mx-2 space-y-1">
                  {history.data.map((h) => (
                    <li key={h.id}>
                      <button
                        type="button"
                        onClick={() => setShown({ question: h.question, answer: h.answer, created_at: h.created_at, docs: unique(h.sources) })}
                        className="w-full rounded-xl px-2 py-2 text-left transition-colors hover:bg-muted"
                      >
                        <span className="block truncate text-sm font-medium">{h.question}</span>
                        <span className="block truncate text-xs text-muted-foreground">
                          {h.answer.length > 80 ? `${h.answer.slice(0, 80)}…` : h.answer}
                        </span>
                        <span className="text-[11px] text-muted-foreground">{timeAgo(h.created_at)}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </CardBody>
          </Card>
        </aside>
      </div>
    </div>
  );
}
