import { useState } from "react";
import { useNavigate } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { FileText, ShieldAlert } from "lucide-react";
import { toast } from "sonner";

import { FormError } from "@/components/app/FormError.jsx";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { FileDrop } from "@/components/ui/FileDrop";
import { ProgressBar } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { contractsApi } from "@/lib/api.js";
import { uploadErrorMessage } from "@/lib/format.js";
import { keys } from "@/lib/queries.js";

const ACCEPT = ".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document";

function validate(file) {
  return /\.(pdf|docx)$/i.test(file.name) ? null : "Only PDF and DOCX files are supported. Convert the file and try again.";
}

export default function Upload() {
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) return;
    setError("");
    setProgress(0);
    setUploading(true);
    try {
      const res = await contractsApi.upload(file, (evt) => {
        if (evt.total) setProgress(Math.round((evt.loaded / evt.total) * 100));
      });
      queryClient.invalidateQueries({ queryKey: keys.contracts });
      toast.success("Contract analysed");
      navigate(`/app/contracts/${res.data.id}`);
    } catch (err) {
      setError(uploadErrorMessage(err));
    } finally {
      setUploading(false);
    }
  }

  // Once the bytes are sent the server still runs classification and explanations, so the bar switches to indeterminate.
  const analysing = uploading && progress >= 100;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader
        eyebrow="New analysis"
        title="Upload a contract"
        description="PDF or DOCX. ClauseGuard splits it into clauses, classifies each one, flags predatory terms and scores its complexity."
      />

      <Card>
        <CardHeader title="Choose the contract" description="Scanned images without text cannot be read. Use the original PDF or DOCX." icon={<FileText />} />
        <CardBody>
          <form onSubmit={handleSubmit} className="space-y-5">
            <FileDrop
              file={file}
              onFile={(f) => {
                setFile(f);
                setError("");
              }}
              accept={ACCEPT}
              validate={validate}
              onPick={() => setError("")}
              title="Drop a contract here, or click to browse"
              hint="PDF or DOCX"
              disabled={uploading}
            />

            {uploading && (
              <div className="space-y-2" aria-live="polite">
                {analysing ? (
                  <ProgressBar indeterminate label="Analysing clauses. This can take up to a minute." />
                ) : (
                  <ProgressBar value={progress} label={`Uploading… ${progress}%`} />
                )}
              </div>
            )}

            <FormError message={error} />

            <div className="flex flex-wrap items-center gap-3">
              <Button type="submit" size="lg" disabled={!file || uploading} loading={uploading}>
                {uploading ? "Analysing…" : error ? "Try again" : "Analyse contract"}
              </Button>
              <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <ShieldAlert className="size-3.5" /> The file is read for analysis and removed from the server afterwards.
              </p>
            </div>
          </form>
        </CardBody>
      </Card>
    </div>
  );
}
