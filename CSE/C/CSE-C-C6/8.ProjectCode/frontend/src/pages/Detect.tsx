import { useMutation } from "@tanstack/react-query";
import { Eraser, FileSearch, ScanSearch, Wand2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";

import { ResultPanel } from "@/components/detect/ResultPanel";
import { VerdictBadge } from "@/components/detect/VerdictBadge";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader } from "@/components/ui/Card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { FormField, Input, Textarea } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage, LABELS, type Prediction } from "@/lib/api";
import { useModel, useSamples } from "@/lib/queries";
import { VERDICT } from "@/lib/verdict";
import { prefersReducedMotion } from "@/lib/utils";

const MIN_WORDS = 5;
const countWords = (s: string) => s.trim().split(/\s+/).filter(Boolean).length;

function ResultSkeleton() {
  return (
    <div className="space-y-4" role="status" aria-label="Analysing article">
      <div className="glass space-y-4 rounded-2xl p-6">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="h-9 w-40 rounded-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-2 w-full" />
      </div>
      <Skeleton className="h-72 w-full rounded-2xl" />
    </div>
  );
}

export default function Detect() {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);
  const samples = useSamples();
  const model = useModel();
  const resultRef = useRef<HTMLDivElement>(null);

  const detect = useMutation({
    mutationFn: async (payload: { title: string; text: string }) => (await api.post<Prediction>("/predict", payload)).data,
    onSuccess: (r) => toast.success(`Verdict: ${r.label}`, { description: r.confidence !== null ? `${(r.confidence * 100).toFixed(1)}% confident` : undefined }),
    onError: (e) => toast.error("Detection failed", { description: errorMessage(e) }),
  });

  // bring the verdict into view once it arrives (the form is tall on small screens)
  useEffect(() => {
    if (detect.data) resultRef.current?.scrollIntoView({ behavior: prefersReducedMotion() ? "auto" : "smooth", block: "start" });
  }, [detect.data]);

  // one example per class from the built-in corpus
  const chips = useMemo(
    () => LABELS.map((l) => samples.data?.find((s) => s.label === l)).filter((s): s is NonNullable<typeof s> => Boolean(s)),
    [samples.data],
  );

  function run(t = title, b = body) {
    if (countWords(`${t} ${b}`) < MIN_WORDS) {
      setFieldError(`Please enter at least ${MIN_WORDS} words of news text.`);
      return;
    }
    setFieldError(null);
    detect.mutate({ title: t, text: b });
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    run();
  }

  function loadSample(text: string) {
    setTitle("");
    setBody(text);
    setFieldError(null);
    run("", text);
  }

  function clear() {
    setTitle("");
    setBody("");
    setFieldError(null);
    detect.reset();
  }

  const words = countWords(`${title} ${body}`);

  return (
    <>
      <PageHeader
        eyebrow="Detect"
        title="Analyse a news article"
        description="Paste a headline and the article text. The model returns REAL, PARTIALLY TRUE or FAKE with its confidence and the cue words it noticed."
      />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.55fr)_minmax(0,1fr)]">
        <div className="min-w-0 space-y-6">
          <Card strong className="p-5 sm:p-6">
            <form onSubmit={onSubmit} className="space-y-4" noValidate>
              <FormField label="Headline (optional)">
                {(p) => <Input {...p} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Central bank announces new policy" autoComplete="off" />}
              </FormField>
              <FormField
                label="Article text"
                error={fieldError}
                hint={`${words} ${words === 1 ? "word" : "words"} · at least ${MIN_WORDS} needed · Ctrl+Enter to analyse`}
              >
                {(p) => (
                  <Textarea
                    {...p}
                    value={body}
                    rows={8}
                    onChange={(e) => {
                      setBody(e.target.value);
                      if (fieldError) setFieldError(null);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                        e.preventDefault();
                        run();
                      }
                    }}
                    placeholder="Paste the full news text here…"
                  />
                )}
              </FormField>
              <div className="flex flex-wrap items-center gap-2">
                <Button type="submit" size="lg" loading={detect.isPending} className="flex-1 sm:flex-none">
                  <ScanSearch /> Detect fake news
                </Button>
                <Button type="button" variant="secondary" size="lg" onClick={clear} disabled={detect.isPending || (!title && !body && !detect.data)}>
                  <Eraser /> Clear
                </Button>
              </div>
              <div className="space-y-2 border-t border-[var(--glass-border)] pt-4">
                <p className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                  <Wand2 className="size-3.5" aria-hidden /> No article handy? Try an example from the demo corpus
                </p>
                {samples.isPending ? (
                  <div className="flex gap-2" role="status" aria-label="Loading examples">
                    {[0, 1, 2].map((i) => (
                      <Skeleton key={i} className="h-8 w-32 rounded-xl" />
                    ))}
                  </div>
                ) : samples.isError ? (
                  <p className="text-xs text-muted-foreground">Examples unavailable: {errorMessage(samples.error)}</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {chips.map((s) => {
                      const Icon = VERDICT[s.label].icon;
                      return (
                        <Button key={s.label} type="button" variant="outline" size="sm" magnetic={false} disabled={detect.isPending} onClick={() => loadSample(s.text)}>
                          <Icon aria-hidden /> {s.label === "PARTIALLY TRUE" ? "Mixed-claims" : s.label === "REAL" ? "Sourced" : "Clickbait"} example
                        </Button>
                      );
                    })}
                  </div>
                )}
              </div>
            </form>
          </Card>

          <div ref={resultRef} className="scroll-mt-24" />
          {detect.isPending ? (
            <ResultSkeleton />
          ) : detect.isError ? (
            <ErrorState
              error={detect.error}
              title="Couldn't analyse this article"
              hint="Your text is still in the box. Check that the backend is running, then try again."
              onRetry={() => run()}
            />
          ) : detect.data ? (
            <ResultPanel result={detect.data} />
          ) : (
            <EmptyState
              icon={<FileSearch />}
              title="Nothing analysed yet"
              description="Paste an article above, or start with an example to see the full result: verdict, confidence, probabilities and cues."
              action={
                chips[0] && (
                  <Button variant="secondary" onClick={() => loadSample(chips[0].text)}>
                    <Wand2 /> Analyse an example
                  </Button>
                )
              }
            />
          )}
        </div>

        <aside className="min-w-0 space-y-4 lg:sticky lg:top-24 lg:self-start" aria-label="How it works">
          <Card>
            <CardHeader title="How it works" description="From raw text to a verdict in four steps" />
            <ol className="space-y-3 p-5 pt-4">
              {model.isPending ? (
                [0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-12 w-full" />)
              ) : model.isError ? (
                <li className="text-sm text-muted-foreground">Couldn&apos;t load the pipeline description: {errorMessage(model.error)}</li>
              ) : (
                model.data.pipeline.map((s, i) => (
                  <li key={s.title} className="flex gap-3">
                    <span className="grid size-7 shrink-0 place-items-center rounded-full bg-grad-primary text-xs font-semibold text-white">{i + 1}</span>
                    <div className="min-w-0">
                      <div className="text-sm font-medium">{s.title}</div>
                      <div className="text-sm text-muted-foreground">{s.text}</div>
                    </div>
                  </li>
                ))
              )}
            </ol>
          </Card>
          <Card>
            <CardHeader title="Reading the verdict" />
            <ul className="space-y-3 p-5 pt-4">
              {LABELS.map((l) => (
                <li key={l} className="space-y-1">
                  <VerdictBadge label={l} />
                  <p className="text-sm text-muted-foreground">{VERDICT[l].meaning}</p>
                </li>
              ))}
            </ul>
          </Card>
        </aside>
      </div>
    </>
  );
}
