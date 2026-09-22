import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { Flag, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { api, apiError } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

export function ReportButton({ upi, category, className }: { upi: string; category: string; className?: string }) {
  const { t, tx } = useI18n();
  const [done, setDone] = useState(false);
  const report = useMutation({
    mutationFn: async () => (await api.post("/reports", { upi_id: upi, category, source: "payment" })).data,
    onSuccess: () => {
      setDone(true);
      toast.success(t("report.thanks"));
    },
    onError: (err) => toast.error(tx(`error.${apiError(err).code}`, apiError(err).message)),
  });
  return (
    <Button variant="outline" size="lg" className={className} disabled={done || report.isPending} onClick={() => report.mutate()}>
      {report.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Flag className="mr-2 h-4 w-4" />}
      {done ? t("report.done") : t("report.button")}
    </Button>
  );
}

export function BackHome() {
  const { t } = useI18n();
  return (
    <Button asChild size="lg" className="flex-1">
      <Link to="/app">{t("common.done")}</Link>
    </Button>
  );
}
