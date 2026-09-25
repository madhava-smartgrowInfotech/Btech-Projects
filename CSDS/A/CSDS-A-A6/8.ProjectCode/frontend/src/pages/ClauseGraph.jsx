import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { contractsApi, getErrorMessage } from "../api.js";
import { LoadingState, ErrorState } from "../components/StatusStates.jsx";

const WIDTH = 640;
const HEIGHT = 480;
const RADIUS = 190;

export default function ClauseGraph() {
  const { id } = useParams();
  const [graph, setGraph] = useState(null);
  const [error, setError] = useState("");
  const [hovered, setHovered] = useState(null);

  function load() {
    setError("");
    setGraph(null);
    contractsApi
      .getGraph(id)
      .then((res) => setGraph(res.data))
      .catch((err) => setError(getErrorMessage(err)));
  }

  useEffect(load, [id]);

  const positions = useMemo(() => {
    if (!graph) return {};
    const cx = WIDTH / 2;
    const cy = HEIGHT / 2;
    const n = graph.nodes.length || 1;
    const map = {};
    graph.nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / n - Math.PI / 2;
      map[node.id] = { x: cx + RADIUS * Math.cos(angle), y: cy + RADIUS * Math.sin(angle) };
    });
    return map;
  }, [graph]);

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!graph) return <LoadingState label="Loading clause graph..." />;

  return (
    <div className="py-6">
      <Link to={`/contracts/${id}`} className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-brand-600">
        <ArrowLeft className="h-4 w-4" /> Back to report
      </Link>
      <h1 className="mt-4 text-2xl font-semibold text-slate-900">Clause graph</h1>
      <p className="mt-1 text-sm text-slate-600">
        Each node is a clause. Red nodes triggered a predatory-clause rule. Lines connect clauses whose
        rules form a risky combination - dangerous together even if each clause looks fine alone.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-4 lg:col-span-2">
          <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="w-full">
            {graph.edges.map((edge, i) => {
              const a = positions[edge.source];
              const b = positions[edge.target];
              if (!a || !b) return null;
              return (
                <line
                  key={i}
                  x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                  stroke={hovered === edge.combo_id ? "#dc2626" : "#f59e0b"}
                  strokeWidth={hovered === edge.combo_id ? 3 : 2}
                  strokeDasharray="6 4"
                  onMouseEnter={() => setHovered(edge.combo_id)}
                  onMouseLeave={() => setHovered(null)}
                />
              );
            })}
            {graph.nodes.map((node) => {
              const pos = positions[node.id];
              if (!pos) return null;
              return (
                <g key={node.id}>
                  <circle
                    cx={pos.x} cy={pos.y} r={16}
                    fill={node.risky ? "#ef4444" : "#22c55e"}
                    stroke="#fff" strokeWidth={2}
                  />
                  <title>{`${node.clause_type}: ${node.text_preview}`}</title>
                </g>
              );
            })}
          </svg>
          <div className="mt-2 flex gap-4 text-xs text-slate-500">
            <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-full bg-red-500" /> Flagged clause</span>
            <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-full bg-green-500" /> Clean clause</span>
            <span className="flex items-center gap-1"><span className="h-3 border-t-2 border-dashed border-amber-500" /> Risky combination</span>
          </div>
        </div>

        <div>
          <h2 className="font-semibold text-slate-900">Risky combinations found</h2>
          {graph.risky_combinations.length === 0 && (
            <p className="mt-2 text-sm text-slate-500">None detected for this contract.</p>
          )}
          <ul className="mt-2 space-y-3">
            {graph.risky_combinations.map((combo) => (
              <li
                key={combo.combo_id}
                onMouseEnter={() => setHovered(combo.combo_id)}
                onMouseLeave={() => setHovered(null)}
                className={`rounded-lg border p-3 text-sm transition-colors ${
                  hovered === combo.combo_id ? "border-red-400 bg-red-50" : "border-amber-200 bg-amber-50"
                }`}
              >
                <p className="font-medium text-amber-900">{combo.rule_ids.join(" + ")}</p>
                <p className="mt-1 text-amber-800">{combo.reason}</p>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
