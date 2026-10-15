import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, GitGraph } from "lucide-react";
import { Link, useParams } from "react-router";

import { humanize } from "@/components/app/RiskBadges.jsx";
import { SERIES, STATUS } from "@/components/charts/Chart";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/Layout";
import { useBreadcrumb } from "@/components/ui/AppShell";
import { contractsApi } from "@/lib/api.js";
import { keys } from "@/lib/queries.js";

const WIDTH = 640;
const HEIGHT = 480;
const RADIUS = 190;

export default function ClauseGraph() {
  const { id } = useParams();
  const [activeId, setActiveId] = useState(null);

  const query = useQuery({
    queryKey: keys.graph(id),
    queryFn: async () => (await contractsApi.getGraph(id)).data,
  });
  const graph = query.data;

  useBreadcrumb("Clause graph");

  // Nodes sit evenly on a circle, starting at the top.
  const positions = useMemo(() => {
    const map = {};
    const nodes = graph?.nodes ?? [];
    nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / (nodes.length || 1) - Math.PI / 2;
      map[node.id] = { x: WIDTH / 2 + RADIUS * Math.cos(angle), y: HEIGHT / 2 + RADIUS * Math.sin(angle) };
    });
    return map;
  }, [graph]);

  const active = graph?.nodes.find((n) => n.id === activeId) ?? null;
  const activeEdgeIds = new Set(
    (graph?.edges ?? []).filter((e) => e.source === activeId || e.target === activeId).map((e) => e.combo_id),
  );

  const back = (
    <Button asChild variant="ghost" size="sm" className="-ml-3">
      <Link to={`/app/contracts/${id}`}>
        <ArrowLeft /> Back to report
      </Link>
    </Button>
  );

  if (query.isPending) {
    return (
      <div className="space-y-6" role="status" aria-label="Loading clause graph">
        {back}
        <Skeleton className="h-10 w-1/3" />
        <Skeleton className="h-[480px] rounded-2xl" />
      </div>
    );
  }

  if (query.isError) {
    return (
      <div className="space-y-6">
        {back}
        <ErrorState
          error={query.error}
          title="Couldn't load the clause graph"
          hint="Check that the backend is running, then try again."
          onRetry={() => query.refetch()}
        />
      </div>
    );
  }

  if (graph.nodes.length === 0) {
    return (
      <div className="space-y-6">
        {back}
        <EmptyState icon={<GitGraph />} title="No clauses to graph" description="This contract has no extracted clauses yet." />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {back}
      <PageHeader
        eyebrow="Clause graph"
        title="Clauses and risky combinations"
        description="Each node is a clause. Red nodes triggered a predatory-clause rule. A line joins clauses whose rules form a risky combination: dangerous together even if each looks fine alone."
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="p-3 sm:p-5 lg:col-span-2">
          <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="w-full" role="img" aria-label={`Clause graph with ${graph.nodes.length} clauses and ${graph.risky_combinations.length} risky combinations`}>
            {graph.edges.map((edge, i) => {
              const a = positions[edge.source];
              const b = positions[edge.target];
              if (!a || !b) return null;
              const lit = activeId !== null && (edge.source === activeId || edge.target === activeId || activeEdgeIds.has(edge.combo_id));
              return (
                <line
                  key={`${edge.source}-${edge.target}-${i}`}
                  x1={a.x}
                  y1={a.y}
                  x2={b.x}
                  y2={b.y}
                  stroke={STATUS.serious}
                  strokeWidth={lit ? 3 : 1.5}
                  opacity={activeId === null || lit ? 0.85 : 0.2}
                />
              );
            })}

            {graph.nodes.map((node, i) => {
              const p = positions[node.id];
              const isActive = node.id === activeId;
              const fill = node.risky ? STATUS.critical : SERIES[0];
              const label = humanize(node.clause_type);
              const select = () => setActiveId(node.id);
              return (
                <g
                  key={node.id}
                  tabIndex={0}
                  role="button"
                  aria-label={`${label} clause${node.risky ? ", flagged" : ""}. Press Enter to see details.`}
                  onMouseEnter={select}
                  onFocus={select}
                  onClick={select}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      select();
                    }
                  }}
                  className="cursor-pointer outline-none focus-visible:[&>circle]:stroke-cyan"
                >
                  <circle cx={p.x} cy={p.y} r={isActive ? 20 : 15} fill={fill} stroke="white" strokeOpacity={0.5} strokeWidth={2} />
                  <text x={p.x} y={p.y + 32} textAnchor="middle" fontSize={11} className="fill-foreground">
                    {label.length > 16 ? `${label.slice(0, 15)}…` : label}
                  </text>
                </g>
              );
            })}
          </svg>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader title="Selected clause" />
            <CardBody>
              {active ? (
                <div className="space-y-3">
                  <p className="font-medium">{humanize(active.clause_type)}</p>
                  {active.flags.length > 0 && (
                    <p className="text-sm text-muted-foreground">Rules triggered: {active.flags.map(humanize).join(", ")}</p>
                  )}
                  <p className="line-clamp-4 text-sm text-muted-foreground">{active.text_preview}</p>
                  <Button asChild variant="outline" size="sm">
                    <Link to={`/app/contracts/${id}/clauses/${active.id}`}>Open clause</Link>
                  </Button>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Hover over or focus a node to see its clause.</p>
              )}
            </CardBody>
          </Card>

          <Card className="border-warning/35">
            <CardHeader title="Risky combinations found" />
            <CardBody>
              {graph.risky_combinations.length === 0 ? (
                <p className="text-sm text-muted-foreground">None detected for this contract.</p>
              ) : (
                <ul className="space-y-3 text-sm">
                  {graph.risky_combinations.map((combo, i) => (
                    <li key={combo.combo_id ?? i} className="rounded-xl border border-warning/30 bg-warning/10 p-3">
                      {combo.reason || "Risky combination of clauses."}
                    </li>
                  ))}
                </ul>
              )}
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}
