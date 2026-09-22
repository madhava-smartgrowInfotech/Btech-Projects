import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Loader2, UserPlus } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AuthShell } from "@/pages/auth/AuthShell";
import { apiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { LANGUAGES, useI18n, type Language } from "@/lib/i18n";
import type { MessageKey } from "@/locales/en";

export default function Register() {
  const { t, tx, lang, setLang } = useI18n();
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", phone: "", email: "", password: "", pin: "" });
  const [language, setLanguage] = useState<Language>(lang);
  const [errors, setErrors] = useState<Partial<Record<keyof typeof form, MessageKey>>>({});
  const [busy, setBusy] = useState(false);

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const validate = () => {
    const next: typeof errors = {};
    if (form.full_name.trim().length < 2) next.full_name = "error.name_short";
    if (!/^[6-9]\d{9}$/.test(form.phone)) next.phone = "error.phone_invalid";
    if (form.password.length < 8) next.password = "error.password_short";
    if (!/^\d{4}$/.test(form.pin)) next.pin = "error.pin_invalid";
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setBusy(true);
    try {
      await register({ ...form, email: form.email.trim() || undefined, language });
      navigate("/app", { replace: true });
    } catch (err) {
      const d = apiError(err);
      toast.error(tx(`error.${d.code}`, d.message));
    } finally {
      setBusy(false);
    }
  };

  const field = (k: keyof typeof form, label: string, props: React.InputHTMLAttributes<HTMLInputElement> = {}, hint?: string) => (
    <div className="space-y-2">
      <Label htmlFor={k}>{label}</Label>
      <Input id={k} value={form[k]} onChange={set(k)} aria-invalid={!!errors[k]} aria-describedby={`${k}-help`} {...props} />
      {errors[k] ? (
        <p id={`${k}-help`} className="text-xs text-danger">
          {t(errors[k]!)}
        </p>
      ) : hint ? (
        <p id={`${k}-help`} className="text-xs text-muted-foreground">
          {hint}
        </p>
      ) : null}
    </div>
  );

  return (
    <AuthShell>
      <h1 className="font-display text-3xl font-semibold">{t("auth.register.title")}</h1>
      <p className="mt-1 text-muted-foreground">{t("auth.register.subtitle")}</p>
      <form onSubmit={submit} className="mt-8 space-y-4" noValidate>
        {field("full_name", t("auth.full_name"), { autoComplete: "name" })}
        <div className="grid gap-4 sm:grid-cols-2">
          {field("phone", t("auth.phone"), { inputMode: "numeric", autoComplete: "tel-national", maxLength: 10 })}
          {field("email", `${t("auth.email")} (${t("common.optional")})`, { type: "email", autoComplete: "email" })}
        </div>
        {field("password", t("auth.password"), { type: "password", autoComplete: "new-password" }, t("auth.password_hint"))}
        <div className="grid gap-4 sm:grid-cols-2">
          {field("pin", t("auth.pin"), { type: "password", inputMode: "numeric", maxLength: 4, autoComplete: "off" }, t("auth.pin_hint"))}
          <div className="space-y-2">
            <Label>{t("auth.language")}</Label>
            <Select
              value={language}
              onValueChange={(v) => {
                setLanguage(v as Language);
                setLang(v as Language);
              }}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {LANGUAGES.map((l) => (
                  <SelectItem key={l.code} value={l.code}>
                    {l.native}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <Button type="submit" size="lg" className="w-full" disabled={busy}>
          {busy ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <UserPlus className="mr-2 h-4 w-4" />}
          {t("auth.register.submit")}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted-foreground">
        {t("auth.have_account")}{" "}
        <Link to="/login" className="font-medium text-primary hover:underline">
          {t("auth.login.link")}
        </Link>
      </p>
    </AuthShell>
  );
}
