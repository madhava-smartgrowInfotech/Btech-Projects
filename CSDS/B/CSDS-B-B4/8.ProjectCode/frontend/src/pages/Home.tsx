import { useAuth } from "@/lib/auth";
import { formatINR } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { PageHeader } from "@/components/common/States";

export default function Home() {
  const { user } = useAuth();
  const { t } = useI18n();
  if (!user) return null;
  return (
    <div>
      <PageHeader title={user.full_name} subtitle={user.upi_id} />
      <div className="surface p-6">
        <p className="text-sm text-muted-foreground">{t("common.sandbox")}</p>
        <p className="mt-2 font-display text-4xl font-semibold tabular">{formatINR(user.balance)}</p>
      </div>
    </div>
  );
}
