import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ClipboardCheck, FileText, Plus, Trash2, UploadCloud } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router";

import { Badge } from "@/components/ui/Badge";
import { Button, IconButton } from "@/components/ui/Button";
import { CardsSkeleton, EmptyState, ErrorState } from "@/components/ui/Feedback";
import { SearchField } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { ConfirmModal } from "@/components/ui/Overlay";
import { Table, type Column } from "@/components/ui/Table";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage, type Doc } from "@/lib/api";
import { keys } from "@/lib/queries";
import { formatDate } from "@/lib/utils";

const SHOWN_TOPICS = 5;

export default function Documents() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const query = useQuery({ queryKey: keys.documents, queryFn: async () => (await api.get<Doc[]>("/documents")).data });

  const remove = useMutation({
    mutationFn: async (doc: Doc) => {
      await api.delete(`/documents/${doc.id}`);
      return doc;
    },
    onSuccess: (doc) => {
      toast.success("Document removed", { description: doc.filename });
      void qc.invalidateQueries({ queryKey: keys.documents });
      void qc.invalidateQueries({ queryKey: keys.dashboard });
    },
    onError: (e) => toast.error("Couldn't delete the document", { description: errorMessage(e) }),
  });

  const rows = useMemo(() => {
    const needle = search.trim().toLowerCase();
    const all = query.data ?? [];
    if (!needle) return all;
    return all.filter((d) => [d.filename, d.subject, ...d.topics].some((s) => s.toLowerCase().includes(needle)));
  }, [query.data, search]);

  const columns: Column<Doc>[] = [
    {
      key: "filename",
      header: "Document",
      sortValue: (d) => d.filename,
      cell: (d) => (
        <span className="flex min-w-0 items-center gap-2.5">
          <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-grad-soft text-violet-ink">
            <FileText className="size-4" />
          </span>
          <span className="min-w-0 break-words font-medium">{d.filename}</span>
        </span>
      ),
    },
    { key: "subject", header: "Subject", sortValue: (d) => d.subject, cell: (d) => <Badge tone="violet">{d.subject}</Badge> },
    {
      key: "topics",
      header: "Detected topics",
      cell: (d) =>
        d.topics.length === 0 ? (
          <span className="text-muted-foreground">None detected</span>
        ) : (
          <span className="flex flex-wrap gap-1 sm:max-w-xs">
            {d.topics.slice(0, SHOWN_TOPICS).map((t) => (
              <Badge key={t} tone="cyan">
                {t}
              </Badge>
            ))}
            {d.topics.length > SHOWN_TOPICS && <Badge>+{d.topics.length - SHOWN_TOPICS}</Badge>}
          </span>
        ),
    },
    {
      key: "chunks",
      header: "Chunks",
      align: "right",
      sortValue: (d) => d.chunk_count ?? 0,
      cell: (d) => <span className="tabular-nums">{d.chunk_count ?? 0}</span>,
    },
    { key: "uploaded", header: "Uploaded", sortValue: (d) => d.uploaded_at, cell: (d) => <span className="whitespace-nowrap text-muted-foreground">{formatDate(d.uploaded_at, true)}</span> },
    {
      key: "actions",
      header: <span className="sr-only">Actions</span>,
      align: "right",
      cell: (d) => (
        <span className="flex items-center justify-end gap-1.5">
          <Button size="sm" variant="outline" onClick={() => navigate(`/app/quiz?doc=${d.id}`)}>
            <ClipboardCheck /> Generate quiz
          </Button>
          <ConfirmModal
            title="Delete this document?"
            description={`"${d.filename}" and its indexed passages will be removed. Your past quiz results are kept.`}
            confirmLabel="Delete"
            onConfirm={() => remove.mutateAsync(d)}
            trigger={
              <IconButton label={`Delete ${d.filename}`} size="icon-sm" className="text-danger hover:text-danger">
                <Trash2 />
              </IconButton>
            }
          />
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Knowledge repository"
        title="Your documents"
        description="Everything you upload is searchable in Ask and can be turned into a quiz."
        actions={
          <Button asChild>
            <Link to="/app/upload">
              <Plus /> Upload new
            </Link>
          </Button>
        }
      />

      {query.isPending ? (
        <CardsSkeleton count={3} />
      ) : query.isError ? (
        <ErrorState error={query.error} title="Couldn't load your documents" onRetry={() => query.refetch()} />
      ) : query.data.length === 0 ? (
        <EmptyState
          icon={<UploadCloud />}
          title="No documents yet"
          description="Upload your first PDF, DOCX or TXT and its topics will show up here."
          action={
            <Button asChild>
              <Link to="/app/upload">Upload your first document</Link>
            </Button>
          }
        />
      ) : (
        <>
          <SearchField value={search} onChange={setSearch} label="Search documents" placeholder="Search by name, subject or topic…" className="max-w-md" />
          <Table
            caption="Uploaded documents"
            columns={columns}
            rows={rows}
            rowKey={(d) => d.id}
            initialSort={{ key: "uploaded", dir: "desc" }}
            empty={
              <EmptyState
                icon={<FileText />}
                title="No matches"
                description={`Nothing matches "${search}".`}
                action={
                  <Button variant="secondary" onClick={() => setSearch("")}>
                    Clear search
                  </Button>
                }
              />
            }
          />
        </>
      )}
    </div>
  );
}
