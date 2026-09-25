const GRADE_COLORS = {
  A: "bg-green-100 text-green-800 border-green-300",
  B: "bg-lime-100 text-lime-800 border-lime-300",
  C: "bg-yellow-100 text-yellow-800 border-yellow-300",
  D: "bg-orange-100 text-orange-800 border-orange-300",
  F: "bg-red-100 text-red-800 border-red-300",
};

export function GradeBadge({ grade, size = "md" }) {
  const cls = GRADE_COLORS[grade] || "bg-slate-100 text-slate-700 border-slate-300";
  const sizeCls = size === "lg" ? "h-16 w-16 text-3xl" : "h-9 w-9 text-lg";
  return (
    <div className={`flex ${sizeCls} items-center justify-center rounded-full border-2 font-bold ${cls}`}>
      {grade || "-"}
    </div>
  );
}

const SEVERITY_COLORS = {
  high: "bg-red-100 text-red-700 border-red-300",
  medium: "bg-amber-100 text-amber-700 border-amber-300",
  low: "bg-slate-100 text-slate-600 border-slate-300",
  none: "bg-slate-50 text-slate-400 border-slate-200",
};

export function SeverityBadge({ severity }) {
  const cls = SEVERITY_COLORS[severity] || SEVERITY_COLORS.none;
  return (
    <span className={`inline-block rounded-full border px-2 py-0.5 text-xs font-medium capitalize ${cls}`}>
      {severity}
    </span>
  );
}
