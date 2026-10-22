import { useMutation } from "@tanstack/react-query";
import { Bot, Lightbulb, Send, ShieldAlert, Sparkles, Trash2 } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";

import { LogoMark } from "@/components/brand/Logo";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ErrorState, Skeleton } from "@/components/ui/Feedback";
import { Input } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { api, errorMessage } from "@/lib/api";
import { useInsights } from "@/lib/queries";
import { cn } from "@/lib/utils";

interface Message {
  role: "user" | "assistant";
  text: string;
  source?: string;
  failed?: boolean;
}

const STORE = "finjarvis-chat";
const EXAMPLES = [
  "How much did I spend on Food?",
  "Where am I spending the most money?",
  "Can I save 10000 this month?",
  "How can I reduce my expenses?",
  "What is my financial health?",
];

function loadChat(): Message[] {
  try {
    return JSON.parse(sessionStorage.getItem(STORE) ?? "[]");
  } catch {
    return [];
  }
}

export default function Assistant() {
  const insights = useInsights();
  const [messages, setMessages] = useState<Message[]>(loadChat);
  const [draft, setDraft] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    try {
      sessionStorage.setItem(STORE, JSON.stringify(messages.filter((m) => !m.failed)));
    } catch {
      /* chat just won't survive a reload */
    }
    endRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [messages]);

  const ask = useMutation({
    mutationFn: async (question: string) => (await api.post<{ answer: string; source?: string }>("/assistant/ask", { question })).data,
    onSuccess: (r) => setMessages((m) => [...m, { role: "assistant", text: r.answer, source: r.source }]),
    onError: (e) => setMessages((m) => [...m, { role: "assistant", text: `${errorMessage(e)} You can ask again.`, failed: true }]),
  });

  function send(text: string) {
    const q = text.trim();
    if (!q || ask.isPending) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setDraft("");
    ask.mutate(q);
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    send(draft);
  }

  return (
    <>
      <PageHeader
        title="AI assistant"
        description={insights.data?.disclaimer ?? "Ask about your spending, budgets, savings or financial health."}
        actions={
          messages.length > 0 && (
            <Button variant="ghost" size="sm" onClick={() => setMessages([])}>
              <Trash2 /> Clear chat
            </Button>
          )
        }
      />

      {insights.data && !insights.data.llm_enabled && (
        <p role="note" className="mb-4 flex items-start gap-2 rounded-xl border border-info/30 bg-info/10 px-4 py-3 text-sm text-info">
          <ShieldAlert className="mt-0.5 size-4 shrink-0" />
          Free-form AI chat is running on built-in analytics only. Set AI_API_KEY in the .env file and restart the server to enable richer natural-language answers.
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-[1fr_22rem]">
        <Card className="flex min-h-[28rem] flex-col">
          <CardHeader title="Ask FINJARVIS" description="Answers use only your own recorded data." icon={<Bot />} />
          <CardBody className="flex flex-1 flex-col gap-4">
            <div className="scrollbar-thin flex max-h-[26rem] min-h-[14rem] flex-1 flex-col gap-3 overflow-y-auto pr-1" aria-live="polite" aria-label="Conversation">
              {messages.length === 0 && (
                <div className="m-auto max-w-sm space-y-3 text-center text-sm text-muted-foreground">
                  <LogoMark className="mx-auto size-10" />
                  <p>Ask a question below, or tap one of these:</p>
                </div>
              )}
              {messages.map((m, i) =>
                m.role === "user" ? (
                  <div key={i} className="ml-auto w-fit max-w-[85%] whitespace-pre-line rounded-2xl rounded-br-md bg-grad-primary px-3.5 py-2 text-sm text-white shadow-[0_8px_24px_-10px_rgba(124,92,255,0.8)]">
                    {m.text}
                  </div>
                ) : (
                  <div key={i} className="flex gap-2">
                    <LogoMark className="size-7" />
                    <div
                      className={cn(
                        "min-w-0 max-w-[90%] whitespace-pre-line rounded-2xl rounded-tl-md border p-3 text-sm",
                        m.failed ? "border-danger/30 bg-danger/10 text-danger" : "border-[var(--glass-border)] bg-[var(--glass)]",
                      )}
                    >
                      {m.text}
                      {m.source && !m.failed && (
                        <span className="mt-2 block text-[11px] text-muted-foreground">{m.source === "llm" ? "AI language model" : m.source === "analytics" ? "Calculated from your data" : "Built-in help"}</span>
                      )}
                    </div>
                  </div>
                ),
              )}
              {ask.isPending && (
                <div className="flex gap-2" role="status" aria-label="FINJARVIS is thinking">
                  <LogoMark className="size-7" />
                  <div className="space-y-2 rounded-2xl rounded-tl-md border border-[var(--glass-border)] bg-[var(--glass)] p-3">
                    <Skeleton className="h-3 w-48" />
                    <Skeleton className="h-3 w-32" />
                  </div>
                </div>
              )}
              <div ref={endRef} />
            </div>

            <ul className="flex flex-wrap gap-2" aria-label="Example questions">
              {EXAMPLES.map((ex) => (
                <li key={ex}>
                  <button
                    type="button"
                    onClick={() => send(ex)}
                    disabled={ask.isPending}
                    className="rounded-full border border-[var(--glass-border)] bg-[var(--glass)] px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-[var(--violet)] hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan disabled:opacity-50"
                  >
                    {ex}
                  </button>
                </li>
              ))}
            </ul>

            <form onSubmit={onSubmit} className="flex items-center gap-2">
              <Input
                aria-label="Your question"
                wrapperClassName="flex-1"
                placeholder="Ask about your spending, budgets, savings or financial health…"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                maxLength={500}
              />
              <Button type="submit" size="icon" aria-label="Send question" loading={ask.isPending} disabled={!draft.trim()}>
                <Send />
              </Button>
            </form>
          </CardBody>
        </Card>

        <Card className="h-fit">
          <CardHeader title="Insights" description="Spotted in your recorded data" icon={<Lightbulb />} />
          <CardBody>
            {insights.isPending ? (
              <div className="space-y-2" role="status" aria-label="Loading insights">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-4/5" />
                <Skeleton className="h-4 w-3/5" />
              </div>
            ) : insights.isError ? (
              <ErrorState error={insights.error} title="Couldn't load insights" onRetry={() => void insights.refetch()} />
            ) : (
              <ul className="space-y-3">
                {insights.data.insights.map((s, i) => (
                  <li key={i} className="flex gap-2 text-sm">
                    <Sparkles className="mt-0.5 size-4 shrink-0 text-violet-ink" />
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>
      </div>
    </>
  );
}
