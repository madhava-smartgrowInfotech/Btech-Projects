import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, ClipboardCheck, FileText, Library, Plus, UploadCloud } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/Feedback";
import { FormField, Input } from "@/components/ui/Field";
import { FileDrop } from "@/components/ui/FileDrop";
import { PageHeader } from "@/components/ui/Layout";
import { toast } from "@/components/ui/Toast";
import { api, errorMessage, type UploadResult } from "@/lib/api";
import { keys } from "@/lib/queries";

const MAX_BYTES = 16 * 1024 * 1024;
const EXTENSIONS = ["pdf", "docx", "txt"];

function validate(file: File) {
  const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
  if (!EXTENSIONS.includes(ext)) return "Unsupported file type. Please upload a PDF, DOCX or TXT file.";
  if (file.size > MAX_BYTES) return "That file is larger than 16 MB. Split it or upload a smaller one.";
  if (file.size === 0) return "That file is empty.";
  return null;
}

export default function Upload() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [subject, setSubject] = useState("");
  const [result, setResult] = useState<UploadResult | null>(null);

  const upload = useMutation({
    mutationFn: async () => {
      const form = new FormData();
      form.append("document", file as File);
      form.append("subject", subject.trim());
      return (await api.post<UploadResult>("/documents", form)).data;
    },
    onSuccess: (data) => {
      setResult(data);
      setFile(null);
      setSubject("");
      void qc.invalidateQueries({ queryKey: keys.documents });
      void qc.invalidateQueries({ queryKey: keys.dashboard });
      if (data.warning) toast.warning(data.warning);
      else toast.success(`'${data.document.filename}' processed`, { description: `${data.topics_count} topics detected, ${data.chunks_count} chunks indexed.` });
    },
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (file) upload.mutate();
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        eyebrow="Upload"
        title="Add study material"
        description="Syllabi, lecture notes, timetables or question banks. The text is extracted, split into passages and scanned for topics."
      />

      {result && (
        <Card className="border-success/30" role="status" aria-live="polite">
          <CardHeader
            icon={result.warning ? <AlertTriangle /> : <CheckCircle2 />}
            title={result.warning ? "Uploaded, but nothing readable was found" : "Document processed"}
            description={
              result.warning ??
              `'${result.document.filename}' - ${result.topics_count} topics detected, ${result.chunks_count} chunks indexed.`
            }
          />
          <CardBody className="space-y-4">
            {result.document.topics.length > 0 && (
              <div className="flex flex-wrap gap-1.5" aria-label="Detected topics">
                {result.document.topics.map((t) => (
                  <Badge key={t} tone="cyan">
                    {t}
                  </Badge>
                ))}
              </div>
            )}
            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" size="sm" onClick={() => navigate("/app/documents")}>
                <Library /> View documents
              </Button>
              {!result.warning && (
                <Button size="sm" onClick={() => navigate(`/app/quiz?doc=${result.document.id}`)}>
                  <ClipboardCheck /> Generate quiz
                </Button>
              )}
              <Button variant="ghost" size="sm" onClick={() => setResult(null)}>
                <Plus /> Upload another
              </Button>
            </div>
          </CardBody>
        </Card>
      )}

      <Card>
        <CardHeader icon={<UploadCloud />} title="Choose a file" description="PDF, DOCX or TXT, up to 16 MB." />
        <CardBody>
          <form onSubmit={onSubmit} className="space-y-4">
            <FileDrop
              file={file}
              onFile={setFile}
              accept=".pdf,.docx,.txt"
              validate={validate}
              onPick={() => upload.reset()}
              disabled={upload.isPending}
              title="Drop a file here, or click to browse"
              hint="PDF, DOCX or TXT"
            >
              <FormField label="Subject" hint="Used to group quiz results. Leave blank for General.">
                {(p) => (
                  <Input
                    {...p}
                    name="subject"
                    placeholder="e.g. Data Structures"
                    icon={<FileText />}
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    disabled={upload.isPending}
                  />
                )}
              </FormField>
            </FileDrop>

            {upload.isPending && (
              <div className="space-y-2" role="status">
                <ProgressBar value={0} indeterminate label="Processing document" />
                <p className="text-sm text-muted-foreground">Extracting text, detecting topics and building the search index…</p>
              </div>
            )}
            {upload.isError && (
              <p role="alert" className="rounded-xl border border-danger/30 bg-danger/[0.08] px-3 py-2 text-sm text-danger">
                Upload failed: {errorMessage(upload.error)} Check the file and try again.
              </p>
            )}

            <div className="flex flex-wrap justify-end gap-2">
              <Button asChild variant="ghost">
                <Link to="/app/documents">Cancel</Link>
              </Button>
              <Button type="submit" loading={upload.isPending} disabled={!file}>
                <UploadCloud /> Upload &amp; process
              </Button>
            </div>
          </form>
        </CardBody>
      </Card>
    </div>
  );
}
