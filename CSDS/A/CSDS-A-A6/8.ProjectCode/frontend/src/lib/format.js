import { errorMessage } from "./api.js";

/** 0-1 fraction -> "94%". */
export function pct(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return `${Math.round(value * 100)}%`;
}

/** "restraint_of_trade" -> "Restraint of trade". */
export function humanize(key) {
  const text = String(key ?? "").replace(/_/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export function gradeTone(grade) {
  return { A: "success", B: "info", C: "warning", D: "warning", F: "danger" }[grade] ?? "neutral";
}

export function severityTone(severity) {
  return { high: "danger", medium: "warning", low: "info", none: "neutral" }[severity] ?? "neutral";
}

/** Maps an upload failure to a message that says what failed. Server detail is shown when there is one. */
export function uploadErrorMessage(err) {
  if (!err?.response) return "Can't reach the server. Make sure the backend is running, then try again.";
  if (err.response.status >= 500) {
    return "The analysis failed on the server. The AI service may be busy or over its quota. Wait a few minutes, then try again.";
  }
  return errorMessage(err);
}
