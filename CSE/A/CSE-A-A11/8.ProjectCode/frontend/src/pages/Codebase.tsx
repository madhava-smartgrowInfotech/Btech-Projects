import { useMutation } from "@tanstack/react-query";
import { BookOpen, Boxes, Code2, Compass, FileCode2, FolderGit2, GitBranch, Library, MapIcon, MessageSquare, Network, Package, Send, Sparkles, Waypoints } from "lucide-react";
import { lazy, Suspense, useEffect, useRef, useState, type FormEvent } from "react";

import { CodeBlock } from "@/components/app/CodeBlock";
import { LogoMark } from "@/components/brand/Logo";
import { ChartCard } from "@/components/charts/Chart";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/Display";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { FormField, Input } from "@/components/ui/Field";
import { FileDrop } from "@/components/ui/FileDrop";
import { PageHeader } from "@/components/ui/Layout";
import { TabPanel, Tabs } from "@/components/ui/Navigation";
import { Select } from "@/components/ui/Select";
import { Table, type Column } from "@/components/ui/Table";
import { toast } from "@/components/ui/Toast";
import { api } from "@/lib/api";
import { useMeta } from "@/lib/hooks";
import { useSettings } from "@/lib/settings";
import type { AskResult, Hit, RepoIndexInfo } from "@/lib/types";
import { cn, formatBytes } from "@/lib/utils";

const Markdown = lazy(() => import("@/components/app/Markdown"));

type Source = "demo" | "self" | "upload" | "folder" | "github";
const SOURCES = [
  { value: "demo", label: "Demo shop app" },
  { value: "self", label: "AutoSecAI (this project)" },
  { value: "upload", label: "Upload .zip" },
  { value: "folder", label: "Local folder" },
  { value: "github", label: "GitHub repo URL" },
];

interface Msg {
  role: "user" | "assistant";
  content: string;
  hits?: Hit[];
}

function HitCard({ h }: { h: Hit }) {
  return (
    <details className="group rounded-xl border border-[var(--glass-border)] bg-muted/50">
      <summary className="flex cursor-pointer list-none items-center gap-2 px-3 py-2 text-sm [&::-webkit-details-marker]:hidden">
        <Code2 className="size-4 shrink-0 text-violet-ink" />
        <span className="min-w-0 flex-1 truncate">
          <code className="font-mono text-xs">{h.file}</code> · {h.kind === "file" ? "module overview" : h.name} · line {h.line}
        </span>
      </summary>
      <div className="space-y-2 border-t border-[var(--glass-border)] p-3">
        {h.why.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {h.why.map((w) => <Badge key={w} tone="neutral">{w}</Badge>)}
          </div>
        )}
        <CodeBlock code={h.code} language={h.file.endsWith(".py") ? "python" : undefined} maxHeight="14rem" />
      </div>
    </details>
  );
}

function DependencyGraph({ graph }: { graph: RepoIndexInfo["graph"] }) {
  const W = 560, H = 380, P = 48;
  const xs = graph.nodes.map((n) => n.x), ys = graph.nodes.map((n) => n.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
  const sx = (x: number) => P + ((x - minX) / (maxX - minX || 1)) * (W - 2 * P);
  const sy = (y: number) => P + ((y - minY) / (maxY - minY || 1)) * (H - 2 * P);
  const pos = Object.fromEntries(graph.nodes.map((n) => [n.id, { x: sx(n.x), y: sy(n.y) }]));
  const maxDeg = Math.max(...graph.nodes.map((n) => n.degree), 1);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label={`Module dependency graph with ${graph.nodes.length} files and ${graph.edges.length} import links`}>
      {graph.edges.map(([a, b], i) => (
        <line key={i} x1={pos[a].x} y1={pos[a].y} x2={pos[b].x} y2={pos[b].y} stroke="var(--chart-grid)" strokeWidth={1.5} style={{ stroke: "color-mix(in srgb, var(--violet) 35%, transparent)" }} />
      ))}
      {graph.nodes.map((n) => {
        const t = n.degree / maxDeg;
        return (
          <g key={n.id}>
            <title>{`${n.id} (${n.degree} link${n.degree === 1 ? "" : "s"})`}</title>
            <circle cx={pos[n.id].x} cy={pos[n.id].y} r={7 + 9 * t} fill={t > 0.5 ? "#7C5CFF" : "#22D3EE"} fillOpacity={0.85} stroke="var(--background)" strokeWidth={2} />
            <text x={pos[n.id].x} y={pos[n.id].y - 13 - 9 * t} textAnchor="middle" fontSize="10" fill="var(--muted-foreground)">{n.label}</text>
          </g>
        );
      })}
    </svg>
  );
}

export default function Codebase() {
  const meta = useMeta();
  const { settings } = useSettings();
  const [source, setSource] = useState<Source>("demo");
  const [zips, setZips] = useState<File[]>([]);
  const [folder, setFolder] = useState("");
  const [url, setUrl] = useState("");
  const [tab, setTab] = useState("ask");
  const [chat, setChat] = useState<Msg[]>([]);
  const [question, setQuestion] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  const [index, setIndex] = useState<RepoIndexInfo | null>(null);

  const indexer = useMutation({
    mutationFn: async () => {
      if (source === "upload") {
        const fd = new FormData();
        zips.forEach((z) => fd.append("files", z));
        return (await api.post<RepoIndexInfo>("/codebase/index/upload", fd, { headers: { "Content-Type": "multipart/form-data" } })).data;
      }
      return (await api.post<RepoIndexInfo>("/codebase/index", { source, folder, url, gh_token: settings.ghToken || null })).data;
    },
    onSuccess: (data) => {
      setIndex(data);
      setChat([]);
      setTab("ask");
      toast.success(`Indexed ${data.files} files, ${data.units} code units.`);
    },
  });

  const asker = useMutation({
    mutationFn: async (q: string) =>
      (await api.post<AskResult>(`/codebase/${index!.index_id}/ask`, {
        question: q,
        k: 6,
        use_llm: settings.useLlm && Boolean(settings.apiKey || meta.data?.llm_env),
        api_key: settings.apiKey || null,
      })).data,
    onSuccess: (res) => setChat((c) => [...c, { role: "assistant", content: res.answer, hits: res.hits }]),
  });

  useEffect(() => endRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" }), [chat.length, asker.isPending]);

  function ask(q: string) {
    const text = q.trim();
    if (!text || asker.isPending) return;
    setChat((c) => [...c, { role: "user", content: text }]);
    setQuestion("");
    asker.mutate(text);
  }

  const canIndex = source === "upload" ? zips.length > 0 : source === "folder" ? folder.trim().length > 0 : source === "github" ? url.trim().length > 0 : true;
  const o = index?.overview;
  const routeCols: Column<RepoIndexInfo["overview"]["routes"][number]>[] = [
    { key: "m", header: "Method", cell: (r) => <Badge tone="violet">{r.method}</Badge>, sortValue: (r) => r.method },
    { key: "p", header: "Path", cell: (r) => <code className="font-mono text-xs">{r.path}</code>, sortValue: (r) => r.path },
    { key: "h", header: "Handler", cell: (r) => <code className="font-mono text-xs">{r.handler}</code> },
    { key: "f", header: "File", cell: (r) => <span className="font-mono text-xs">{r.file}:{r.line}</span> },
  ];
  const hotCols: Column<RepoIndexInfo["overview"]["hotspots"][number]>[] = [
    { key: "n", header: "Function", cell: (r) => <code className="font-mono text-xs">{r.name}</code>, sortValue: (r) => r.name },
    { key: "f", header: "File", cell: (r) => <span className="font-mono text-xs">{r.file}:{r.line}</span> },
    { key: "c", header: "Cyclomatic", align: "right", cell: (r) => r.cyclomatic, sortValue: (r) => r.cyclomatic },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Codebase assistant"
        title="Codebase intelligence assistant"
        description="Index a repository, then ask natural-language questions. Retrieval combines text similarity, concept detection (auth, routing, UI, database …) and the import / call graph."
      />

      <Card className="space-y-4 p-4 sm:p-6">
        <div className="grid gap-4 md:grid-cols-[18rem_1fr] md:items-start">
          <FormField label="Repository">
            {(p) => <Select {...p} value={source} onValueChange={(v) => setSource(v as Source)} options={SOURCES} />}
          </FormField>
          <div>
            {source === "upload" ? (
              <div className="space-y-2">
                <FileDrop
                  file={null}
                  onFile={() => undefined}
                  multiple
                  onFiles={(picked) => setZips((cur) => [...cur, ...picked])}
                  accept=".zip"
                  validate={(f) => (f.name.toLowerCase().endsWith(".zip") ? null : `${f.name} is not a .zip file.`)}
                  title="Drop a .zip of the repository"
                  hint="Source files are indexed in memory; nothing is stored."
                />
                {zips.length > 0 && (
                  <p className="text-sm text-muted-foreground">
                    {zips.map((z) => `${z.name} (${formatBytes(z.size)})`).join(", ")} ·{" "}
                    <button type="button" className="text-violet-ink underline" onClick={() => setZips([])}>clear</button>
                  </p>
                )}
              </div>
            ) : source === "folder" ? (
              <FormField label="Folder path" hint="Read by the machine running the API.">
                {(p) => <Input {...p} icon={<FolderGit2 />} value={folder} onChange={(e) => setFolder(e.target.value)} placeholder="C:\projects\my-app" />}
              </FormField>
            ) : source === "github" ? (
              <FormField label="Repository URL" hint={settings.ghToken ? "Using the GitHub token from Settings." : "Public repositories work without a token."}>
                {(p) => <Input {...p} type="url" icon={<GitBranch />} value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://github.com/owner/repo" />}
              </FormField>
            ) : (
              <p className="pt-8 text-sm text-muted-foreground">{source === "demo" ? "A small Flask shop app, built into AutoSecAI." : "AutoSecAI's own Python source."} Ready to index.</p>
            )}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={() => indexer.mutate()} loading={indexer.isPending} disabled={!canIndex}>
            <Library /> Index repository
          </Button>
          {indexer.isPending && <span className="text-sm text-muted-foreground" role="status">Parsing files, building call graph and search index…</span>}
        </div>
        {indexer.isError && <ErrorState error={indexer.error} title="Indexing failed" hint="Check the source and try again." onRetry={() => indexer.mutate()} />}
      </Card>

      {!index ? (
        <EmptyState icon={<Compass />} title="Index a repository to start asking questions" description="Pick a source above. The demo shop app indexes in about a second." />
      ) : (
        <Tabs
          value={tab}
          onValueChange={setTab}
          tabs={[
            { value: "ask", label: "Ask", icon: <MessageSquare /> },
            { value: "map", label: "Repository map", icon: <MapIcon /> },
            { value: "guide", label: "Onboarding guide", icon: <BookOpen /> },
          ]}
        >
          <TabPanel value="ask" className="space-y-4">
            <div>
              <div className="mb-2 flex items-center gap-1.5 text-sm font-medium"><Sparkles className="size-4 text-violet-ink" /> Try asking</div>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {(meta.data?.suggested ?? []).map((q) => (
                  <Button key={q} variant="secondary" size="sm" className="h-auto justify-start whitespace-normal py-2 text-left" onClick={() => ask(q)} disabled={asker.isPending}>
                    {q}
                  </Button>
                ))}
              </div>
            </div>

            <Card className="p-4 sm:p-5">
              <div className="space-y-4" aria-live="polite" aria-label="Conversation">
                {chat.length === 0 && !asker.isPending && (
                  <p className="py-8 text-center text-sm text-muted-foreground">
                    Indexed <strong>{index.name}</strong>. Ask a question below, or pick one of the suggestions.
                  </p>
                )}
                {chat.map((m, i) =>
                  m.role === "user" ? (
                    <div key={i} className="ml-auto w-fit max-w-[88%] rounded-2xl rounded-br-md bg-grad-primary px-4 py-2 text-sm text-white">{m.content}</div>
                  ) : (
                    <div key={i} className="flex gap-2">
                      <LogoMark className="size-7" />
                      <div className="min-w-0 flex-1 space-y-2 rounded-2xl rounded-tl-md border border-[var(--glass-border)] bg-[var(--glass)] p-3">
                        <Suspense fallback={<Skeleton className="h-12" />}><Markdown>{m.content}</Markdown></Suspense>
                        {m.hits && m.hits.length > 0 && (
                          <div className="space-y-1.5">{m.hits.slice(0, 5).map((h, j) => <HitCard key={j} h={h} />)}</div>
                        )}
                      </div>
                    </div>
                  ),
                )}
                {asker.isPending && (
                  <div className="flex gap-2" role="status" aria-label="Searching the codebase">
                    <LogoMark className="size-7" />
                    <div className="flex-1 space-y-2 rounded-2xl rounded-tl-md border border-[var(--glass-border)] bg-[var(--glass)] p-3">
                      <Skeleton className="h-4 w-2/3" />
                      <Skeleton className="h-4 w-1/2" />
                    </div>
                  </div>
                )}
                {asker.isError && <ErrorState error={asker.error} title="Couldn't answer that" hint="If the index was lost (API restarted), index the repository again." className="py-6" />}
                <div ref={endRef} />
              </div>
              <form onSubmit={(e: FormEvent) => { e.preventDefault(); ask(question); }} className="mt-4 flex gap-2 border-t border-[var(--glass-border)] pt-4">
                <Input aria-label="Ask about the codebase" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask about the codebase…" wrapperClassName="flex-1" />
                <Button type="submit" disabled={!question.trim() || asker.isPending} aria-label="Send question"><Send /> <span className="hidden sm:inline">Ask</span></Button>
              </form>
            </Card>
          </TabPanel>

          <TabPanel value="map" className="space-y-5">
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
              <StatCard label="Files" value={o!.files} icon={<FileCode2 />} />
              <StatCard label="Lines" value={o!.loc} icon={<Code2 />} accent="cyan" />
              <StatCard label="Functions" value={o!.functions} icon={<Waypoints />} accent="magenta" />
              <StatCard label="Classes" value={o!.classes} icon={<Boxes />} />
              <StatCard label="Import links" value={o!.import_edges} icon={<Network />} accent="cyan" />
            </div>
            <div className="grid gap-5 xl:grid-cols-2">
              <div className="min-w-0 space-y-5">
                <section className="space-y-2">
                  <h3 className="font-display text-lg font-semibold">API routes</h3>
                  {o!.routes.length ? (
                    <Table columns={routeCols} rows={o!.routes} rowKey={(r) => `${r.method}${r.path}${r.file}${r.line}`} pageSize={8} caption="API routes" />
                  ) : (
                    <p className="text-sm text-muted-foreground">No routes were detected in this repository.</p>
                  )}
                </section>
                <Card>
                  <CardHeader title="Where things live" icon={<Package />} />
                  <CardBody>
                    {o!.by_concept.length ? (
                      <ul className="space-y-2 text-sm">
                        {o!.by_concept.map((c) => (
                          <li key={c.key}>
                            <strong>{c.label}:</strong>{" "}
                            {c.files.slice(0, 4).map((f, i) => <span key={f}>{i > 0 && ", "}<code className="font-mono text-xs">{f}</code></span>)}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-muted-foreground">No concept signals were strong enough to list.</p>
                    )}
                  </CardBody>
                </Card>
                {o!.hotspots.length > 0 && (
                  <section className="space-y-2">
                    <h3 className="font-display text-lg font-semibold">Complexity hotspots</h3>
                    <Table columns={hotCols} rows={o!.hotspots} rowKey={(r) => `${r.file}${r.name}${r.line}`} pageSize={6} caption="Complexity hotspots" initialSort={{ key: "c", dir: "desc" }} />
                  </section>
                )}
              </div>
              <ChartCard
                title="Module dependency graph"
                description="Files that import each other. Bigger, violet nodes have more links."
                icon={<Network />}
                empty={index.graph.nodes.length < 2 ? "No module-level import links to draw." : undefined}
                table={{ columns: ["Imports from", "To"], rows: index.graph.edges.map(([a, b]) => [a, b]) }}
                className={cn("min-w-0")}
              >
                <DependencyGraph graph={index.graph} />
              </ChartCard>
            </div>
          </TabPanel>

          <TabPanel value="guide">
            <Card className="p-5">
              <Suspense fallback={<Skeleton className="h-48" />}><Markdown>{index.guide}</Markdown></Suspense>
            </Card>
          </TabPanel>
        </Tabs>
      )}
    </div>
  );
}
