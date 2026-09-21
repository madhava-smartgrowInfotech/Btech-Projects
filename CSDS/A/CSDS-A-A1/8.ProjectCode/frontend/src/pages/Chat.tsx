import {
  ArrowUp,
  CircleSlash,
  FileText,
  Languages,
  Loader2,
  MessageSquarePlus,
  MessageSquareText,
  PanelLeft,
  Search,
  ShieldCheck,
  Sparkles,
  Trash2,
} from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { toast } from "sonner";

import { AnswerMarkdown } from "@/components/chat/AnswerMarkdown";
import { CitationSheet, type CitationTarget } from "@/components/chat/CitationSheet";
import { FaithfulnessBadge } from "@/components/chat/FaithfulnessBadge";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { LanguageSelect } from "@/components/common/LanguageSelect";
import { EmptyState, ErrorState } from "@/components/common/States";
import { LogoMark } from "@/components/brand/Logo";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import {
  useAsk,
  useConversation,
  useConversations,
  useCreateConversation,
  useDeleteConversation,
  usePolicies,
} from "@/lib/queries";
import type { Citation, Language, Message } from "@/lib/types";
import { cn, formatMs, timeAgo } from "@/lib/utils";

const SUGGESTIONS = [
  "Is cataract surgery covered and after how long?",
  "What is the waiting period for pre-existing diseases?",
  "Is there a room rent limit or co-payment?",
  "Are ambulance charges covered? Up to how much?",
  "How do I file a cashless claim?",
  "Is dental treatment covered?",
];

const PIPELINE = ["Searching the policy's clauses", "Reading the most relevant clauses", "Writing a cited answer", "Checking faithfulness"];

function ConversationList({ activeId, onPick }: { activeId: number | null; onPick?: () => void }) {
  const { data, isLoading } = useConversations();
  const del = useDeleteConversation();
  const navigate = useNavigate();
  if (isLoading) return <Skeleton className="h-40" />;
  if (!data?.length) return <p className="px-2 text-sm text-muted-foreground">No conversations yet.</p>;
  return (
    <ul className="space-y-1">
      {data.map((c) => (
        <li key={c.id} className="group relative">
          <Link
            to={`/app/chat/${c.id}`}
            onClick={onPick}
            className={cn(
              "block rounded-lg px-3 py-2 pr-9 text-sm transition-colors hover:bg-accent",
              c.id === activeId && "bg-accent text-accent-foreground",
            )}
          >
            <div className="truncate font-medium">{c.title}</div>
            <div className="truncate text-xs text-muted-foreground">
              {c.policy_name} · {timeAgo(c.updated_at)}
            </div>
          </Link>
          <ConfirmDialog
            trigger={
              <Button
                variant="ghost"
                size="icon-xs"
                className="absolute right-1.5 top-2.5 opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
                aria-label="Delete conversation"
              >
                <Trash2 />
              </Button>
            }
            title="Delete this conversation?"
            description="The questions and answers in it will be removed."
            confirmLabel="Delete"
            destructive
            onConfirm={() =>
              del.mutate(c.id, {
                onSuccess: () => c.id === activeId && navigate("/app/chat"),
                onError: (e) => toast.error(errorMessage(e)),
              })
            }
          />
        </li>
      ))}
    </ul>
  );
}

function PolicyPicker() {
  const { data, isLoading, error } = usePolicies();
  const create = useCreateConversation();
  const navigate = useNavigate();
  const ready = data?.filter((p) => p.document.status === "ready") ?? [];

  if (error) return <ErrorState error={error} />;
  if (isLoading) return <Skeleton className="h-48" />;
  if (!ready.length) {
    return (
      <EmptyState
        icon={<FileText />}
        title="Add a policy first"
        description="Upload your policy wording (or add the sample policies) and it will be ready to answer questions in about a minute."
        action={
          <Button asChild>
            <Link to="/app/policies">Go to My policies</Link>
          </Button>
        }
      />
    );
  }
  return (
    <div className="space-y-4">
      <div className="text-center">
        <LogoMark className="mx-auto mb-3 size-12" />
        <h2 className="text-xl font-semibold">Which policy should I read?</h2>
        <p className="text-sm text-muted-foreground">Answers come only from the policy you pick, with clause and page citations.</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {ready.map((p) => (
          <motion.button
            key={p.id}
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.98 }}
            onClick={() =>
              create.mutate(p.id, {
                onSuccess: (conv) => navigate(`/app/chat/${conv.id}`),
                onError: (e) => toast.error(errorMessage(e)),
              })
            }
            disabled={create.isPending}
            className="flex items-start gap-3 rounded-xl border bg-card p-4 text-left transition-colors hover:border-primary/50"
          >
            <FileText className="mt-0.5 size-5 shrink-0 text-primary" />
            <span className="min-w-0">
              <span className="block truncate font-medium">{p.display_name}</span>
              <span className="block truncate text-xs text-muted-foreground">{p.document.insurer}</span>
            </span>
          </motion.button>
        ))}
      </div>
    </div>
  );
}

function ThinkingIndicator() {
  const [step, setStep] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setStep((s) => Math.min(s + 1, PIPELINE.length - 1)), 1600);
    return () => clearInterval(t);
  }, []);
  return (
    <div className="flex items-start gap-3" role="status" aria-live="polite">
      <LogoMark className="size-7" />
      <Card className="gap-2 px-4 py-3">
        {PIPELINE.map((label, i) => (
          <div key={label} className={cn("flex items-center gap-2 text-xs", i > step && "opacity-40")}>
            {i < step ? (
              <ShieldCheck className="size-3.5 text-success" />
            ) : i === step ? (
              <Loader2 className="size-3.5 animate-spin text-primary" />
            ) : (
              <span className="size-3.5 rounded-full border" />
            )}
            {label}
          </div>
        ))}
      </Card>
    </div>
  );
}

function AssistantMessage({
  message,
  policyId,
  onCite,
  onFollowUp,
  isLast,
}: {
  message: Message;
  policyId: number;
  onCite: (t: CitationTarget) => void;
  onFollowUp: (q: string) => void;
  isLast: boolean;
}) {
  const [english, setEnglish] = useState(false);
  const citations = message.citations ?? [];
  const cite = (c: Citation) =>
    onCite({ policyId, ordinal: c.ordinal, label: c.label, page: c.page, quote: c.quote, bboxes: c.bboxes });
  const text = english && message.content_en ? message.content_en : message.content;
  const followUps = message.retrieval?.follow_ups ?? [];

  return (
    <div className="flex items-start gap-3">
      <LogoMark className="mt-0.5 size-7" />
      <div className="min-w-0 flex-1 space-y-2">
        <Card className="gap-3 px-4 py-3">
          {message.status === "not_in_policy" && (
            <Badge variant="outline" className="w-fit gap-1 text-muted-foreground">
              <CircleSlash className="size-3" /> Not covered in this policy document
            </Badge>
          )}
          {message.status === "partial" && (
            <Badge variant="outline" className="w-fit text-warning-foreground dark:text-warning">
              Partly answered by the policy
            </Badge>
          )}
          <AnswerMarkdown text={text} citations={citations} onCite={cite} />
          {citations.length > 0 && (
            <div className="space-y-1.5 border-t pt-3">
              <div className="text-xs font-medium text-muted-foreground">Sources</div>
              <div className="grid gap-1.5 sm:grid-cols-2">
                {citations.map((c, i) => (
                  <button
                    key={c.ordinal}
                    type="button"
                    onClick={() => cite(c)}
                    className="flex min-w-0 items-start gap-2 rounded-lg border bg-muted/30 p-2 text-left text-xs transition-colors hover:border-primary/40 hover:bg-accent"
                  >
                    <span className="grid size-5 shrink-0 place-items-center rounded-md bg-primary/10 font-semibold text-primary">{i + 1}</span>
                    <span className="min-w-0">
                      <span className="line-clamp-1 font-medium">{c.label}</span>
                      <span className="text-muted-foreground">Page {c.page}</span>
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </Card>
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <FaithfulnessBadge faithfulness={message.faithfulness_detail} />
          {message.total_ms && <span>Answered in {formatMs(message.total_ms)}</span>}
          {message.model && <span className="hidden sm:inline">· {message.model}</span>}
          {message.language !== "en" && message.content_en && (
            <Button variant="ghost" size="xs" onClick={() => setEnglish((v) => !v)}>
              <Languages /> {english ? "Show original" : "Show in English"}
            </Button>
          )}
        </div>
        {isLast && followUps.length > 0 && (
          <div className="flex flex-wrap gap-2 pt-1">
            {followUps.map((q) => (
              <Button key={q} variant="outline" size="sm" className="h-auto whitespace-normal py-1.5 text-left text-xs" onClick={() => onFollowUp(q)}>
                {q}
              </Button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function Chat() {
  const { conversationId } = useParams();
  const id = conversationId ? Number(conversationId) : null;
  const { user } = useAuth();
  const conversation = useConversation(id);
  const ask = useAsk(id);
  const [question, setQuestion] = useState("");
  const [pending, setPending] = useState<string | null>(null);
  const [language, setLanguage] = useState<Language>(user?.language ?? "en");
  const [citation, setCitation] = useState<CitationTarget | null>(null);
  const [listOpen, setListOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const messages = conversation.data?.messages ?? [];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, pending]);

  function send(text?: string) {
    const q = (text ?? question).trim();
    if (q.length < 2 || !id || ask.isPending) return;
    setPending(q);
    setQuestion("");
    ask.mutate(
      { question: q, language },
      {
        onError: (err) => {
          toast.error(errorMessage(err));
          setQuestion(q);
        },
        onSettled: () => {
          setPending(null);
          inputRef.current?.focus();
        },
      },
    );
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  const sidebar = (onPick?: () => void) => (
    <div className="space-y-3">
      <Button asChild className="w-full" onClick={onPick}>
        <Link to="/app/chat">
          <MessageSquarePlus /> New conversation
        </Link>
      </Button>
      <ConversationList activeId={id} onPick={onPick} />
    </div>
  );

  return (
    <div className="grid gap-6 lg:grid-cols-[260px_minmax(0,1fr)]">
      <aside className="hidden lg:block">
        <div className="sticky top-20 max-h-[calc(100dvh-7rem)] overflow-auto pr-1">{sidebar()}</div>
      </aside>

      <section className="flex min-h-[calc(100dvh-8rem)] min-w-0 flex-col">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <Sheet open={listOpen} onOpenChange={setListOpen}>
            <SheetTrigger asChild>
              <Button variant="outline" size="icon" className="lg:hidden" aria-label="Conversations">
                <PanelLeft />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-80 p-4">
              <SheetHeader className="p-0">
                <SheetTitle>Conversations</SheetTitle>
                <SheetDescription className="sr-only">Your conversations</SheetDescription>
              </SheetHeader>
              <div className="mt-4">{sidebar(() => setListOpen(false))}</div>
            </SheetContent>
          </Sheet>
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-xl font-bold tracking-tight">{conversation.data?.title ?? "Ask your policy"}</h1>
            {conversation.data && (
              <Link to={`/app/policies/${conversation.data.policy_id}`} className="truncate text-xs text-muted-foreground hover:text-primary">
                {conversation.data.policy_name}
              </Link>
            )}
          </div>
          {id && <LanguageSelect value={language} onChange={setLanguage} />}
        </div>

        {!id ? (
          <div className="mx-auto w-full max-w-2xl py-6">
            <PolicyPicker />
          </div>
        ) : conversation.isError ? (
          <ErrorState error={conversation.error} onRetry={() => conversation.refetch()} />
        ) : conversation.isLoading ? (
          <div className="space-y-4">
            <Skeleton className="ml-auto h-10 w-2/3" />
            <Skeleton className="h-32 w-5/6" />
          </div>
        ) : (
          <>
            <div className="flex-1 space-y-5 pb-4">
              {messages.length === 0 && !pending && (
                <div className="mx-auto max-w-2xl py-8 text-center">
                  <Sparkles className="mx-auto mb-3 size-8 text-primary" />
                  <h2 className="text-lg font-semibold">Ask anything about this policy</h2>
                  <p className="mb-5 text-sm text-muted-foreground">
                    Answers quote the exact clause and page. If the policy doesn't say, PolicyLens tells you instead of guessing.
                  </p>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {SUGGESTIONS.map((s) => (
                      <button
                        key={s}
                        type="button"
                        onClick={() => send(s)}
                        className="flex items-center gap-2 rounded-xl border bg-card px-3 py-2.5 text-left text-sm transition-colors hover:border-primary/50 hover:bg-accent"
                      >
                        <Search className="size-4 shrink-0 text-primary" /> {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              <AnimatePresence initial={false}>
                {messages.map((m, i) => (
                  <motion.div key={m.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
                    {m.role === "user" ? (
                      <div className="flex justify-end">
                        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-sm text-primary-foreground">{m.content}</div>
                      </div>
                    ) : (
                      <AssistantMessage
                        message={m}
                        policyId={conversation.data!.policy_id}
                        onCite={setCitation}
                        onFollowUp={(q) => send(q)}
                        isLast={i === messages.length - 1 && !pending}
                      />
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
              {pending && (
                <>
                  <div className="flex justify-end">
                    <div className="max-w-[85%] rounded-2xl rounded-br-md bg-primary/80 px-4 py-2.5 text-sm text-primary-foreground">{pending}</div>
                  </div>
                  <ThinkingIndicator />
                </>
              )}
              <div ref={bottomRef} />
            </div>

            <div className="sticky bottom-0 -mx-1 bg-gradient-to-t from-background via-background to-transparent px-1 pb-2 pt-4">
              <div className="flex items-end gap-2 rounded-2xl border bg-card p-2 shadow-sm focus-within:ring-2 focus-within:ring-ring/40">
                <Textarea
                  ref={inputRef}
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={onKeyDown}
                  placeholder={
                    language === "hi"
                      ? "अपनी पॉलिसी के बारे में पूछें…"
                      : language === "te"
                        ? "మీ పాలసీ గురించి అడగండి…"
                        : "Ask about cover, waiting periods, limits, claims…"
                  }
                  rows={1}
                  maxLength={1500}
                  className="max-h-40 min-h-10 resize-none border-0 shadow-none focus-visible:ring-0 dark:bg-transparent"
                  aria-label="Your question"
                />
                <Button size="icon" onClick={() => send()} disabled={question.trim().length < 2 || ask.isPending} aria-label="Send question">
                  {ask.isPending ? <Loader2 className="animate-spin" /> : <ArrowUp />}
                </Button>
              </div>
              <p className="mt-1.5 flex items-center gap-1 text-[11px] text-muted-foreground">
                <MessageSquareText className="size-3" /> Enter to send · Shift+Enter for a new line · Answers are generated from your policy text and
                should be confirmed with your insurer for a final decision.
              </p>
            </div>
          </>
        )}
      </section>
      <CitationSheet target={citation} onClose={() => setCitation(null)} />
    </div>
  );
}
