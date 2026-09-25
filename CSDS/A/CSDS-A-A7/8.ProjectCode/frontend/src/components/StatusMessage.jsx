export function Loading({ label = "Loading..." }) {
  return (
    <div className="flex items-center justify-center py-10 text-slate-400 text-sm">
      <div className="animate-spin h-4 w-4 border-2 border-brand-500 border-t-transparent rounded-full mr-2" />
      {label}
    </div>
  );
}

export function ErrorMessage({ message }) {
  if (!message) return null;
  return (
    <div className="bg-red-950/50 border border-red-800 text-red-300 text-sm rounded-lg px-3 py-2 my-2">
      {message}
    </div>
  );
}
