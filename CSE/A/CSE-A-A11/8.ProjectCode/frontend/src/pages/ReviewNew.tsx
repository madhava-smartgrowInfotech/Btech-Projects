import { useQueryClient } from "@tanstack/react-query";
import { FileCode2, FolderGit2, GitBranch, GitCompare, Link2, Rocket, Settings2, X } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router";

import { AgentProgress } from "@/components/app/Bits";
import { CodeBlock } from "@/components/app/CodeBlock";
import { Badge } from "@/components/ui/Badge";
import { Button, IconButton } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { FormField, Input, Textarea } from "@/components/ui/Field";
import { ErrorState } from "@/components/ui/Feedback";
import { FileDrop } from "@/components/ui/FileDrop";
import { PageHeader } from "@/components/ui/Layout";
import { Tabs, TabPanel } from "@/components/ui/Navigation";
import { Skeleton } from "@/components/ui/Feedback";
import { Segmented } from "@/components/ui/Toggles";
import { toast } from "@/components/ui/Toast";
import { api } from "@/lib/api";
import { startReview, useMeta, useSamples } from "@/lib/hooks";
import { useJob } from "@/lib/jobs";
import { keys } from "@/lib/queries";
import { useSettings } from "@/lib/settings";
import { formatBytes } from "@/lib/utils";

type Mode = "demo" | "diff" | "versions" | "github" | "upload";

const MODES = [
  { value: "demo", label: "Demo PR", icon: <Rocket /> },
  { value: "diff", label: "Paste diff", icon: <FileCode2 /> },
  { value: "versions", label: "Compare versions", icon: <GitCompare /> },
  { value: "github", label: "GitHub PR link", icon: <Link2 /> },
  { value: "upload", label: "Upload files / repo", icon: <FolderGit2 /> },
];

export default function ReviewNew() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const meta = useMeta();
  const { settings, options } = useSettings();
  const job = useJob<{ review_id: string }>();

  const [mode, setMode] = useState<Mode>("demo");
  const [sample, setSample] = useState<"diff" | "versions">("diff");
  const samples = useSamples(mode === "demo");

  const [title, setTitle] = useState("");
  const [diff, setDiff] = useState("");
  const [diffFile, setDiffFile] = useState<File | null>(null);
  const [filename, setFilename] = useState("app.py");
  const [before, setBefore] = useState("");
  const [after, setAfter] = useState("");
  const [url, setUrl] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [folder, setFolder] = useState("");

  const ready =
    mode === "demo" ? Boolean(samples.data) :
    mode === "diff" ? diff.trim().length > 0 :
    mode === "versions" ? after.trim().length > 0 :
    mode === "github" ? url.trim().length > 0 :
    files.length > 0 || folder.trim().length > 0;

  async function run() {
    const opts = options(meta.data?.llm_env ?? false);
    const done = await job.run(async () => {
      if (mode === "upload" && files.length > 0) {
        const fd = new FormData();
        files.forEach((f) => fd.append("files", f));
        fd.append("title", title.trim() || "Repository scan");
        fd.append("options", JSON.stringify(opts));
        return (await api.post<{ job_id: string }>("/reviews/upload", fd, { headers: { "Content-Type": "multipart/form-data" } })).data.job_id;
      }
      const t = title.trim() || undefined;
      switch (mode) {
        case "demo":
          return startReview({ kind: sample === "diff" ? "demo-diff" : "demo-versions", options: opts });
        case "diff":
          return startReview({ kind: "diff", title: t, diff, options: opts });
        case "versions":
          return startReview({ kind: "versions", title: t, filename, old: before, new: after, options: opts });
        case "github":
          return startReview({ kind: "github", url: url.trim(), options: opts });
        default:
          return startReview({ kind: "folder", title: t, folder: folder.trim(), options: opts });
      }
    });
    if (!done?.result) return;
    await qc.invalidateQueries({ queryKey: keys.reviews });
    toast.success(`Review complete in ${done.seconds?.toFixed(1)} s`);
    navigate(`/app/review/${done.result.review_id}`);
  }

  async function readDiff(f: File | null) {
    setDiffFile(f);
    if (f) setDiff(await f.text());
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="PR review"
        title="Pull request review"
        description="Choose how to provide the change. Only lines added or modified by the PR block the merge; older issues are shown separately."
      />

      <Card className="space-y-5 p-4 sm:p-6">
        <Tabs value={mode} onValueChange={(v) => setMode(v as Mode)} tabs={MODES} listClassName="max-w-full">
          <TabPanel value="demo" className="space-y-4">
            <Segmented
              label="Demo sample"
              value={sample}
              onChange={setSample}
              options={[
                { value: "diff", label: "Vulnerable Flask API (diff)" },
                { value: "versions", label: "Before / after of one file" },
              ]}
            />
            {samples.isPending ? (
              <Skeleton className="h-56" />
            ) : samples.isError ? (
              <ErrorState error={samples.error} title="Couldn't load the demo sample" onRetry={() => samples.refetch()} />
            ) : sample === "diff" ? (
              <CodeBlock code={samples.data.demo_diff} language="diff" maxHeight="18rem" label="Preview diff · app/users.py" />
            ) : (
              <div className="grid gap-3 md:grid-cols-2">
                <CodeBlock code={samples.data.before} language="python" maxHeight="18rem" label={`Before · ${samples.data.filename}`} />
                <CodeBlock code={samples.data.after} language="python" maxHeight="18rem" label={`After · ${samples.data.filename}`} />
              </div>
            )}
          </TabPanel>

          <TabPanel value="diff" className="space-y-4">
            <FormField label="Title">{(p) => <Input {...p} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Pasted pull request" />}</FormField>
            <FileDrop
              file={diffFile}
              onFile={readDiff}
              accept=".diff,.patch,.txt"
              title="Drop a .diff / .patch file, or click to browse"
              hint="Its text fills the box below. Or paste a unified diff directly."
            />
            <FormField label="Unified diff (git diff / PR .diff)" hint="Starts with diff --git, or with --- / +++ lines.">
              {(p) => (
                <Textarea
                  {...p}
                  value={diff}
                  onChange={(e) => setDiff(e.target.value)}
                  className="min-h-64 font-mono text-xs"
                  spellCheck={false}
                  placeholder={"diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1,3 +1,5 @@ ..."}
                />
              )}
            </FormField>
          </TabPanel>

          <TabPanel value="versions" className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField label="Title">{(p) => <Input {...p} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Local change" />}</FormField>
              <FormField label="File name" hint="The extension picks the language rules.">
                {(p) => <Input {...p} value={filename} onChange={(e) => setFilename(e.target.value)} />}
              </FormField>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <FormField label="Before (optional)" hint="Leave empty for a new file.">
                {(p) => <Textarea {...p} value={before} onChange={(e) => setBefore(e.target.value)} className="min-h-72 font-mono text-xs" spellCheck={false} />}
              </FormField>
              <FormField label="After">
                {(p) => <Textarea {...p} value={after} onChange={(e) => setAfter(e.target.value)} className="min-h-72 font-mono text-xs" spellCheck={false} />}
              </FormField>
            </div>
          </TabPanel>

          <TabPanel value="github" className="space-y-4">
            <FormField
              label="Pull request URL"
              hint="Public PRs work without a token (60 requests/hour). Add a token in Settings for private repositories."
            >
              {(p) => <Input {...p} type="url" icon={<GitBranch />} value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://github.com/owner/repo/pull/123" />}
            </FormField>
            {!settings.ghToken && (
              <p className="text-xs text-muted-foreground">
                No GitHub token saved. <Link to="/app/settings" className="text-violet-ink underline">Add one in Settings</Link> if you hit rate limits.
              </p>
            )}
          </TabPanel>

          <TabPanel value="upload" className="space-y-4">
            <FormField label="Title">{(p) => <Input {...p} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Repository scan" />}</FormField>
            <FileDrop
              file={null}
              onFile={() => undefined}
              multiple
              onFiles={(picked) => setFiles((cur) => [...cur, ...picked.filter((p) => !cur.some((c) => c.name === p.name && c.size === p.size))])}
              accept=""
              title="Drop source files or a .zip of a repository"
              hint="Every line is treated as changed (full scan)."
            />
            {files.length > 0 && (
              <ul className="space-y-1.5" aria-label="Selected files">
                {files.map((f) => (
                  <li key={f.name + f.size} className="glass flex items-center gap-2 rounded-xl px-3 py-2 text-sm">
                    <span className="min-w-0 flex-1 truncate">{f.name}</span>
                    <span className="text-xs text-muted-foreground">{formatBytes(f.size)}</span>
                    <IconButton label={`Remove ${f.name}`} size="icon-sm" onClick={() => setFiles((cur) => cur.filter((x) => x !== f))}>
                      <X />
                    </IconButton>
                  </li>
                ))}
              </ul>
            )}
            <FormField label="…or a local folder path" hint="Read by the machine running the API. Used only when no files are selected.">
              {(p) => <Input {...p} icon={<FolderGit2 />} value={folder} onChange={(e) => setFolder(e.target.value)} placeholder="C:\projects\my-app" disabled={files.length > 0} />}
            </FormField>
          </TabPanel>
        </Tabs>

        <div className="flex flex-col gap-3 border-t border-[var(--glass-border)] pt-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
            <Settings2 className="size-4" />
            <Badge tone={settings.ml ? "success" : "neutral"}>ML risk agent {settings.ml ? "on" : "off"}</Badge>
            <Badge tone="neutral">min severity: {settings.minSeverity}</Badge>
            <Badge tone={settings.useLlm && (settings.apiKey || meta.data?.llm_env) ? "violet" : "neutral"}>
              LLM explanations {settings.useLlm && (settings.apiKey || meta.data?.llm_env) ? "on" : "off"}
            </Badge>
            <Link to="/app/settings" className="text-violet-ink underline">Change</Link>
          </div>
          <Button size="lg" onClick={run} loading={job.running} disabled={!ready} className="w-full sm:w-auto">
            <Rocket /> Run multi-agent review
          </Button>
        </div>
      </Card>

      {job.running && <AgentProgress messages={job.messages} title="Agents are reviewing the pull request…" />}
      {job.error && !job.running && (
        <ErrorState error={new Error(job.error)} title="Could not complete the review" hint="Check the input and try again." onRetry={run} />
      )}
    </div>
  );
}
