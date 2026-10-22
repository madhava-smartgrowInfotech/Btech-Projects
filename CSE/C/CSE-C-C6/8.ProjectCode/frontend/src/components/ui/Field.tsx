import { Eye, EyeOff, Search, X } from "lucide-react";
import {
  forwardRef,
  useId,
  useState,
  type InputHTMLAttributes,
  type ReactNode,
  type TextareaHTMLAttributes,
} from "react";

import { cn } from "@/lib/utils";

export function Label({ htmlFor, children, className }: { htmlFor?: string; children: ReactNode; className?: string }) {
  return (
    <label htmlFor={htmlFor} className={cn("text-sm font-medium text-foreground/90", className)}>
      {children}
    </label>
  );
}

/** Label + control + hint / error, wired with ids so screen readers announce them. */
export function FormField({
  label,
  hint,
  error,
  children,
  className,
  id: idProp,
}: {
  label?: ReactNode;
  hint?: ReactNode;
  error?: ReactNode;
  className?: string;
  id?: string;
  children: (props: { id: string; "aria-describedby"?: string; "aria-invalid"?: boolean }) => ReactNode;
}) {
  const auto = useId();
  const id = idProp ?? auto;
  const describedBy = error ? `${id}-error` : hint ? `${id}-hint` : undefined;
  return (
    <div className={cn("space-y-1.5", className)}>
      {label && <Label htmlFor={id}>{label}</Label>}
      {children({ id, "aria-describedby": describedBy, "aria-invalid": error ? true : undefined })}
      {error ? (
        <p id={`${id}-error`} className="text-xs text-danger" role="alert">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="text-xs text-muted-foreground">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  icon?: ReactNode;
  trailing?: ReactNode;
  wrapperClassName?: string;
}

/** Text input with a gradient border that brightens on focus. */
export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, wrapperClassName, icon, trailing, ...props },
  ref,
) {
  return (
    <div className={cn("field", wrapperClassName)} data-invalid={props["aria-invalid"] ? "true" : undefined}>
      <div className="field-inner flex h-10 items-center gap-2 px-3">
        {icon && <span className="text-muted-foreground [&_svg]:size-4">{icon}</span>}
        <input
          ref={ref}
          className={cn(
            "h-full w-full min-w-0 bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground/70 disabled:cursor-not-allowed disabled:opacity-60",
            className,
          )}
          {...props}
        />
        {trailing}
      </div>
    </div>
  );
});

export const PasswordInput = forwardRef<HTMLInputElement, InputProps>(function PasswordInput(props, ref) {
  const [show, setShow] = useState(false);
  return (
    <Input
      ref={ref}
      type={show ? "text" : "password"}
      {...props}
      trailing={
        <button
          type="button"
          onClick={() => setShow((v) => !v)}
          className="rounded-md p-1 text-muted-foreground transition-colors hover:text-foreground"
          aria-label={show ? "Hide password" : "Show password"}
        >
          {show ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
        </button>
      }
    />
  );
});

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement> & { wrapperClassName?: string }>(
  function Textarea({ className, wrapperClassName, ...props }, ref) {
    return (
      <div className={cn("field", wrapperClassName)} data-invalid={props["aria-invalid"] ? "true" : undefined}>
        <textarea
          ref={ref}
          className={cn(
            "field-inner block min-h-20 w-full resize-y px-3 py-2.5 text-sm text-foreground outline-none placeholder:text-muted-foreground/70",
            className,
          )}
          {...props}
        />
      </div>
    );
  },
);

export function SearchField({
  value,
  onChange,
  placeholder = "Search…",
  label = "Search",
  className,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  label?: string;
  className?: string;
}) {
  return (
    <Input
      type="search"
      aria-label={label}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={(e) => e.key === "Escape" && value && (e.stopPropagation(), onChange(""))}
      placeholder={placeholder}
      icon={<Search />}
      wrapperClassName={className}
      className="[&::-webkit-search-cancel-button]:hidden"
      trailing={
        value ? (
          <button
            type="button"
            onClick={() => onChange("")}
            className="rounded-md p-0.5 text-muted-foreground hover:text-foreground"
            aria-label="Clear search"
          >
            <X className="size-4" />
          </button>
        ) : null
      }
    />
  );
}
