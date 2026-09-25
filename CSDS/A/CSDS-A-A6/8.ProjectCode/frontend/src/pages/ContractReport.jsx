import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { GitGraph, ChevronRight } from "lucide-react";
import { contractsApi, getErrorMessage } from "../api.js";
import { LoadingState, ErrorState } from "../components/StatusStates.jsx";
import { GradeBadge, SeverityBadge } from "../components/Badges.jsx";

export default function ContractReport() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  function load() {
    setError("");
    setReport(null);
    contractsApi
      .get(id)
      .then((res) => setReport(res.data))
      .catch((err) => setError(getErrorMessage(err)));
  }

  useEffect(load, [id]);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!report) return <LoadingState label="Loading report..." />;

  return (
    <div className="py-6">
      <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">{report.filename}</h1>
          <p className="mt-1 text-sm text-slate-500">
            Uploaded {new Date(report.uploaded_at).toLocaleString()}
          </p>
        </div>
        <div className="flex items-center gap-4 rounded-lg border border-slate-200 bg-white px-5 py-3">
          <GradeBadge grade={report.complexity_grade} size="lg" />
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">Complexity</p>
            <p className="text-lg font-semibold text-slate-900">{report.complexity_score}/100</p>
          </div>
        </div>
      </div>

      <div className="mt-4">
        <Link
          to={`/contracts/${id}/graph`}
          className="inline-flex items-center gap-1 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100"
        >
          <GitGraph className="h-4 w-4" /> View clause graph
        </Link>
      </div>

      <section className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Metric label="Readability" value={report.readability_score} hint="Flesch reading ease (higher = easier)" />
        <Metric label="Legalese density" value={`${report.legalese_density}%`} hint="Legal jargon per 100 words" />
        <Metric label="Cross-references" value={report.cross_reference_count} hint="Section/clause references" />
        <Metric label="Avg sentence length" value={report.avg_sentence_length} hint="Words per sentence" />
      </section>

      <section className="mt-8 rounded-lg border border-slate-200 bg-white p-5">
        <h2 className="font-semibold text-slate-900">Plain-language summary</h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-700">{report.plain_summary}</p>
        {report.key_obligations?.length > 0 && (
          <>
            <h3 className="mt-4 text-sm font-semibold text-slate-900">Key obligations</h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
              {report.key_obligations.map((o, i) => (
                <li key={i}>{o}</li>
              ))}
            </ul>
          </>
        )}
      </section>

      {report.combo_flags?.length > 0 && (
        <section className="mt-8 rounded-lg border border-amber-300 bg-amber-50 p-5">
          <h2 className="font-semibold text-amber-900">Risky clause combinations</h2>
          <ul className="mt-2 space-y-2 text-sm text-amber-900">
            {report.combo_flags.map((combo) => (
              <li key={combo.combo_id}>{combo.reason}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="mt-8">
        <h2 className="font-semibold text-slate-900">Clauses ({report.clauses.length})</h2>
        <div className="mt-3 divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
          {report.clauses.map((c) => (
            <Link
              key={c.id}
              to={`/contracts/${id}/clauses/${c.id}`}
              className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-slate-50"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-slate-900">
                  {c.index_in_doc + 1}. {c.clause_type}
                  <span className="ml-2 text-xs font-normal text-slate-400">p.{c.page_number}</span>
                </p>
                <p className="truncate text-xs text-slate-500">{c.text_preview}</p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                {c.flag_count > 0 && <SeverityBadge severity={c.max_severity} />}
                <ChevronRight className="h-4 w-4 text-slate-400" />
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value, hint }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-slate-900">{value}</p>
      <p className="mt-0.5 text-xs text-slate-400">{hint}</p>
    </div>
  );
}
