import { useEffect, useState } from "react";
import { evalApi, getErrorMessage } from "../api.js";
import { LoadingState, ErrorState } from "../components/StatusStates.jsx";

export default function Evaluation() {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState("");

  function load() {
    setError("");
    setMetrics(null);
    evalApi
      .getMetrics()
      .then((res) => setMetrics(res.data))
      .catch((err) => setError(getErrorMessage(err)));
  }

  useEffect(load, []);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!metrics) return <LoadingState label="Loading evaluation results..." />;

  return (
    <div className="py-6">
      <h1 className="text-2xl font-semibold text-slate-900">Evaluation</h1>
      <p className="mt-1 text-sm text-slate-600">
        Clause classification is scored on a held-out CUAD sample; predatory-clause detection is scored
        separately on a curated Indian contract-law test set. Regenerate with{" "}
        <code className="rounded bg-slate-100 px-1">python ml/eval.py</code>.
      </p>

      {!metrics.available && (
        <div className="mt-6 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {metrics.message}
        </div>
      )}

      {metrics.available && (
        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h2 className="font-semibold text-slate-900">Predatory-clause detection</h2>
            <p className="mt-1 text-xs text-slate-500">
              {metrics.predatory_detection.num_examples} curated labelled examples, rule-based detector.
            </p>
            <div className="mt-4 grid grid-cols-3 gap-3 text-center">
              <Stat label="Precision" value={metrics.predatory_detection.precision} />
              <Stat label="Recall" value={metrics.predatory_detection.recall} />
              <Stat label="F1" value={metrics.predatory_detection.f1} />
            </div>
            <table className="mt-4 w-full text-xs">
              <thead>
                <tr className="text-left text-slate-500">
                  <th className="py-1">Rule</th>
                  <th className="py-1 text-right">Precision</th>
                  <th className="py-1 text-right">Recall</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(metrics.predatory_detection.per_rule).map(([ruleId, v]) => (
                  <tr key={ruleId} className="border-t border-slate-100">
                    <td className="py-1 text-slate-700">{ruleId}</td>
                    <td className="py-1 text-right">{v.precision}</td>
                    <td className="py-1 text-right">{v.recall}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h2 className="font-semibold text-slate-900">CUAD clause classification</h2>
            {!metrics.cuad_classification ? (
              <p className="mt-3 text-sm text-slate-500">
                Not yet computed - add GEMINI_API_KEY to .env and re-run <code>python ml/eval.py</code>.
              </p>
            ) : (
              <>
                <p className="mt-1 text-xs text-slate-500">
                  {metrics.cuad_classification.num_examples} held-out examples across{" "}
                  {metrics.cuad_classification.num_categories} CUAD categories.
                </p>
                <div className="mt-4 grid grid-cols-2 gap-3 text-center">
                  <Stat label="Top-1 accuracy" value={metrics.cuad_classification.top1_accuracy} />
                  <Stat label="Top-3 accuracy" value={metrics.cuad_classification.top3_accuracy} />
                </div>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded-md bg-slate-50 py-3">
      <p className="text-lg font-semibold text-slate-900">{value}</p>
      <p className="text-xs text-slate-500">{label}</p>
    </div>
  );
}
