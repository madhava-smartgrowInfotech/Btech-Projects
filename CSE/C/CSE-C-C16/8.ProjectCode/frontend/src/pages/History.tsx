import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Camera, Download, FileText, Plus, SearchX, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router";

import { ResultCard } from "@/components/agri/bits";
import { Button, IconButton } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { CardsSkeleton, EmptyState, ErrorState } from "@/components/ui/Feedback";
import { SearchField } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { ConfirmModal } from "@/components/ui/Overlay";
import { Select } from "@/components/ui/Select";
import { Segmented } from "@/components/ui/Toggles";
import { toast } from "@/components/ui/Toast";
import { api, downloadFile, errorMessage, type ResultSummary } from "@/lib/api";
import { useLang } from "@/lib/i18n";
import { useHistory } from "@/lib/queries";

const PAGE = 12;

export default function History() {
  const { t } = useLang();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [q, setQ] = useState("");
  const [crop, setCrop] = useState("");
  const [disease, setDisease] = useState("");
  const [page, setPage] = useState(0);
  const [toDelete, setToDelete] = useState<ResultSummary | null>(null);
  const [exporting, setExporting] = useState(false);

  // wait for a pause in typing before asking the API
  useEffect(() => {
    const id = setTimeout(() => {
      setQ(search.trim());
      setPage(0);
    }, 300);
    return () => clearTimeout(id);
  }, [search]);

  const query = useHistory({ q, crop, disease, limit: PAGE, offset: page * PAGE });
  const data = query.data;
  const pages = data ? Math.max(1, Math.ceil(data.total_count / PAGE)) : 1;
  const filtered = Boolean(q || crop || disease);

  const remove = useMutation({
    mutationFn: async (id: string) => api.delete(`/v1/history/${id}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["history"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["analytics"] });
      toast.success("Record deleted");
    },
  });

  async function exportAll() {
    setExporting(true);
    try {
      await downloadFile("/v1/history/export", "agrivision-history.csv");
      toast.success("History exported as CSV");
    } catch (e) {
      toast.error(`Couldn't export: ${errorMessage(e)}`);
    } finally {
      setExporting(false);
    }
  }

  async function pdf(r: ResultSummary) {
    try {
      await downloadFile(`/v1/history/${r.result_id}/export?format=pdf`, `agrivision-${r.result_id.slice(0, 8)}.pdf`);
    } catch (e) {
      toast.error(`Couldn't export the PDF: ${errorMessage(e)}`);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("history.title", "Detection history")}
        description={data ? `${data.all_count} saved scan${data.all_count === 1 ? "" : "s"}` : "Every leaf you have scanned."}
        actions={
          <>
            <Button variant="secondary" magnetic={false} loading={exporting} onClick={exportAll} disabled={!data?.all_count}>
              <Download /> {t("common.exportCsv", "Export CSV")}
            </Button>
            <Button asChild>
              <Link to="/detect">
                <Plus /> {t("common.newScan", "New scan")}
              </Link>
            </Button>
          </>
        }
      />

      <Card className="grid gap-3 p-4 md:grid-cols-[1fr_14rem_auto] md:items-center">
        <SearchField value={search} onChange={setSearch} label="Search history" placeholder="Search by disease or crop…" />
        <Select
          aria-label="Filter by crop"
          value={crop || "all"}
          onValueChange={(v) => {
            setCrop(v === "all" ? "" : v);
            setPage(0);
          }}
          options={[{ value: "all", label: "All crops" }, ...(data?.crops ?? []).map((c) => ({ value: c, label: c }))]}
        />
        <Segmented
          label="Health filter"
          size="sm"
          value={(disease || "all") as "all" | "diseased" | "healthy"}
          onChange={(v) => {
            setDisease(v === "all" ? "" : v);
            setPage(0);
          }}
          options={[
            { value: "all", label: "All" },
            { value: "diseased", label: "Diseased" },
            { value: "healthy", label: "Healthy" },
          ]}
        />
      </Card>

      {query.isError ? (
        <ErrorState error={query.error} title="Couldn't load your history" onRetry={() => query.refetch()} />
      ) : query.isPending ? (
        <CardsSkeleton count={6} />
      ) : data && data.total_count === 0 ? (
        filtered ? (
          <EmptyState
            icon={<SearchX />}
            title="No records match"
            description="Nothing in your history fits these filters."
            action={
              <Button
                variant="secondary"
                onClick={() => {
                  setSearch("");
                  setCrop("");
                  setDisease("");
                }}
              >
                Clear filters
              </Button>
            }
          />
        ) : (
          <EmptyState
            icon={<Camera />}
            title="No scans yet"
            description="Your detections are saved here with their photo, diagnosis and treatment plan."
            action={
              <Button asChild>
                <Link to="/detect">Scan a leaf</Link>
              </Button>
            }
          />
        )
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-busy={query.isFetching}>
            {data?.results.map((r) => (
              <ResultCard
                key={r.result_id}
                r={r}
                footer={
                  <div className="mt-1 flex gap-2">
                    <Button asChild variant="secondary" size="sm" className="flex-1" magnetic={false}>
                      <Link to={`/result/${r.result_id}`}>{t("common.view", "View")}</Link>
                    </Button>
                    <IconButton label={`Download PDF for ${r.predicted_disease}`} variant="secondary" size="icon-sm" onClick={() => pdf(r)}>
                      <FileText />
                    </IconButton>
                    <IconButton label={`Delete record: ${r.predicted_disease}`} variant="secondary" size="icon-sm" className="text-danger" onClick={() => setToDelete(r)}>
                      <Trash2 />
                    </IconButton>
                  </div>
                }
              />
            ))}
          </div>
          {pages > 1 && (
            <div className="flex items-center justify-center gap-3 text-sm text-muted-foreground">
              <Button variant="secondary" size="sm" magnetic={false} disabled={page === 0} onClick={() => setPage(page - 1)}>
                Previous
              </Button>
              <span className="tabular-nums">
                Page {page + 1} of {pages}
              </span>
              <Button variant="secondary" size="sm" magnetic={false} disabled={page >= pages - 1} onClick={() => setPage(page + 1)}>
                Next
              </Button>
            </div>
          )}
        </>
      )}

      <ConfirmModal
        open={Boolean(toDelete)}
        onOpenChange={(o) => !o && setToDelete(null)}
        title="Delete this record?"
        description={toDelete ? `${toDelete.predicted_disease} and its photo will be removed permanently.` : ""}
        confirmLabel="Delete"
        onConfirm={async () => {
          if (!toDelete) return;
          try {
            await remove.mutateAsync(toDelete.result_id);
          } catch (e) {
            toast.error(`Couldn't delete: ${errorMessage(e)}`);
          }
        }}
      />
    </div>
  );
}
