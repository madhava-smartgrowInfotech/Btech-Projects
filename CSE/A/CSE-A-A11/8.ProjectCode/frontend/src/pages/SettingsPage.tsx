import { GitBranch, KeyRound, LogOut, Palette, RotateCcw, ShieldCheck, SlidersHorizontal, Sparkles } from "lucide-react";
import { useNavigate } from "react-router";

import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { FormField, Label, PasswordInput } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { Select } from "@/components/ui/Select";
import { Segmented, Switch } from "@/components/ui/Toggles";
import { toast } from "@/components/ui/Toast";
import { useAuth } from "@/lib/auth";
import { SEV_ORDER } from "@/lib/domain";
import { useMeta } from "@/lib/hooks";
import { useSettings } from "@/lib/settings";
import { useTheme } from "@/lib/theme";
import type { Severity } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";

function Row({ id, title, text, children }: { id: string; title: string; text: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-[var(--glass-border)] py-4 last:border-0">
      <div className="min-w-0">
        <Label htmlFor={id}>{title}</Label>
        <p className="mt-0.5 text-sm text-muted-foreground">{text}</p>
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}

export default function SettingsPage() {
  const { settings, update, reset } = useSettings();
  const { theme, setTheme } = useTheme();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const meta = useMeta();
  const llmReady = Boolean(settings.apiKey) || Boolean(meta.data?.llm_env);

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Settings" title="Settings" description="Applied to every review and codebase question you run. Saved in this browser only." />

      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader title="Analysis" icon={<SlidersHorizontal />} />
          <CardBody className="pt-2">
            <Row id="ml" title="ML risk agent (base paper)" text="Scores each changed function with the metric-based model.">
              <Switch id="ml" checked={settings.ml} onCheckedChange={(v) => update({ ml: v })} />
            </Row>
            <Row id="sev" title="Minimum severity shown" text="Hide findings below this level.">
              <div className="w-36">
                <Select
                  id="sev"
                  value={settings.minSeverity}
                  onValueChange={(v) => update({ minSeverity: v as Severity })}
                  options={[...SEV_ORDER].reverse().map((s) => ({ value: s, label: s[0].toUpperCase() + s.slice(1) }))}
                />
              </div>
            </Row>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Optional integrations" icon={<Sparkles />} description="Everything works offline without these." />
          <CardBody className="space-y-4 pt-2">
            <FormField label="Anthropic API key (optional)" hint="Enables LLM-written explanations for the top findings and answers. Stored in this browser; sent to the API only with a review or question.">
              {(p) => <PasswordInput {...p} icon={<KeyRound />} value={settings.apiKey} onChange={(e) => update({ apiKey: e.target.value.trim() })} placeholder="sk-ant-…" autoComplete="off" />}
            </FormField>
            <Row id="llm" title="LLM explanations" text={llmReady ? "Findings and answers are rewritten by the LLM agent." : "Add an API key to turn this on."}>
              <Switch id="llm" checked={settings.useLlm && llmReady} disabled={!llmReady} onCheckedChange={(v) => update({ useLlm: v })} />
            </Row>
            <FormField label="GitHub token (optional)" hint="For private repositories and higher rate limits on PR links and repo indexing.">
              {(p) => <PasswordInput {...p} icon={<GitBranch />} value={settings.ghToken} onChange={(e) => update({ ghToken: e.target.value.trim() })} placeholder="ghp_…" autoComplete="off" />}
            </FormField>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Appearance" icon={<Palette />} />
          <CardBody className="pt-2">
            <Row id="theme" title="Theme" text="Aurora Glass is dark by default. “System” follows your OS.">
              <Segmented
                label="Theme"
                value={theme}
                onChange={(v) => setTheme(v)}
                options={[{ value: "light", label: "Light" }, { value: "dark", label: "Dark" }, { value: "system", label: "System" }]}
              />
            </Row>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Account" icon={<ShieldCheck />} />
          <CardBody className="space-y-4 pt-2">
            {user && (
              <div className="flex items-center gap-3">
                <Avatar name={user.name} className="size-11 text-sm" />
                <div className="min-w-0">
                  <div className="truncate font-medium">{user.name} {user.is_demo && <Badge tone="violet" className="ml-1">demo</Badge>}</div>
                  <div className="truncate text-sm text-muted-foreground">{user.email}</div>
                </div>
              </div>
            )}
            <p className="text-sm text-muted-foreground">Runs 100 % locally in Python. No code leaves your machine unless you enable the LLM option.</p>
            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" onClick={() => { logout(); navigate("/login"); }}><LogOut /> Sign out</Button>
              <Button variant="outline" onClick={() => { reset(); toast.success("Settings reset to defaults."); }}><RotateCcw /> Reset settings</Button>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
