/** Inline form error. Announced to screen readers because it has role="alert". */
export function FormError({ message }) {
  if (!message) return null;
  return (
    <div role="alert" className="rounded-xl border border-danger/30 bg-danger/10 px-3 py-2.5 text-sm text-danger">
      {message}
    </div>
  );
}
