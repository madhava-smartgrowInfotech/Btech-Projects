import { X } from "lucide-react";
import { Dialog } from "radix-ui";
import { useState, type ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

const overlayCls =
  "fixed inset-0 z-[60] bg-[var(--overlay)] backdrop-blur-sm data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=closed]:animate-out data-[state=closed]:fade-out-0";

/** Centered glass dialog. Radix traps focus, closes on Escape and restores focus on close. */
export function Modal({
  open,
  onOpenChange,
  title,
  description,
  children,
  footer,
  className,
  trigger,
}: {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  title: ReactNode;
  description?: ReactNode;
  children?: ReactNode;
  footer?: ReactNode;
  className?: string;
  trigger?: ReactNode;
}) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      {trigger && <Dialog.Trigger asChild>{trigger}</Dialog.Trigger>}
      <Dialog.Portal>
        <Dialog.Overlay className={overlayCls} />
        <Dialog.Content
          className={cn(
            "glass-strong fixed left-1/2 top-1/2 z-[61] flex max-h-[calc(100dvh-2rem)] w-[calc(100vw-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-3xl bg-popover data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95 data-[state=open]:slide-in-from-bottom-2 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95",
            className,
          )}
        >
          <div className="flex items-start justify-between gap-4 px-6 pt-6">
            <div className="min-w-0 space-y-1">
              <Dialog.Title className="font-display text-lg font-semibold">{title}</Dialog.Title>
              {description ? (
                <Dialog.Description className="text-sm text-muted-foreground">{description}</Dialog.Description>
              ) : (
                <Dialog.Description className="sr-only">{typeof title === "string" ? title : "Dialog"}</Dialog.Description>
              )}
            </div>
            <Dialog.Close asChild>
              <Button variant="ghost" size="icon-sm" aria-label="Close" magnetic={false}>
                <X />
              </Button>
            </Dialog.Close>
          </div>
          {children && <div className="scrollbar-thin min-h-0 flex-1 overflow-y-auto px-6 py-4">{children}</div>}
          {footer && <div className="flex flex-wrap justify-end gap-2 border-t border-[var(--glass-border)] px-6 py-4">{footer}</div>}
          {!children && !footer && <div className="pb-6" />}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

/** Confirmation dialog for destructive actions. Keeps itself open while `onConfirm` runs. */
export function ConfirmModal({
  trigger,
  title,
  description,
  confirmLabel = "Delete",
  onConfirm,
  open: openProp,
  onOpenChange,
}: {
  trigger?: ReactNode;
  title: string;
  description: ReactNode;
  confirmLabel?: string;
  onConfirm: () => Promise<unknown> | void;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}) {
  const [inner, setInner] = useState(false);
  const [busy, setBusy] = useState(false);
  const open = openProp ?? inner;
  const setOpen = onOpenChange ?? setInner;
  return (
    <Modal
      open={open}
      onOpenChange={(v) => !busy && setOpen(v)}
      trigger={trigger}
      title={title}
      description={description}
      footer={
        <>
          <Button variant="secondary" onClick={() => setOpen(false)} disabled={busy}>
            Cancel
          </Button>
          <Button
            variant="danger"
            loading={busy}
            onClick={async () => {
              setBusy(true);
              try {
                await onConfirm();
                setOpen(false);
              } finally {
                setBusy(false);
              }
            }}
          >
            {confirmLabel}
          </Button>
        </>
      }
    />
  );
}

/** Side panel (right by default; left for navigation). Same focus/Escape behaviour as Modal. */
export function Drawer({
  open,
  onOpenChange,
  title,
  description,
  side = "right",
  children,
  className,
  hideTitle,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: ReactNode;
  description?: ReactNode;
  side?: "left" | "right";
  children: ReactNode;
  className?: string;
  hideTitle?: boolean;
}) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className={overlayCls} />
        <Dialog.Content
          className={cn(
            "glass-strong fixed inset-y-0 z-[61] flex w-[min(100vw,28rem)] flex-col bg-popover shadow-2xl data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=open]:duration-300 data-[state=closed]:duration-200",
            side === "right"
              ? "right-0 rounded-l-3xl data-[state=open]:slide-in-from-right data-[state=closed]:slide-out-to-right"
              : "left-0 rounded-r-3xl data-[state=open]:slide-in-from-left data-[state=closed]:slide-out-to-left",
            className,
          )}
        >
          <div className={cn("flex items-start justify-between gap-3 px-5 pt-5", hideTitle && "absolute right-0 top-0 z-10")}>
            <div className={cn("min-w-0 space-y-1", hideTitle && "sr-only")}>
              <Dialog.Title className="font-display text-lg font-semibold">{title}</Dialog.Title>
              <Dialog.Description className={cn("text-sm text-muted-foreground", !description && "sr-only")}>
                {description ?? (typeof title === "string" ? title : "Panel")}
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <Button variant="ghost" size="icon-sm" aria-label="Close" magnetic={false}>
                <X />
              </Button>
            </Dialog.Close>
          </div>
          <div className="scrollbar-thin min-h-0 flex-1 overflow-y-auto p-5">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
