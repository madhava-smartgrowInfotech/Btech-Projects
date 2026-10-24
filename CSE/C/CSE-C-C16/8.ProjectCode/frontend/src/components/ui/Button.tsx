import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";
import { Slot } from "radix-ui";
import { forwardRef, type ButtonHTMLAttributes } from "react";

import { MagneticButton } from "@/components/motion/MagneticButton";
import { cn } from "@/lib/utils";

export const buttonVariants = cva(
  "relative inline-flex shrink-0 select-none items-center justify-center gap-2 whitespace-nowrap rounded-xl font-medium transition-[background,box-shadow,color,border-color,transform,opacity] duration-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98] [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        primary:
          "bg-grad-primary text-white shadow-[0_8px_24px_-8px_rgba(34,160,107,0.7),inset_0_1px_0_rgba(255,255,255,0.35)] hover:shadow-[0_12px_32px_-8px_rgba(34,160,107,0.85),0_0_0_1px_rgba(255,255,255,0.15),inset_0_1px_0_rgba(255,255,255,0.4)] hover:brightness-110",
        secondary:
          "glass text-foreground hover:bg-[var(--glass-hover)] hover:border-[color-mix(in_srgb,var(--violet)_45%,var(--glass-border))]",
        ghost: "text-muted-foreground hover:bg-muted hover:text-foreground",
        danger:
          "bg-grad-danger text-white shadow-[0_8px_24px_-10px_rgba(244,63,94,0.7),inset_0_1px_0_rgba(255,255,255,0.3)] hover:brightness-110",
        outline:
          "border border-[var(--glass-border)] bg-transparent text-foreground hover:border-[color-mix(in_srgb,var(--violet)_55%,transparent)] hover:bg-accent",
        link: "h-auto px-0 text-violet-ink underline-offset-4 hover:underline",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-4 text-sm",
        lg: "h-12 px-6 text-base",
        icon: "size-10",
        "icon-sm": "size-8 rounded-lg",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
  /** Lean toward the cursor. On by default for primary buttons. */
  magnetic?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant, size, asChild, loading, magnetic, disabled, children, ...props },
  ref,
) {
  const Comp = asChild ? Slot.Root : "button";
  const button = (
    <Comp
      ref={ref}
      className={cn(buttonVariants({ variant, size }), variant === "link" && "h-auto px-0", className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {asChild ? (
        children
      ) : (
        <>
          {loading && <Loader2 className="animate-spin" />}
          {children}
        </>
      )}
    </Comp>
  );
  const isMagnetic = magnetic ?? (variant == null || variant === "primary");
  if (!isMagnetic) return button;
  // carry width utilities to the wrapper so full-width buttons stay full width
  const widths = (className ?? "").split(/\s+/).filter((c) => /^((sm|md|lg):)?(w-full|w-auto|flex-1)$/.test(c));
  return (
    <MagneticButton disabled={disabled || loading} strength={size === "lg" ? 0.3 : 0.18} className={widths.join(" ") || undefined}>
      {button}
    </MagneticButton>
  );
});

export const IconButton = forwardRef<HTMLButtonElement, ButtonProps & { label: string }>(function IconButton(
  { label, variant = "ghost", size = "icon", ...props },
  ref,
) {
  return <Button ref={ref} variant={variant} size={size} aria-label={label} title={label} magnetic={false} {...props} />;
});
