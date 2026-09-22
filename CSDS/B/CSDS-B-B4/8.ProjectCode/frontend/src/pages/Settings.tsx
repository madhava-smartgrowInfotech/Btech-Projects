import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Clock3, FlaskConical, KeyRound, Languages, LogOut, Moon, Volume2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { CardSkeleton, ErrorState, PageHeader } from "@/components/common/States";
import { GuideButton } from "@/components/voice/SpeakButton";
import { api, apiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { LANGUAGES, useI18n, type Language } from "@/lib/i18n";
import { useTheme, type Theme } from "@/lib/theme";
import type { Settings as S } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useSettings } from "@/lib/voice";

function Row({ icon: Icon, title, hint, children }: { icon: typeof Clock3; title: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-3">
        <Icon className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
        <div>
          <p className="font-medium">{title}</p>
          {hint && <p className="text-sm text-muted-foreground">{hint}</p>}
        </div>
      </div>
      <div className="sm:shrink-0">{children}</div>
    </div>
  );
}

export default function Settings() {
  const { t, tx, lang, setLang } = useI18n();
  const { theme, setTheme } = useTheme();
  const { logout } = useAuth();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const s = useSettings();
  const [clock, setClock] = useState<string>("");
  const [pins, setPins] = useState({ current: "", next: "" });

  const save = useMutation({
    mutationFn: async (patch: Partial<S> & { sandbox_clock?: string | null }) => (await api.put<S>("/settings", patch)).data,
    onSuccess: (d) => {
      qc.setQueryData(["settings"], d);
      qc.invalidateQueries({ queryKey: ["me"] });
      toast.success(t("common.saved"));
    },
    onError: (err) => toast.error(tx(`error.${apiError(err).code}`, apiError(err).message)),
  });
  const changePin = useMutation({
    mutationFn: async () => api.post("/auth/pin", { current_pin: pins.current, new_pin: pins.next }),
    onSuccess: () => {
      toast.success(t("settings.pin_changed"));
      setPins({ current: "", next: "" });
    },
    onError: (err) => toast.error(tx(`error.${apiError(err).code}`, apiError(err).message)),
  });

  if (s.isLoading) return <CardSkeleton rows={6} />;
  if (s.isError || !s.data) return <ErrorState error={s.error} onRetry={() => s.refetch()} />;
  const d = s.data;

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <PageHeader title={t("nav.settings")} subtitle={t("settings.subtitle")} actions={<GuideButton screen="settings" />} />

      <section className="surface divide-y px-5">
        <Row icon={Languages} title={t("nav.language")} hint={t("settings.language_hint")}>
          <div className="flex rounded-full border p-0.5" role="group" aria-label={t("nav.language")}>
            {LANGUAGES.map((l) => (
              <button
                key={l.code}
                onClick={() => {
                  setLang(l.code as Language);
                  save.mutate({ language: l.code as Language });
                }}
                className={cn("rounded-full px-3 py-1.5 text-sm", lang === l.code ? "bg-primary text-primary-foreground" : "text-muted-foreground")}
                aria-pressed={lang === l.code}
              >
                {l.native}
              </button>
            ))}
          </div>
        </Row>
        <Row icon={Volume2} title={t("settings.voice")} hint={t("settings.voice_hint")}>
          <Switch checked={d.voice_enabled} onCheckedChange={(v) => save.mutate({ voice_enabled: v })} aria-label={t("settings.voice")} />
        </Row>
        <Row icon={Volume2} title={t("settings.auto_speak")} hint={t("settings.auto_speak_hint")}>
          <Switch checked={d.auto_speak} disabled={!d.voice_enabled} onCheckedChange={(v) => save.mutate({ auto_speak: v })} aria-label={t("settings.auto_speak")} />
        </Row>
        <Row icon={Clock3} title={t("settings.hold")} hint={t("settings.hold_hint")}>
          <Select value={String(d.hold_minutes)} onValueChange={(v) => save.mutate({ hold_minutes: Number(v) })}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {d.hold_choices.map((m) => (
                <SelectItem key={m} value={String(m)}>
                  {t("common.minutes", { n: m })}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </Row>
        <Row icon={Clock3} title={t("trusted.require_approval")} hint={d.has_trusted_approver ? t("trusted.require_approval_hint") : t("trusted.need_contact_first")}>
          <div className="flex items-center gap-2">
            {!d.has_trusted_approver && (
              <Button asChild variant="outline" size="sm">
                <Link to="/app/trusted">{t("trusted.add")}</Link>
              </Button>
            )}
            <Switch checked={d.trusted_approval_required} disabled={!d.has_trusted_approver} onCheckedChange={(v) => save.mutate({ trusted_approval_required: v })} aria-label={t("trusted.require_approval")} />
          </div>
        </Row>
        <Row icon={Moon} title={t("nav.theme")}>
          <Select value={theme} onValueChange={(v) => setTheme(v as Theme)}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="light">{t("theme.light")}</SelectItem>
              <SelectItem value="dark">{t("theme.dark")}</SelectItem>
              <SelectItem value="system">{t("theme.system")}</SelectItem>
            </SelectContent>
          </Select>
        </Row>
      </section>

      <section className="surface p-5">
        <h2 className="flex items-center gap-2 font-display text-base font-semibold">
          <FlaskConical className="h-4 w-4 text-caution" />
          {t("settings.clock")}
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">{t("settings.clock_hint")}</p>
        <p className="mt-3 text-sm">{d.sandbox_clock ? t("settings.clock_on", { time: d.sandbox_clock }) : t("settings.clock_off")}</p>
        <div className="mt-3 flex flex-wrap items-end gap-2">
          <div className="space-y-1">
            <Label htmlFor="clock">{t("settings.clock_time")}</Label>
            <Input id="clock" type="time" value={clock || d.sandbox_clock || ""} onChange={(e) => setClock(e.target.value)} className="w-36" />
          </div>
          <Button onClick={() => save.mutate({ sandbox_clock: clock || "01:30" })}>{t("settings.clock_set")}</Button>
          <Button variant="outline" onClick={() => { setClock(""); save.mutate({ sandbox_clock: "" }); }} disabled={!d.sandbox_clock}>
            {t("settings.clock_real")}
          </Button>
        </div>
      </section>

      <section className="surface p-5">
        <h2 className="flex items-center gap-2 font-display text-base font-semibold">
          <KeyRound className="h-4 w-4 text-primary" />
          {t("settings.pin")}
        </h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
          <div className="space-y-1">
            <Label htmlFor="pin-cur">{t("settings.pin_current")}</Label>
            <Input id="pin-cur" type="password" inputMode="numeric" maxLength={4} value={pins.current} onChange={(e) => setPins((p) => ({ ...p, current: e.target.value.replace(/\D/g, "") }))} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="pin-new">{t("settings.pin_new")}</Label>
            <Input id="pin-new" type="password" inputMode="numeric" maxLength={4} value={pins.next} onChange={(e) => setPins((p) => ({ ...p, next: e.target.value.replace(/\D/g, "") }))} />
          </div>
          <Button onClick={() => changePin.mutate()} disabled={pins.current.length !== 4 || pins.next.length !== 4 || changePin.isPending}>
            {t("common.save")}
          </Button>
        </div>
      </section>

      <Button
        variant="outline"
        className="w-full text-danger"
        onClick={() => {
          logout();
          navigate("/login");
        }}
      >
        <LogOut className="mr-2 h-4 w-4" />
        {t("nav.logout")}
      </Button>
    </div>
  );
}
