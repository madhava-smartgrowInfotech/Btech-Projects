import { Check, Languages, Loader2, Monitor, Moon, Palette, Sun, UserRound } from "lucide-react";
import { useState, type FormEvent } from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/common/PageHeader";
import { PasswordInput } from "@/components/common/PasswordInput";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { LANGUAGES } from "@/lib/i18n";
import { useTheme, type Theme } from "@/lib/theme";
import type { Language } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function Settings() {
  const { user, updateUser } = useAuth();
  const { theme, setTheme } = useTheme();
  const [name, setName] = useState(user?.full_name ?? "");
  const [savingName, setSavingName] = useState(false);
  const [savingLang, setSavingLang] = useState<Language | null>(null);
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [savingPw, setSavingPw] = useState(false);

  async function saveLanguage(code: Language) {
    setSavingLang(code);
    try {
      await updateUser({ language: code });
      toast.success(`Answers will be in ${LANGUAGES.find((l) => l.code === code)?.name}`);
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSavingLang(null);
    }
  }

  async function saveName(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setSavingName(true);
    try {
      await updateUser({ full_name: name.trim() });
      toast.success("Name updated");
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSavingName(false);
    }
  }

  async function savePassword(e: FormEvent) {
    e.preventDefault();
    setSavingPw(true);
    try {
      await api.post("/users/me/password", { current_password: current, new_password: next });
      toast.success("Password changed");
      setCurrent("");
      setNext("");
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setSavingPw(false);
    }
  }

  const themes: { value: Theme; label: string; icon: typeof Sun }[] = [
    { value: "light", label: "Light", icon: Sun },
    { value: "dark", label: "Dark", icon: Moon },
    { value: "system", label: "System", icon: Monitor },
  ];

  return (
    <div className="max-w-3xl">
      <PageHeader title="Settings" description="Answer language, appearance and your account." />
      <div className="space-y-5">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Languages className="size-5 text-primary" /> Answer language
            </CardTitle>
            <CardDescription>
              Chat answers, Claim Copilot results, comparisons and Policy Cards are shown in this language. Clause quotes stay in the policy's
              original English. You can also switch per question in the chat.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-3">
            {LANGUAGES.map((l) => {
              const active = user?.language === l.code;
              return (
                <button
                  key={l.code}
                  type="button"
                  onClick={() => !active && saveLanguage(l.code)}
                  className={cn(
                    "flex items-center justify-between rounded-xl border p-4 text-left transition-colors hover:bg-accent",
                    active && "border-primary bg-primary/5 ring-1 ring-primary",
                  )}
                  aria-pressed={active}
                >
                  <span>
                    <span className="block text-lg font-semibold">{l.native}</span>
                    <span className="text-xs text-muted-foreground">{l.name}</span>
                  </span>
                  {savingLang === l.code ? <Loader2 className="size-4 animate-spin" /> : active && <Check className="size-5 text-primary" />}
                </button>
              );
            })}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Palette className="size-5 text-primary" /> Appearance
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-3 gap-3">
            {themes.map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                type="button"
                onClick={() => {
                  setTheme(value);
                  updateUser({ theme: value }).catch(() => undefined);
                }}
                className={cn(
                  "flex flex-col items-center gap-2 rounded-xl border p-4 text-sm transition-colors hover:bg-accent",
                  theme === value && "border-primary bg-primary/5 ring-1 ring-primary",
                )}
                aria-pressed={theme === value}
              >
                <Icon className="size-5" /> {label}
              </button>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserRound className="size-5 text-primary" /> Account
            </CardTitle>
            <CardDescription>{user?.email}</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6 md:grid-cols-2">
            <form onSubmit={saveName} className="space-y-3">
              <div className="space-y-1.5">
                <Label htmlFor="full-name">Full name</Label>
                <Input id="full-name" value={name} onChange={(e) => setName(e.target.value)} maxLength={120} />
              </div>
              <Button type="submit" variant="outline" disabled={savingName || !name.trim() || name.trim() === user?.full_name}>
                {savingName && <Loader2 className="animate-spin" />} Save name
              </Button>
            </form>
            <form onSubmit={savePassword} className="space-y-3">
              <div className="space-y-1.5">
                <Label htmlFor="current-pw">Current password</Label>
                <PasswordInput id="current-pw" autoComplete="current-password" value={current} onChange={(e) => setCurrent(e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="new-pw">New password</Label>
                <PasswordInput id="new-pw" autoComplete="new-password" value={next} onChange={(e) => setNext(e.target.value)} />
                <p className="text-xs text-muted-foreground">At least 8 characters, with a letter and a number.</p>
              </div>
              <Button type="submit" variant="outline" disabled={savingPw || !current || next.length < 8}>
                {savingPw && <Loader2 className="animate-spin" />} Change password
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
