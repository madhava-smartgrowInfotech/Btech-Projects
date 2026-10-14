import { AnimatePresence, motion } from "framer-motion";
import { FileText, UploadCloud, X } from "lucide-react";
import { useEffect, useRef, useState, type DragEvent, type ReactNode } from "react";

import { IconButton } from "@/components/ui/Button";
import { cn, formatBytes } from "@/lib/utils";

/**
 * Drag-and-drop file picker with validation and a preview of the chosen file
 * (a live first-page preview for PDFs on larger screens).
 */
export function FileDrop({
  file,
  onFile,
  accept = "application/pdf,.pdf",
  validate,
  onPick,
  title = "Drop a file here, or click to browse",
  hint,
  disabled,
  children,
  className,
}: {
  file: File | null;
  onFile: (file: File | null) => void;
  accept?: string;
  /** Return an error message to reject the file. */
  validate?: (file: File) => string | null;
  /** Called whenever a new file is picked (accepted or not) - lets the parent clear stale errors. */
  onPick?: () => void;
  title?: ReactNode;
  hint?: ReactNode;
  disabled?: boolean;
  /** Extra controls shown under the preview (name field, submit button…). */
  children?: ReactNode;
  className?: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  useEffect(() => {
    if (!file || !(file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf"))) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  function pick(f: File | undefined | null) {
    setError(null);
    if (!f) return;
    onPick?.();
    const problem = validate?.(f) ?? null;
    if (problem) {
      setError(problem);
      return;
    }
    onFile(f);
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    if (!disabled) pick(e.dataTransfer.files?.[0]);
  }

  return (
    <div className={cn("space-y-3", className)}>
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled}
        aria-label="Choose a file to upload"
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(e) => {
          if (disabled || (e.key !== "Enter" && e.key !== " ")) return;
          e.preventDefault();
          inputRef.current?.click();
        }}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={cn(
          "group relative flex cursor-pointer flex-col items-center justify-center gap-3 overflow-hidden rounded-2xl border-2 border-dashed px-6 py-10 text-center transition-all duration-300",
          dragging
            ? "scale-[1.01] border-[var(--cyan)] bg-cyan/[0.07] shadow-[0_0_40px_-10px_rgba(34,211,238,0.6)]"
            : "border-[var(--glass-border)] bg-[var(--glass)] hover:border-[color-mix(in_srgb,var(--violet)_60%,transparent)]",
          disabled && "pointer-events-none opacity-60",
        )}
      >
        <div className="pointer-events-none absolute inset-0 bg-grad-soft opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
        <motion.div
          animate={dragging ? { scale: 1.15, y: -6, rotate: -4 } : { scale: 1, y: 0, rotate: 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 18 }}
          className="relative grid size-14 place-items-center rounded-2xl bg-grad-primary text-white shadow-[0_10px_30px_-10px_rgba(124,92,255,0.8)]"
        >
          <UploadCloud className="size-6" />
        </motion.div>
        <div className="relative text-sm font-medium">{dragging ? "Release to add the file" : title}</div>
        {hint && <div className="relative text-xs text-muted-foreground">{hint}</div>}
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          className="sr-only"
          tabIndex={-1}
          onChange={(e) => {
            pick(e.target.files?.[0]);
            e.target.value = "";
          }}
        />
      </div>

      <AnimatePresence initial={false}>
        {file && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="glass flex flex-col gap-4 rounded-2xl p-4 sm:flex-row">
              {preview && (
                <div className="relative hidden h-40 w-32 shrink-0 overflow-hidden rounded-xl border border-[var(--glass-border)] bg-white sm:block">
                  <iframe title="File preview" src={`${preview}#toolbar=0&navpanes=0&view=FitH`} className="pointer-events-none h-[200%] w-[200%] origin-top-left scale-50" tabIndex={-1} />
                </div>
              )}
              <div className="min-w-0 flex-1 space-y-3">
                <div className="flex items-center gap-3">
                  <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-grad-soft text-violet-ink">
                    <FileText className="size-5" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">{file.name}</div>
                    <div className="text-xs text-muted-foreground">{formatBytes(file.size)}</div>
                  </div>
                  <IconButton label="Remove file" size="icon-sm" onClick={() => onFile(null)} disabled={disabled}>
                    <X />
                  </IconButton>
                </div>
                {children}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {error && (
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      )}
    </div>
  );
}
