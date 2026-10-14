import { useMutation } from "@tanstack/react-query";
import { Bot, FileText, Languages, Send, Sparkles, X } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { FormField, Input } from "@/components/ui/Field";
import { InlineLoader, ProgressBar } from "@/components/ui/Feedback";
import { Select } from "@/components/ui/Select";
import { api, errorMessage } from "@/lib/api";
import { LANGUAGES } from "@/lib/constants";
import type { AssistantReply, TimelineItem } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Markdown } from "@/components/records/Markdown";

type Kind = "explain" | "summary" | "ask";

interface Props {
  /** "me" for the patient's own assistant, or a UniHealth person id for a consented doctor. */
  personId: string;
  /** A diagnostic report chosen from the timeline, to explain. */
  report?: TimelineItem | null;
  onClearReport?: () => void;
}

/** Plain-language explanations of records, in the chosen language. Never a diagnosis. */
export function AssistantPanel({ personId, report, onClearReport }: Props) {
  const [language, setLanguage] = useState("English");
  const [question, setQuestion] = useState("");

  const ask = useMutation({
    mutationFn: async ({ kind, body = {} }: { kind: Kind; body?: Record<string, unknown> }) =>
      (await api.post<AssistantReply>(`/assistant/${kind}`, { person_id: personId, language, ...body })).data,
  });

  const pending = ask.isPending ? ask.variables?.kind : undefined;

  return (
    <Card>
      <CardHeader
        icon={<Bot />}
        title="AI health assistant"
        description="Explains results in plain language. Not a diagnosis."
        action={
          <div className="flex items-center gap-2">
            <Languages className="size-4 text-muted-foreground" aria-hidden />
            <Select
              aria-label="Answer language"
              value={language}
              onValueChange={setLanguage}
              options={LANGUAGES.map((l) => ({ value: l, label: l }))}
              className="w-36"
            />
          </div>
        }
      />
      <CardBody className="space-y-4">
        <div className="flex flex-wrap gap-2">
          {report ? (
            <>
              <Button loading={pending === "explain"} onClick={() => ask.mutate({ kind: "explain", body: { report_id: report.id } })}>
                <FileText /> Explain {report.title || report.type}
                {report.date ? ` (${formatDate(report.date)})` : ""}
              </Button>
              <Button variant="ghost" onClick={onClearReport}>
                <X /> Clear
              </Button>
            </>
          ) : (
            <Button loading={pending === "explain"} onClick={() => ask.mutate({ kind: "explain" })}>
              <FileText /> Explain latest lipid panel
            </Button>
          )}
          <Button variant="secondary" loading={pending === "summary"} onClick={() => ask.mutate({ kind: "summary" })}>
            <Sparkles /> Summarise treatment
          </Button>
        </div>

        <form
          className="flex flex-col gap-2 sm:flex-row sm:items-end"
          onSubmit={(e) => {
            e.preventDefault();
            if (question.trim()) ask.mutate({ kind: "ask", body: { question: question.trim() } });
          }}
        >
          <FormField label="Ask a question" className="flex-1">
            {(p) => (
              <Input
                {...p}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask about your medicines, results or next steps"
              />
            )}
          </FormField>
          <Button type="submit" loading={pending === "ask"} disabled={!question.trim()}>
            <Send /> Ask
          </Button>
        </form>

        <div aria-live="polite" className="space-y-3">
          {pending && (
            <div className="space-y-2">
              <InlineLoader label="Asking the assistant..." />
              <ProgressBar value={0} indeterminate label="Assistant is working" />
            </div>
          )}
          {ask.isError && (
            <p role="alert" className="rounded-xl border border-danger/30 bg-danger/[0.06] p-3 text-sm text-danger">
              {errorMessage(ask.error)}
            </p>
          )}
          {ask.data && !pending && (
            <div className="space-y-2 rounded-xl border border-[var(--glass-border)] bg-[var(--glass)] p-4">
              {ask.data.title && <div className="text-xs text-muted-foreground">{ask.data.title}</div>}
              {ask.data.values && ask.data.values.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {ask.data.values.map((v) => (
                    <Badge key={v} tone="violet">
                      {v}
                    </Badge>
                  ))}
                </div>
              )}
              <div className="text-sm leading-relaxed"><Markdown text={ask.data.text} /></div>
              <p className="text-xs text-muted-foreground">{ask.data.disclaimer}</p>
            </div>
          )}
        </div>
      </CardBody>
    </Card>
  );
}
