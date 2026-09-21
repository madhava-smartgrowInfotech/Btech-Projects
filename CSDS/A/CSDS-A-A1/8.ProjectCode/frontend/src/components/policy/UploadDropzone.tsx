import { FileUp, Loader2, UploadCloud, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useRef, useState, type DragEvent } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { errorMessage } from "@/lib/api";
import { useUploadPolicy } from "@/lib/queries";
import type { Policy } from "@/lib/types";
import { cn, formatBytes } from "@/lib/utils";

const MAX_MB = 25;

export function UploadDropzone({ onUploaded }: { onUploaded?: (policy: Policy) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState("");
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const upload = useUploadPolicy();

  function pick(f: File | undefined | null) {
    setError(null);
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".pdf") && f.type !== "application/pdf") {
      setError("Please choose a PDF file - your policy wording document.");
      return;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      setError(`This file is ${formatBytes(f.size)}. The limit is ${MAX_MB} MB.`);
      return;
    }
    setFile(f);
    setName(
      f.name
        .replace(/\.pdf$/i, "")
        .replace(/[_-]+/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase()),
    );
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    pick(e.dataTransfer.files?.[0]);
  }

  async function submit() {
    if (!file) return;
    setProgress(0);
    try {
      const policy = await upload.mutateAsync({ file, name: name.trim() || undefined, onProgress: setProgress });
      toast.success("Policy uploaded", {
        description:
          policy.document.status === "ready" ? "This document was already processed - it's ready." : "We're reading it now. This takes about a minute.",
      });
      setFile(null);
      setName("");
      onUploaded?.(policy);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <div className="space-y-3">
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-6 py-8 text-center transition-colors",
          dragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-muted/40",
        )}
        aria-label="Upload a policy PDF"
      >
        <motion.div animate={dragging ? { scale: 1.1, y: -4 } : { scale: 1, y: 0 }} className="rounded-full bg-accent p-3 text-accent-foreground">
          <UploadCloud className="size-6" />
        </motion.div>
        <div className="text-sm font-medium">Drop your policy wording PDF here, or click to browse</div>
        <div className="text-xs text-muted-foreground">PDF with selectable text · up to {MAX_MB} MB</div>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="sr-only"
          onChange={(e) => {
            pick(e.target.files?.[0]);
            e.target.value = "";
          }}
        />
      </div>

      <AnimatePresence>
        {file && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="space-y-3 rounded-xl border bg-card p-4">
              <div className="flex items-center gap-3">
                <FileUp className="size-5 shrink-0 text-primary" />
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium">{file.name}</div>
                  <div className="text-xs text-muted-foreground">{formatBytes(file.size)}</div>
                </div>
                <Button variant="ghost" size="icon-sm" onClick={() => setFile(null)} aria-label="Remove file" disabled={upload.isPending}>
                  <X />
                </Button>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="policy-name">Name in your library</Label>
                <Input id="policy-name" value={name} onChange={(e) => setName(e.target.value)} maxLength={200} />
              </div>
              {upload.isPending && <Progress value={progress} aria-label="Upload progress" />}
              <Button onClick={submit} disabled={upload.isPending} className="w-full sm:w-auto">
                {upload.isPending ? <Loader2 className="animate-spin" /> : <UploadCloud />}
                {upload.isPending ? `Uploading… ${progress}%` : "Upload and analyse"}
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
