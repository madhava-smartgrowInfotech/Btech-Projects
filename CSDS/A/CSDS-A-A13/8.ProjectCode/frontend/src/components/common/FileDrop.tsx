import { useRef, useState, type DragEvent, type KeyboardEvent } from "react";
import { FileSpreadsheet, UploadCloud } from "lucide-react";
import { cn } from "@/lib/utils";

export function FileDrop({
  onFile,
  accept = ".csv,.xlsx",
  disabled,
  hint,
}: {
  onFile: (file: File) => void;
  accept?: string;
  disabled?: boolean;
  hint?: string;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  function pick(files: FileList | null) {
    const file = files?.[0];
    if (file) onFile(file);
    if (input.current) input.current.value = "";
  }

  function onDrop(event: DragEvent) {
    event.preventDefault();
    setOver(false);
    if (!disabled) pick(event.dataTransfer.files);
  }

  function onKey(event: KeyboardEvent) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      input.current?.click();
    }
  }

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-disabled={disabled}
      aria-label="Choose a file to import"
      onClick={() => !disabled && input.current?.click()}
      onKeyDown={onKey}
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={onDrop}
      className={cn(
        "group flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors",
        over ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-accent/40",
        disabled && "pointer-events-none opacity-60",
      )}
    >
      <div className="flex size-12 items-center justify-center rounded-xl bg-primary/10 text-primary transition-transform group-hover:-translate-y-0.5">
        {over ? <FileSpreadsheet className="size-6" /> : <UploadCloud className="size-6" />}
      </div>
      <div>
        <div className="text-sm font-medium">
          <span className="text-primary">Choose a file</span> or drag it here
        </div>
        <div className="mt-1 text-xs text-muted-foreground">{hint ?? "Excel (.xlsx) or CSV, up to 15 MB"}</div>
      </div>
      <input ref={input} type="file" accept={accept} className="hidden" onChange={(e) => pick(e.target.files)} />
    </div>
  );
}
