import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Check, ClipboardCheck, FileText, Play, RotateCcw, Route, UploadCloud, X } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";

import { CountUp, Stagger, StaggerItem } from "@/components/motion";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { CardsSkeleton, EmptyState, ErrorState, InlineLoader, ProgressBar } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage, type Doc, type Quiz as QuizData, type QuizResult } from "@/lib/api";
import { keys } from "@/lib/queries";
import { cn } from "@/lib/utils";

export default function Quiz() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const autoStarted = useRef(false);

  const [quiz, setQuiz] = useState<QuizData | null>(null);
  const [answers, setAnswers] = useState<(number | null)[]>([]);
  const [result, setResult] = useState<QuizResult | null>(null);

  const docs = useQuery({ queryKey: keys.documents, queryFn: async () => (await api.get<Doc[]>("/documents")).data });

  const generate = useMutation({
    mutationFn: async (docId: number) => (await api.post<QuizData>("/quiz/generate", { doc_id: docId })).data,
    onSuccess: (q) => {
      setQuiz(q);
      setAnswers(q.questions.map(() => null));
      setResult(null);
    },
    onError: (e) => toast.error("Couldn't build a quiz", { description: errorMessage(e) }),
  });

  const submit = useMutation({
    mutationFn: async () => (await api.post<QuizResult>("/quiz/submit", { answers })).data,
    onSuccess: (r) => {
      setResult(r);
      setQuiz(null);
      toast.success(`Quiz submitted: ${r.correct}/${r.total} (${r.score_pct}%)`);
      void qc.invalidateQueries({ queryKey: keys.roadmap });
      void qc.invalidateQueries({ queryKey: keys.dashboard });
    },
    onError: (e) => toast.error("Couldn't submit the quiz", { description: errorMessage(e) }),
  });

  // /app/quiz?doc=ID (from Documents) starts that quiz straight away, like the original app did.
  useEffect(() => {
    const id = Number(params.get("doc"));
    if (!id || autoStarted.current) return;
    autoStarted.current = true;
    generate.mutate(id);
    setParams({}, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (answers.every((a) => a !== null)) submit.mutate();
  }

  const answered = answers.filter((a) => a !== null).length;

  /* ---------------- results ---------------- */
  if (result) {
    const docId = docs.data?.find((d) => d.filename === result.doc_name)?.id;
    return (
      <div className="mx-auto max-w-3xl space-y-6">
        <PageHeader eyebrow="Quiz" title="Your result" description={`From ${result.doc_name}`} />
        <Card strong>
          <CardBody className="flex flex-col items-center gap-2 py-8 text-center">
            <div className="font-display text-6xl font-semibold tabular-nums">
              <CountUp value={result.score_pct} format={(n) => `${Math.round(n)}%`} className="text-gradient" />
            </div>
            <p className="text-muted-foreground">
              {result.correct} of {result.total} correct
            </p>
            <ProgressBar value={result.score_pct} label="Score" className="mt-2 max-w-xs" />
          </CardBody>
        </Card>

        <Stagger className="space-y-3" aria-label="Question review">
          {result.results.map((r, i) => (
            <StaggerItem key={i}>
              <Card sweep={false}>
                <CardBody className="space-y-2">
                  <div className="flex items-start gap-3">
                    <span
                      className={cn(
                        "mt-0.5 grid size-6 shrink-0 place-items-center rounded-full",
                        r.is_correct ? "bg-success/15 text-success" : "bg-danger/15 text-danger",
                      )}
                    >
                      {r.is_correct ? <Check className="size-4" /> : <X className="size-4" />}
                      <span className="sr-only">{r.is_correct ? "Correct" : "Incorrect"}</span>
                    </span>
                    <div className="min-w-0 space-y-1.5">
                      <p className="font-medium">
                        {i + 1}. {r.question}
                      </p>
                      <p className="text-sm">
                        {r.is_correct ? (
                          <span className="text-success">Correct: {r.options[r.answer_index]}</span>
                        ) : (
                          <>
                            <span className="text-danger">Your answer: {r.selected !== null ? r.options[r.selected] : "No answer"}</span>
                            <span className="ml-3 text-success">Correct: {r.options[r.answer_index]}</span>
                          </>
                        )}
                      </p>
                      <Badge tone="neutral">Topic: {r.topic}</Badge>
                    </div>
                  </div>
                </CardBody>
              </Card>
            </StaggerItem>
          ))}
        </Stagger>

        <div className="flex flex-wrap gap-2">
          <Button onClick={() => navigate("/app/roadmap")}>
            <Route /> View updated roadmap
          </Button>
          {docId && (
            <Button variant="secondary" loading={generate.isPending} onClick={() => generate.mutate(docId)}>
              <RotateCcw /> New quiz on this document
            </Button>
          )}
          <Button variant="ghost" onClick={() => setResult(null)}>
            <ArrowLeft /> Back to documents
          </Button>
        </div>
      </div>
    );
  }

  /* ---------------- taking a quiz ---------------- */
  if (quiz) {
    return (
      <div className="mx-auto max-w-3xl space-y-6">
        <PageHeader
          eyebrow="Quiz"
          title="Adaptive quiz"
          description={`Generated from ${quiz.doc_name}. Answer every question, then submit.`}
          actions={
            <Button variant="ghost" onClick={() => setQuiz(null)} disabled={submit.isPending}>
              <ArrowLeft /> Cancel
            </Button>
          }
        />
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>
              {answered} of {quiz.questions.length} answered
            </span>
          </div>
          <ProgressBar value={(answered / quiz.questions.length) * 100} label="Questions answered" />
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          {quiz.questions.map((q, qi) => (
            <Card key={qi} sweep={false}>
              <CardBody>
                <fieldset className="space-y-3">
                  <legend className="mb-1 font-medium">
                    {qi + 1}. {q.question}
                  </legend>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {q.options.map((opt, oi) => {
                      const id = `q${qi}o${oi}`;
                      const checked = answers[qi] === oi;
                      return (
                        <label
                          key={id}
                          htmlFor={id}
                          className={cn(
                            "flex cursor-pointer items-center gap-3 rounded-xl border px-3 py-2.5 text-sm transition-colors has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-cyan",
                            checked
                              ? "border-violet bg-accent text-foreground"
                              : "border-[var(--glass-border)] bg-[var(--glass)] hover:border-[color-mix(in_srgb,var(--violet)_50%,transparent)]",
                          )}
                        >
                          <input
                            id={id}
                            type="radio"
                            name={`q${qi}`}
                            value={oi}
                            checked={checked}
                            onChange={() => setAnswers((a) => a.map((v, i) => (i === qi ? oi : v)))}
                            className="size-4 shrink-0 accent-[var(--violet)]"
                          />
                          <span className="min-w-0 break-words">{opt}</span>
                        </label>
                      );
                    })}
                  </div>
                </fieldset>
              </CardBody>
            </Card>
          ))}
          <div className="flex flex-wrap items-center justify-end gap-3">
            {answered < answers.length && <span className="text-sm text-muted-foreground">Answer all questions to submit.</span>}
            <Button type="submit" size="lg" loading={submit.isPending} disabled={answered < answers.length}>
              <Check /> Submit quiz
            </Button>
          </div>
        </form>
      </div>
    );
  }

  /* ---------------- choose a document ---------------- */
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        eyebrow="Quiz"
        title="Adaptive quiz"
        description="Pick a document and get five multiple-choice questions built from its key terms."
      />

      {generate.isPending && <InlineLoader label="Building your quiz…" />}

      {docs.isPending ? (
        <CardsSkeleton count={2} className="sm:grid-cols-1 lg:grid-cols-1" />
      ) : docs.isError ? (
        <ErrorState error={docs.error} title="Couldn't load your documents" onRetry={() => docs.refetch()} />
      ) : docs.data.length === 0 ? (
        <EmptyState
          icon={<UploadCloud />}
          title="Upload a document first"
          description="Quizzes are generated from your own material, so there is nothing to quiz on yet."
          action={
            <Button asChild>
              <Link to="/app/upload">Upload now</Link>
            </Button>
          }
        />
      ) : (
        <Card>
          <CardHeader icon={<ClipboardCheck />} title="Select a document" description="Your results update the study roadmap." />
          <CardBody className="pt-3">
            {generate.isError && (
              <p role="alert" className="mb-3 rounded-xl border border-danger/30 bg-danger/[0.08] px-3 py-2 text-sm text-danger">
                {errorMessage(generate.error)}
              </p>
            )}
            <ul className="space-y-2">
              {docs.data.map((d) => (
                <li key={d.id} className="flex items-center justify-between gap-3 rounded-xl border border-[var(--glass-border)] bg-[var(--glass)] p-3">
                  <div className="flex min-w-0 items-center gap-3">
                    <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-grad-soft text-violet-ink">
                      <FileText className="size-4" />
                    </span>
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium">{d.filename}</div>
                      <Badge tone="violet">{d.subject}</Badge>
                    </div>
                  </div>
                  <Button size="sm" onClick={() => generate.mutate(d.id)} disabled={generate.isPending} aria-label={`Start quiz on ${d.filename}`}>
                    <Play /> Start
                  </Button>
                </li>
              ))}
            </ul>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
