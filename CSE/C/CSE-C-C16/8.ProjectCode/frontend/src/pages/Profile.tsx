import { useMutation } from "@tanstack/react-query";
import { Download, LogOut, MapPin, Save, UserRound } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router";

import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { KeyValueList } from "@/components/ui/Display";
import { FormField, Input } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { Select } from "@/components/ui/Select";
import { Checkbox } from "@/components/ui/Toggles";
import { toast } from "@/components/ui/Toast";
import { api, downloadFile, errorMessage, PROFILE_CROPS, type User } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { LANGS, useLang, type Lang } from "@/lib/i18n";
import { formatDate } from "@/lib/utils";

export default function Profile() {
  const { user, setUser, logout } = useAuth();
  const { t, setLang } = useLang();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", region: "", language: "en" as Lang, crops: [] as string[] });
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (user) setForm({ full_name: user.full_name, region: user.region, language: user.language, crops: user.crops });
  }, [user]);

  const save = useMutation({
    mutationFn: async () => (await api.put<User>("/v1/profile", form)).data,
    onSuccess: (u) => {
      setUser(u);
      setLang(u.language);
      toast.success("Profile updated");
    },
  });

  if (!user) return null;

  function toggleCrop(c: string, on: boolean) {
    setForm((f) => ({ ...f, crops: on ? [...new Set([...f.crops, c])] : f.crops.filter((x) => x !== c) }));
  }

  async function exportMine() {
    setExporting(true);
    try {
      await downloadFile("/v1/history/export", "agrivision-history.csv");
      toast.success("Your data was exported as CSV");
    } catch (e) {
      toast.error(`Couldn't export: ${errorMessage(e)}`);
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader title={t("profile.title", "My profile")} description="Your details and the crops you monitor." />

      <Card className="flex items-center gap-4 p-5">
        <Avatar name={user.full_name || user.email} className="size-14 text-lg" />
        <div className="min-w-0">
          <div className="truncate font-display text-lg font-semibold">{user.full_name || "Unnamed farmer"}</div>
          <div className="truncate text-sm text-muted-foreground">{user.email}</div>
        </div>
      </Card>

      <Card>
        <CardHeader title="Edit profile" icon={<UserRound />} />
        <CardBody>
          <form
            className="space-y-5"
            onSubmit={(e: FormEvent) => {
              e.preventDefault();
              save.mutate();
            }}
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField label="Full name">
                {(p) => <Input {...p} autoComplete="name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} icon={<UserRound />} />}
              </FormField>
              <FormField label="Region">
                {(p) => <Input {...p} value={form.region} onChange={(e) => setForm({ ...form, region: e.target.value })} placeholder="Maharashtra" icon={<MapPin />} />}
              </FormField>
              <FormField label={t("common.language", "Language")} className="sm:col-span-2">
                {(p) => (
                  <Select id={p.id} aria-label="Language" value={form.language} onValueChange={(v) => setForm({ ...form, language: v as Lang })} options={LANGS.map((l) => ({ value: l.value, label: l.label }))} />
                )}
              </FormField>
            </div>
            <fieldset className="space-y-2">
              <legend className="text-sm font-medium">Crops monitored</legend>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
                {PROFILE_CROPS.map((c) => (
                  <label key={c} className="glass-flat flex cursor-pointer items-center gap-2 rounded-xl px-3 py-2 text-sm capitalize">
                    <Checkbox checked={form.crops.includes(c)} onCheckedChange={(on) => toggleCrop(c, on)} aria-label={c} />
                    {c}
                  </label>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">If none are ticked, tomato is saved by default.</p>
            </fieldset>
            {save.isError && (
              <p role="alert" className="rounded-xl border border-danger/30 bg-danger/[0.07] px-3 py-2 text-sm text-danger">
                {errorMessage(save.error)}
              </p>
            )}
            <Button type="submit" size="lg" className="w-full" loading={save.isPending}>
              <Save /> {t("common.save", "Save profile")}
            </Button>
          </form>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Account" />
        <CardBody className="space-y-4">
          <KeyValueList
            items={[
              { label: "Email", value: user.email },
              { label: "Role", value: <span className="capitalize">{user.role}</span> },
              { label: "Phone", value: user.phone || "Not set" },
              { label: "Member since", value: formatDate(user.created_at) },
            ]}
          />
          <div className="grid gap-2 sm:grid-cols-2">
            <Button variant="secondary" magnetic={false} loading={exporting} onClick={exportMine}>
              <Download /> My data (CSV)
            </Button>
            <Button
              variant="outline"
              magnetic={false}
              className="text-danger"
              onClick={() => {
                logout();
                navigate("/");
              }}
            >
              <LogOut /> {t("common.signout", "Sign out")}
            </Button>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
