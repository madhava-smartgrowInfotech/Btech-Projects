import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, ScrollText, Scale, Sparkles } from "lucide-react";
import { contractsApi, getErrorMessage } from "../api.js";
import { LoadingState, ErrorState } from "../components/StatusStates.jsx";
import { SeverityBadge } from "../components/Badges.jsx";

export default function ClauseDetail() {
  const { id, clauseId } = useParams();
  const [clause, setClause] = useState(null);
  const [error, setError] = useState("");

  function load() {
    setError("");
    setClause(null);
    contractsApi
      .getClause(id, clauseId)
      .then((res) => setClause(res.data))
      .catch((err) => setError(getErrorMessage(err)));
  }

  useEffect(load, [id, clauseId]);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!clause) return <LoadingState label="Loading clause..." />;

  return (
    <div className="py-6">
      <Link to={`/contracts/${id}`} className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-brand-600">
        <ArrowLeft className="h-4 w-4" /> Back to report
      </Link>

      <div className="mt-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-900">
          Clause {clause.index_in_doc + 1}: {clause.clause_type}
        </h1>
        <span className="text-xs text-slate-500">
          page {clause.page_number} - classified via {clause.classification_method} ({Math.round(clause.classification_confidence * 100)}% confidence)
        </span>
      </div>

      <section className="mt-4 rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
          <ScrollText className="h-4 w-4" /> Clause text
        </h2>
        <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-slate-700">{clause.text}</p>
      </section>

      {clause.flags.length === 0 && (
        <p className="mt-6 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
          No predatory-clause rules were triggered for this clause.
        </p>
      )}

      {clause.flags.map((flag) => (
        <section key={flag.id} className="mt-6 rounded-lg border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-slate-900">{flag.rule_label}</h2>
            <SeverityBadge severity={flag.severity} />
          </div>

          <div className="mt-3">
            <h3 className="flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
              <Scale className="h-3.5 w-3.5" /> Why this is flagged
            </h3>
            <p className="mt-1 text-sm text-slate-700">{flag.reason}</p>
          </div>

          {flag.provision && (
            <div className="mt-3">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Provision</h3>
              <p className="mt-1 rounded bg-slate-100 px-3 py-2 text-sm italic text-slate-700">"{flag.provision}"</p>
            </div>
          )}

          {flag.safer_wording && (
            <div className="mt-3">
              <h3 className="flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <Sparkles className="h-3.5 w-3.5" /> Safer wording
              </h3>
              <p className="mt-1 rounded bg-brand-50 px-3 py-2 text-sm text-brand-900">{flag.safer_wording}</p>
            </div>
          )}
        </section>
      ))}
    </div>
  );
}
